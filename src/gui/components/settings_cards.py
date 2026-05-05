import flet as ft


def section_header(icon: ft.Icon, title: str, badge: ft.Control | None = None) -> ft.Container:
    row_controls = [
        ft.Container(
            content=icon,
            width=32,
            height=32,
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
        content=ft.Row(
            controls=row_controls,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=16, right=16, top=12, bottom=12),
        border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.WHITE_12)),
    )


def setting_row(label: str, hint: str, control: ft.Control) -> ft.Container:
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


def settings_card(*rows: ft.Control) -> ft.Container:
    return ft.Container(
        content=ft.Column(controls=list(rows), spacing=0, tight=True),
        margin=ft.Margin(bottom=12),
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
