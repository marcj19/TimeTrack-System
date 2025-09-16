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
                        ft.Text(self.title, size=14, color=ft.Colors.GREY),
                        ft.Text(self.value, size=24, weight=ft.FontWeight.BOLD)
                    ], spacing=5)
                ], alignment=ft.MainAxisAlignment.START, spacing=15),
                padding=20,
                width=250
            ),
            elevation=5
        )

class TimeCard:
    def __init__(self, is_checked_in, on_checkin, on_checkout, on_break_start, on_break_end, 
                 checkin_time, project_dropdown, task_dropdown=None, is_on_break=False, 
                 break_start_time=None, on_manual_entry=None, is_admin=False):
        self.is_checked_in = is_checked_in
        self.is_on_break = is_on_break
        self.on_checkin = on_checkin
        self.on_checkout = on_checkout
        self.on_break_start = on_break_start
        self.on_break_end = on_break_end
        self.on_manual_entry = on_manual_entry
        self.is_admin = is_admin
        self.checkin_time = checkin_time
        self.break_start_time = break_start_time
        self.project_dropdown = project_dropdown
        self.task_dropdown = task_dropdown  # Novo: dropdown de tarefas
        
        # Dropdown para tipos de pausa
        self.break_type_dropdown = ft.Dropdown(
            label="Tipo de Pausa",
            options=[
                ft.dropdown.Option("lunch", "Almoço"),
                ft.dropdown.Option("rest", "Descanso"),
                ft.dropdown.Option("other", "Outro")
            ],
            width=200,
            border_radius=10,
        )

    def build(self):
        checkin_btn = ft.ElevatedButton(
            "▶️ Check-in",
            on_click=self.on_checkin,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            disabled=self.is_checked_in
        )
        
        checkout_btn = ft.ElevatedButton(
            "⏹️ Check-out",
            on_click=self.on_checkout,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
            disabled=not self.is_checked_in or self.is_on_break
        )
        
        break_btn = ft.ElevatedButton(
            "⏸️ Iniciar Pausa" if not self.is_on_break else "▶️ Retornar da Pausa",
            on_click=self.on_break_start if not self.is_on_break else self.on_break_end,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE if not self.is_on_break else ft.Colors.GREEN,
                color=ft.Colors.WHITE
            ),
            disabled=not self.is_checked_in
        )
        
        # Desabilita controles conforme o estado
        self.project_dropdown.disabled = self.is_checked_in
        self.break_type_dropdown.disabled = self.is_on_break or not self.is_checked_in

        # Displays de tempo
        time_display = "N/A"
        if self.is_checked_in and self.checkin_time:
            time_display = self.checkin_time.strftime('%H:%M:%S')
            
        break_time_display = "N/A"
        if self.is_on_break and self.break_start_time:
            break_time_display = self.break_start_time.strftime('%H:%M:%S')

        # Botão de registro manual
        manual_entry_btn = ft.OutlinedButton(
            "📝 Registro Manual",
            on_click=self.on_manual_entry,
            style=ft.ButtonStyle(color=ft.Colors.BLUE),
        ) if self.on_manual_entry else None

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Controle de Ponto", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        manual_entry_btn
                    ]) if manual_entry_btn else ft.Text("Controle de Ponto", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    self.project_dropdown,
                    ft.Row(
                        [checkin_btn, checkout_btn],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND
                    ),
                    ft.Divider(height=10),
                    ft.Text("Controle de Pausas", size=16, weight=ft.FontWeight.BOLD),
                    self.break_type_dropdown if not self.is_on_break else None,
                    break_btn,
                    ft.Row(
                        [
                            ft.Column([
                                ft.Text("Check-in às:"),
                                ft.Text(time_display, weight=ft.FontWeight.BOLD)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.VerticalDivider(),
                            ft.Column([
                                ft.Text("Início da Pausa:"),
                                ft.Text(
                                    break_time_display,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ORANGE if self.is_on_break else None
                                )
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND
                    )
                ], spacing=15),
                padding=20
            ),
            expand=True
        )