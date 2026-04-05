from utils.logger import Logger

import aiohttp
import os
import re
import subprocess
import sys
import tempfile
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
            os.remove(self.archive_path)

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

    def _build_updater_bat(self, app_exe: str, archive_path: str, version: str) -> str:
        app_dir = os.path.dirname(app_exe)
        work_dir = os.path.join(tempfile.gettempdir(), "HarukaTrans_update_work")
        script_path = os.path.join(tempfile.gettempdir(), "HarukaTrans_apply_update.bat")

        lines = [
            "@echo off",
            "setlocal",
            f'set "APP_EXE={app_exe}"',
            f'set "APP_DIR={app_dir}"',
            f'set "ZIP_PATH={archive_path}"',
            f'set "WORK_DIR={work_dir}"',
            "timeout /t 2 /nobreak >nul",
            "if exist \"%WORK_DIR%\" rmdir /s /q \"%WORK_DIR%\"",
            "mkdir \"%WORK_DIR%\"",
            "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Expand-Archive -LiteralPath '%ZIP_PATH%' -DestinationPath '%WORK_DIR%' -Force\"",
            "if errorlevel 1 goto fail",
            "set \"NEW_EXE=\"",
            "for /f \"delims=\" %%I in ('dir /b /s \"%WORK_DIR%\\HarukaTrans.exe\"') do set \"NEW_EXE=%%I\"",
            "if defined NEW_EXE (",
            "  copy /y \"%NEW_EXE%\" \"%APP_EXE%\" >nul",
            ") else (",
            "  xcopy \"%WORK_DIR%\\*\" \"%APP_DIR%\\\" /e /i /y >nul",
            ")",
            "if errorlevel 1 goto fail",
            "start \"\" \"%APP_EXE%\"",
            "exit /b 0",
            ":fail",
            "start \"\" \"%APP_EXE%\"",
            "exit /b 1",
        ]

        with open(script_path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write("\r\n".join(lines))

        Log.info(f"Prepared updater script for {version}: {script_path}")
        return script_path

    def apply_update_and_restart(self, version: str) -> bool:
        if not getattr(sys, "frozen", False):
            Log.error("Auto replace is only available in packaged executable mode.")
            return False

        app_exe = os.path.abspath(sys.executable)
        archive_path = os.path.abspath(self.archive_path)
        if not os.path.exists(archive_path):
            Log.error("Downloaded archive not found.")
            return False

        script_path = self._build_updater_bat(app_exe, archive_path, version)
        subprocess.Popen(
            ["cmd", "/c", script_path],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
        return True
        
    async def update(self, version: str):
        downloaded = await self.download(version)
        if not downloaded:
            return False
        return self.apply_update_and_restart(version)
        
        