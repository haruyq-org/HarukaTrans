import flet as ft


def build_app_view(app_bar: ft.AppBar, app_root: ft.Control) -> ft.View:
    return ft.View(
        route="/app",
        appbar=app_bar,
        controls=[app_root],
    )
