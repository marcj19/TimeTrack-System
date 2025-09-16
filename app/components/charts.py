import flet as ft
from datetime import datetime, timedelta

class WeeklyChart:
    def __init__(self, data, admin_view=False):
        self.data = data
        self.admin_view = admin_view
        
        # Process data to separate breaks
        self.total_hours = {}
        self.break_hours = {}
        self.effective_hours = {}
        
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
            # Vista colaborador: por dia com pausas
            daily_totals = {}
            daily_breaks = {}
            for record in self.data:
                day = record['date'].strftime('%d/%m') if record['date'] else 'N/A'
                total_hours = float(record['daily_hours'] or 0)
                break_hours = float(record['break_hours'] or 0)
                effective_hours = float(record['effective_hours'] or 0)
                
                # Acumular horas por dia
                daily_totals[day] = total_hours
                daily_breaks[day] = break_hours
                
            # Criar lista de tuplas (dia, horas_efetivas, horas_pausa)
            chart_data = [(day, daily_totals[day], daily_breaks[day]) 
                         for day in daily_totals.keys()]
            
        if not chart_data:
            return ft.Container(
                content=ft.Text("Sem dados suficientes", text_align=ft.TextAlign.CENTER),
                height=300
            )
            
        # Criar barras compostas (trabalho + pausa)
        max_hours = max([total for _, total, _ in chart_data]) if chart_data else 1
        bars = []
        
        for label, total_hours, break_hours in chart_data[:7]:  # Máximo 7 itens
            effective_hours = total_hours - break_hours
            effective_height = (effective_hours / max_hours) * 200 if max_hours > 0 else 0
            break_height = (break_hours / max_hours) * 200 if max_hours > 0 else 0
            
            bars.append(
                ft.Column([
                    ft.Stack([
                        # Barra de trabalho efetivo
                        ft.Container(
                            bgcolor=ft.Colors.BLUE,
                            height=effective_height,
                            width=40,
                            border_radius=ft.border_radius.only(
                                top_left=5, top_right=5
                            ),
                            tooltip=f"Trabalho: {effective_hours:.1f}h"
                        ),
                        # Barra de pausa
                        ft.Container(
                            bgcolor=ft.Colors.ORANGE,
                            height=break_height,
                            width=40,
                            bottom=effective_height,
                            border_radius=ft.border_radius.only(
                                top_left=5, top_right=5
                            ) if effective_height == 0 else None,
                            tooltip=f"Pausas: {break_hours:.1f}h"
                        )
                    ], height=effective_height + break_height),
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
                ft.Row([
                    ft.Row([
                        ft.Container(bgcolor=ft.Colors.BLUE, width=20, height=10),
                        ft.Text("Trabalho", size=12)
                    ]),
                    ft.Row([
                        ft.Container(bgcolor=ft.Colors.ORANGE, width=20, height=10),
                        ft.Text("Pausas", size=12)
                    ])
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
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