# Arquivo: db.py (VERSÃO CORRIGIDA E SEGURA PARA ATUALIZAÇÃO)

import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime, date
import bcrypt

# Mover a importação de AuthManager para o topo se não causar importação circular
# Se causar, mantenha dentro de create_default_admin
# from auth import AuthManager 

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'timetrack_db')
        self.connection = None
        
        # Rotina de inicialização segura
        self.create_database_if_not_exists()
        self.create_tables()
        self._update_schema() # NOVO: Roda a "migração" de forma segura
        self.create_default_admin()
        self.create_default_projects()

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
        # ... seu código original aqui, está perfeito ...
        try:
            connection = mysql.connector.connect(
                host=self.host, user=self.user, password=self.password
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            connection.close()
        except Error as e:
            print(f"Erro ao criar banco de dados: {e}")

    def create_tables(self):
        """Cria as tabelas necessárias se elas não existirem."""
        if not self.connect(): return
        
        cursor = self.connection.cursor()
        
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            role ENUM('admin', 'colaborador') NOT NULL,
            hourly_rate DECIMAL(10,2) NULL,
            location_tracking_consent BOOLEAN DEFAULT FALSE,
            activity_tracking_consent BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        
        projects_table = """
        CREATE TABLE IF NOT EXISTS projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT NULL,
            hourly_rate DECIMAL(10,2) NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        
        tasks_table = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT NULL,
            status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )"""
        
        timetrack_table = """
        CREATE TABLE IF NOT EXISTS timetrack (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            project_id INT NULL,
            task_id INT NULL,
            check_in DATETIME NOT NULL,
            check_out DATETIME NULL,
            total_hours DECIMAL(5,2) NULL,
            date DATE NOT NULL,
            location_lat DECIMAL(10,8) NULL,
            location_lng DECIMAL(11,8) NULL,
            manual_entry BOOLEAN DEFAULT FALSE,
            manual_entry_reason TEXT NULL,
            approved_by INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
        )"""
        
        breaks_table = """
        CREATE TABLE IF NOT EXISTS breaks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timetrack_id INT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NULL,
            break_type ENUM('lunch', 'rest', 'other') NOT NULL,
            total_minutes INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (timetrack_id) REFERENCES timetrack(id) ON DELETE CASCADE
        )"""
        
        activity_logs_table = """
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timetrack_id INT NOT NULL,
            timestamp DATETIME NOT NULL,
            activity_level INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (timetrack_id) REFERENCES timetrack(id) ON DELETE CASCADE
        )"""
        
        try:
            cursor.execute(users_table)
            cursor.execute(projects_table)
            cursor.execute(timetrack_table)
            self.connection.commit()
        except Error as e:
            print(f"Erro ao criar tabelas: {e}")
        finally:
            cursor.close()
            self.connection.close()
    
    # NOVO: Função de "migração" que roda uma vez
    def _update_schema(self):
        """Verifica e aplica atualizações necessárias no schema do banco de dados."""
        if not self.connect(): return

        cursor = self.connection.cursor()
        try:
            # Add new columns to users table
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{self.database}' 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'hourly_rate'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE users
                    ADD COLUMN hourly_rate DECIMAL(10,2) NULL,
                    ADD COLUMN location_tracking_consent BOOLEAN DEFAULT FALSE,
                    ADD COLUMN activity_tracking_consent BOOLEAN DEFAULT FALSE
                """)
                print("Users table updated with new columns")

            # Add new columns to timetrack table
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{self.database}' 
                AND TABLE_NAME = 'timetrack' 
                AND COLUMN_NAME = 'location_lat'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE timetrack 
                    ADD COLUMN location_lat DECIMAL(10,8) NULL,
                    ADD COLUMN location_lng DECIMAL(11,8) NULL,
                    ADD COLUMN manual_entry BOOLEAN DEFAULT FALSE,
                    ADD COLUMN manual_entry_reason TEXT NULL,
                    ADD COLUMN approved_by INT NULL,
                    ADD CONSTRAINT fk_approved_by FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
                """)
                print("Timetrack table updated with new columns")

            # Add hourly_rate to projects if not exists
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{self.database}' 
                AND TABLE_NAME = 'projects' 
                AND COLUMN_NAME = 'hourly_rate'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE projects
                    ADD COLUMN hourly_rate DECIMAL(10,2) NULL,
                    ADD COLUMN description TEXT NULL
                """)
                print("Projects table updated with new columns")

            self.connection.commit()
            print("Schema atualizado com sucesso!")

        except Error as e:
            print(f"Erro ao atualizar o schema: {e}")
        finally:
            cursor.close()
            self.connection.close()

    def create_default_admin(self):
        # ... seu código original aqui, está perfeito ...
        if self.connect():
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] == 0:
                password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, %s)",
                    ("admin", password.decode('utf-8'), "Administrador", "admin")
                )
                self.connection.commit()
                print("Usuário admin padrão criado - Login: admin | Senha: admin123")
            cursor.close()
            self.connection.close()

    def create_default_projects(self):
        # ... código para adicionar projetos que sugeri antes ...
        if self.connect():
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM projects")
            if cursor.fetchone()[0] == 0:
                default_projects = [('Projeto Corporativo',), ('Desenvolvimento App',), ('Marketing Digital',)]
                cursor.executemany("INSERT INTO projects (name) VALUES (%s)", default_projects)
                self.connection.commit()
                print("Projetos padrão criados.")
            cursor.close()
            self.connection.close()

    def execute_query(self, query, params=None):
        # ... seu código original aqui, está perfeito ...
        if not self.connect(): return None
        
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
    
    # NOVO: Método específico para buscar projetos
    def get_active_projects(self):
        query = """
            SELECT p.*, 
                COUNT(t.id) as total_tasks,
                SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            WHERE p.is_active = TRUE
            GROUP BY p.id, p.name
            ORDER BY p.name
        """
        return self.execute_query(query)

    def get_project_tasks(self, project_id):
        """Retorna todas as tarefas de um projeto"""
        query = """
            SELECT t.*,
                SUM(tt.total_hours) as total_hours_spent,
                COUNT(DISTINCT tt.user_id) as total_users
            FROM tasks t
            LEFT JOIN timetrack tt ON t.id = tt.task_id
            WHERE t.project_id = %s
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """
        return self.execute_query(query, (project_id,))

    def add_task(self, project_id, name, description=None):
        """Adiciona uma nova tarefa ao projeto"""
        query = """
            INSERT INTO tasks (project_id, name, description, status)
            VALUES (%s, %s, %s, 'pending')
        """
        return self.execute_query(query, (project_id, name, description))

    def update_task_status(self, task_id, status):
        """Atualiza o status de uma tarefa"""
        if status not in ['pending', 'in_progress', 'completed']:
            return False
            
        query = "UPDATE tasks SET status = %s WHERE id = %s"
        return self.execute_query(query, (status, task_id))

    def get_task_time_entries(self, task_id):
        """Retorna todos os registros de tempo para uma tarefa"""
        query = """
            SELECT t.*, u.full_name
            FROM timetrack t
            JOIN users u ON t.user_id = u.id
            WHERE t.task_id = %s
            ORDER BY t.check_in DESC
        """
        return self.execute_query(query, (task_id,))

    def get_project_statistics(self, project_id):
        """Retorna estatísticas detalhadas do projeto"""
        query = """
            SELECT 
                p.*,
                COUNT(DISTINCT t.id) as total_tasks,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
                COUNT(DISTINCT tt.user_id) as total_users,
                SUM(tt.total_hours) as total_hours,
                AVG(tt.total_hours) as avg_hours_per_entry
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            LEFT JOIN timetrack tt ON p.id = tt.project_id
            WHERE p.id = %s
            GROUP BY p.id
        """
        return self.execute_query(query, (project_id,))

    def assign_task(self, task_id, user_id):
        """Atribui uma tarefa a um usuário"""
        query = """
            INSERT INTO task_assignments (task_id, user_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE assigned_at = CURRENT_TIMESTAMP
        """
        return self.execute_query(query, (task_id, user_id))

    def get_user_tasks(self, user_id):
        """Retorna todas as tarefas atribuídas a um usuário"""
        query = """
            SELECT t.*, p.name as project_name,
                SUM(tt.total_hours) as hours_spent
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            JOIN task_assignments ta ON t.id = ta.task_id
            LEFT JOIN timetrack tt ON t.id = tt.task_id AND tt.user_id = ta.user_id
            WHERE ta.user_id = %s
            GROUP BY t.id, p.name
            ORDER BY t.status, t.created_at DESC
        """
        return self.execute_query(query, (user_id,))

    # Métodos restantes adaptados (check_in, get_history, etc.)
    
    def get_user_timetrack_today(self, user_id):
        query = """
            SELECT t.*, p.name as project_name
            FROM timetrack t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.user_id = %s AND t.date = %s
            ORDER BY t.check_in DESC LIMIT 1
        """
        return self.execute_query(query, (user_id, date.today()))

    # ALTERADO para aceitar project_id
    def check_in_user(self, user_id, project_id):
        now = datetime.now()
        query = "INSERT INTO timetrack (user_id, project_id, check_in, date) VALUES (%s, %s, %s, %s)"
        return self.execute_query(query, (user_id, project_id, now, now.date()))

    def check_out_user(self, timetrack_id):
        now = datetime.now()
        query_select = "SELECT check_in FROM timetrack WHERE id = %s"
        result = self.execute_query(query_select, (timetrack_id,))
        
        if result:
            check_in_time = result[0]['check_in']
            total_hours = (now - check_in_time).total_seconds() / 3600
            
            query_update = "UPDATE timetrack SET check_out = %s, total_hours = %s WHERE id = %s"
            return self.execute_query(query_update, (now, total_hours, timetrack_id))
        return False

    def get_user_history(self, user_id, days=30):
        # ALTERADO para incluir o nome do projeto
        query = """
            SELECT t.*, p.name as project_name
            FROM timetrack t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.user_id = %s AND t.date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY t.check_in DESC
        """
        return self.execute_query(query, (user_id, days))

    def get_all_users_status(self):
        # ALTERADO para incluir o nome do projeto atual
        query = """
            SELECT u.id, u.username, u.full_name, t.check_in, t.check_out, p.name as project_name
            FROM users u
            LEFT JOIN (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY check_in DESC) as rn
                FROM timetrack WHERE date = CURDATE()
            ) t ON u.id = t.user_id AND t.rn = 1
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE u.role = 'colaborador'
            ORDER BY u.full_name
        """
        return self.execute_query(query)

    def get_weekly_report(self, user_id=None):
        # ALTERADO para incluir o nome do projeto no agrupamento e considerar pausas
        base_query = """
            SELECT 
                u.full_name, 
                p.name as project_name, 
                t.date, 
                SUM(t.total_hours) as daily_hours,
                COALESCE(SUM(b.total_minutes)/60, 0) as break_hours,
                SUM(t.total_hours) - COALESCE(SUM(b.total_minutes)/60, 0) as effective_hours
            FROM timetrack t
            JOIN users u ON t.user_id = u.id
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN breaks b ON t.id = b.timetrack_id
            WHERE t.date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
            AND t.total_hours IS NOT NULL
        """
        
        if user_id:
            query = base_query + " AND t.user_id = %s GROUP BY t.date, p.name, u.full_name ORDER BY t.date"
            return self.execute_query(query, (user_id,))
        else:
            query = base_query + " GROUP BY u.full_name, p.name, t.date ORDER BY u.full_name, t.date"
            return self.execute_query(query)

    # Métodos para controle de pausas
    def start_break(self, timetrack_id, break_type='rest'):
        """Inicia uma pausa no registro de ponto"""
        query = """
            INSERT INTO breaks (timetrack_id, start_time, break_type)
            VALUES (%s, NOW(), %s)
        """
        return self.execute_query(query, (timetrack_id, break_type))

    def end_break(self, break_id):
        """Finaliza uma pausa e calcula o tempo total"""
        now = datetime.now()
        query_select = "SELECT start_time FROM breaks WHERE id = %s"
        result = self.execute_query(query_select, (break_id,))
        
        if result:
            start_time = result[0]['start_time']
            total_minutes = int((now - start_time).total_seconds() / 60)
            
            query_update = """
                UPDATE breaks 
                SET end_time = %s, total_minutes = %s 
                WHERE id = %s
            """
            return self.execute_query(query_update, (now, total_minutes, break_id))
        return False

    def get_active_break(self, timetrack_id):
        """Retorna a pausa ativa para um registro de ponto, se houver"""
        query = """
            SELECT * FROM breaks 
            WHERE timetrack_id = %s 
            AND end_time IS NULL
            ORDER BY start_time DESC 
            LIMIT 1
        """
        return self.execute_query(query, (timetrack_id,))

    # Métodos para registro de atividade
    def update_activity_level(self, timetrack_id, activity_level):
        """Atualiza o nível de atividade do usuário"""
        query = """
            INSERT INTO activity_logs (timetrack_id, timestamp, activity_level)
            VALUES (%s, NOW(), %s)
        """
        return self.execute_query(query, (timetrack_id, activity_level))
        
    def get_activity_history(self, timetrack_id):
        """Retorna o histórico de atividade para visualização em gráfico"""
        query = """
            SELECT 
                DATE_FORMAT(timestamp, '%H:%i') as time,
                activity_level,
                UNIX_TIMESTAMP(timestamp) as timestamp_unix
            FROM activity_logs
            WHERE timetrack_id = %s
            AND timestamp >= DATE_SUB(NOW(), INTERVAL 4 HOUR)
            ORDER BY timestamp
        """
        return self.execute_query(query, (timetrack_id,))
        
    def get_activity_stats(self, timetrack_id):
        """Retorna estatísticas da atividade para um registro de ponto"""
        query = """
            SELECT 
                AVG(activity_level) as avg_activity,
                MAX(activity_level) as max_activity,
                MIN(activity_level) as min_activity,
                COUNT(*) as total_readings
            FROM activity_logs
            WHERE timetrack_id = %s
        """
        return self.execute_query(query, (timetrack_id,))

    def get_today_activity(self, user_id):
        """Retorna a atividade do dia atual para um usuário"""
        query = """
            SELECT 
                al.*,
                DATE_FORMAT(al.timestamp, '%H:%i') as time
            FROM activity_logs al
            JOIN timetrack t ON al.timetrack_id = t.id
            WHERE t.user_id = %s 
            AND DATE(al.timestamp) = CURDATE()
            ORDER BY al.timestamp DESC
        """
        return self.execute_query(query, (user_id,))

    # Métodos para ajuste manual de ponto
    def create_manual_entry(self, user_id, project_id, check_in, check_out, reason):
        """Cria um registro manual de ponto (requer aprovação)"""
        total_hours = (check_out - check_in).total_seconds() / 3600
        
        query = """
            INSERT INTO timetrack (
                user_id, project_id, check_in, check_out, 
                total_hours, date, manual_entry, manual_entry_reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s)
        """
        return self.execute_query(query, (
            user_id, project_id, check_in, check_out,
            total_hours, check_in.date(), reason
        ))

    def approve_manual_entry(self, timetrack_id, approver_id):
        """Aprova um registro manual de ponto"""
        query = """
            UPDATE timetrack 
            SET approved_by = %s
            WHERE id = %s AND manual_entry = TRUE
        """
        return self.execute_query(query, (approver_id, timetrack_id))

    def get_pending_approvals(self):
        """Retorna todos os registros manuais pendentes de aprovação"""
        query = """
            SELECT t.*, u.full_name, p.name as project_name
            FROM timetrack t
            JOIN users u ON t.user_id = u.id
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.manual_entry = TRUE 
            AND t.approved_by IS NULL
            ORDER BY t.date DESC
        """
        return self.execute_query(query)
        
    def update_user_consent(self, user_id, activity_consent=None, location_consent=None):
        """Atualiza as configurações de consentimento do usuário"""
        updates = []
        params = []
        
        if activity_consent is not None:
            updates.append("activity_tracking_consent = %s")
            params.append(activity_consent)
            
        if location_consent is not None:
            updates.append("location_tracking_consent = %s")
            params.append(location_consent)
            
        if not updates:
            return False
            
        query = f"""
            UPDATE users 
            SET {', '.join(updates)}
            WHERE id = %s
        """
        params.append(user_id)
        return self.execute_query(query, tuple(params))