import flet as ft
import plotly.graph_objects as go
from datetime import datetime, timedelta

class ActivityGraph:
    def __init__(self, activity_data):
        self.activity_data = activity_data
        
    def build(self):
        """Constrói gráfico de atividade"""
        if not self.activity_data:
            return ft.Container(
                content=ft.Text("Sem dados de atividade", text_align=ft.TextAlign.CENTER),
                padding=20
            )
            
        # Preparar dados para o gráfico
        timestamps = []
        activity_levels = []
        
        for record in self.activity_data:
            timestamps.append(record['timestamp'].strftime('%H:%M'))
            activity_levels.append(record['activity_level'])
            
        # Criar gráfico com plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=activity_levels,
            mode='lines+markers',
            name='Nível de Atividade',
            line=dict(color='#2196F3', width=2),
            fill='tozeroy'
        ))
        
        fig.update_layout(
            title="Nível de Atividade ao Longo do Dia",
            xaxis_title="Hora",
            yaxis_title="Nível de Atividade (%)",
            yaxis=dict(range=[0, 100]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#666666'),
            margin=dict(t=40, r=20, b=40, l=40),
            showlegend=False
        )
        
        # Convertendo para HTML
        graph_html = fig.to_html(
            include_plotlyjs=True,
            config={'displayModeBar': False}
        )
        
        return ft.WebView(
            content=graph_html,
            height=300,
            visible=True
        )

class ActivityCard:
    def __init__(self, current_level=0, consent_status=False, on_consent_change=None):
        self.current_level = current_level
        self.consent_status = consent_status
        self.on_consent_change = on_consent_change
        
    def build(self):
        """Constrói card de monitoramento de atividade"""
        consent_switch = ft.Switch(
            label="Permitir monitoramento de atividade",
            value=self.consent_status,
            on_change=self.on_consent_change
        )
        
        activity_indicator = ft.ProgressBar(
            value=self.current_level / 100,
            color=self._get_level_color(self.current_level),
            bgcolor=ft.Colors.GREY_300,
            height=15,
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Monitoramento de Atividade",
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Divider(),
                    consent_switch,
                    ft.Column([
                        ft.Text(
                            f"Nível de Atividade: {self.current_level}%",
                            size=14
                        ),
                        activity_indicator
                    ]) if self.consent_status else None,
                    ft.Text(
                        "O monitoramento de atividade ajuda a validar seu tempo de trabalho "
                        "através de eventos de mouse e teclado, respeitando sua privacidade.",
                        size=12,
                        color=ft.Colors.GREY,
                        text_align=ft.TextAlign.CENTER
                    )
                ], spacing=15),
                padding=20
            )
        )
        
    def _get_level_color(self, level):
        """Retorna a cor baseada no nível de atividade"""
        if level < 30:
            return ft.Colors.RED
        elif level < 70:
            return ft.Colors.ORANGE
        else:
            return ft.Colors.GREEN