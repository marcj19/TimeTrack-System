# Arquivo: app/components/reports_ui.py (VERSÃO PARA FLET ATUALIZADO)

import flet as ft
from datetime import datetime, timedelta
import pandas as pd
import tempfile
import os
from reports import ReportGenerator

class ReportsScreen:
    def __init__(self, user, db, on_back):
        self.user = user
        self.db = db
        self.on_back = on_back
        self.report_generator = ReportGenerator(db)
        
        today = datetime.now().date()
        start_default = today - timedelta(days=30)
        
        self.file_picker = ft.FilePicker()
        
        # Define os valores iniciais das datas
        self.start_date = start_default
        self.end_date = today
        
        # Cria os pickers
        self.start_date_picker = ft.DatePicker(
            on_change=self._on_start_date_change
        )
        self.end_date_picker = ft.DatePicker(
            on_change=self._on_end_date_change
        )
        
        # Inicializa os campos de texto
        self.start_date_field = ft.TextField(
            label="Data Inicial",
            value=start_default.strftime('%d/%m/%Y'),
            read_only=True,
            width=150
        )
        self.end_date_field = ft.TextField(
            label="Data Final",
            value=today.strftime('%d/%m/%Y'),
            read_only=True,
            width=150
        )
        
        # Define os valores iniciais dos date pickers
        self.start_date = start_default
        self.end_date = today
        
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
        self._load_reports_data()

    def _on_start_date_change(self, e):
        if hasattr(e, 'control') and e.control and hasattr(e.control, 'value'):
            self.start_date = e.control.value
            self.start_date_field.value = self.start_date.strftime('%d/%m/%Y')
            self.start_date_field.update()
            self._load_reports_data()

    def _on_end_date_change(self, e):
        if hasattr(e, 'control') and e.control and hasattr(e.control, 'value'):
            self.end_date = e.control.value
            self.end_date_field.value = self.end_date.strftime('%d/%m/%Y')
            self.end_date_field.update()
            self._load_reports_data()

    def _load_reports_data(self):
        self.content.controls = [ft.Row([ft.ProgressRing()], alignment=ft.MainAxisAlignment.CENTER)]
        if self.content.page:
             self.content.update()

        user_id = None if self.user.get('role') == 'admin' else self.user['id']
        project_id = None if not self.project_dropdown or self.project_dropdown.value == "todos" else int(self.project_dropdown.value)
        
        productivity_data = self.report_generator.generate_productivity_report(
            user_id=user_id,
            project_id=project_id,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.content.controls = []
        
        if productivity_data:
            total_hours = sum(float(d.get('total_hours', 0) or 0) for d in productivity_data)
            valid_activity = [d for d in productivity_data if d.get('avg_activity') is not None]
            avg_activity = sum(float(d.get('avg_activity', 0) or 0) for d in valid_activity) / len(valid_activity) if valid_activity else 0
            completed_tasks = sum(int(d.get('completed_tasks', 0) or 0) for d in productivity_data)

            metrics_row = ft.Row([
                self.create_metric_card("Horas Totais", f"{total_hours:.1f}h", ft.Icons.TIMER, ft.colors.BLUE),
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
        
    def _handle_export(self, e=None):
        user_id = None if self.user.get('role') == 'admin' else self.user['id']
        project_id = None if not self.project_dropdown or self.project_dropdown.value == "todos" else int(self.project_dropdown.value)
        
        # Get the data
        data = self.report_generator.generate_productivity_report(
            user_id=user_id,
            project_id=project_id,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        if not data:
            self.content.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Não há dados para exportar no período selecionado."))
            )
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            df.to_csv(tmp.name, index=False, encoding='utf-8-sig')
            
            # Configure the file picker
            self.file_picker.save_file(
                dialog_title="Salvar Relatório",
                file_name=f"relatorio_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.csv",
                initial_directory=os.path.expanduser("~\\Documents"),
                allowed_extensions=["csv"],
                on_result=lambda e: self._save_exported_file(e, tmp.name) if e.path else None
            )
            
    def _save_exported_file(self, e, temp_file_path):
        """Save the exported file to the user's chosen location."""
        try:
            # Read the temporary file
            with open(temp_file_path, 'rb') as src:
                data = src.read()
                
            # Write to the destination
            with open(e.path, 'wb') as dst:
                dst.write(data)
                
            self.content.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Relatório exportado com sucesso!"))
            )
        except Exception as error:
            self.content.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Erro ao exportar relatório: {str(error)}"))
            )
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    def build(self, page: ft.Page):
        """Constrói a tela de relatórios."""
        # Adiciona os controles necessários ao overlay da página
        page.overlay.extend([
            self.start_date_picker,
            self.end_date_picker,
            self.file_picker
        ])
        
        # Adiciona os manipuladores de eventos para os campos de data
        self.start_date_field.on_click = lambda _: page.open(self.start_date_picker)
        self.end_date_field.on_click = lambda _: page.open(self.end_date_picker)
        
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
                ft.IconButton(
                    icon=ft.Icons.DOWNLOAD,
                    tooltip="Exportar Relatório",
                    on_click=self._handle_export
                ),
                filters_row
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        self._load_reports_data()
        
        return ft.Column([
            header,
            self.content
        ], expand=True)