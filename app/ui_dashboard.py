import flet as ft
from datetime import datetime, timedelta
import pandas as pd
from components.navbar import NavBar
from components.cards import StatsCard, TimeCard
from components.charts import WeeklyChart
from components.tables import HistoryTable, UsersTable

class DashboardScreen:
    def __init__(self, user, db, auth, on_logout, toggle_theme, dark_mode):
        self.user = user
        self.db = db
        self.auth = auth
        self.on_logout = on_logout
        self.toggle_theme = toggle_theme
        self.dark_mode = dark_mode
        self.current_timetrack = None
        self.is_checked_in = False
        self.page_content = ft.Column()
        self.load_current_status()
        
    def load_current_status(self):
        """Carrega status atual do usuário"""
        today_records = self.db.get_user_timetrack_today(self.user['id'])
        if today_records and len(today_records) > 0:
            self.current_timetrack = today_records[0]
            self.is_checked_in = self.current_timetrack['check_out'] is None
            
    def handle_checkin(self, e):
        """Processa check-in"""
        if not self.is_checked_in:
            result = self.db.check_in_user(self.user['id'])
            if result:
                self.load_current_status()
                self.refresh_dashboard()
                
    def handle_checkout(self, e):
        """Processa check-out"""
        if self.is_checked_in and self.current_timetrack:
            result = self.db.check_out_user(self.current_timetrack['id'])
            if result:
                self.load_current_status()
                self.refresh_dashboard()
                
    def refresh_dashboard(self):
        """Atualiza dashboard"""
        if self.auth.is_admin(self.user):
            self.page_content.controls = self.build_admin_content()
        else:
            self.page_content.controls = self.build_colaborador_content()
        self.page_content.update()
        
    def build_colaborador_content(self):
        """Constrói conteúdo para colaborador"""
        # Status atual
        status_text = "Trabalhando" if self.is_checked_in else "Fora do expediente"
        status_color = ft.colors.GREEN if self.is_checked_in else ft.colors.GREY
        
        # Horas do dia
        daily_hours = 0
        if self.current_timetrack and self.current_timetrack['total_hours']:
            daily_hours = float(self.current_timetrack['total_hours'])
        elif self.is_checked_in and self.current_timetrack:
            delta = datetime.now() - self.current_timetrack['check_in']
            daily_hours = delta.total_seconds() / 3600
            
        # Cards de estatísticas
        status_card = StatsCard("Status", status_text, ft.icons.SCHEDULE, status_color)
        hours_card = StatsCard("Horas Hoje", f"{daily_hours:.2f}h", ft.icons.TIMER, ft.colors.BLUE)
        
        # Card de controle de ponto
        time_card = TimeCard(
            self.is_checked_in,
            self.handle_checkin,
            self.handle_checkout,
            self.current_timetrack['check_in'] if self.current_timetrack else None
        )
        
        # Histórico
        history_data = self.db.get_user_history(self.user['id'], 15)
        history_table = HistoryTable(history_data or [])
        
        # Gráfico semanal
        weekly_data = self.db.get_weekly_report(self.user['id'])
        weekly_chart = WeeklyChart(weekly_data or [])
        
        return [
            ft.Text(f"Olá, {self.user['full_name']}!", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.colors.TRANSPARENT),
            
            # Cards superiores
            ft.Row([
                status_card.build(),
                hours_card.build(),
                time_card.build()
            ], spacing=20),
            
            ft.Divider(height=20, color=ft.colors.TRANSPARENT),
            
            # Conteúdo principal
            ft.Row([
                ft.Column([
                    ft.Text("Histórico Recente", size=20, weight=ft.FontWeight.BOLD),
                    history_table.build()
                ], expand=1),
                
                ft.VerticalDivider(width=20, color=ft.colors.TRANSPARENT),
                
                ft.Column([
                    ft.Text("Horas da Semana", size=20, weight=ft.FontWeight.BOLD),
                    weekly_chart.build()
                ], expand=1)
            ], expand=True, spacing=20)
        ]
        
    def build_admin_content(self):
        """Constrói conteúdo para administrador"""
        # Dados dos usuários
        users_data = self.db.get_all_users_status() or []
        online_count = len([u for u in users_data if u['check_in'] and not u['check_out']])
        total_users = len(users_data)
        
        # Cards de estatísticas
        users_card = StatsCard("Total Usuários", str(total_users), ft.icons.GROUP, ft.colors.BLUE)
        online_card = StatsCard("Online Agora", str(online_count), ft.icons.CIRCLE, ft.colors.GREEN)
        
        # Tabela de usuários
        users_table = UsersTable(users_data)
        
        # Relatório semanal geral
        weekly_data = self.db.get_weekly_report()
        weekly_chart = WeeklyChart(weekly_data or [], admin_view=True)
        
        return [
            ft.Text("Painel Administrativo", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.colors.TRANSPARENT),
            
            # Cards superiores
            ft.Row([
                users_card.build(),
                online_card.build(),
                ft.Container(expand=True)  # Espaçador
            ], spacing=20),
            
            ft.Divider(height=20, color=ft.colors.TRANSPARENT),
            
            # Conteúdo principal
            ft.Row([
                ft.Column([
                    ft.Text("Status dos Colaboradores", size=20, weight=ft.FontWeight.BOLD),
                    users_table.build()
                ], expand=1),
                
                ft.VerticalDivider(width=20, color=ft.colors.TRANSPARENT),
                
                ft.Column([
                    ft.Text("Relatório Semanal", size=20, weight=ft.FontWeight.BOLD),
                    weekly_chart.build()
                ], expand=1)
            ], expand=True, spacing=20)
        ]
        
    def build(self):
        """Constrói interface principal"""
        # Navbar
        navbar = NavBar(
            self.user,
            self.on_logout,
            self.toggle_theme,
            self.dark_mode
        )
        
        # Conteúdo baseado no tipo de usuário
        if self.auth.is_admin(self.user):
            content = self.build_admin_content()
        else:
            content = self.build_colaborador_content()
            
        self.page_content = ft.Column(
            content,
            scroll=ft.ScrollMode.AUTO,
            spacing=20
        )
        
        return ft.Column([
            navbar.build(),
            ft.Container(
                content=self.page_content,
                padding=30,
                expand=True
            )
        ], spacing=0, expand=True)