import flet as ft
from datetime import datetime

class TaskCard:
    def __init__(self, task, on_status_change=None, on_select=None):
        self.task = task
        self.on_status_change = on_status_change
        self.on_select = on_select
        
        # Define cores baseadas no status
        self.status_colors = {
            'pending': ft.colors.ORANGE,
            'in_progress': ft.colors.BLUE,
            'completed': ft.colors.GREEN
        }
        
    def build(self):
        status_dropdown = ft.Dropdown(
            value=self.task['status'],
            options=[
                ft.dropdown.Option('pending', 'Pendente'),
                ft.dropdown.Option('in_progress', 'Em Andamento'),
                ft.dropdown.Option('completed', 'Concluída')
            ],
            on_change=lambda e: self.on_status_change(self.task['id'], e.data) if self.on_status_change else None,
            width=150
        )
        
        hours_spent = float(self.task['total_hours_spent']) if self.task.get('total_hours_spent') else 0
        users_count = int(self.task['total_users']) if self.task.get('total_users') else 0
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            self.task['name'],
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            expand=True
                        ),
                        status_dropdown
                    ]),
                    ft.Text(
                        self.task['description'] or "Sem descrição",
                        size=14,
                        color=ft.colors.GREY
                    ),
                    ft.Divider(),
                    ft.Row([
                        ft.Text(
                            f"⏱️ {hours_spent:.1f}h",
                            size=12,
                            color=ft.colors.BLUE
                        ),
                        ft.Text(
                            f"👥 {users_count} usuário(s)",
                            size=12,
                            color=ft.colors.GREY
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=15,
                on_click=lambda e: self.on_select(self.task) if self.on_select else None
            ),
            elevation=2
        )

class ProjectManager:
    def __init__(self, db, user):
        self.db = db
        self.user = user
        self.selected_project = None
        self.current_tasks = []
        
        # Dialog de nova tarefa
        self.task_name_field = ft.TextField(
            label="Nome da Tarefa",
            autofocus=True
        )
        self.task_description_field = ft.TextField(
            label="Descrição",
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        self.task_error_text = ft.Text("", color=ft.colors.RED, size=12)
        
        self.new_task_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nova Tarefa"),
            content=ft.Column([
                self.task_name_field,
                self.task_description_field,
                self.task_error_text
            ], tight=True, spacing=15),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dialog),
                ft.FilledButton("Criar", on_click=self.handle_new_task),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        # Dialog de detalhes da tarefa
        self.task_details_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalhes da Tarefa"),
            content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=400),
            actions=[
                ft.TextButton("Fechar", on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
    def close_dialog(self, e):
        if hasattr(self, 'page') and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
            
    def show_task_dialog(self, e=None):
        self.task_name_field.value = ""
        self.task_description_field.value = ""
        self.task_error_text.value = ""
        
        self.page.dialog = self.new_task_dialog
        self.new_task_dialog.open = True
        self.page.update()
        
    def handle_new_task(self, e):
        name = self.task_name_field.value.strip()
        description = self.task_description_field.value.strip()
        
        if not name:
            self.task_error_text.value = "O nome da tarefa é obrigatório"
            self.page.dialog.update()
            return
            
        result = self.db.add_task(
            self.selected_project['id'],
            name,
            description or None
        )
        
        if result:
            self.close_dialog(e)
            self.load_tasks()  # Recarrega as tarefas
        else:
            self.task_error_text.value = "Erro ao criar tarefa"
            self.page.dialog.update()
            
    def handle_task_status_change(self, task_id, new_status):
        result = self.db.update_task_status(task_id, new_status)
        if result:
            self.load_tasks()
            
    def show_task_details(self, task):
        entries = self.db.get_task_time_entries(task['id'])
        
        content = [
            ft.Text(task['name'], size=20, weight=ft.FontWeight.BOLD),
            ft.Text(
                task['description'] or "Sem descrição",
                size=14,
                color=ft.colors.GREY
            ),
            ft.Divider(),
            ft.Text("Registros de Tempo:", size=16, weight=ft.FontWeight.BOLD)
        ]
        
        if entries:
            for entry in entries:
                content.append(
                    ft.ListTile(
                        title=ft.Text(entry['full_name']),
                        subtitle=ft.Text(
                            f"{entry['check_in'].strftime('%d/%m %H:%M')} - "
                            f"{entry['check_out'].strftime('%H:%M') if entry['check_out'] else 'Em andamento'}"
                        ),
                        trailing=ft.Text(
                            f"{float(entry['total_hours']):.1f}h" if entry['total_hours'] else "--"
                        )
                    )
                )
        else:
            content.append(
                ft.Text(
                    "Nenhum registro de tempo para esta tarefa",
                    color=ft.colors.GREY
                )
            )
            
        self.task_details_dialog.content.controls = content
        self.page.dialog = self.task_details_dialog
        self.task_details_dialog.open = True
        self.page.update()
        
    def load_tasks(self):
        if self.selected_project:
            self.current_tasks = self.db.get_project_tasks(self.selected_project['id'])
            self.tasks_view.update()
            
    def build(self, page):
        self.page = page
        
        # Dropdown de projetos
        projects = self.db.get_active_projects()
        project_dropdown = ft.Dropdown(
            label="Selecione um Projeto",
            options=[
                ft.dropdown.Option(
                    key=str(p['id']),
                    text=f"{p['name']} ({p['completed_tasks']}/{p['total_tasks']} tarefas)"
                )
                for p in projects
            ],
            width=300,
            on_change=lambda e: self.on_project_selected(
                next(p for p in projects if str(p['id']) == e.data)
            )
        )
        
        # Botão de nova tarefa
        new_task_btn = ft.ElevatedButton(
            "Nova Tarefa",
            icon=ft.icons.ADD,
            on_click=self.show_task_dialog,
            disabled=True  # Inicia desabilitado
        )
        
        # View de tarefas
        self.tasks_view = ft.GridView(
            expand=True,
            runs_count=5,
            max_extent=250,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        def update_tasks_view():
            if not self.current_tasks:
                self.tasks_view.controls = [
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.TASK, size=40, color=ft.colors.GREY_400),
                            ft.Text("Nenhuma tarefa encontrada", color=ft.colors.GREY_400)
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        alignment=ft.alignment.center
                    )
                ]
            else:
                self.tasks_view.controls = [
                    TaskCard(
                        task,
                        on_status_change=self.handle_task_status_change,
                        on_select=self.show_task_details
                    ).build()
                    for task in self.current_tasks
                ]
        
        self.tasks_view.update = update_tasks_view
        
        def on_project_selected(project):
            self.selected_project = project
            new_task_btn.disabled = False
            self.load_tasks()
            new_task_btn.update()
            
        self.on_project_selected = on_project_selected
        
        return ft.Column([
            ft.Row([
                project_dropdown,
                new_task_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.tasks_view
        ], expand=True, spacing=20)