from typing import Callable

import flet as ft


def build_app_bar(
    version: str,
    translate_btn: ft.Control,
    on_settings_click: Callable[[], None],
) -> ft.AppBar:
    return ft.AppBar(
        title=ft.Text(
            spans=[
                ft.TextSpan(
                    "HarukaTrans",
                    ft.TextStyle(size=22),
                ),
                ft.TextSpan(
                    f"  {version}",
                    ft.TextStyle(size=12, color=ft.Colors.WHITE_54),
                ),
            ]
        ),
        bgcolor=ft.Colors.BLUE_900,
        actions=[
            translate_btn,
            ft.IconButton(
                ft.Icons.SETTINGS,
                margin=ft.Margin(right=10),
                on_click=lambda _: on_settings_click(),
            ),
        ],
    )
