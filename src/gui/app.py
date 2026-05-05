import src.main as STT_main
from src.config import config
from src.gui.components.app_bar import build_app_bar
from src.gui.components.mic_status import (
    build_mic_status,
    get_curr_mic,
    set_mic_indicator,
)
from src.gui.components.textareas import build_textarea_row
from src.gui.components.update_notice import build_update_notice
from src.gui.constants import (
    LANGUAGE_MAP,
    REVERSE_LANG_MAP,
    REVERSE_SOURCE_LANG_MAP,
    SOURCE_LANGUAGE_MAP,
)
from src.gui.views.app_view import build_app_view
from src.gui.views.settings_view import build_settings_view
from src.utils.osc import OSC
from src.utils.path import resource_path
from src.utils.update import AutoUpdater
from src.version import __version__

import asyncio
import flet as ft
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main(page: ft.Page):
    page.title = "HarukaTrans"
    page.window.icon = resource_path("assets/icon.ico")
    page.window.width = 900
    page.window.height = 600
    page.window.resizable = False
    page.window.maximizable = False
    page.theme_mode = ft.ThemeMode.DARK

    stop_event = None
    updater = AutoUpdater(__version__)
    update_notice: ft.Container | None = None
    update_notice_body: ft.Text | None = None
    update_now_btn: ft.FilledButton | None = None
    update_later_btn: ft.TextButton | None = None

    def refresh_translate_button_and_text():
        translate_btn.icon_color = ft.Colors.GREEN_500 if config.USE_TRANSLATE else ft.Colors.WHITE_54
        translate_btn.tooltip = f"Translation: {'ON' if config.USE_TRANSLATE else 'OFF'}"
        if config.USE_TRANSLATE:
            text_translation.value = "Waiting for translation..." if start_btn.disabled else "Translation will appear here..."
        else:
            text_translation.value = "(Translation is disabled)"

    def toggle_translate(e):
        config.USE_TRANSLATE = not config.USE_TRANSLATE
        config.save()
        refresh_translate_button_and_text()
        page.update()

    translate_btn = ft.IconButton(
        ft.Icons.TRANSLATE,
        margin=ft.Margin(right=10),
        on_click=toggle_translate,
        icon_color=ft.Colors.GREEN_500 if config.USE_TRANSLATE else ft.Colors.WHITE_54,
        tooltip=f"Translation: {'ON' if config.USE_TRANSLATE else 'OFF'}",
    )

    def open_settings():
        asyncio.create_task(page.push_route("/settings"))

    app_appbar = build_app_bar(__version__, translate_btn, open_settings)
    
    def on_source_lang_change(e):
        selected_lang = e.control.value
        if config.STT_ENGINE == "edgestt" and selected_lang:
            config.SOURCE_LANG = SOURCE_LANGUAGE_MAP.get(selected_lang, "ja-JP")
            config.save()

    def on_lang_change(e):
        selected_lang = e.control.value
        config.TARGET_LANG = LANGUAGE_MAP.get(selected_lang, "en")
        config.save()

    source_lang_dropdown = ft.Dropdown(
        width=200,
        options=[ft.dropdown.Option("Auto")],
        value="Auto",
        border_color=ft.Colors.WHITE_54,
        disabled=True,
        on_select=on_source_lang_change,
    )

    def refresh_source_lang_dropdown():
        is_edgestt = config.STT_ENGINE == "edgestt"
        source_lang_dropdown.disabled = not is_edgestt
        if is_edgestt:
            source_lang_dropdown.options = [
                ft.dropdown.Option(lang) for lang in SOURCE_LANGUAGE_MAP.keys()
            ]
            source_lang_dropdown.value = REVERSE_SOURCE_LANG_MAP.get(config.SOURCE_LANG, "Japanese")
        else:
            source_lang_dropdown.options = [ft.dropdown.Option("Auto")]
            source_lang_dropdown.value = "Auto"

    lang_row = ft.Row(
        controls=[
            source_lang_dropdown,
            ft.Icon(ft.Icons.SWAP_HORIZ, color="#2675c0"),
            ft.Dropdown(
                width=200,
                options=[ft.dropdown.Option(lang) for lang in LANGUAGE_MAP.keys()],
                value=REVERSE_LANG_MAP.get(config.TARGET_LANG, "English"),
                border_color=ft.Colors.WHITE_54,
                on_select=on_lang_change
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
        margin=ft.Margin(top=20)
    )
    
    async def handle_transcription_submit(e):
        text = text_transcription.value.strip()
        if not text or text in ("Transcription will appear here...", "Listening...", "Running..."):
            return
        
        if config.USE_TRANSLATE:
            text_translation.value = "Translating..."
            page.update()
            
            translator = STT_main.init_translator()
            if translator:
                try:
                    translated = await translator.translate_async(text, config.TARGET_LANG)
                    text_translation.value = translated
                except Exception as ex:
                    text_translation.value = f"Error: {ex}"
                    STT_main.Log.error(f"Translation error: {ex}")
        else:
            text_translation.value = "(Translation is disabled)"
            translated = None
            
        page.update()
        
        osc = OSC()
        message = translated if (config.USE_TRANSLATE and translated) else text
        
        if len(message) >= 144:
            messages = [message[i : i + 144] for i in range(0, len(message), 144)]
        else:
            messages = [message]
            
        for msg in messages:
            osc.send_chatbox(msg)
            wait = max(1.4, min(len(msg) * 0.1, 8.0))
            await asyncio.sleep(wait)

    text_transcription = ft.TextField(
        value="Transcription will appear here...", 
        text_size=17, 
        multiline=True, 
        min_lines=8, 
        max_lines=8, 
        border=ft.InputBorder.NONE, 
        expand=True,
        shift_enter=True,
        on_submit=lambda e: page.run_task(handle_transcription_submit, e)
    )
    text_translation = ft.TextField(
        value="Translation will appear here...", 
        text_size=17,
        read_only=True,
        multiline=True,
        min_lines=8,
        max_lines=8,
        border=ft.InputBorder.NONE,
        expand=True
    )

    textarea_row = build_textarea_row(text_transcription, text_translation)

    async def refresh_mic_name(running: bool, force_refresh: bool = False):
        nonlocal current_mic
        loop = asyncio.get_event_loop()
        if force_refresh:
            await asyncio.sleep(0.3)
        current_mic = await loop.run_in_executor(None, lambda: get_curr_mic(force_refresh))
        status = "Running" if running else "Stopped"
        set_mic_indicator(mic_icon, mic_status, running, f"{status} ({current_mic})")
        page.update()

    current_mic = get_curr_mic()
    mic_status_row, mic_icon, mic_status = build_mic_status(current_mic)
    
    def gui_callback(msg_type: str, message: str):
        if msg_type == "transcribe":
            text_transcription.value = message
        elif msg_type == "translate":
            text_translation.value = message
        page.update()

    def hide_update_notice(_=None):
        if update_notice:
            update_notice.visible = False
        page.update()

    async def run_update(version: str):
        if not update_notice_body or not update_now_btn or not update_later_btn:
            return

        update_now_btn.disabled = True
        update_later_btn.disabled = True
        update_notice_body.value = f"Updating to {version}..."
        page.update()

        started = await updater.update(page)

        if not started:
            update_notice_body.value = "Failed to update."
            update_now_btn.disabled = False
            update_later_btn.disabled = False
        else:
            update_notice_body.value = "Update started. The app will restart soon."
        page.update()

    def show_update_notice(version: str):
        if not update_notice or not update_notice_body or not update_now_btn or not update_later_btn:
            return

        update_notice_body.value = f"New version {version} is available. Do you want to update now?"
        update_now_btn.disabled = False
        update_later_btn.disabled = False
        update_now_btn.on_click = lambda _: page.run_task(run_update, version)
        update_notice.visible = True
        page.update()

    async def check_for_updates():
        try:
            latest = await updater.check()
        except Exception as ex:
            STT_main.Log.error(f"Update check failed: {ex}", exc_info=True)
            latest = None

        if latest:
            show_update_notice(latest)

    def start_clicked(e):
        nonlocal stop_event
        
        start_btn.disabled = True
        stop_btn.disabled = False
        set_mic_indicator(mic_icon, mic_status, True, f"Running ({current_mic})")
        text_transcription.value = "Listening..."
        if config.USE_TRANSLATE:
            text_translation.value = "Waiting for translation..."
        else:
            text_translation.value = "(Translation is disabled)"
        page.update()
        
        stop_event = asyncio.Event()
        
        page.run_task(STT_main.run_loop, stop_event, gui_callback)
        page.run_task(refresh_mic_name, True, False)

    def stop_clicked(e):
        nonlocal stop_event
        if stop_event:
            stop_event.set()

        if text_transcription.value in ("Listening...", "Running..."):
            text_transcription.value = "Transcription will appear here..."
        if config.USE_TRANSLATE:
            if text_translation.value == "Waiting for translation...":
                text_translation.value = "Translation will appear here..."
        else:
            text_translation.value = "(Translation is disabled)"
            
        start_btn.disabled = False
        stop_btn.disabled = True
        set_mic_indicator(mic_icon, mic_status, False, f"Stopped ({current_mic})")
        page.update()
        page.run_task(refresh_mic_name, False, True)

    start_btn = ft.FilledButton("Start", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, width=120, height=40, on_click=start_clicked)
    stop_btn = ft.FilledButton("Stop", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, width=120, height=40, on_click=stop_clicked, disabled=True)
    refresh_translate_button_and_text()
    
    toggle_row = ft.Row(
        controls=[start_btn, stop_btn],
        alignment=ft.MainAxisAlignment.CENTER,
        margin=ft.Margin(top=5)
    )

    app_content = ft.Column(
        controls=[
            lang_row,
            textarea_row,
            mic_status_row,
            toggle_row
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20
    )

    update_notice, update_notice_body, update_now_btn, update_later_btn = build_update_notice(
        hide_update_notice
    )

    app_root = ft.Stack(
        controls=[app_content, update_notice],
        expand=True,
    )

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        if page.route == "/settings":
            page.views.append(build_app_view(app_appbar, app_root))
            page.views.append(build_settings_view(page, config, refresh_source_lang_dropdown))
        else:
            page.views.append(build_app_view(app_appbar, app_root))
        page.update()

    async def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    refresh_source_lang_dropdown()
    asyncio.create_task(page.push_route("/app"))
    page.run_task(check_for_updates)

if __name__ == '__main__':
    ft.run(main)
