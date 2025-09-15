import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime, date
import pandas as pd

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'timetrack_db')
        self.connection = None
        self.create_database_if_not_exists()
        self.create_tables()
        self.create_default_admin()
        
    def connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return True
        except Error as e:
            print(f"Erro ao conectar com MySQL: {e}")
            return False
            
    def create_database_if_not_exists(self):
        """Cria o banco de dados se não existir"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            connection.close()
        except Error as e:
            print(f"Erro ao criar banco de dados: {e}")
            
    def create_tables(self):
        """Cria as tabelas necessárias"""
        if not self.connect():
            return
            
        cursor = self.connection.cursor()
        
        # Tabela de usuários
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            role ENUM('admin', 'colaborador') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Tabela de registros de ponto
        timetrack_table = """
        CREATE TABLE IF NOT EXISTS timetrack (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            check_in DATETIME NOT NULL,
            check_out DATETIME NULL,
            total_hours DECIMAL(5,2) NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
        
        try:
            cursor.execute(users_table)
            cursor.execute(timetrack_table)
            self.connection.commit()
        except Error as e:
            print(f"Erro ao criar tabelas: {e}")
        finally:
            cursor.close()
            self.connection.close()
            
    def create_default_admin(self):
        """Cria usuário admin padrão se não existir"""
        from auth import AuthManager
        if self.connect():
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                import bcrypt
                password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
                cursor.execute("""
                    INSERT INTO users (username, password, full_name, role)
                    VALUES (%s, %s, %s, %s)
                """, ("admin", password.decode('utf-8'), "Administrador", "admin"))
                self.connection.commit()
                print("Usuário admin padrão criado - Login: admin | Senha: admin123")
                
            cursor.close()
            self.connection.close()
            
    def execute_query(self, query, params=None):
        """Executa uma query e retorna os resultados"""
        if not self.connect():
            return None
            
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if query.strip().lower().startswith('select'):
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = cursor.lastrowid
            return result
        except Error as e:
            print(f"Erro na query: {e}")
            return None
        finally:
            cursor.close()
            self.connection.close()
            
    def get_user_timetrack_today(self, user_id):
        """Busca registro de ponto do dia atual"""
        query = """
            SELECT * FROM timetrack 
            WHERE user_id = %s AND date = %s
            ORDER BY check_in DESC LIMIT 1
        """
        return self.execute_query(query, (user_id, date.today()))
        
    def check_in_user(self, user_id):
        """Registra check-in do usuário"""
        now = datetime.now()
        query = """
            INSERT INTO timetrack (user_id, check_in, date)
            VALUES (%s, %s, %s)
        """
        return self.execute_query(query, (user_id, now, now.date()))
        
    def check_out_user(self, timetrack_id):
        """Registra check-out e calcula horas trabalhadas"""
        now = datetime.now()
        
        # Busca o check-in
        query_select = "SELECT check_in FROM timetrack WHERE id = %s"
        result = self.execute_query(query_select, (timetrack_id,))
        
        if result:
            check_in_time = result[0]['check_in']
            total_hours = (now - check_in_time).total_seconds() / 3600
            
            query_update = """
                UPDATE timetrack 
                SET check_out = %s, total_hours = %s
                WHERE id = %s
            """
            return self.execute_query(query_update, (now, total_hours, timetrack_id))
        return False
        
    def get_user_history(self, user_id, days=30):
        """Busca histórico de registros do usuário"""
        query = """
            SELECT * FROM timetrack 
            WHERE user_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY date DESC, check_in DESC
        """
        return self.execute_query(query, (user_id, days))
        
    def get_all_users_status(self):
        """Busca status de todos os usuários (admin)"""
        query = """
            SELECT u.id, u.username, u.full_name,
                   t.check_in, t.check_out, t.total_hours, t.date
            FROM users u
            LEFT JOIN timetrack t ON u.id = t.user_id AND t.date = CURDATE()
            WHERE u.role = 'colaborador'
            ORDER BY u.full_name
        """
        return self.execute_query(query)
        
    def get_weekly_report(self, user_id=None):
        """Gera relatório semanal"""
        base_query = """
            SELECT u.full_name, t.date, SUM(t.total_hours) as daily_hours
            FROM timetrack t
            JOIN users u ON t.user_id = u.id
            WHERE t.date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            AND t.total_hours IS NOT NULL
        """
        
        if user_id:
            query = base_query + " AND t.user_id = %s GROUP BY t.date ORDER BY t.date"
            return self.execute_query(query, (user_id,))
        else:
            query = base_query + " GROUP BY u.full_name, t.date ORDER BY u.full_name, t.date"
            return self.execute_query(query)

# ====================================
# auth.py - Autenticação de usuários
# ====================================

import bcrypt

class AuthManager:
    def __init__(self, db):
        self.db = db
        self.current_user = None
        
    def login(self, username, password):
        """Autentica usuário"""
        query = "SELECT * FROM users WHERE username = %s"
        users = self.db.execute_query(query, (username,))
        
        if users and len(users) > 0:
            user = users[0]
            stored_password = user['password'].encode('utf-8')
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                self.current_user = user
                return user
        return None
        
    def logout(self):
        """Desloga usuário atual"""
        self.current_user = None
        
    def register_user(self, username, password, full_name, role='colaborador'):
        """Registra novo usuário (apenas admin)"""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        query = """
            INSERT INTO users (username, password, full_name, role)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.execute_query(query, (username, hashed_password.decode('utf-8'), full_name, role))
        
    def is_admin(self, user=None):
        """Verifica se usuário é admin"""
        if user is None:
            user = self.current_user
        return user and user.get('role') == 'admin'

# ====================================
# ui_login.py - Tela de login
# ====================================

import flet as ft

class LoginScreen:
    def __init__(self, auth_manager, on_success, toggle_theme):
        self.auth = auth_manager
        self.on_success = on_success
        self.toggle_theme = toggle_theme
        self.username_field = ft.TextField()
        self.password_field = ft.TextField()
        self.error_text = ft.Text()
        
    def handle_login(self, e):
        """Processa tentativa de login"""
        username = self.username_field.value
        password = self.password_field.value
        
        if not username or not password:
            self.show_error("Por favor, preencha todos os campos")
            return
            
        user = self.auth.login(username, password)
        if user:
            self.on_success(user)
        else:
            self.show_error("Usuário ou senha inválidos")
            
    def show_error(self, message):
        """Exibe mensagem de erro"""
        self.error_text.value = message
        self.error_text.color = ft.colors.RED
        self.error_text.update()
        
    def build(self):
        """Constrói interface de login"""
        # Campos de entrada
        self.username_field = ft.TextField(
            label="Usuário",
            prefix_icon=ft.icons.PERSON,
            border_radius=10,
            width=300
        )
        
        self.password_field = ft.TextField(
            label="Senha",
            prefix_icon=ft.icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            width=300,
            on_submit=self.handle_login
        )
        
        # Botão de login
        login_btn = ft.ElevatedButton(
            text="Entrar",
            on_click=self.handle_login,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=50, vertical=15),
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)
            ),
            width=300
        )
        
        # Botão tema
        theme_btn = ft.IconButton(
            icon=ft.icons.BRIGHTNESS_6,
            tooltip="Alternar tema",
            on_click=lambda _: self.toggle_theme()
        )
        
        # Mensagem de erro
        self.error_text = ft.Text(
            size=14,
            text_align=ft.TextAlign.CENTER
        )
        
        # Card de login
        login_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ACCESS_TIME, size=60, color=ft.colors.BLUE),
                    ft.Text(
                        "TimeTrack",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Sistema de Controle de Ponto",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.GREY
                    ),
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    self.username_field,
                    self.password_field,
                    self.error_text,
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    login_btn,
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    ft.Text(
                        "Login padrão: admin / admin123",
                        size=12,
                        color=ft.colors.GREY,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
                ),
                padding=40,
                width=400,
                border_radius=15
            ),
            elevation=10
        )
        
        # Layout principal
        return ft.Container(
            content=ft.Stack([
                ft.Container(
                    content=ft.Column([
                        login_card
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    expand=True
                ),
                ft.Container(
                    content=theme_btn,
                    alignment=ft.alignment.top_right,
                    padding=20
                )
            ]),
            expand=True,
            gradient=ft.LinearGradient([
                ft.colors.BLUE_50,
                ft.colors.INDIGO_100
            ])
        )