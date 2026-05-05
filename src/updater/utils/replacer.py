from utils.logger import Logger

import os
import shutil

Log = Logger(__name__)

class Replacer:
    def __init__(self, main_exe: str, new_exe: str):
        self.main_exe = main_exe
        self.new_exe = new_exe

    async def replace(self):
        old_path = self.main_exe + ".old"
        
        try:
            if os.path.exists(old_path):
                os.remove(old_path)
            shutil.move(self.main_exe, old_path)
            shutil.move(self.new_exe, self.main_exe)
            Log.info("Replacement successful.")
            return True
            
        except Exception as e:
            Log.error(f"Replacement failed: {e}")
            if os.path.exists(old_path):
                shutil.move(old_path, self.main_exe)
            return False