from utils.logger import Logger
from utils.path import resource_path
from utils.download import Downloader
from utils.replacer import Replacer

import asyncio
import sys
import subprocess
from typing import Any
from argparse import ArgumentParser

Log = Logger(__name__)

async def updater(args: Any):
    downloader = Downloader(
        url=args.url,
        out_dir=args.out_dir
    )
    new_exe = await downloader.download()
    if not new_exe:
        Log.error("Download or extraction failed. Aborting update.")
        return
    
    replacer = Replacer(
        main_exe=args.main_exe,
        new_exe=new_exe
    )
    replaced = await replacer.replace()
    if not replaced:
        Log.error("Replacement failed. Aborting update.")
        return
    
    await asyncio.sleep(2)
    
    try:
        subprocess.Popen([args.main_exe], creationflags=subprocess.CREATE_NEW_CONSOLE)
    except Exception as e:
        Log.error(f"Failed to start updated app: {e}")
        return
    
    sys.exit(0)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--url", type=str, required=True)
    parser.add_argument("--out-dir", type=str, required=True)
    parser.add_argument("--main-exe", type=str, required=True)
    args = parser.parse_args()
    
    asyncio.run(updater(args))