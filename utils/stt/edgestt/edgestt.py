from utils.logger import Logger
from utils.stt.base import BaseSTT
from utils.stt.edgestt.utils import EdgeSTTUtils
from utils.mic import MicInput

import websockets
import struct
import json
import asyncio
import contextlib
import numpy as np
from typing import Callable, Optional

Log = Logger(__name__)

WSS_HOST = "speech.platform.bing.com"
WSS_PATH = "/speech/recognition/edge/interactive/v1"

MS_VERSION = "1-145.0.3800.70"
TRUSTED_TOKEN   = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"
CHANNELS        = 1
BITS_PER_SAMPLE = 16
SAMPLE_RATE     = 16000

EXTRA_HEADERS = {
    "Pragma":        "no-cache",
    "Cache-Control": "no-cache",
    "Origin":        "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
    ),
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
}

class EdgeSTT:
    def __init__(
        self,
        language: str = "ja-JP",
        on_result: Optional[Callable[[str, bool], None]] = None,
        sample_rate: int = 16000,
    ):
        self.language = language
        self.on_result = on_result
        self.sample_rate = sample_rate
 
        self._ws = None
        self._connection_id = ""
        self._request_id = ""
        self._stream_id = 1
        self._service_tag = None
        self._bytes_sent = 0
        self._audio_active = False
        self._restart_pending = False
        self._running = False
        self._loop = None
        
        self.utils = EdgeSTTUtils()
    
    async def connect(self):
        self._connection_id = self.utils.gen_uuid()
        self._request_id = self.utils.gen_uuid()
        self._stream_id = 1
        self._bytes_sent = 0
        self._running = True
        
        gec = self.utils.gen_sec_ms_gec()
        
        url = (
            f"wss://{WSS_HOST}{WSS_PATH}"
            f"?TrustedClientToken={TRUSTED_TOKEN}"
            f"&Sec-MS-GEC={gec}"
            f"&Sec-MS-GEC-Version={MS_VERSION}"
            f"&language={self.language}"
            f"&profanity=raw"
        )
        Log.debug(f"Connecting to EdgeSTT at {url}")
        
        self._ws = await websockets.connect(
            url,
            additional_headers=EXTRA_HEADERS,
            ping_interval=None,
        )
        await self._on_open()
        
        Log.info(f"EdgeSTT connection established. language: {self.language}")
        
    async def _on_open(self):
        await self._send_text(self.utils.create_text_message(
            "speech.config",
            {
                "context": {
                    "audio": {
                        "source": {
                            "bitspersample": str(BITS_PER_SAMPLE),
                            "channelcount": str(CHANNELS),
                            "model": "",
                            "samplerate": str(self.sample_rate),
                            "type": "Stream",
                        }
                    },
                    "os":     {"name": "Client", "platform": "Windows", "version": "10"},
                    "system": {"build": "Windows-x64", "name": "SpeechSDK", "version": "1.15.0"},
                }
            },
            content_type="application/json",
        ))
 
        await self._send_text(self.utils.create_text_message(
            "speech.context",
            {"audio": {"streams": {"1": None}}},
            request_id=self._request_id,
        ))
 
        await self._send_wav_header()

    async def _handle_message(self, msg: str):
        if "Path:turn.start" in msg:
            self._parse_service_tag(msg)
 
        elif "Path:speech.hypothesis" in msg:
            try:
                body = json.loads(msg.split("\r\n\r\n", 1)[1])
                text = body.get("Text", "")
                if text and self.on_result:
                    self.on_result(text, False)
            except Exception as e:
                Log.error(f"[EdgeSTT] hypothesis parse error: {e}")
 
        elif "Path:speech.phrase" in msg:
            try:
                body = json.loads(msg.split("\r\n\r\n", 1)[1])
                text = body.get("DisplayText", "")
                if text and self.on_result:
                    self.on_result(text, True)
            except Exception as e:
                Log.error(f"[EdgeSTT] phrase parse error: {e}")
 
        elif "Path:turn.end" in msg:
            await self._handle_turn_restart()
 
    def _parse_service_tag(self, msg: str):
        try:
            parts = msg.split("\r\n\r\n", 1)
            if len(parts) > 1:
                data = json.loads(parts[1])
                tag  = data.get("context", {}).get("serviceTag")
                if tag:
                    self._service_tag = tag
        except Exception:
            Log.error(f"[EdgeSTT] Failed to parse service tag from message: {msg}")
 
    async def _handle_turn_restart(self):
        if not self._ws:
            return
 
        self._restart_pending = True
        self._request_id = self.utils.gen_uuid()
        self._stream_id += 1
 
        if self._stream_id > 20:
            Log.debug("[EdgeSTT] Reinitializing connection after 20 turns...")
            await self.close()
            return
 
        bytes_per_second = self.sample_rate * CHANNELS * (BITS_PER_SAMPLE // 8)
        seconds_sent = self._bytes_sent / bytes_per_second
        offset_100ns = int(seconds_sent * 10_000_000)
 
        context_payload = {
            "audio": {"streams": {"1": None}},
            "continuation": {
                "audio": {"streams": {"1": {"offset": str(offset_100ns)}}},
                "previousServiceTag": self._service_tag,
            },
        }
 
        await self._send_text(self.utils.create_text_message(
            "speech.context",
            context_payload,
            content_type="application/json",
            request_id=self._request_id,
        ))
        await self._send_wav_header()
 
        self._restart_pending = False

    async def _send_text(self, msg: str):
        if self._ws:
            await self._ws.send(msg)
 
    async def _send_wav_header(self):
        self._audio_active = True
        msg = self.utils.create_bin_message(
            "audio",
            str(self._stream_id),
            self._request_id,
            self.utils.create_wav_header(self.sample_rate),
            content_type="audio/x-wav",
        )
        await self._ws.send(msg)

    async def send_audio_chunk(self, pcm_bytes: bytes):
        if not self._ws or self._restart_pending or not self._audio_active:
            return
 
        self._bytes_sent += len(pcm_bytes)
        msg = self.utils.create_bin_message(
            "audio",
            str(self._stream_id),
            self._request_id,
            pcm_bytes,
        )
        await self._ws.send(msg)
 
    async def receive_loop(self):
        async for raw in self._ws:
            if isinstance(raw, bytes):
                msg_str = self._decode_binary_msg(raw)
            else:
                msg_str = raw
 
            await self._handle_message(msg_str)
 
    async def close(self):
        self._running = False
        self._audio_active = False
        if self._ws:
            await self._ws.close()
            self._ws = None
 
    @staticmethod
    def _decode_binary_msg(data: bytes) -> str:
        if len(data) < 2:
            return ""
        header_len  = struct.unpack(">H", data[:2])[0]
        header_part = data[2:2 + header_len].decode("utf-8", errors="replace")
        body_part   = data[2 + header_len:].decode("utf-8", errors="replace")
        return f"{header_part}\r\n\r\n{body_part}" if body_part else header_part

class EdgeStreamingSTT(BaseSTT):
    def __init__(self, stop_event, on_result, lang):
        super().__init__(on_result)
        self.stop_event = stop_event
        self.lang = lang
        self.stt = None
        self.mic = None
        self.receive_task = None
        self.mic_task = None

    @staticmethod
    def _log_task_exception(task: asyncio.Task, task_name: str):
        with contextlib.suppress(asyncio.CancelledError):
            exc = task.exception()
            if exc:
                Log.error(f"{task_name} failed: {exc}", exc_info=exc)

    async def start(self):
        def cb(text, final):
            if final:
                self.emit_result(text, True)

        self.stt = EdgeSTT(language=self.lang, on_result=cb)
        await self.stt.connect()
        self.receive_task = asyncio.create_task(self.stt.receive_loop())
        self.receive_task.add_done_callback(
            lambda t: self._log_task_exception(t, "Edge receive loop")
        )

        self.mic_task = asyncio.create_task(self._mic_loop())
        self.mic_task.add_done_callback(
            lambda t: self._log_task_exception(t, "Edge mic loop")
        )

    async def _mic_loop(self):
        self.mic = MicInput(rate=16000, chunk=512)
        await asyncio.to_thread(self.mic.start)

        try:
            while not self.stop_event.is_set():
                chunk = await asyncio.to_thread(self.mic.read, 0.05)
                if chunk is None:
                    await asyncio.sleep(0)
                    continue

                pcm16 = (np.clip(chunk, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
                if not self.stt:
                    break
                await self.stt.send_audio_chunk(pcm16)
        finally:
            await asyncio.to_thread(self.mic.stop)
            self.mic = None

    async def stop(self):
        if self.mic_task:
            self.mic_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.mic_task
            self.mic_task = None

        if self.receive_task:
            self.receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.receive_task
            self.receive_task = None

        if self.stt:
            await self.stt.close()
            self.stt = None