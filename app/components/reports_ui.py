import flet as ft
from datetime import datetime, timedelta
from reports import ReportGenerator

class ReportsScreen:
    def __init__(self, user, db, on_back):
        self.user = user
        self.db = db
        self.on_back = on_back
        self.report_generator = ReportGenerator(db)
        
        # Filtros de data
        today = datetime.now()
        self.start_date = ft.DatePicker(
            label="Data Inicial",
            value=today - timedelta(days=30),
            on_change=self.update_reports
        )
        self.end_date = ft.DatePicker(
            label="Data Final",
            value=today,
            on_change=self.update_reports
        )
        
        # Seletor de projeto para administradores
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
                on_change=self.update_reports
            )
        
        # Container para gráficos e relatórios
        self.content = ft.Column(scroll=ft.ScrollMode.AUTO)
        
    def create_metric_card(self, title, value, icon, color):
        """Cria um card de métrica."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=30, color=color),
                    ft.Text(title, size=16, color=ft.colors.GREY_800),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                padding=20
            ),
            width=200
        )
        
    def create_chart_card(self, title, chart_html):
        """Cria um card com gráfico."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    ft.Html(content=chart_html, expand=True)
                ], spacing=10),
                padding=20
            ),
            expand=True
        )
        
    def create_project_summary_card(self, summary_data):
        """Cria um card de resumo do projeto."""
        if not summary_data:
            return None
            
        metrics = []
        for metric in summary_data['metrics']:
            metrics.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(metric['label'], size=12, color=ft.colors.GREY_700),
                        ft.Text(metric['value'], size=16, weight=ft.FontWeight.BOLD)
                    ], spacing=5),
                    padding=10
                )
            )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(summary_data['title'], size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(summary_data['description'], size=14, color=ft.colors.GREY_700),
                    ft.Divider(),
                    ft.Row(metrics, wrap=True)
                ], spacing=10),
                padding=20
            )
        )
        
    def update_reports(self, e=None):
        """Atualiza todos os relatórios com base nos filtros."""
        self.content.controls = []
        
        # Obtém dados filtrados
        user_id = None if self.user.get('role') == 'admin' else self.user['id']
        project_id = None if not self.project_dropdown or self.project_dropdown.value == "todos" else int(self.project_dropdown.value)
        
        # Gera relatórios
        productivity_data = self.report_generator.generate_productivity_report(
            user_id=user_id,
            start_date=self.start_date.value,
            end_date=self.end_date.value
        )
        
        if productivity_data:
            total_hours = sum(float(d['total_hours'] or 0) for d in productivity_data)
            avg_activity = sum(float(d['avg_activity'] or 0) for d in productivity_data) / len(productivity_data)
            completed_tasks = sum(int(d['completed_tasks'] or 0) for d in productivity_data)
            
            # Métricas principais
            metrics_row = ft.Row([
                self.create_metric_card("Horas Totais", f"{total_hours:.1f}h", ft.icons.TIMER, ft.colors.BLUE),
                self.create_metric_card("Atividade Média", f"{avg_activity:.1f}%", ft.icons.TRENDING_UP, ft.colors.GREEN),
                self.create_metric_card("Tarefas Concluídas", str(completed_tasks), ft.icons.TASK_ALT, ft.colors.ORANGE)
            ], alignment=ft.MainAxisAlignment.CENTER)
            
            self.content.controls.append(metrics_row)
            
            # Gráficos de produtividade
            charts = self.report_generator.plot_productivity_trends(productivity_data)
            if charts:
                self.content.controls.extend([
                    ft.Divider(height=20),
                    self.create_chart_card("Horas por Projeto", charts['hours']),
                    ft.Divider(height=20),
                    self.create_chart_card("Nível de Atividade", charts['activity'])
                ])
                
            # Heatmap de atividade para usuário específico
            if user_id:
                activity_data = self.report_generator.generate_activity_heatmap(
                    user_id,
                    self.start_date.value,
                    self.end_date.value
                )
                if activity_data:
                    heatmap_html = self.report_generator.plot_activity_heatmap(activity_data)
                    if heatmap_html:
                        self.content.controls.extend([
                            ft.Divider(height=20),
                            self.create_chart_card("Padrão de Atividade", heatmap_html)
                        ])
                        
            # Resumo do projeto se selecionado
            if project_id:
                project_data = self.report_generator.generate_project_summary(
                    project_id,
                    self.start_date.value,
                    self.end_date.value
                )
                if project_data:
                    summary_card = self.create_project_summary_card(
                        self.report_generator.format_summary_card(project_data)
                    )
                    progress_chart = self.report_generator.plot_project_progress(project_data)
                    
                    self.content.controls.extend([
                        ft.Divider(height=20),
                        summary_card,
                        ft.Divider(height=20),
                        self.create_chart_card("Progresso do Projeto", progress_chart)
                    ])
                    
        self.content.update()
        
    def build(self):
        """Constrói a tela de relatórios."""
        # Barra superior com filtros
        filters_row = ft.Row([
            self.start_date,
            self.end_date
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
        
        if self.project_dropdown:
            filters_row.controls.append(self.project_dropdown)
            
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    tooltip="Voltar",
                    on_click=self.on_back
                ),
                ft.Text("Relatórios e Análises", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                filters_row
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        # Atualiza relatórios iniciais
        self.update_reports()
        
        return ft.Column([
            header,
            self.content
        ], expand=True, scroll=ft.ScrollMode.AUTO)