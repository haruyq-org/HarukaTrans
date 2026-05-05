import flet as ft


def create_textarea(text_control: ft.Control) -> ft.Container:
    return ft.Container(
        content=text_control,
        border=ft.Border.all(1, ft.Colors.WHITE_54),
        border_radius=8,
        padding=10,
        width=400,
        height=250,
        alignment=ft.Alignment(-1.0, -1.0),
    )


def build_textarea_row(
    text_transcription: ft.Control,
    text_translation: ft.Control,
) -> ft.Row:
    return ft.Row(
        controls=[
            create_textarea(text_transcription),
            create_textarea(text_translation),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
        margin=ft.Margin(top=10),
    )
