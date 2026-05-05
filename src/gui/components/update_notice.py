from typing import Callable

import flet as ft


def build_update_notice(
    on_later_click: Callable[[ft.ControlEvent], None],
) -> tuple[ft.Container, ft.Text, ft.FilledButton, ft.TextButton]:
    update_notice_body = ft.Text(size=14, selectable=False)
    update_later_btn = ft.TextButton("Later", on_click=on_later_click)
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

    return update_notice, update_notice_body, update_now_btn, update_later_btn
