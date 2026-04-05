from utils.path import resource_path
from utils.logger import Logger

import urllib.request
import os

Log = Logger(__name__)

def init_vad_model():
    path = resource_path("vad/silero_vad.onnx")
    Log.debug(f"Checking for VAD model at: {path}")

    if os.path.exists(path):
        return
    try:
        Log.info("VAD model not found. Downloading...")
        os.makedirs(resource_path("vad"), exist_ok=True)
        url = "https://raw.githubusercontent.com/snakers4/silero-vad/refs/heads/master/src/silero_vad/data/silero_vad.onnx"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                with open(path, 'wb') as f:
                    f.write(resp.read())
                Log.info("VAD model downloaded successfully.")
            
    except Exception as e:
        Log.error(f"Error occurred while downloading VAD model: {e}")
        