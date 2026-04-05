from utils.logger import Logger

import aiohttp
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

Log = Logger(__name__)

class AutoUpdater:
    def __init__(self, curr_version: str):
        self.curr_version = curr_version
        self.latest_url = "https://api.github.com/repos/haruyq-org/HarukaTrans/releases/latest"
        self.archive_path = os.path.abspath("temp/HarukaTrans.zip")
        self.latest_tag: str | None = None
        self.latest_download_url: str | None = None
        self.latest_page_url: str | None = None
        
        if os.path.exists(self.archive_path):
            try:
                os.remove(self.archive_path)
            except Exception:
                pass

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

        import threading
        threading.Thread(target=cleanup_old, daemon=True).start()

    @staticmethod
    def _normalize_version(value: str) -> tuple[int, ...]:
        parts = re.findall(r"\d+", value or "")
        return tuple(int(p) for p in parts)

    def _is_newer(self, latest_tag: str) -> bool:
        latest = self._normalize_version(latest_tag)
        current = self._normalize_version(self.curr_version)

        max_len = max(len(latest), len(current))
        latest = latest + (0,) * (max_len - len(latest))
        current = current + (0,) * (max_len - len(current))
        return latest > current

    @staticmethod
    def _pick_asset_download_url(data: dict[str, Any]) -> str | None:
        assets = data.get("assets") or []
        if not isinstance(assets, list):
            return None

        zip_assets = [
            asset
            for asset in assets
            if isinstance(asset, dict) and str(asset.get("name", "")).lower().endswith(".zip")
        ]
        if not zip_assets:
            return None

        preferred = next(
            (
                asset
                for asset in zip_assets
                if "harukatrans" in str(asset.get("name", "")).lower()
            ),
            zip_assets[0],
        )
        url = preferred.get("browser_download_url")
        return str(url) if url else None
    
    async def check(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.latest_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    latest_ver = data.get("tag_name", "")
                    if latest_ver and self._is_newer(latest_ver):
                        self.latest_tag = latest_ver
                        self.latest_download_url = self._pick_asset_download_url(data)
                        self.latest_page_url = data.get("html_url")
                        Log.info(f"New version available: {latest_ver} (Current: v{self.curr_version})")
                        return latest_ver
                else:
                    Log.error(f"Failed to check for updates: {resp.status}")
        return None
    
    async def download(self, version: str):
        download_url = self.latest_download_url
        if not download_url:
            normalized = version.lstrip("vV")
            download_url = f"https://github.com/haruyq-org/HarukaTrans/releases/download/{version}/HarukaTrans-{normalized}.zip"

        archive_dir = os.path.dirname(self.archive_path)
        if archive_dir:
            os.makedirs(archive_dir, exist_ok=True)
        Log.info(f"Downloading...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    with open(self.archive_path, "wb") as f:
                        f.write(content)
                    Log.info("Download completed.")
                    return True
                else:
                    Log.error(f"Download failed: {resp.status}")
        return False

    def apply_update(self) -> str | None:
        if not getattr(sys, "frozen", False):
            Log.error("Auto replace is only available in packaged executable mode.")
            return None

        app_exe = os.path.abspath(sys.executable)
        app_dir = os.path.dirname(app_exe)
        archive_path = os.path.abspath(self.archive_path)
        if not os.path.exists(archive_path):
            Log.error("Downloaded archive not found.")
            return None

        old_exe = app_exe + ".old"
        
        import zipfile
        import shutil
        work_dir = os.path.join(tempfile.gettempdir(), "HarukaTrans_update_work")
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
        os.makedirs(work_dir, exist_ok=True)
        
        Log.info("Extracting update...")
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(work_dir)
        except Exception as e:
            Log.error(f"Failed to extract update: {e}")
            return None
            
        new_exe = None
        for root, dirs, files in os.walk(work_dir):
            for f in files:
                if f.lower() == "harukatrans.exe":
                    new_exe = os.path.join(root, f)
                    break
            if new_exe:
                break
                
        if not new_exe:
            Log.error("Could not find HarukaTrans.exe in the update archive.")
            return None
            
        new_app_dir = os.path.dirname(new_exe)

        if os.path.exists(old_exe):
            try:
                os.remove(old_exe)
            except Exception:
                pass
                
        try:
            os.rename(app_exe, old_exe)
        except Exception as e:
            Log.error(f"Failed to rename current executable: {e}")
            return None
            
        try:
            def copytree_overwrite(src, dst):
                for item in os.listdir(src):
                    s = os.path.join(src, item)
                    d = os.path.join(dst, item)
                    if os.path.isdir(s):
                        if not os.path.exists(d):
                            os.makedirs(d)
                        copytree_overwrite(s, d)
                    else:
                        shutil.copy2(s, d)
            
            copytree_overwrite(new_app_dir, app_dir)
        except Exception as e:
            Log.error(f"Failed to copy new files: {e}")
            try:
                os.rename(old_exe, app_exe)
            except Exception:
                pass
            return None
            
        Log.info("Update ready. Restart required.")
        return app_exe
        
    async def update(self, version: str) -> str | None:
        downloaded = await self.download(version)
        if not downloaded:
            return None
        return self.apply_update()
    
    async def restart(self):
        if not getattr(sys, "frozen", False):
            Log.error("Auto restart is only available in packaged executable mode.")
            return False

        app_exe = os.path.abspath(sys.executable)
        try:
            subprocess.Popen([app_exe], close_fds=True)
            return True
        except Exception as e:
            Log.error(f"Failed to restart application: {e}")
            return False