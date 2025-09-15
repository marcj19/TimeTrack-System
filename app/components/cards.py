import flet as ft
from datetime import datetime

class StatsCard:
    def __init__(self, title, value, icon, color):
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        
    def build(self):
        """Constrói card de estatística"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(self.icon, size=40, color=self.color),
                    ft.Column([
                        ft.Text(self.title, size=14, color=ft.colors.GREY),
                        ft.Text(self.value, size=24, weight=ft.FontWeight.BOLD)
                    ], spacing=5)
                ], alignment=ft.MainAxisAlignment.START, spacing=15),
                padding=20,
                width=250
            ),
            elevation=5
        )

class TimeCard:
    def __init__(self, is_checked_in, on_checkin, on_checkout, check_in_time):
        self.is_checked_in = is_checked_in
        self.on_checkin = on_checkin
        self.on_checkout = on_checkout
        self.check_in_time = check_in_time
        
    def build(self):
        """Constrói card de controle de ponto"""
        button_text = "Check-out" if self.is_checked_in else "Check-in"
        button_color = ft.colors.RED if self.is_checked_in else ft.colors.GREEN
        button_icon = ft.icons.LOGOUT if self.is_checked_in else ft.icons.LOGIN
        on_click = self.on_checkout if self.is_checked_in else self.on_checkin
        
        time_info = ft.Text("--:--", size=16, weight=ft.FontWeight.BOLD)
        if self.check_in_time:
            time_info = ft.Text(
                f"Entrada: {self.check_in_time.strftime('%H:%M')}",
                size=14,
                color=ft.colors.GREY
            )
            
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Controle de Ponto", size=16, weight=ft.FontWeight.BOLD),
                    time_info,
                    ft.ElevatedButton(
                        text=button_text,
                        icon=button_icon,
                        on_click=on_click,
                        style=ft.ButtonStyle(
                            bgcolor=button_color,
                            color=ft.colors.WHITE
                        ),
                        width=150
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                padding=20,
                width=250
            ),
            elevation=5
        )