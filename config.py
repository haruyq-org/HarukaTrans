import json
import os
from typing import Callable, Any

class Config:
    __version__: str = "0.1.6"
    
    BASE_URL: str = "http://example.com"
    STT_ENGINE: str = "edgestt"
    SOURCE_LANG: str = "ja-JP"
    USE_VAD: bool = True
    VAD_THRESHOLD: float = 0.5
    VAD_THREADS: int = 1
    USE_TRANSLATE: bool = False
    TRANSLATOR: str = "google"
    API_KEY: str = ""
    TARGET_LANG: str = "en"
    LOG_LEVEL: str = "INFO"

    def __init__(self):
        self.__dict__['_callbacks'] = []
        self.load()

    def __setattr__(self, key: str, value: Any):
        if key.startswith('_'):
            self.__dict__[key] = value
            return
            
        curr = getattr(self, key, None)
        if curr != value:
            self.__dict__[key] = value
            self._notify_observers(key, value)        

    def load(self):
        try:
            with open("configs/config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
            
        for key in self.__class__.__annotations__.keys():
            if key in data:
                setattr(self, key, data[key])

    def save(self):
        data = {key: getattr(self, key) for key in self.__class__.__annotations__.keys()}
        try:
            os.makedirs("configs", exist_ok=True)
            with open("configs/config.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def add_observer(self, callback: Callable[[str, Any], None]):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_observer(self, callback: Callable[[str, Any], None]):
        if callback in self._callbacks:
            self._callbacks.remove(callback)
        
    def _notify_observers(self, key: str, value: Any):
        for callback in self._callbacks:
            callback(key, value)

config = Config()