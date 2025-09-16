import flet as ft
from components.project_manager import ProjectManager

class ProjectManagerScreen:
    def __init__(self, db, user, on_back):
        self.db = db
        self.user = user
        self.on_back = on_back
        self.project_manager = ProjectManager(db, user)
        
    def build(self, page):
        """Constrói a interface de gerenciamento de projetos"""
        header = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self.on_back,
                icon_color=ft.Colors.BLUE
            ),
            ft.Text("Gerenciamento de Projetos", size=24, weight=ft.FontWeight.BOLD),
        ])
        
        return ft.Column([
            header,
            ft.Divider(),
            self.project_manager.build(page)
        ], expand=True)