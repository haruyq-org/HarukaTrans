from utils.path import resource_path
from utils.logger import Logger

import os

Log = Logger(__name__)

def init_vad_model():
    path = resource_path("vad/silero_vad.onnx")
    Log.debug(f"Checking for VAD model at: {path}")

    if os.path.exists(path):
        return True
    try:
        Log.info("VAD model not found. Downloading...")
        os.makedirs(resource_path("vad"), exist_ok=True)
        import requests
        url = "https://raw.githubusercontent.com/snakers4/silero-vad/refs/heads/master/src/silero_vad/data/silero_vad.onnx"
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
            Log.info("VAD model downloaded successfully.")
            return True
    except Exception as e:
        Log.error(f"Error occurred while downloading VAD model: {e}")
        