import src.main as STT_main
from src.utils.osc import OSC
from src.utils.path import resource_path
from src.utils.update import AutoUpdater
from src.config import config
from src.version import __version__

import flet as ft
import asyncio
import sys
import os
import re
import sounddevice as sd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LANGUAGE_MAP = {
    "English": "en",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Russian": "ru"
}
REVERSE_LANG_MAP = {v: k for k, v in LANGUAGE_MAP.items()}

SOURCE_LANGUAGE_MAP = {
    "English": "en-US",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Chinese": "zh-CN",
    "French": "fr-FR",
    "Spanish": "es-ES",
    "German": "de-DE",
    "Russian": "ru-RU",
}
REVERSE_SOURCE_LANG_MAP = {v: k for k, v in SOURCE_LANGUAGE_MAP.items()}

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

    app_appbar = ft.AppBar(
        title=ft.Text(
            spans=[
                ft.TextSpan(
                    "HarukaTrans",
                    ft.TextStyle(size=22)
                ),
                ft.TextSpan(
                    f"  {__version__}",
                    ft.TextStyle(size=12, color=ft.Colors.WHITE_54)
                ),
            ]
        ),
        bgcolor=ft.Colors.BLUE_900,
        actions=[
            translate_btn,
            ft.IconButton(
                ft.Icons.SETTINGS,
                margin=ft.Margin(right=10),
                on_click=lambda _: asyncio.create_task(page.push_route("/settings"))
            )
        ]
    )
    
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

    def create_textarea(text_control: ft.Control):
        return ft.Container(
            content=text_control,
            border=ft.Border.all(1, ft.Colors.WHITE_54),
            border_radius=8,
            padding=10,
            width=400,
            height=250,
            alignment=ft.Alignment(-1.0, -1.0)
        )
    
    textarea_row = ft.Row(
        controls=[
            create_textarea(text_transcription),
            create_textarea(text_translation)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
        margin=ft.Margin(top=10)
    )
    
    def get_curr_mic(force_refresh: bool = False):
        try:
            if force_refresh:
                sd._terminate()
                sd._initialize()
            device = sd.query_devices(kind="input")
            name = device["name"].strip().rstrip("\x00")
            
            match = re.search(r'\((.+?)\)', name)
            if match:
                return match.group(1).strip()
            
            return name if name else "Unknown Mic"
        except Exception:
            try:
                sd._initialize()
                device = sd.query_devices(kind="input")
                name = device["name"].strip().rstrip("\x00")
                return name if name else "Unknown Mic"
            except Exception:
                return "Unknown Mic"
    
    async def refresh_mic_name(running: bool, force_refresh: bool = False):
        nonlocal current_mic
        loop = asyncio.get_event_loop()
        if force_refresh:
            await asyncio.sleep(0.3)
        current_mic = await loop.run_in_executor(None, lambda: get_curr_mic(force_refresh))
        status = "Running" if running else "Stopped"
        set_mic_indicator(running, f"{status} ({current_mic})")
        page.update()

    current_mic = get_curr_mic()
    
    mic_status = ft.Text(f"Stopped ({current_mic})", color=ft.Colors.RED_500, size=16)
    mic_icon = ft.Icon(ft.Icons.MIC_OFF, color=ft.Colors.RED_500, size=20)

    def set_mic_indicator(running: bool, status_text: str):
        icon_value = ft.Icons.MIC if running else ft.Icons.MIC_OFF
        color_value = ft.Colors.GREEN_500 if running else ft.Colors.RED_500

        # Flet version differences: some use `name`, others use `icon`.
        if hasattr(mic_icon, "name"):
            mic_icon.name = icon_value
        if hasattr(mic_icon, "icon"):
            mic_icon.icon = icon_value

        mic_icon.color = color_value
        mic_status.value = status_text
        mic_status.color = color_value
    
    mic_status_row = ft.Row(
        controls=[
            mic_icon,
            mic_status
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
        margin=ft.Margin(top=5)
    )
    
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
        update_notice_body.value = f"Downloading {version}..."
        page.update()

        try:
            exe_path = await updater.update(version)
        except Exception as ex:
            exe_path = None
            STT_main.Log.error(f"Update failed: {ex}", exc_info=True)

        if exe_path:
            update_notice_body.value = "Restarting application..."
            page.update()
            await page.window.destroy()
            await updater.restart()
            return

        update_notice_body.value = "Failed to update."
        update_now_btn.disabled = False
        update_later_btn.disabled = False
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
        set_mic_indicator(True, f"Running ({current_mic})")
        text_transcription.value = "Listening..."
        if config.USE_TRANSLATE:
            text_translation.value = "Waiting for translation..."
        else:
            text_translation.value = "(Translation is disabled)"
        page.update()
        
        # create the event in Flet's active loop
        stop_event = asyncio.Event()
        
        # Run STT entirely inside Flet's async loop
        page.run_task(STT_main.run_loop, stop_event, gui_callback)
        page.run_task(refresh_mic_name, True, False)

    def stop_clicked(e):
        nonlocal stop_event
        if stop_event:
            stop_event.set()

        # Keep recognized content, but clear interim states when stopped without speech.
        if text_transcription.value in ("Listening...", "Running..."):
            text_transcription.value = "Transcription will appear here..."
        if config.USE_TRANSLATE:
            if text_translation.value == "Waiting for translation...":
                text_translation.value = "Translation will appear here..."
        else:
            text_translation.value = "(Translation is disabled)"
            
        start_btn.disabled = False
        stop_btn.disabled = True
        set_mic_indicator(False, f"Stopped ({current_mic})")
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

    update_notice_body = ft.Text(size=14, selectable=False)
    update_later_btn = ft.TextButton("Later", on_click=hide_update_notice)
    update_now_btn = ft.FilledButton("Update Now")

    update_notice = ft.Container(
        visible=False,
        alignment=ft.Alignment.BOTTOM_RIGHT,
        margin=ft.Margin(top=10, right=10),
        content=ft.Card(
            elevation=6,
            content=ft.Container(
                width=300,
                padding=10,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SYSTEM_UPDATE, color=ft.Colors.BLUE_300),
                                ft.Text("Update", weight=ft.FontWeight.W_600),
                            ],
                            spacing=8,
                        ),
                        update_notice_body,
                        ft.Row(
                            controls=[update_later_btn, update_now_btn],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    tight=True,
                    spacing=10,
                ),
            ),
        ),
    )

    app_root = ft.Stack(
        controls=[app_content, update_notice],
        expand=True,
    )

    def build_app_view() -> ft.View:
        return ft.View(
            route="/app",
            appbar=app_appbar,
            controls=[app_root]
        )

    def save_settings(e):
        config.STT_ENGINE = stt_engine.value
        config.BASE_URL = base_url.value
        use_vad_value = use_vad.value
        if isinstance(use_vad_value, str):
            config.USE_VAD = use_vad_value.lower() == "true"
        else:
            config.USE_VAD = bool(use_vad_value)
        try:
            config.VAD_THRESHOLD = float(vad_threashold.value)
        except ValueError:
            pass  # Ignore invalid input
        try:
            config.VAD_THREADS = int(vad_threads.value)
        except ValueError:
            pass  # Ignore invalid input
        config.TRANSLATOR = translator.value
        config.API_KEY = api_key.value
        config.LOG_LEVEL = log_level.value
        config.save()
        refresh_source_lang_dropdown()
        page.update()

    # Settings
    def section_header(icon: ft.Icon, title: str, badge: ft.Control | None = None):
        row_controls = [
            ft.Container(
                content=icon,
                width=32, height=32,
                border_radius=6,
                bgcolor=ft.Colors.BLUE_900,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(
                controls=[
                    ft.Text(title, size=15, weight=ft.FontWeight.W_500),
                ],
                spacing=1,
                tight=True,
            ),
        ]
        if badge:
            row_controls.append(
                ft.Container(content=badge, expand=True, alignment=ft.Alignment.CENTER_RIGHT)
            )
        return ft.Container(
            content=ft.Row(controls=row_controls, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=16, right=16, top=12, bottom=12),
            border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.WHITE_12)),
        )

    def setting_row(label: str, hint: str, control: ft.Control):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(label, size=13, weight=ft.FontWeight.W_500),
                            ft.Text(hint, size=11, color=ft.Colors.WHITE_54),
                        ],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                    control,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=16, right=16, top=12, bottom=12),
        )

    def settings_card(*rows: ft.Control):
        return ft.Container(
            content=ft.Column(controls=list(rows), spacing=0, tight=True),
            margin=ft.Margin(bottom=12)
        )

    DROPDOWN_STYLE = dict(
        border_color=ft.Colors.WHITE_24,
        width=200,
        text_size=13,
    )

    TEXTFIELD_STYLE = dict(
        border_color=ft.Colors.WHITE_24,
        width=260,
        text_size=13,
        border_radius=8,
    )

    stt_engine = ft.Dropdown(
        label=None,
        options=[
            ft.dropdown.Option("voxbox", "VoxBox"),
            ft.dropdown.Option("edgestt", "EdgeSTT"),
        ],
        value=config.STT_ENGINE,
        on_select=save_settings,
        **DROPDOWN_STYLE,
    )

    base_url = ft.TextField(
        hint_text="http://localhost:8080",
        value=config.BASE_URL,
        on_change=save_settings,
        **TEXTFIELD_STYLE,
    )

    use_vad = ft.Dropdown(
        label=None,
        options=[
            ft.dropdown.Option("true", "Enabled"),
            ft.dropdown.Option("false", "Disabled"),
        ],
        value="true" if config.USE_VAD else "false",
        on_select=save_settings,
        **DROPDOWN_STYLE,
    )

    vad_threashold = ft.TextField(
        hint_text="0.5",
        value=str(config.VAD_THRESHOLD),
        width=100,
        text_align=ft.TextAlign.RIGHT,
        text_size=13,
        border_color=ft.Colors.WHITE_24,
        border_radius=8,
        on_change=save_settings,
    )

    vad_threads = ft.TextField(
        hint_text="4",
        value=str(config.VAD_THREADS),
        width=100,
        text_align=ft.TextAlign.RIGHT,
        text_size=13,
        border_color=ft.Colors.WHITE_24,
        border_radius=8,
        on_change=save_settings,
    )

    translator = ft.Dropdown(
        label=None,
        options=[
            ft.dropdown.Option("google", "Google Translate"),
            ft.dropdown.Option("deepl", "DeepL"),
            ft.dropdown.Option("gemini", "Gemini"),
        ],
        value=config.TRANSLATOR,
        on_select=save_settings,
        **DROPDOWN_STYLE,
    )

    api_key = ft.TextField(
        hint_text="Enter API Key",
        value=config.API_KEY,
        password=True,
        can_reveal_password=True,
        on_change=save_settings,
        **TEXTFIELD_STYLE,
    )

    log_level = ft.Dropdown(
        label=None,
        options=[ft.dropdown.Option(l) for l in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]],
        value=config.LOG_LEVEL,
        on_select=save_settings,
        **DROPDOWN_STYLE,
    )

    def build_settings_view() -> ft.View:
        content = ft.Column(
            controls=[
                settings_card(
                    section_header(
                        ft.Icon(ft.Icons.MIC, size=16, color=ft.Colors.WHITE_54),
                        "Speech to Text",
                    ),
                    setting_row("STT Engine", "Vox-Box uses local, EdgeSTT uses MS Cloud", stt_engine),
                    setting_row("Base URL", "Vox-Box API endpoint (e.g http://localhost:8080)", base_url),
                ),
                settings_card(
                    section_header(
                        ft.Icon(ft.Icons.GRAPHIC_EQ, size=16, color=ft.Colors.WHITE_54),
                        "Voice Activity Detection",
                    ),
                    setting_row("Use VAD", "Available only when using Vox-Box", use_vad),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=setting_row(
                                        "Threshold",
                                        "Sensitivity: 0.0 (high) - 1.0 (low)",
                                        vad_threashold,
                                    ),
                                    expand=True,
                                    border=ft.Border(right=ft.BorderSide(1, ft.Colors.WHITE_12)),
                                ),
                                ft.Container(
                                    content=setting_row(
                                        "Threads",
                                        "Number of threads used for processing",
                                        vad_threads,
                                    ),
                                    expand=True,
                                ),
                            ],
                            spacing=0,
                        ),
                    ),
                ),
                settings_card(
                    section_header(
                        ft.Icon(ft.Icons.TRANSLATE, size=16, color=ft.Colors.WHITE_54),
                        "Translation",
                    ),
                    setting_row(
                        "Translation Provider",
                        "Google is free. DeepL and Gemini require an API key",
                        translator,
                    ),
                    setting_row(
                        "API Key",
                        "Required when using DeepL or Gemini",
                        api_key,
                    ),
                ),
                settings_card(
                    section_header(
                        ft.Icon(ft.Icons.SETTINGS, size=16, color=ft.Colors.WHITE_54),
                        "System",
                    ),
                    setting_row(
                        "Log Level",
                        "INFO is recommended normally. Change to DEBUG when issues occur",
                        log_level,
                    ),
                ),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.View(
            route="/settings",
            appbar=ft.AppBar(
                title=ft.Text("Settings"),
                leading=ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda _: asyncio.create_task(page.push_route("/app")),
                ),
                bgcolor=ft.Colors.BLUE_900,
            ),
            controls=[
                ft.Container(
                    content=content,
                    padding=ft.Padding(left=24, right=24, top=20, bottom=20),
                    expand=True,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        if page.route == "/settings":
            page.views.append(build_app_view())
            page.views.append(build_settings_view())
        else:
            page.views.append(build_app_view())
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
