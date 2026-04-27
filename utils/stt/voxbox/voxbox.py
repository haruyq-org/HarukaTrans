from utils.logger import Logger
from utils.stt.base import BaseSTT
from config import config
from .audio import Audio

import aiohttp
import asyncio

Log = Logger(__name__)

class VoxBox:
    def __init__(self, base_url: str):
        self.base_url = base_url + "/v1"
        self.api_key = "none"
        self.model = "FasterWhisper"
        
    async def transcribe(self, audio_data: bytes) -> str | None:
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        data = aiohttp.FormData()
        data.add_field("model", self.model)
        data.add_field("file", audio_data, filename="audio.wav", content_type="audio/wav")
        data.add_field('prompt', "えー、あのー、といったフィラーや、背景の雑音、無意味な文字列は無視してください。")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/audio/transcriptions", headers=headers, data=data) as resp:
                    resp_json = await resp.json()
                    if resp.status == 200:
                        return resp_json.get("text", None)
                    else:
                        Log.error(f"transcription failed: {resp_json}")
                        return None
                    
        except Exception as e:
            Log.error(f"transcription error: {e}")
            return None

class VoxBoxSTT(BaseSTT):
    def __init__(self, stop_event, on_result):
        super().__init__(on_result)
        self.audio = Audio(stop_event=stop_event)
        self.vb = VoxBox(config.BASE_URL)
        self.stop_event = stop_event
        self.task = None

    async def _loop(self):
        while not self.stop_event.is_set():
            audio_data, elapsed = await self.audio.listen_async()
            if not audio_data:
                continue

            text = await self.vb.transcribe(audio_data)
            if text:
                self.emit_result(text, True, elapsed)

    async def start(self):
        self.task = asyncio.create_task(self._loop())

    async def stop(self):
        self.audio.close()
        if self.task:
            self.task.cancel()