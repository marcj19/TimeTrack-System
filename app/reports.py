import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

class ReportGenerator:
    def __init__(self, db):
        self.db = db

    def generate_productivity_report(self, user_id=None, project_id=None, start_date=None, end_date=None):
        """Gera relatório detalhado de produtividade."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Converte datetime para date se necessário
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()

        query = """
            SELECT 
                t.date,
                u.full_name,
                p.name as project_name,
                SUM(t.total_hours) as total_hours,
                AVG(al.activity_level) as avg_activity,
                COUNT(DISTINCT b.id) as total_breaks,
                SUM(b.total_minutes) / 60 as total_break_hours,
                COUNT(DISTINCT tsk.id) as completed_tasks
            FROM timetrack t
            JOIN users u ON t.user_id = u.id
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN activity_logs al ON t.id = al.timetrack_id
            LEFT JOIN breaks b ON t.id = b.timetrack_id
            LEFT JOIN tasks tsk ON t.task_id = tsk.id AND tsk.status = 'completed'
            WHERE t.date BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if user_id:
            query += " AND t.user_id = %s"
            params.append(user_id)
            
        if project_id:
            query += " AND t.project_id = %s"
            params.append(project_id)

        query += " GROUP BY t.date, u.full_name, p.name ORDER BY t.date"

        data = self.db.execute_query(query, tuple(params))
        return data if data else []

    def generate_activity_heatmap(self, user_id, start_date=None, end_date=None):
        """Gera um heatmap de atividade por hora do dia."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        query = """
            SELECT 
                DATE(al.timestamp) as date,
                HOUR(al.timestamp) as hour,
                AVG(al.activity_level) as activity_level
            FROM activity_logs al
            JOIN timetrack t ON al.timetrack_id = t.id
            WHERE t.user_id = %s
            AND al.timestamp BETWEEN %s AND %s
            GROUP BY DATE(al.timestamp), HOUR(al.timestamp)
            ORDER BY date, hour
        """
        
        data = self.db.execute_query(query, (user_id, start_date, end_date))
        return data if data else []

    def generate_project_summary(self, project_id, start_date=None, end_date=None):
        """Gera um resumo detalhado do projeto."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Converte datetime para date se necessário
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()

        query = """
            SELECT 
                p.name as project_name,
                p.description,
                COUNT(DISTINCT t.user_id) as total_users,
                SUM(t.total_hours) as total_hours,
                COUNT(DISTINCT tsk.id) as total_tasks,
                SUM(CASE WHEN tsk.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN tsk.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                AVG(al.activity_level) as avg_activity
            FROM projects p
            LEFT JOIN timetrack t ON p.id = t.project_id
            LEFT JOIN tasks tsk ON p.id = tsk.project_id
            LEFT JOIN activity_logs al ON t.id = al.timetrack_id
            WHERE p.id = %s
            AND (t.date BETWEEN %s AND %s OR t.date IS NULL)
            GROUP BY p.id, p.name, p.description
        """
        
        project_data = self.db.execute_query(query, (project_id, start_date, end_date))
        
        # Obtém detalhes de custos e faturamento
        if project_data and len(project_data) > 0:
            total_hours = float(project_data[0]['total_hours'] or 0)
            hourly_rate = self.db.get_project_hourly_rate(project_id)
            
            project_data[0]['estimated_cost'] = total_hours * hourly_rate if hourly_rate else 0
            
        return project_data[0] if project_data else None

    def generate_presence_summary(self, start_date=None, end_date=None):
        """Gera um resumo de presença dos usuários."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Converte datetime para date se necessário
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()

        query = """
            SELECT 
                u.full_name,
                COUNT(DISTINCT t.date) as days_present,
                AVG(t.total_hours) as avg_daily_hours,
                SUM(t.total_hours) as total_hours,
                COUNT(DISTINCT b.id) as total_breaks,
                SUM(b.total_minutes) / 60 as total_break_hours,
                COUNT(DISTINCT CASE WHEN t.manual_entry = 1 THEN t.id END) as manual_entries
            FROM users u
            LEFT JOIN timetrack t ON u.id = t.user_id
            LEFT JOIN breaks b ON t.id = b.timetrack_id
            WHERE u.role = 'colaborador'
            AND t.date BETWEEN %s AND %s
            GROUP BY u.id, u.full_name
            ORDER BY u.full_name
        """
        
        return self.db.execute_query(query, (start_date, end_date))

    def plot_activity_heatmap(self, data):
        """Cria um heatmap de atividade usando Plotly."""
        if not data:
            return None
            
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        pivot_table = df.pivot(index='date', columns='hour', values='activity_level')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index.strftime('%Y-%m-%d'),
            colorscale='Viridis',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title='Heatmap de Atividade por Hora',
            xaxis_title='Hora do Dia',
            yaxis_title='Data',
            height=400
        )
        
        return fig.to_html(include_plotlyjs=True, full_html=False)

    def plot_productivity_trends(self, data):
        """Cria gráficos de tendências de produtividade."""
        if not data:
            return None
            
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Gráfico de horas por projeto
        fig_hours = px.line(df, 
            x='date', 
            y='total_hours',
            color='project_name',
            title='Horas Trabalhadas por Projeto'
        )
        
        # Gráfico de nível de atividade médio
        fig_activity = px.line(df,
            x='date',
            y='avg_activity',
            color='project_name',
            title='Nível de Atividade Médio'
        )
        
        return {
            'hours': fig_hours.to_html(include_plotlyjs=True, full_html=False),
            'activity': fig_activity.to_html(include_plotlyjs=True, full_html=False)
        }

    def plot_project_progress(self, project_data):
        """Cria visualizações do progresso do projeto."""
        if not project_data:
            return None
            
        # Gráfico de tarefas
        task_data = {
            'Status': ['Concluídas', 'Em Progresso', 'Pendentes'],
            'Quantidade': [
                project_data['completed_tasks'],
                project_data['in_progress_tasks'],
                project_data['total_tasks'] - (project_data['completed_tasks'] + project_data['in_progress_tasks'])
            ]
        }
        
        df_tasks = pd.DataFrame(task_data)
        fig_tasks = px.pie(df_tasks, 
            values='Quantidade', 
            names='Status',
            title='Distribuição de Tarefas'
        )
        
        return fig_tasks.to_html(include_plotlyjs=True, full_html=False)

    def format_summary_card(self, data):
        """Formata dados para exibição em um card de resumo."""
        if not data:
            return None
            
        return {
            'title': data['project_name'],
            'metrics': [
                {'label': 'Total de Horas', 'value': f"{data['total_hours']:.1f}h"},
                {'label': 'Colaboradores', 'value': str(data['total_users'])},
                {'label': 'Tarefas Concluídas', 'value': f"{data['completed_tasks']}/{data['total_tasks']}"},
                {'label': 'Atividade Média', 'value': f"{data['avg_activity']:.1f}%"},
                {'label': 'Custo Estimado', 'value': f"R$ {data['estimated_cost']:.2f}"}
            ],
            'description': data['description']
        }