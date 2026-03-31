import asyncio
import inspect
from abc import ABC

class BaseSTT(ABC):
    def __init__(self, on_result):
        self.on_result = on_result

    def emit_result(self, text: str, final: bool):
        if inspect.iscoroutinefunction(self.on_result):
            asyncio.create_task(self.on_result(text, final))
        else:
            self.on_result(text, final)

    async def start(self):
        pass

    async def stop(self):
        pass