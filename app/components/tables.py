import flet as ft

class HistoryTable:
    def __init__(self, data):
        self.data = data
        
    def build(self):
        """Constrói tabela de histórico"""
        if not self.data:
            return ft.Container(
                content=ft.Text("Nenhum registro encontrado", 
                               text_align=ft.TextAlign.CENTER),
                padding=20
            )
            
        rows = []
        for record in self.data[:10]:  # Últimos 10 registros
            check_in = record['check_in'].strftime('%d/%m %H:%M') if record['check_in'] else '--'
            check_out = record['check_out'].strftime('%H:%M') if record['check_out'] else 'Em andamento'
            total_hours = f"{record['total_hours']:.2f}h" if record['total_hours'] else '--'
            
            rows.append(ft.DataRow([
                ft.DataCell(ft.Text(check_in, size=12)),
                ft.DataCell(ft.Text(check_out, size=12)),
                ft.DataCell(ft.Text(total_hours, size=12))
            ]))
            
        return ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data/Entrada", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Saída", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Horas", weight=ft.FontWeight.BOLD))
                ],
                rows=rows,
                border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                border_radius=10,
                show_checkbox_column=False
            ),
            height=400,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=10,
            padding=10
        )

class UsersTable:
    def __init__(self, data):
        self.data = data
        
    def build(self):
        """Constrói tabela de usuários (admin)"""
        if not self.data:
            return ft.Container(
                content=ft.Text("Nenhum usuário encontrado", 
                               text_align=ft.TextAlign.CENTER),
                padding=20
            )
            
        rows = []
        for user in self.data:
            name = user['full_name'] or '--'
            
            if user['check_in'] and not user['check_out']:
                status = "Online"
                status_color = ft.colors.GREEN
                entry_time = user['check_in'].strftime('%H:%M')
            elif user['check_in'] and user['check_out']:
                status = "Finalizado"
                status_color = ft.colors.BLUE
                entry_time = user['check_in'].strftime('%H:%M')
            else:
                status = "Offline"
                status_color = ft.colors.GREY
                entry_time = "--:--"
                
            hours = f"{user['total_hours']:.2f}h" if user['total_hours'] else "--"
            
            rows.append(ft.DataRow([
                ft.DataCell(ft.Text(name, size=12)),
                ft.DataCell(ft.Container(
                    content=ft.Text(status, size=11, color=ft.colors.WHITE),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=20
                )),
                ft.DataCell(ft.Text(entry_time, size=12)),
                ft.DataCell(ft.Text(hours, size=12))
            ]))
            
        return ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Colaborador", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Entrada", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Horas", weight=ft.FontWeight.BOLD))
                ],
                rows=rows,
                border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                border_radius=10,
                show_checkbox_column=False
            ),
            height=400,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=10,
            padding=10
        )