import flet as ft
from datetime import datetime, timedelta

class WeeklyChart:
    def __init__(self, data, admin_view=False):
        self.data = data
        self.admin_view = admin_view
        
    def build(self):
        """Constrói gráfico semanal simples"""
        if not self.data:
            return ft.Container(
                content=ft.Column([
                    ft.Text("Sem dados para exibir", text_align=ft.TextAlign.CENTER),
                    ft.Icon(ft.Icons.BAR_CHART, size=60, color=ft.Colors.GREY_400)
                ], alignment=ft.MainAxisAlignment.CENTER),
                height=300,
                width=400
            )
        
        # Processar dados para gráfico simples
        if self.admin_view:
            # Vista admin: agregar por usuário
            user_totals = {}
            for record in self.data:
                user = record['full_name']
                hours = float(record['daily_hours'] or 0)
                user_totals[user] = user_totals.get(user, 0) + hours
                
            chart_data = list(user_totals.items())
        else:
            # Vista colaborador: por dia
            daily_totals = {}
            for record in self.data:
                day = record['date'].strftime('%d/%m') if record['date'] else 'N/A'
                hours = float(record['daily_hours'] or 0)
                daily_totals[day] = hours
                
            chart_data = list(daily_totals.items())
            
        if not chart_data:
            return ft.Container(
                content=ft.Text("Sem dados suficientes", text_align=ft.TextAlign.CENTER),
                height=300
            )
            
        # Criar barras simples
        max_hours = max([hours for _, hours in chart_data]) if chart_data else 1
        bars = []
        
        for label, hours in chart_data[:7]:  # Máximo 7 itens
            bar_height = (hours / max_hours) * 200 if max_hours > 0 else 0
            bars.append(
                ft.Column([
                    ft.Container(
                        bgcolor=ft.Colors.BLUE,
                        height=bar_height,
                        width=40,
                        border_radius=ft.border_radius.only(
                            top_left=5, top_right=5
                        ),
                        tooltip=f"{hours:.1f}h"
                    ),
                    ft.Text(
                        label[:8],  # Limitar texto
                        size=10,
                        text_align=ft.TextAlign.CENTER,
                        width=50
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=5)
            )
            
        return ft.Container(
            content=ft.Column([
                ft.Row(
                    bars,
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    spacing=10
                ),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                ft.Text(
                    f"Máximo: {max_hours:.1f}h",
                    size=12,
                    color=ft.Colors.GREY,
                    text_align=ft.TextAlign.CENTER
                )
            ], alignment=ft.MainAxisAlignment.END),
            height=300,
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=10
        )