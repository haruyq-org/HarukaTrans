from utils.osc import OSC
from utils.translation import AITranslation, DeepLTranslation, GoogleTranslation
from utils.logger import Logger
from utils.stt.factory import create_stt
from config import config

import asyncio
import argparse
import os
import sys
import contextlib
from typing import Any

Log = Logger(__name__)

if getattr(sys, "frozen", False):
    os.environ["FLET_APP_STORAGE"] = os.path.dirname(sys.executable)

async def chatbox_worker(queue: asyncio.Queue, osc: OSC):
    while True:
        messages = await queue.get()
        for msg in messages:
            osc.send_chatbox(msg)
            wait = max(1.4, min(len(msg) * 0.1, 8.0))
            await asyncio.sleep(wait)
        queue.task_done()

def init_translator():
    if not config.USE_TRANSLATE:
        return None

    match config.TRANSLATOR:
        case "google":
            return GoogleTranslation()
        case "deepl":
            return DeepLTranslation(config.API_KEY)
        case "gemini":
            return AITranslation(config.API_KEY)
        case _:
            Log.error(f"Invalid translator: {config.TRANSLATOR}")
            return None

async def run_loop(stop_event: asyncio.Event, gui_callback=None):
    osc = OSC()
    chatbox_queue = asyncio.Queue()
    chatbox_task = asyncio.create_task(chatbox_worker(chatbox_queue, osc))
    stt_queue = asyncio.Queue()

    state = {
        "trans": init_translator(),
        "stt": None,
        "stt_restart_required": False,
    }

    def on_config_changed(key: str, value: Any):
        if key in ("USE_TRANSLATE", "TRANSLATOR", "API_KEY"):
            Log.info(f"Reloading translator due to {key} change...")
            state["trans"] = init_translator()
        if key in ("STT_ENGINE", "SOURCE_LANG"):
            Log.info(f"STT config changed ({key}), reconnecting...")
            state["stt_restart_required"] = True

    config.add_observer(on_config_changed)

    async def on_stt_result(text: str, final: bool):
        if not text.strip():
            return

        if not final:
            if gui_callback:
                gui_callback("partial", text)
            return

        await stt_queue.put(text)

    async def restart_stt():
        if state["stt"]:
            await state["stt"].stop()
        Log.info(f"Starting STT: {config.STT_ENGINE} ({config.SOURCE_LANG})")
        state["stt"] = create_stt(stop_event, on_stt_result)
        await state["stt"].start()
        state["stt_restart_required"] = False

    await restart_stt()

    try:
        while not stop_event.is_set():
            if state["stt_restart_required"]:
                await restart_stt()

            try:
                transcription = await asyncio.wait_for(stt_queue.get(), timeout=0.2)
            except asyncio.TimeoutError:
                continue

            Log.info(f"Transcription: {transcription}")

            if gui_callback:
                gui_callback("transcribe", transcription)

            translated = None
            if config.USE_TRANSLATE and state["trans"]:
                try:
                    translated = await state["trans"].translate_async(
                        transcription,
                        config.TARGET_LANG,
                    )
                    Log.info(f"Translation: {translated}")
                    if gui_callback:
                        gui_callback("translate", translated)
                except Exception as e:
                    Log.error(f"Translation error: {e}")

            message = translated if translated else transcription

            if len(message) >= 144:
                messages = [
                    message[i : i + 144] for i in range(0, len(message), 144)
                ]
            else:
                messages = [message]

            await chatbox_queue.put(messages)

    finally:
        Log.info("Stopping STT...")
        if state["stt"]:
            await state["stt"].stop()
        config.remove_observer(on_config_changed)
        chatbox_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await chatbox_task

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Speech-to-Text and Translation for VRChat"
    )
    parser.add_argument("--nogui", action="store_true")
    args = parser.parse_args()

    if not args.nogui:
        from gui.app import main
        import flet as ft

        ft.run(main, view=ft.AppView.FLET_APP)

    else:
        stop_event = asyncio.Event()
        try:
            asyncio.run(run_loop(stop_event))
        except KeyboardInterrupt:
            stop_event.set()
            Log.info("Exiting...")