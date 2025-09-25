import flet as ft
from datetime import datetime, time
from components.navbar import NavBar
from components.cards import StatsCard, TimeCard
from components.charts import WeeklyChart
from components.tables import HistoryTable, UsersTable
from components.activity_monitor_ui import ActivityCard, ActivityGraph
from components.location_ui import LocationCard, LocationHistoryTable
from components.reports_ui import ReportsScreen
from activity_monitor import ActivityMonitor
from location_service import GeolocationService

class DashboardScreen:
    def __init__(self, user, db, auth, on_logout, toggle_theme, dark_mode):
        self.user = user
        self.db = db
        self.auth = auth
        self.on_logout = on_logout
        self.toggle_theme = toggle_theme
        self.dark_mode = dark_mode
        self.current_timetrack = None
        self.current_break = None
        self.is_checked_in = False
        self.is_on_break = False
        self.show_projects = False  # Controla a exibição da tela de projetos
        
        # Componentes e estado do monitoramento de atividade
        self.activity_monitor = None
        self.current_activity_level = 0
        self.activity_update_timer = None
        
        # Serviço de geolocalização
        self.location_service = GeolocationService()
        self.current_location = None
        self.location_details = None
        
        # Inicia monitoramento se o usuário estiver em um timetrack ativo e tiver consentido
        self.load_current_status()
        if self.is_checked_in and self.current_timetrack:
            if self.user.get('activity_tracking_consent'):
                self.start_activity_monitoring(self.current_timetrack['id'])
            if self.user.get('location_tracking_consent'):
                self.update_location()

        # Dropdown para projetos e tarefas
        self.project_dropdown = ft.Dropdown(
            label="Selecione um Projeto",
            options=[],
            width=250,
            border_radius=10,
            on_change=self.on_project_selected
        )
        
        # Dropdown para tarefas
        self.task_dropdown = ft.Dropdown(
            label="Selecione uma Tarefa (opcional)",
            options=[],
            width=250,
            border_radius=10
        )

        # --- INÍCIO DA CORREÇÃO: Campos de data e hora para registro manual ---
        
        # 1. Crie os seletores (pickers) como overlays, sem labels
        self.manual_date_picker = ft.DatePicker(
            first_date=datetime(2024, 1, 1),
            last_date=datetime(2025, 12, 31),
            on_change=self.on_date_picked
        )
        self.checkin_time_picker = ft.TimePicker(
            on_change=self.on_checkin_time_picked,
            help_text="Selecione o horário de início"
        )
        self.checkout_time_picker = ft.TimePicker(
            on_change=self.on_checkout_time_picked,
            help_text="Selecione o horário de fim"
        )

        # 2. Crie os campos de texto (TextFields) que serão visíveis para o usuário
        self.manual_date_field = ft.TextField(
            label="Data do Registro", 
            read_only=True, 
            on_focus=lambda _: self.manual_date_picker.pick_date()
        )
        self.checkin_time_field = ft.TextField(
            label="Horário de Entrada", 
            read_only=True, 
            on_focus=lambda _: self.checkin_time_picker.pick_time()
        )
        self.checkout_time_field = ft.TextField(
            label="Horário de Saída", 
            read_only=True, 
            on_focus=lambda _: self.checkout_time_picker.pick_time()
        )
        # --- FIM DA CORREÇÃO ---
        
        self.reason_field = ft.TextField(
            label="Motivo do Ajuste",
            multiline=True,
            min_lines=2,
            max_lines=4
        )
        self.manual_project_dropdown = ft.Dropdown(
            label="Projeto",
            options=[],
            width=250,
            border_radius=10
        )
        self.manual_error_text = ft.Text(value="", color=ft.Colors.RED, size=12)

        # Dialog de registro manual
        self.manual_entry_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registro Manual de Ponto"),
            # 3. Use os TextFields no layout do diálogo
            content=ft.Column([
                ft.Text("Selecione a data e horários do registro:", size=14),
                self.manual_date_field,
                ft.Row([self.checkin_time_field, self.checkout_time_field], spacing=10),
                self.manual_project_dropdown,
                self.reason_field,
                self.manual_error_text
            ], tight=True, spacing=15),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dialog),
                ft.FilledButton("Salvar", on_click=self.handle_manual_entry),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Dialog para aprovações pendentes
        self.approvals_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Aprovações Pendentes"),
            content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=400),
            actions=[
                ft.TextButton("Fechar", on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.project_dropdown = ft.Dropdown(
            label="Selecione um Projeto",
            options=[],
            width=250,
            border_radius=10
        )
        
        self.page_content = ft.Column()
        
        # --- Fim dos componentes ---

        self.load_current_status()
        self.load_projects()

    # --- Funções de callback para os seletores de data/hora ---
    def on_date_picked(self, e):
        """Atualiza o campo de texto da data quando uma data é escolhida."""
        if self.manual_date_picker.value:
            self.manual_date_field.value = self.manual_date_picker.value.strftime('%d/%m/%Y')
            self.manual_date_field.update()

    def on_checkin_time_picked(self, e):
        """Atualiza o campo de texto da hora de entrada."""
        if self.checkin_time_picker.value:
            self.checkin_time_field.value = self.checkin_time_picker.value.strftime('%H:%M')
            self.checkin_time_field.update()

    def on_checkout_time_picked(self, e):
        """Atualiza o campo de texto da hora de saída."""
        if self.checkout_time_picker.value:
            self.checkout_time_field.value = self.checkout_time_picker.value.strftime('%H:%M')
            self.checkout_time_field.update()

    def close_dialog(self, e):
        """Fecha qualquer diálogo aberto"""
        if hasattr(self.page, 'dialog') and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
        
    def show_snackbar(self, message):
        """Exibe uma mensagem rápida no rodapé da página."""
        self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
        self.page.snack_bar.open = True
        self.page.update()

    def open_manual_entry_dialog(self, e):
        """Abre o diálogo de registro manual de ponto"""
        # Limpa os valores dos seletores e dos campos de texto
        self.manual_date_picker.value = None
        self.checkin_time_picker.value = None
        self.checkout_time_picker.value = None
        
        self.manual_date_field.value = ""
        self.checkin_time_field.value = ""
        self.checkout_time_field.value = ""
        self.reason_field.value = ""
        self.manual_error_text.value = ""
        self.manual_project_dropdown.value = None
        
        # Update project options
        projects = self.db.get_active_projects()
        if projects:
            self.manual_project_dropdown.options = [
                ft.dropdown.Option(key=str(proj['id']), text=proj['name']) 
                for proj in projects
            ]
        
        self.page.dialog = self.manual_entry_dialog
        self.manual_entry_dialog.open = True
        self.page.update()
        
    def handle_manual_entry(self, e):
        """Processa o registro manual de ponto"""
        # 4. Valide usando os valores dos pickers, não dos campos
        if not self.manual_date_picker.value:
            self.manual_error_text.value = "Selecione uma data."
            self.page.dialog.update()
            return
            
        if not self.checkin_time_picker.value or not self.checkout_time_picker.value:
            self.manual_error_text.value = "Selecione os horários de entrada e saída."
            self.page.dialog.update()
            return
            
        if not self.manual_project_dropdown.value:
            self.manual_error_text.value = "Selecione um projeto."
            self.page.dialog.update()
            return
            
        if not self.reason_field.value.strip():
            self.manual_error_text.value = "Informe o motivo do ajuste."
            self.page.dialog.update()
            return

        try:
            # Criar objetos datetime completos combinando os valores dos seletores
            # O .value do DatePicker é um datetime e o do TimePicker é um time
            check_in = datetime.combine(
                self.manual_date_picker.value.date(),
                self.checkin_time_picker.value
            )
            check_out = datetime.combine(
                self.manual_date_picker.value.date(),
                self.checkout_time_picker.value
            )
            
            # Validar se check_out é depois de check_in
            if check_out <= check_in:
                self.manual_error_text.value = "Horário de saída deve ser posterior ao de entrada."
                self.page.dialog.update()
                return
            
            # Criar o registro manual
            project_id = int(self.manual_project_dropdown.value)
            result = self.db.create_manual_entry(
                self.user['id'],
                project_id,
                check_in,
                check_out,
                self.reason_field.value.strip()
            )
            
            if result:
                self.close_dialog(e)
                self.show_snackbar("Registro manual criado e enviado para aprovação!")
                self.refresh_dashboard()
            else:
                self.manual_error_text.value = "Erro ao criar registro manual."
                self.page.dialog.update()
                
        except ValueError as err:
            self.manual_error_text.value = f"Erro nos dados: {str(err)}"
            self.page.dialog.update()
            
    def show_pending_approvals(self, pending_approvals):
        """Mostra o diálogo com as aprovações pendentes"""
        if not pending_approvals:
            self.show_snackbar("Não há registros manuais pendentes de aprovação.")
            return
            
        content_list = []
        for entry in pending_approvals:
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"Colaborador: {entry['full_name']}",
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            f"Projeto: {entry['project_name']}",
                            size=14,
                            color=ft.Colors.BLUE
                        ),
                        ft.Text(
                            f"Data: {entry['date'].strftime('%d/%m/%Y')}",
                            size=14
                        ),
                        ft.Text(
                            f"Horário: {entry['check_in'].strftime('%H:%M')} - {entry['check_out'].strftime('%H:%M')}",
                            size=14
                        ),
                        ft.Text(
                            f"Total: {entry['total_hours']:.2f}h",
                            size=14
                        ),
                        ft.Text(
                            f"Motivo: {entry['manual_entry_reason']}",
                            size=14,
                            italic=True
                        ),
                        ft.Row([
                            ft.OutlinedButton(
                                "❌ Rejeitar",
                                on_click=lambda e, id=entry['id']: self.handle_entry_rejection(id)
                            ),
                            ft.FilledButton(
                                "✅ Aprovar",
                                on_click=lambda e, id=entry['id']: self.handle_entry_approval(id)
                            ),
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=10),
                    padding=20
                ),
                margin=ft.margin.only(bottom=10)
            )
            content_list.append(card)
            
        self.approvals_dialog.content.controls = content_list
        self.page.dialog = self.approvals_dialog
        self.approvals_dialog.open = True
        self.page.update()
        
    def handle_entry_approval(self, timetrack_id):
        """Aprova um registro manual"""
        result = self.db.approve_manual_entry(timetrack_id, self.user['id'])
        if result:
            self.show_snackbar("Registro aprovado com sucesso!")
            self.close_dialog(None)
            self.refresh_dashboard()
        else:
            self.show_snackbar("Erro ao aprovar registro.")
            
    def handle_entry_rejection(self, timetrack_id):
        """Rejeita um registro manual (remove o registro)"""
        # Aqui você pode implementar a lógica de rejeição
        # Por exemplo, movendo o registro para uma tabela de histórico
        # ou simplesmente deletando
        self.show_snackbar("Função de rejeição a ser implementada.")
    # --- Fim das Funções de Cadastro ---

    def load_current_status(self):
        """Carrega status atual do usuário"""
        today_records = self.db.get_user_timetrack_today(self.user['id'])
        if today_records and len(today_records) > 0:
            self.current_timetrack = today_records[0]
            self.is_checked_in = self.current_timetrack['check_out'] is None
            
            if self.is_checked_in:
                active_break = self.db.get_active_break(self.current_timetrack['id'])
                if active_break and len(active_break) > 0:
                    self.current_break = active_break[0]
                    self.is_on_break = True
                else:
                    self.current_break = None
                    self.is_on_break = False
        else:
            self.current_timetrack = None
            self.current_break = None
            self.is_checked_in = False
            self.is_on_break = False

    def load_projects(self):
        """Carrega os projetos ativos do banco de dados e preenche o dropdown."""
        projects = self.db.get_active_projects()
        
        if projects:
            self.project_dropdown.options = [
                ft.dropdown.Option(key=proj['id'], text=proj['name']) for proj in projects
            ]
            
        if self.is_checked_in and self.current_timetrack and self.current_timetrack.get('project_id'):
            self.project_dropdown.value = self.current_timetrack['project_id']
            self.project_dropdown.disabled = True
        else:
            self.project_dropdown.disabled = False
            
    def on_project_selected(self, e):
        """Atualiza as tarefas disponíveis quando um projeto é selecionado"""
        if e.data:  # Se um projeto foi selecionado
            tasks = self.db.get_project_tasks(int(e.data))
            if tasks:
                self.task_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(task['id']),
                        text=f"{task['name']} ({task['status']})"
                    )
                    for task in tasks
                ]
            else:
                self.task_dropdown.options = []
            self.task_dropdown.value = None
            self.task_dropdown.update()
                
    def handle_checkin(self, e):
        """Processa check-in, agora exigindo um projeto."""
        project_id = self.project_dropdown.value
        task_id = self.task_dropdown.value
        
        if not project_id:
            self.show_snackbar("ERRO: Por favor, selecione um projeto antes de iniciar.")
            return

        if not self.is_checked_in:
            # Se uma tarefa foi selecionada, atualiza seu status para 'in_progress'
            if task_id:
                self.db.update_task_status(int(task_id), 'in_progress')
                
            # Obtém localização para check-in se consentido
            location = None
            if self.user.get('location_tracking_consent'):
                location = self.location_service.get_current_location()
                if not location:
                    self.show_snackbar("Aviso: Não foi possível obter sua localização.")
                
            result = self.db.check_in_user(self.user['id'], project_id)
            if result:
                # Registra localização se disponível
                if location:
                    lat, lon = location
                    self.current_location = location
                    self.location_details = self.location_service.get_location_details(lat, lon)
                    self.db.log_location(result, lat, lon, self.location_details)
                    
                self.show_snackbar("Check-in realizado com sucesso!")
                self.load_current_status()
                self.load_projects()
                
                # Inicia monitoramentos conforme consentimento
                if self.user.get('activity_tracking_consent'):
                    self.start_activity_monitoring(result)  # result é o timetrack_id
                    
                self.refresh_dashboard()
                
    def handle_checkout(self, e):
        """Processa check-out"""
        if self.is_checked_in and self.current_timetrack:
            # Para o monitoramento de atividade se estiver ativo
            if hasattr(self, 'activity_monitor') and self.activity_monitor:
                self.stop_activity_monitoring()
                
            # Obtém localização para check-out se consentido
            if self.user.get('location_tracking_consent'):
                location = self.location_service.get_current_location()
                if location:
                    lat, lon = location
                    self.location_details = self.location_service.get_location_details(lat, lon)
                    self.db.log_location(self.current_timetrack['id'], lat, lon, self.location_details)
                else:
                    self.show_snackbar("Aviso: Não foi possível obter sua localização.")

            result = self.db.check_out_user(self.current_timetrack['id'])
            if result:
                self.show_snackbar("Check-out realizado com sucesso!")
                self.load_current_status()
                self.project_dropdown.value = None
                self.load_projects()
                self.refresh_dashboard()
                
    def refresh_dashboard(self):
        """Atualiza o conteúdo principal do dashboard."""
        if self.auth.is_admin(self.user):
            self.page_content.controls = self.build_admin_content()
        else:
            self.page_content.controls = self.build_colaborador_content()
        
        self.page_content.update()
        
    def update_location(self):
        """Atualiza a localização atual e registra no banco de dados se necessário"""
        if not self.user.get('location_tracking_consent'):
            return False
            
        location = self.location_service.get_current_location()
        if location:
            lat, lon = location
            self.current_location = location
            self.location_details = self.location_service.get_location_details(lat, lon)
            
            if self.current_timetrack:
                self.db.log_location(
                    self.current_timetrack['id'],
                    lat,
                    lon,
                    self.location_details
                )
            return True
        return False
        
    def get_location_card(self):
        """Retorna o componente de card de localização com dados atuais"""
        if not self.user.get('location_tracking_consent'):
            return None
            
        cached_location, last_update = self.location_service.get_cached_location()
        if cached_location:
            lat, lon = cached_location
        else:
            lat = lon = None
            
        return LocationCard(
            lat=lat,
            lon=lon,
            details=self.location_details,
            last_update=last_update
        ).build()
        
    def get_location_history(self):
        """Retorna o componente de histórico de localizações"""
        if not self.user.get('location_tracking_consent'):
            return None
            
        history_data = self.db.get_location_history(
            self.user['id'],
            start_date=datetime.now().replace(hour=0, minute=0, second=0)
        )
        return LocationHistoryTable(history_data).build()
        
    def start_activity_monitoring(self, timetrack_id):
        """Inicia o monitoramento de atividade do usuário."""
        if not hasattr(self, 'activity_monitor') or not self.activity_monitor:
            self.activity_monitor = ActivityMonitor()
            self.activity_monitor.start()
            
            # Configura o timer para atualizar o nível de atividade
            def update_activity():
                if self.activity_monitor and self.activity_monitor.is_running:
                    current_level = self.activity_monitor.get_activity_level()
                    if current_level != self.current_activity_level:
                        self.current_activity_level = current_level
                        self.db.update_activity_level(timetrack_id, current_level)
                        # Atualiza o gráfico de atividade se estiver visível
                        self.refresh_dashboard()
                
            # Atualiza a cada 5 minutos
            self.activity_update_timer = ft.Timer(update_activity, 300)
            self.activity_update_timer.start()
            
    def stop_activity_monitoring(self):
        """Para o monitoramento de atividade do usuário."""
        if hasattr(self, 'activity_monitor') and self.activity_monitor:
            self.activity_monitor.stop()
            self.activity_monitor = None
            
        if hasattr(self, 'activity_update_timer') and self.activity_update_timer:
            self.activity_update_timer.stop()
            self.activity_update_timer = None
    def handle_break_start(self, e):
        """Inicia uma pausa"""
        if self.is_checked_in and not self.is_on_break and self.current_timetrack:
            break_type = self.time_card.break_type_dropdown.value or 'rest'
            result = self.db.start_break(self.current_timetrack['id'], break_type)
            if result:
                self.show_snackbar("Pausa iniciada com sucesso!")
                self.load_current_status()
                self.refresh_dashboard()
                
    def handle_break_end(self, e):
        """Finaliza uma pausa"""
        if self.is_checked_in and self.is_on_break and self.current_break:
            result = self.db.end_break(self.current_break['id'])
            if result:
                self.show_snackbar("Pausa finalizada com sucesso!")
                self.load_current_status()
                self.refresh_dashboard()
    
    def build_colaborador_content(self):
        """Constrói o conteúdo da UI para um colaborador."""
        if self.is_on_break:
            status_text = "Em Pausa"
            status_color = ft.Colors.ORANGE
        elif self.is_checked_in:
            status_text = "Trabalhando"
            status_color = ft.Colors.GREEN
        else:
            status_text = "Fora do expediente"
            status_color = ft.Colors.GREY
        
        daily_hours = 0.0
        if self.current_timetrack and self.current_timetrack.get('total_hours'):
            daily_hours = float(self.current_timetrack['total_hours'])
        elif self.is_checked_in and self.current_timetrack:
            delta = datetime.now() - self.current_timetrack['check_in']
            daily_hours = delta.total_seconds() / 3600
            
        status_card = StatsCard("Status", status_text, ft.Icons.SCHEDULE, status_color)
        hours_card = StatsCard("Horas Hoje", f"{daily_hours:.2f}h", ft.Icons.TIMER, ft.Colors.BLUE)
        
        self.time_card = TimeCard(
            self.is_checked_in,
            self.handle_checkin,
            self.handle_checkout,
            self.handle_break_start,
            self.handle_break_end,
            self.current_timetrack['check_in'] if self.current_timetrack else None,
            self.project_dropdown,
            self.is_on_break,
            self.current_break['start_time'] if self.current_break else None,
            on_manual_entry=self.open_manual_entry_dialog
        )
        
        history_data = self.db.get_user_history(self.user['id'], 15)
        history_table = HistoryTable(history_data or [])
        
        weekly_data = self.db.get_weekly_report(self.user['id'])
        weekly_chart = WeeklyChart(weekly_data or [])

        # Componentes de monitoramento de atividade
        activity_components = []
        if self.user.get('activity_tracking_consent'):
            activity_card = ActivityCard(
                self.current_activity_level if hasattr(self, 'activity_monitor') and self.activity_monitor else 0
            )
            activity_graph = ActivityGraph(
                self.db.get_activity_history(self.current_timetrack['id']) if self.current_timetrack else []
            )
            activity_components = [
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row([
                    ft.Column([
                        ft.Text("Nível de Atividade", size=20, weight=ft.FontWeight.BOLD),
                        activity_card.build()
                    ], expand=1),
                    ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
                    ft.Column([
                        ft.Text("Histórico de Atividade", size=20, weight=ft.FontWeight.BOLD),
                        activity_graph.build()
                    ], expand=1)
                ], expand=True, spacing=20)
            ]
        
        return [
            ft.Text(f"Olá, {self.user['full_name']}!", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Row([status_card.build(), hours_card.build(), self.time_card.build()], spacing=20),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Row([
                ft.Column([
                    ft.Text("Histórico Recente", size=20, weight=ft.FontWeight.BOLD),
                    history_table.build()
                ], expand=1),
                ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
                ft.Column([
                    ft.Text("Horas da Semana", size=20, weight=ft.FontWeight.BOLD),
                    weekly_chart.build()
                ], expand=1)
            ], expand=True, spacing=20),
            *activity_components,
            # Adiciona componentes de localização se consentido
            *([] if not self.user.get('location_tracking_consent') else [
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row([
                    ft.Column([
                        ft.Text("Localização Atual", size=20, weight=ft.FontWeight.BOLD),
                        self.get_location_card() or ft.Text("Localização indisponível")
                    ], expand=1),
                    ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
                    ft.Column([
                        ft.Text("Histórico de Localizações", size=20, weight=ft.FontWeight.BOLD),
                        self.get_location_history() or ft.Text("Sem histórico de localizações hoje")
                    ], expand=1)
                ], expand=True, spacing=20)
            ])
        ]
        
    def build_admin_content(self):
        """Constrói o conteúdo da UI para um administrador."""
        users_data = self.db.get_all_users_status() or []
        online_count = sum(1 for u in users_data if u.get('check_in') and not u.get('check_out'))
        total_users = len(users_data)
        
        users_card = StatsCard("Total Usuários", str(total_users), ft.Icons.GROUP, ft.Colors.BLUE)
        online_card = StatsCard("Online Agora", str(online_count), ft.Icons.CIRCLE, ft.Colors.GREEN)
        
        users_table = UsersTable(users_data)
        
        weekly_data = self.db.get_weekly_report()
        weekly_chart = WeeklyChart(weekly_data or [], admin_view=True)

        collab_button = ft.ElevatedButton(
            "Gerenciar Colaboradores",
            icon=ft.Icons.PEOPLE,
            on_click=lambda _: self.show_collaborators_screen(),
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
        )

        projects_button = ft.ElevatedButton(
            "Gerenciar Projetos",
            icon=ft.Icons.FOLDER,
            on_click=lambda _: self.show_project_screen(),
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
        )

        pending_approvals = self.db.get_pending_approvals()
        approvals_count = len(pending_approvals) if pending_approvals else 0
        
        approvals_button = ft.ElevatedButton(
            f"Aprovações Pendentes ({approvals_count})",
            icon=ft.Icons.PENDING_ACTIONS,
            on_click=lambda e: self.show_pending_approvals(pending_approvals),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE if approvals_count > 0 else ft.Colors.GREY,
                color=ft.Colors.WHITE
            )
        )
        
        return [
            ft.Row([
                ft.Text("Painel Administrativo", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                projects_button,
                ft.Container(width=10),  # Espaçamento
                approvals_button,
                ft.Container(width=10),  # Espaçamento
                ft.ElevatedButton(
                    "Relatórios",
                    icon=ft.Icons.ANALYTICS,
                    on_click=lambda _: self.show_reports_screen(),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO, color=ft.Colors.WHITE)
                ),
                ft.Container(width=10),  # Espaçamento
                collab_button
            ]),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Row([users_card.build(), online_card.build(), ft.Container(expand=True)], spacing=20),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Row([
                ft.Column([
                    ft.Text("Status dos Colaboradores", size=20, weight=ft.FontWeight.BOLD),
                    users_table.build()
                ], expand=1),
                ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
                ft.Column([
                    ft.Text("Relatório Semanal", size=20, weight=ft.FontWeight.BOLD),
                    weekly_chart.build()
                ], expand=1)
            ], expand=True, spacing=20)
        ]
        
    def show_project_screen(self):
        """Mostra a tela de gerenciamento de projetos"""
        from ui_project_manager import ProjectManagerScreen
        
        self.show_projects = True
        project_screen = ProjectManagerScreen(
            self.db,
            self.user,
            lambda _: self.hide_project_screen()
        )
        self.page_content.controls = [project_screen.build(self.page)]
        self.page_content.update()
        
    def hide_project_screen(self):
        """Volta para a tela principal"""
        self.show_projects = False
        self.refresh_dashboard()
        
    def show_reports_screen(self):
        """Mostra a tela de relatórios"""
        self.show_projects = False  # Garante que a tela de projetos está fechada
        reports_screen = ReportsScreen(
            self.user,
            self.db,
            lambda _: self.hide_reports_screen()
        )
        self.page_content.controls = [reports_screen.build(self.page)]
        self.page_content.update()
        
    def hide_reports_screen(self):
        """Volta para a tela principal"""
        self.refresh_dashboard()
        
    def show_collaborators_screen(self):
        """Mostra a tela de gerenciamento de colaboradores"""
        from components.collaborators_ui import CollaboratorsScreen
        
        collaborators_screen = CollaboratorsScreen(
            self.user,
            self.db,
            lambda _: self.hide_collaborators_screen()
        )
        self.page_content.controls = [collaborators_screen.build(self.page)]
        self.page_content.update()
        
    def hide_collaborators_screen(self):
        """Volta para a tela principal"""
        self.refresh_dashboard()
        
    def build(self, page: ft.Page):
        """Constrói a interface principal do dashboard."""
        self.page = page

        # 5. Adicione os seletores à camada de sobreposição (overlay) da página.
        #    Isso é crucial para que eles possam ser exibidos.
        page.overlay.extend([
            self.manual_date_picker, 
            self.checkin_time_picker, 
            self.checkout_time_picker
        ])
        
        navbar = NavBar(self.user, self.db, self.on_logout, self.toggle_theme, self.dark_mode)
        
        if self.auth.is_admin(self.user):
            content = self.build_admin_content()
        else:
            content = self.build_colaborador_content()
            
        self.page_content.controls = content
        
        return ft.Column([
            navbar.build(),
            ft.Container(
                content=self.page_content,
                padding=30,
                expand=True
            )
        ], spacing=0, expand=True)