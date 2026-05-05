from src.config import config
from src.utils.stt.voxbox import VoxBoxSTT
from src.utils.stt.edgestt import EdgeStreamingSTT

def create_stt(stop_event, on_result):
    if config.STT_ENGINE == "edgestt":
        return EdgeStreamingSTT(stop_event, on_result, config.SOURCE_LANG)
    else:
        return VoxBoxSTT(stop_event, on_result)