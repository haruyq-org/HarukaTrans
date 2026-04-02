from utils.vad import init_vad_model
from utils.osc import OSC
from utils.path import resource_path
from utils.logger import Logger
from utils.mic import MicInput
from config import config

import asyncio
import io
import wave
import numpy as np
import threading

Log = Logger(__name__)

CHANNELS = 1
RATE = 16000
CHUNK_DURATION_MS = 30
CHUNK_SIZE = 512

class Audio:
    def __init__(self, stop_event: threading.Event | None = None) -> None:
        self.model = None
        if config.USE_VAD:
            init_vad_model()
            import onnxruntime
            session_options = onnxruntime.SessionOptions()
            session_options.intra_op_num_threads = max(1, int(config.VAD_THREADS))
            session_options.inter_op_num_threads = 1
            session_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
            session_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL

            self.model = onnxruntime.InferenceSession(
                resource_path("vad/silero_vad.onnx"),
                sess_options=session_options,
                providers=["CPUExecutionProvider"],
            )
            self._vad_state = np.zeros((2, 1, 128), dtype=np.float32)
            self._vad_context = np.zeros((1, 64), dtype=np.float32)
            self._vad_sr = np.array(16000, dtype=np.int64)
            
        self._stop_event = stop_event
        self._closed = False
        self.mic = MicInput(rate=RATE, chunk=CHUNK_SIZE)
        self.mic.start()
        
        self.pre_buffer = []
        self.pre_buffer_size = 5
        
        self.osc = OSC()

    @staticmethod
    def _float32_to_pcm16_bytes(audio_float32: np.ndarray) -> bytes:
        clipped = np.clip(audio_float32, -1.0, 1.0)
        return (clipped * 32767).astype(np.int16).tobytes()

    @staticmethod
    def _build_wav_bytes(chunks: list[bytes]) -> bytes:
        audio_file = io.BytesIO()
        with wave.open(audio_file, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(chunks))
        return audio_file.getvalue()

    def listen(self) -> bytes | None:
        try:
            if not config.USE_VAD:
                fixed_chunks = max(1, int(1000 / CHUNK_DURATION_MS))
                buffer = []

                while not self._is_stopped() and len(buffer) < fixed_chunks:
                    chunk = self.mic.read(timeout=0.2)
                    if chunk is None:
                        continue
                    buffer.append(self._float32_to_pcm16_bytes(chunk))

                if not buffer:
                    return None

                return self._build_wav_bytes(buffer)

            is_speech = False
            buffer = []
            silence_threshold = 15
            silence_count = 0
            
            Log.info("Listening for audio...")

            while not self._is_stopped():
                chunk = self.mic.read(timeout=0.2)
                if chunk is None:
                    continue
                
                audio_float32 = np.asarray(chunk, dtype=np.float32)
                data = self._float32_to_pcm16_bytes(audio_float32)
                
                audio_chunk = np.expand_dims(audio_float32, axis=0)
                input_x = np.concatenate([self._vad_context, audio_chunk], axis=1)
                
                inputs = {
                    'input': input_x,
                    'sr': self._vad_sr,
                    'state': self._vad_state
                }
                out, self._vad_state = self.model.run(None, inputs)
                
                self._vad_context = input_x[..., -64:]
                confidence = float(out[0][0])
                
                if confidence > config.VAD_THRESHOLD:
                    if not is_speech:
                        Log.info("Speech detected.")
                        is_speech = True
                        buffer.extend(self.pre_buffer)
                        self.osc.send_typing(True)
                    
                    buffer.append(data)
                    silence_count = 0
                else:
                    if is_speech:
                        buffer.append(data)
                        silence_count += 1
                        
                        if silence_count > silence_threshold:
                            wav_data = self._build_wav_bytes(buffer)
                            is_speech = False
                            buffer.clear()
                            self.pre_buffer.clear()
                            silence_count = 0
                            
                            self.osc.send_typing(False)
                            Log.debug("Speech ended.")
                            
                            return wav_data
                    else:
                        self.pre_buffer.append(data)
                        if len(self.pre_buffer) > self.pre_buffer_size:
                            self.pre_buffer.pop(0)

            return None
                
        except Exception as e:
            Log.error(f"audio error: {e}", exc_info=True)
            return None
    
    async def listen_async(self) -> bytes | None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.listen)

    def _is_stopped(self) -> bool:
        return self._closed or (self._stop_event is not None and self._stop_event.is_set())

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        try:
            self.mic.stop()
        finally:
            pass