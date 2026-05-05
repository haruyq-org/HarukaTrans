import asyncio
import inspect
from abc import ABC

class BaseSTT(ABC):
    def __init__(self, on_result):
        self.on_result = on_result

    def emit_result(self, text: str, final: bool, elapsed: float = 0.0):
        if inspect.iscoroutinefunction(self.on_result):
            asyncio.create_task(self.on_result(text, final, elapsed))
        else:
            self.on_result(text, final, elapsed)

    async def start(self):
        pass

    async def stop(self):
        pass