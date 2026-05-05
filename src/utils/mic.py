import queue

import numpy as np
import sounddevice as sd


class MicInput:
    def __init__(self, rate=16000, chunk=1024, device=None):
        self.rate = rate
        self.chunk = chunk
        self.device = device
        self.q = queue.Queue()
        self.stream = None

    @staticmethod
    def _is_not_initialized_error(err: Exception) -> bool:
        return "PortAudio not initialized" in str(err)

    @staticmethod
    def _ensure_portaudio_initialized():
        try:
            sd.query_hostapis()
        except Exception as e:
            if not MicInput._is_not_initialized_error(e):
                raise
            # Recover global SoundDevice backend state.
            sd._initialize()

    def _find_first_input_device(self):
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                return idx
        return None

    def _default_input_device(self):
        default_device = sd.default.device
        if isinstance(default_device, (tuple, list)):
            return default_device[0]
        return default_device

    def _candidate_devices(self):
        candidates = []
        if self.device is not None:
            candidates.append(self.device)

        try:
            default_input = self._default_input_device()
            if default_input not in (None, -1):
                candidates.append(default_input)
        except Exception:
            pass

        try:
            fallback = self._find_first_input_device()
            if fallback is not None:
                candidates.append(fallback)
        except Exception:
            pass

        seen = set()
        unique = []
        for device in candidates:
            key = str(device)
            if key in seen:
                continue
            seen.add(key)
            unique.append(device)
        return unique

    def start(self):
        self._ensure_portaudio_initialized()

        def callback(indata, frames, time, status):
            chunk = np.asarray(indata, dtype=np.float32).reshape(-1)
            self.q.put(chunk.copy())

        last_error = None
        for device in self._candidate_devices():
            try:
                self.stream = sd.InputStream(
                    samplerate=self.rate,
                    channels=1,
                    dtype="float32",
                    blocksize=self.chunk,
                    callback=callback,
                    device=device,
                )
                self.stream.start()
                return
            except Exception as e:
                if self._is_not_initialized_error(e):
                    self._ensure_portaudio_initialized()
                last_error = e

        try:
            self.stream = sd.InputStream(
                samplerate=self.rate,
                channels=1,
                dtype="float32",
                blocksize=self.chunk,
                callback=callback,
            )
            self.stream.start()
            return
        except Exception as e:
            if self._is_not_initialized_error(e):
                self._ensure_portaudio_initialized()
            last_error = e

        raise RuntimeError(f"Failed to start microphone input stream: {last_error}")

    def read(self, timeout=None):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        if not self.stream:
            return
        self.stream.stop()
        self.stream.close()
        self.stream = None