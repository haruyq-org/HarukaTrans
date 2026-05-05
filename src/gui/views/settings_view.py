import asyncio

import flet as ft

from src.gui.components.settings_cards import (
    DROPDOWN_STYLE,
    TEXTFIELD_STYLE,
    section_header,
    setting_row,
    settings_card,
)


def build_settings_view(page: ft.Page, config, refresh_source_lang_dropdown) -> ft.View:
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
        options=[
            ft.dropdown.Option(l)
            for l in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        ],
        value=config.LOG_LEVEL,
        on_select=save_settings,
        **DROPDOWN_STYLE,
    )

    content = ft.Column(
        controls=[
            settings_card(
                section_header(
                    ft.Icon(ft.Icons.MIC, size=16, color=ft.Colors.WHITE_54),
                    "Speech to Text",
                ),
                setting_row(
                    "STT Engine",
                    "Vox-Box uses local, EdgeSTT uses MS Cloud",
                    stt_engine,
                ),
                setting_row(
                    "Base URL",
                    "Vox-Box API endpoint (e.g http://localhost:8080)",
                    base_url,
                ),
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
