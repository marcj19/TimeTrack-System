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
            break_hours = f"{record['break_hours']:.2f}h" if record.get('break_hours') else '--'
            effective_hours = f"{record['effective_hours']:.2f}h" if record.get('effective_hours') else '--'
            project = record.get('project_name', '--')
            
            rows.append(ft.DataRow([
                ft.DataCell(ft.Text(check_in, size=12)),
                ft.DataCell(ft.Text(check_out, size=12)),
                ft.DataCell(ft.Text(total_hours, size=12)),
                ft.DataCell(ft.Text(break_hours, size=12, color=ft.colors.ORANGE)),
                ft.DataCell(ft.Text(effective_hours, size=12, color=ft.colors.BLUE)),
                ft.DataCell(ft.Text(project, size=12))
            ]))
            
        return ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data/Entrada", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Saída", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Pausas", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Efetivo", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Projeto", weight=ft.FontWeight.BOLD))
                ],
                rows=rows,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=10,
                show_checkbox_column=False
            ),
            height=400,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
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
                if user.get('is_on_break'):
                    status = "Em Pausa"
                    status_color = ft.Colors.ORANGE
                else:
                    status = "Online"
                    status_color = ft.Colors.GREEN
                entry_time = user['check_in'].strftime('%H:%M')
                project = user.get('project_name', '--')
            elif user['check_in'] and user['check_out']:
                status = "Finalizado"
                status_color = ft.Colors.BLUE
                entry_time = user['check_in'].strftime('%H:%M')
                project = "--"
            else:
                status = "Offline"
                status_color = ft.Colors.GREY
                entry_time = "--:--"
                project = "--"
                
            hours = f"{user['total_hours']:.2f}h" if user['total_hours'] else "--"
            break_hours = f"{user['break_hours']:.2f}h" if user.get('break_hours') else "--"
            
            rows.append(ft.DataRow([
                ft.DataCell(ft.Text(name, size=12)),
                ft.DataCell(ft.Container(
                    content=ft.Text(status, size=11, color=ft.Colors.WHITE),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=20
                )),
                ft.DataCell(ft.Text(entry_time, size=12)),
                ft.DataCell(ft.Text(hours, size=12)),
                ft.DataCell(ft.Text(break_hours, size=12, color=ft.Colors.ORANGE)),
                ft.DataCell(ft.Text(project, size=12))
            ]))
            
        return ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Colaborador", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Entrada", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Pausas", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Projeto", weight=ft.FontWeight.BOLD))
                ],
                rows=rows,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=10,
                show_checkbox_column=False
            ),
            height=400,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=10,
            padding=10
        )