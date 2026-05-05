import re

import flet as ft
import sounddevice as sd


def get_curr_mic(force_refresh: bool = False) -> str:
    try:
        if force_refresh:
            sd._terminate()
            sd._initialize()
        device = sd.query_devices(kind="input")
        name = device["name"].strip().rstrip("\x00")

        match = re.search(r"\((.+?)\)", name)
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


def set_mic_indicator(
    mic_icon: ft.Icon,
    mic_status: ft.Text,
    running: bool,
    status_text: str,
) -> None:
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


def build_mic_status(
    current_mic: str,
) -> tuple[ft.Row, ft.Icon, ft.Text]:
    mic_status = ft.Text(
        f"Stopped ({current_mic})",
        color=ft.Colors.RED_500,
        size=16,
    )
    mic_icon = ft.Icon(
        ft.Icons.MIC_OFF,
        color=ft.Colors.RED_500,
        size=20,
    )

    mic_status_row = ft.Row(
        controls=[
            mic_icon,
            mic_status,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
        margin=ft.Margin(top=5),
    )
    return mic_status_row, mic_icon, mic_status
