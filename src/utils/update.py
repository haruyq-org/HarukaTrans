from src.utils.logger import Logger
from src.utils.path import resource_path

import aiohttp
import os
import subprocess
import sys
import threading
import asyncio
import urllib.request as request
from flet import Page
from packaging import version

Log = Logger(__name__)

TEMP_DIR = resource_path("temp", no_meipass=True)

class AutoUpdater:
    def __init__(self, curr_version: str):
        self.curr_version = curr_version
        self.latest_url = "https://api.github.com/repos/haruyq-org/HarukaTrans/releases/latest"
        # self.latest_url = "http://localhost:8000/release.json"
        
        def get_updater():
            if os.path.exists(resource_path("updater.exe", no_meipass=True)):
                return resource_path("updater.exe", no_meipass=True)
            req = request.Request("https://github.com/haruyq-org/HarukaTrans/releases/download/v0.2.1/updater.exe")
            with request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    with open(resource_path("updater.exe", no_meipass=True), 'wb') as f:
                        f.write(resp.read())
                else:
                    Log.error(f"Failed to download updater.exe (HTTP {resp.status})")

        def cleanup_temp():
            if not getattr(sys, "frozen", False): return
            if os.path.exists(TEMP_DIR):
                os.removedirs(TEMP_DIR)

        def cleanup_old():
            if not getattr(sys, "frozen", False): return
            old_exe = sys.executable + ".old"
            import time
            for _ in range(10):
                if os.path.exists(old_exe):
                    try:
                        os.remove(old_exe)
                        break
                    except Exception:
                        time.sleep(1)
                else:
                    break

        threading.Thread(target=get_updater, daemon=True).start()
        threading.Thread(target=cleanup_old, daemon=True).start()
        threading.Thread(target=cleanup_temp, daemon=True).start()

    def _normalize_version(self, value: str) -> str:
        return value.strip().lstrip("v")

    async def check(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.latest_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        Log.error(f"Failed to check for updates. (HTTP {resp.status})")
                        return None
                    
                    data = await resp.json()
                    tag_name = self._normalize_version(str(data.get("tag_name", "")))
                    curr_name = self._normalize_version(str(self.curr_version))
                    if not tag_name or not curr_name:
                        Log.error("Invalid version data for update check.")
                        return None

                    latest_ver = version.parse(tag_name)
                    curr_ver = version.parse(curr_name)

                    if latest_ver <= curr_ver:
                        return None

                    Log.info(f"New version available: {latest_ver} (current: {curr_ver})")
                    assets = data.get("assets", [])
                    return assets[0]["browser_download_url"] if assets else None
            except Exception as e:
                Log.error(f"Update check error: {e}")
                return None
        
    async def update(self, page: Page):
        url = await self.check()
        if not url:
            Log.error("No update URL available.")
            return False
        
        updater_path = resource_path("updater.exe", no_meipass=True)
        
        if not os.path.exists(updater_path):
            Log.error("Updater executable not found.")
            return False

        os.makedirs(TEMP_DIR, exist_ok=True)

        try:
            proc = subprocess.Popen(
                [
                    updater_path,
                    "--url", url,
                    "--out-dir", TEMP_DIR,
                    "--main-exe", sys.executable],
                shell=True
            )
        except Exception as e:
            Log.error(f"Failed to start updater: {e}")
            return False

        return_code = await asyncio.to_thread(proc.wait)
        if return_code != 0:
            Log.error(f"Updater process exited with code {return_code}")
            return False

        await page.window.destroy()
        await asyncio.sleep(2)
        sys.exit(0)
