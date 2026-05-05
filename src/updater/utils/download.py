from utils.logger import Logger

import os
import aiohttp
import asyncio
import zipfile
from datetime import datetime

Log = Logger(__name__)

class Downloader:
    def __init__(self, url: str, out_dir: str):
        self.url = url
        self.out_dir = out_dir
        self.date = datetime.now().strftime("%Y%m%d%H%M%S")

    async def unzip(self, input_path: str):
        def _extract():
            with zipfile.ZipFile(input_path) as zf:
                zf.extractall(self.out_dir)

        await asyncio.to_thread(_extract)

    def _find_executable(self):
        preferred = "HarukaTrans.exe"
        for root, _, files in os.walk(self.out_dir):
            if preferred in files:
                return os.path.join(root, preferred)

        for root, _, files in os.walk(self.out_dir):
            for name in files:
                if name.lower().endswith(".exe") and name.lower() != "updater.exe":
                    return os.path.join(root, name)

        return None
        
    async def download(self):
        os.makedirs(self.out_dir, exist_ok=True)
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, timeout=15) as resp:
                if resp.status == 200:
                    out_path = self.out_dir + f"\\HarukaTrans-{self.date}.zip"
                    content = await resp.read()
                    with open(out_path, 'wb') as f:
                        f.write(content)
                    Log.info(f"Download completed.")
                    
                else:
                    Log.error(f"Download failed. (HTTP {resp.status})")
                    return False
        
        await self.unzip(out_path)
        os.remove(out_path)

        exe_path = self._find_executable()
        if not exe_path:
            Log.error("Failed to locate extracted executable.")
            return None

        Log.info(f"Unzipped to: {exe_path}")

        return exe_path