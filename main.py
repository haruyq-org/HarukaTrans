from utils.osc import OSC
from utils.translation import AITranslation, DeepLTranslation, GoogleTranslation
from utils.logger import Logger
from utils.stt.factory import create_stt
from utils.vad import init_vad_model
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
        "stt_restart_required": True,
        "stt_restart_failures": 0,
    }

    def emit_gui(msg_type: str, message: str):
        if not gui_callback:
            return
        try:
            gui_callback(msg_type, message)
        except Exception as e:
            Log.error(f"GUI callback error ({msg_type}): {e}", exc_info=True)

    def stt_has_failed_task():
        stt = state["stt"]
        if not stt:
            return False

        def is_expected_task_end(task_name: str):
            if task_name != "receive_task":
                return False

            edge_stt = getattr(stt, "stt", None)
            reason = getattr(edge_stt, "_planned_close_reason", None)
            return reason == "turn_limit"

        for task_name in ("task", "receive_task", "mic_task"):
            task = getattr(stt, task_name, None)
            if not isinstance(task, asyncio.Task) or not task.done():
                continue

            if is_expected_task_end(task_name):
                Log.info(f"STT task ended (planned reconnect): {task_name}")
                return True

            Log.warning(f"STT task ended unexpectedly: {task_name}")
            return True

        return False

    def on_config_changed(key: str, value: Any):
        if key in ("USE_TRANSLATE", "TRANSLATOR", "API_KEY"):
            Log.info(f"Reloading translator due to {key} change...")
            state["trans"] = init_translator()
        if key in ("STT_ENGINE", "SOURCE_LANG"):
            Log.info(f"STT config changed ({key}), reconnecting...")
            state["stt_restart_required"] = True

    config.add_observer(on_config_changed)

    async def on_stt_result(text: str, final: bool, elapsed: float = 0.0): # on_result
        if not text.strip():
            return

        if not final:
            emit_gui("partial", text)
            return

        Log.debug(f"STT elapsed: {elapsed:.2f}sec")

        # ハルシネーション対策になるかも？
        if config.STT_ENGINE == "voxbox" and elapsed <= 0.15:
            Log.debug(f"Ignoring: {text} ({elapsed:.2f}sec)")
            return

        await stt_queue.put(text)

    async def restart_stt():
        if state["stt"]:
            await state["stt"].stop()
            state["stt"] = None

        Log.info(f"Starting STT: {config.STT_ENGINE} ({config.SOURCE_LANG})")
        state["stt"] = create_stt(stop_event, on_stt_result)
        await state["stt"].start()
        state["stt_restart_required"] = False
        state["stt_restart_failures"] = 0

    try:
        while not stop_event.is_set():
            if stt_has_failed_task():
                state["stt_restart_required"] = True

            if state["stt_restart_required"]:
                try:
                    await restart_stt()
                except Exception as e:
                    state["stt_restart_failures"] += 1
                    wait_sec = min(10.0, 0.5 * (2 ** (state["stt_restart_failures"] - 1)))
                    Log.error(
                        f"Failed to start STT ({config.STT_ENGINE}): {e}. Retrying in {wait_sec:.1f}s",
                        exc_info=True,
                    )
                    await asyncio.sleep(wait_sec)
                    continue

            try:
                transcription = await asyncio.wait_for(stt_queue.get(), timeout=0.2)
            except asyncio.TimeoutError:
                continue

            Log.info(f"Transcription: {transcription}")

            emit_gui("transcribe", transcription)

            translated = None
            if config.USE_TRANSLATE and state["trans"]:
                try:
                    translated = await state["trans"].translate_async(
                        transcription,
                        config.TARGET_LANG,
                    )
                    Log.info(f"Translation: {translated}")
                    emit_gui("translate", translated)
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
    
    if config.USE_VAD:
        init_vad_model()

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