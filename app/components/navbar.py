import flet as ft
from components.consent_manager import ConsentManager

class NavBar:
    def __init__(self, user, db, on_logout, toggle_theme, dark_mode):
        self.user = user
        self.db = db
        self.on_logout = on_logout
        self.toggle_theme = toggle_theme
        self.dark_mode = dark_mode
        self.consent_manager = None
        
    def build(self):
        """Constrói navbar"""
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, size=30, color=ft.Colors.BLUE),
                    ft.Text("TimeTrack", size=20, weight=ft.FontWeight.BOLD)
                ]),
                
                ft.Row([
                    ft.Text(f"{self.user['full_name']}", size=14),
                    ft.VerticalDivider(width=10),
                    ft.IconButton(
                        icon=ft.Icons.PRIVACY_TIP,
                        tooltip="Configurações de Privacidade",
                        on_click=self.show_privacy_settings
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE if self.dark_mode else ft.Icons.LIGHT_MODE,
                        tooltip="Alternar tema",
                        on_click=lambda _: self.toggle_theme()
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        tooltip="Sair",
                        on_click=lambda _: self.on_logout()
                    )
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=30, vertical=15),
            bgcolor=ft.Colors.ON_SURFACE_VARIANT,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
        )
        
    def show_privacy_settings(self, e):
        """Mostra as configurações de privacidade"""
        if not self.consent_manager:
            self.consent_manager = ConsentManager(self.db, self.user)
        self.consent_manager.show(e.page)