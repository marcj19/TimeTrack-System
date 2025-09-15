import flet as ft
import os
from dotenv import load_dotenv
from db import Database
from auth import AuthManager
from ui_login import LoginScreen
from ui_dashboard import DashboardScreen

load_dotenv()

class TimeTrackApp:
    def __init__(self):
        self.db = Database()
        self.auth = AuthManager(self.db)
        self.current_user = None
        self.dark_mode = True
        
    def main(self, page: ft.Page):
        self.page = page
        page.title = "TimeTrack - Sistema de Controle de Ponto"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.spacing = 0
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600
        
        # Configurar tema personalizado
        page.theme = ft.Theme(
            color_scheme_seed=ft.colors.BLUE,
            use_material3=True
        )
        
        # Iniciar com tela de login
        self.show_login()
        
    def show_login(self):
        login_screen = LoginScreen(self.auth, self.on_login_success, self.toggle_theme)
        self.page.clean()
        self.page.add(login_screen.build())
        self.page.update()
        
    def on_login_success(self, user):
        self.current_user = user
        dashboard = DashboardScreen(
            user=user, 
            db=self.db, 
            auth=self.auth,
            on_logout=self.show_login,
            toggle_theme=self.toggle_theme,
            dark_mode=self.dark_mode
        )
        self.page.clean()
        self.page.add(dashboard.build())
        self.page.update()
        
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.page.theme_mode = ft.ThemeMode.DARK if self.dark_mode else ft.ThemeMode.LIGHT
        self.page.update()

def main(page: ft.Page):
    app = TimeTrackApp()
    app.main(page)

if __name__ == "__main__":
    ft.app(target=main)