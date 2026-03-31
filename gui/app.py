import main as STT_main
from utils.path import resource_path
from config import config

import flet as ft
import asyncio
import sys
import os

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
                    f"  {config.__version__}",
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
    
    text_transcription = ft.Text("Transcription will appear here...", size=18, selectable=True)
    text_translation = ft.Text("Translation will appear here...", size=18, selectable=True)

    def create_textarea(text_control: ft.Text):
        return ft.Container(
            content=text_control,
            border=ft.Border.all(1, ft.Colors.WHITE_54),
            border_radius=8,
            padding=20,
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
    
    mic_status = ft.Text("Not Running", color=ft.Colors.BLUE_500, size=16)
    mic_icon = ft.Icon(ft.Icons.MIC_OFF, color=ft.Colors.BLUE_500, size=20)

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

    def start_clicked(e):
        nonlocal stop_event
        
        start_btn.disabled = True
        stop_btn.disabled = False
        set_mic_indicator(True, "Running (Listening...)")
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
        set_mic_indicator(False, "Stopped")
        page.update()

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

    def build_app_view() -> ft.View:
        return ft.View(
            route="/app",
            appbar=app_appbar,
            controls=[app_content]
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
    stt_engine = ft.Dropdown(
        label="STT Engine",
        options=[
            ft.dropdown.Option("voxbox", "VoxBox"),
            ft.dropdown.Option("edgestt", "EdgeSTT"),
        ],
        value=config.STT_ENGINE,
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        on_select=save_settings,
    )

    base_url = ft.TextField(
        label="VoxBox Base URL",
        value=config.BASE_URL,
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        on_change=save_settings,
    )
    
    use_vad = ft.Dropdown(
        label="Use VAD",
        options=[ft.dropdown.Option(True, "Enabled"), ft.dropdown.Option(False, "Disabled")],
        value=config.USE_VAD,
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        on_select=save_settings,
    )
    
    vad_threashold = ft.TextField(
        label="VAD Threshold",
        value=str(config.VAD_THRESHOLD),
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        on_change=save_settings,
    )
    
    vad_threads = ft.TextField(
        label="VAD Threads",
        value=str(config.VAD_THREADS),
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        on_change=save_settings,
    )
    
    translator = ft.Dropdown(
        label="Translator",
        options=[
            ft.dropdown.Option("google", "Google Translate"),
            ft.dropdown.Option("deepl", "DeepL"),
            ft.dropdown.Option("gemini", "Gemini"),
        ],
        value=config.TRANSLATOR,
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        on_select=save_settings,
    )
    
    api_key = ft.TextField(
        label="Translator API Key",
        value=config.API_KEY,
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        password=True,
        on_change=save_settings,
    )
    
    log_level = ft.Dropdown(
        label="Log Level",
        options=[
            ft.dropdown.Option("DEBUG"),
            ft.dropdown.Option("INFO"),
            ft.dropdown.Option("WARNING"),
            ft.dropdown.Option("ERROR"),
            ft.dropdown.Option("CRITICAL"),
        ],
        value=config.LOG_LEVEL,
        width=400,
        border_color=ft.Colors.WHITE_54,
        margin=ft.Margin(top=10),
        on_select=save_settings,
    )
    
    left_column = ft.Column(
        controls=[
            stt_engine,
            base_url,
            use_vad,
            vad_threashold,
            vad_threads,
        ],
        spacing=20,
    )

    right_column = ft.Column(
        controls=[
            translator,
            api_key,
            log_level,
        ],
        spacing=20,
    )
    
    settings_content = ft.Row(
        controls=[
            ft.Container(left_column, width=420),
            ft.Container(right_column, width=420),
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        spacing=40,
    )

    def build_settings_view() -> ft.View:
        return ft.View(
            route="/settings",
            appbar=ft.AppBar(
                title=ft.Text("Settings"),
                leading=ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda _: asyncio.create_task(page.push_route("/app"))
                ),
                bgcolor=ft.Colors.BLUE_900
            ),
            controls=[settings_content]
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

if __name__ == '__main__':
    ft.run(main)
