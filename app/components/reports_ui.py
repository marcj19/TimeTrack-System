# Arquivo: app/components/reports_ui.py (VERSÃO PARA FLET ATUALIZADO)

import flet as ft
from datetime import datetime, timedelta
from reports import ReportGenerator

class ReportsScreen:
    def __init__(self, user, db, on_back):
        self.user = user
        self.db = db
        self.on_back = on_back
        self.report_generator = ReportGenerator(db)
        
        today = datetime.now().date()
        start_default = today - timedelta(days=30)
        
        # Com o Flet atualizado, o on_change aponta para a função que lida com o evento
        self.start_date_picker = ft.DatePicker(
            value=start_default,
            on_change=self._handle_filter_change
        )
        self.end_date_picker = ft.DatePicker(
            value=today,
            on_change=self._handle_filter_change
        )

        # Usamos o método .pick_date() que existe nas versões recentes do Flet
        self.start_date_field = ft.TextField(
            label="Data Inicial",
            value=start_default.strftime('%d/%m/%Y'),
            read_only=True,
            on_focus=lambda _: self.start_date_picker.pick_date(),
            width=150
        )
        self.end_date_field = ft.TextField(
            label="Data Final",
            value=today.strftime('%d/%m/%Y'),
            read_only=True,
            on_focus=lambda _: self.end_date_picker.pick_date(),
            width=150
        )
        
        self.project_dropdown = None
        if self.user.get('role') == 'admin':
            projects = self.db.get_active_projects()
            self.project_dropdown = ft.Dropdown(
                label="Projeto",
                options=[
                    ft.dropdown.Option("todos", "Todos os Projetos")
                ] + [
                    ft.dropdown.Option(str(p['id']), p['name'])
                    for p in (projects or [])
                ],
                value="todos",
                on_change=self._handle_filter_change,
                width=250
            )
        
        self.content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def _handle_filter_change(self, e=None):
        if self.start_date_picker.value:
            self.start_date_field.value = self.start_date_picker.value.strftime('%d/%m/%Y')
        if self.end_date_picker.value:
            self.end_date_field.value = self.end_date_picker.value.strftime('%d/%m/%Y')
        
        self.start_date_field.update()
        self.end_date_field.update()
        
        self._load_reports_data()

    def _load_reports_data(self):
        self.content.controls = [ft.Row([ft.ProgressRing()], alignment=ft.MainAxisAlignment.CENTER)]
        if self.content.page:
             self.content.update()

        user_id = None if self.user.get('role') == 'admin' else self.user['id']
        project_id = None if not self.project_dropdown or self.project_dropdown.value == "todos" else int(self.project_dropdown.value)
        
        start_date = self.start_date_picker.value
        end_date = self.end_date_picker.value

        productivity_data = self.report_generator.generate_productivity_report(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        self.content.controls = []
        
        if productivity_data:
            total_hours = sum(float(d.get('total_hours', 0) or 0) for d in productivity_data)
            valid_activity = [d for d in productivity_data if d.get('avg_activity') is not None]
            avg_activity = sum(float(d.get('avg_activity', 0) or 0) for d in valid_activity) / len(valid_activity) if valid_activity else 0
            completed_tasks = sum(int(d.get('completed_tasks', 0) or 0) for d in productivity_data)

            metrics_row = ft.Row([
                self.create_metric_card("Horas Totais", f"{total_hours:.1f}h", ft.iIconscons.TIMER, ft.colors.BLUE),
                self.create_metric_card("Atividade Média", f"{avg_activity:.1f}%", ft.Icons.TRENDING_UP, ft.colors.GREEN),
                self.create_metric_card("Tarefas Concluídas", str(completed_tasks), ft.Icons.TASK_ALT, ft.colors.ORANGE)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20, wrap=True)
            self.content.controls.append(metrics_row)
            
            charts = self.report_generator.plot_productivity_trends(productivity_data)
            if charts:
                self.content.controls.extend([
                    ft.Divider(height=20),
                    self.create_chart_card("Horas por Projeto", charts['hours']),
                    ft.Divider(height=20),
                    self.create_chart_card("Nível de Atividade", charts['activity'])
                ])

        else:
            self.content.controls.append(
                ft.Row([ft.Text("Nenhum dado encontrado para os filtros selecionados.", size=16)], alignment=ft.MainAxisAlignment.CENTER)
            )
            
        if self.content.page:
            self.content.update()
        
    def create_metric_card(self, title, value, icon, color):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=30, color=color),
                    ft.Text(title, size=16, color=ft.colors.GREY_800),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
                alignment=ft.alignment.center
            ),
            width=220,
            height=180
        )
        
    def create_chart_card(self, title, chart_html):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(content=ft.Html(data=chart_html), height=400)
                ], spacing=10),
                padding=20
            )
        )
        
    def build(self, page: ft.Page):
        """Constrói a tela de relatórios."""
        page.overlay.extend([self.start_date_picker, self.end_date_picker])

        filters_row = ft.Row([
            self.start_date_field,
            self.end_date_field
        ], alignment=ft.MainAxisAlignment.START, spacing=20, wrap=True)
        
        if self.project_dropdown:
            filters_row.controls.append(self.project_dropdown)
            
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Voltar", on_click=self.on_back),
                ft.Text("Relatórios e Análises", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                filters_row
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        self._load_reports_data()
        
        return ft.Column([
            header,
            self.content
        ], expand=True)