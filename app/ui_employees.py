import flet as ft
from datetime import datetime
import bcrypt

class EmployeeManagementScreen(ft.UserControl):
    def __init__(self, db, page, show_snack_bar, current_user):
        super().__init__()
        self.db = db
        self.page = page
        self.show_snack_bar = show_snack_bar
        self.current_user = current_user
        self.employees = []
        self.init_fields()

    def init_fields(self):
        """Initialize form fields"""
        self.username_field = ft.TextField(
            label="Nome de usuário",
            width=300,
            height=50,
            prefix_icon=ft.Icons.PERSON,
            text_size=14,
            bgcolor=ft.Colors.SURFACE_VARIANT
        )
        
        self.fullname_field = ft.TextField(
            label="Nome completo",
            width=300,
            height=50,
            prefix_icon=ft.Icons.BADGE,
            text_size=14,
            bgcolor=ft.Colors.SURFACE_VARIANT
        )
        
        self.password_field = ft.TextField(
            label="Senha",
            width=300,
            height=50,
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            text_size=14,
            bgcolor=ft.Colors.SURFACE_VARIANT
        )
        
        self.hourly_rate_field = ft.TextField(
            label="Taxa horária (R$)",
            width=300,
            height=50,
            prefix_icon=ft.Icons.ATTACH_MONEY,
            text_size=14,
            bgcolor=ft.Colors.SURFACE_VARIANT,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        self.location_consent = ft.Switch(
            label="Permite rastreamento de localização",
            value=False
        )
        
        self.activity_consent = ft.Switch(
            label="Permite monitoramento de atividade",
            value=False
        )

        # DataTable columns
        self.columns = [
            ft.DataColumn(ft.Text("Nome completo")),
            ft.DataColumn(ft.Text("Usuário")),
            ft.DataColumn(ft.Text("Taxa horária")),
            ft.DataColumn(ft.Text("Rastreamento"), numeric=True),
            ft.DataColumn(ft.Text("Ações"), numeric=True)
        ]

        self.data_table = ft.DataTable(
            columns=self.columns,
            rows=[],
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            column_spacing=50,
            heading_row_height=70,
            data_row_min_height=50,
            data_row_max_height=100,
            divider_thickness=0,
            column_spacing=5,
            width=1100
        )

    def build(self):
        """Build the employee management screen"""
        self.load_employees()
        
        # Title and Add button
        title_row = ft.Row(
            [
                ft.Text("Gerenciamento de Colaboradores", size=24, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE,
                    icon_color=ft.Colors.PRIMARY,
                    icon_size=40,
                    tooltip="Adicionar novo colaborador",
                    on_click=self.show_add_dialog
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Main container with DataTable
        main_content = ft.Container(
            content=ft.Column([
                title_row,
                ft.Divider(height=2, color=ft.Colors.SURFACE_VARIANT),
                self.data_table
            ]),
            padding=20,
            bgcolor=ft.Colors.SURFACE,
            border_radius=10,
            width=1150
        )

        return ft.Container(
            content=main_content,
            padding=20
        )

    def load_employees(self):
        """Load employees from database and update DataTable"""
        query = """
            SELECT id, username, full_name, hourly_rate, location_tracking_consent, activity_tracking_consent 
            FROM users WHERE role = 'colaborador'
            ORDER BY full_name
        """
        self.employees = self.db.execute_query(query)
        
        rows = []
        for emp in self.employees:
            tracking_icons = ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.LOCATION_ON if emp['location_tracking_consent'] else ft.Icons.LOCATION_OFF,
                        color=ft.Colors.PRIMARY if emp['location_tracking_consent'] else ft.Colors.ERROR,
                        size=20
                    ),
                    ft.Icon(
                        ft.Icons.MONITOR_HEART if emp['activity_tracking_consent'] else ft.Icons.MONITOR_HEART_OUTLINED,
                        color=ft.Colors.PRIMARY if emp['activity_tracking_consent'] else ft.Colors.ERROR,
                        size=20
                    ),
                ],
                spacing=5
            )
            
            actions = ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=ft.Colors.PRIMARY,
                        tooltip="Editar",
                        data=emp,
                        on_click=self.show_edit_dialog
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.ERROR,
                        tooltip="Excluir",
                        data=emp,
                        on_click=self.show_delete_dialog
                    )
                ],
                spacing=0
            )
            
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(emp['full_name'])),
                        ft.DataCell(ft.Text(emp['username'])),
                        ft.DataCell(ft.Text(f"R$ {emp['hourly_rate'] or 0:.2f}")),
                        ft.DataCell(tracking_icons),
                        ft.DataCell(actions)
                    ]
                )
            )
        
        self.data_table.rows = rows
        self.update()

    def validate_employee_form(self):
        """Validate employee form fields"""
        if not self.username_field.value or len(self.username_field.value) < 3:
            self.show_snack_bar("O nome de usuário deve ter pelo menos 3 caracteres", "error")
            return False
            
        if not self.fullname_field.value or len(self.fullname_field.value) < 3:
            self.show_snack_bar("O nome completo deve ter pelo menos 3 caracteres", "error")
            return False
            
        if not self.edited_employee and (not self.password_field.value or len(self.password_field.value) < 6):
            self.show_snack_bar("A senha deve ter pelo menos 6 caracteres", "error")
            return False
            
        try:
            hourly_rate = float(self.hourly_rate_field.value or 0)
            if hourly_rate < 0:
                self.show_snack_bar("A taxa horária não pode ser negativa", "error")
                return False
        except ValueError:
            self.show_snack_bar("A taxa horária deve ser um número válido", "error")
            return False
            
        return True

    def save_employee(self, e):
        """Save new or edited employee"""
        if not self.validate_employee_form():
            return
            
        try:
            hourly_rate = float(self.hourly_rate_field.value or 0)
            
            if self.edited_employee:
                # Update existing employee
                query = """
                    UPDATE users 
                    SET full_name = %s, hourly_rate = %s,
                        location_tracking_consent = %s,
                        activity_tracking_consent = %s
                    WHERE id = %s
                """
                params = (
                    self.fullname_field.value,
                    hourly_rate,
                    self.location_consent.value,
                    self.activity_consent.value,
                    self.edited_employee['id']
                )
                
                # Update password if provided
                if self.password_field.value:
                    hashed_password = bcrypt.hashpw(
                        self.password_field.value.encode('utf-8'),
                        bcrypt.gensalt()
                    ).decode('utf-8')
                    query = query.replace("WHERE", ", password = %s WHERE")
                    params = (
                        self.fullname_field.value,
                        hourly_rate,
                        self.location_consent.value,
                        self.activity_consent.value,
                        hashed_password,
                        self.edited_employee['id']
                    )
                
            else:
                # Check if username already exists
                check_query = "SELECT COUNT(*) as count FROM users WHERE username = %s"
                result = self.db.execute_query(check_query, (self.username_field.value,))
                if result and result[0]['count'] > 0:
                    self.show_snack_bar("Este nome de usuário já está em uso", "error")
                    return

                # Create new employee
                hashed_password = bcrypt.hashpw(
                    self.password_field.value.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                query = """
                    INSERT INTO users (
                        username, password, full_name, role, 
                        hourly_rate, location_tracking_consent,
                        activity_tracking_consent
                    ) VALUES (%s, %s, %s, 'colaborador', %s, %s, %s)
                """
                params = (
                    self.username_field.value,
                    hashed_password,
                    self.fullname_field.value,
                    hourly_rate,
                    self.location_consent.value,
                    self.activity_consent.value
                )
            
            self.db.execute_query(query, params)
            self.dlg.open = False
            self.page.update()
            
            action = "atualizado" if self.edited_employee else "criado"
            self.show_snack_bar(f"Colaborador {action} com sucesso!", "success")
            self.load_employees()
            
        except Exception as e:
            print(f"Erro ao salvar colaborador: {e}")
            self.show_snack_bar("Erro ao salvar colaborador. Tente novamente.", "error")

    def delete_employee(self, e):
        """Delete employee"""
        if not self.employee_to_delete:
            return
            
        try:
            query = "DELETE FROM users WHERE id = %s"
            self.db.execute_query(query, (self.employee_to_delete['id'],))
            
            self.delete_dlg.open = False
            self.page.update()
            
            self.show_snack_bar("Colaborador excluído com sucesso!", "success")
            self.load_employees()
            
        except Exception as e:
            print(f"Erro ao excluir colaborador: {e}")
            self.show_snack_bar("Erro ao excluir colaborador. Tente novamente.", "error")

    def show_add_dialog(self, e):
        """Show dialog to add new employee"""
        self.edited_employee = None
        self.username_field.value = ""
        self.fullname_field.value = ""
        self.password_field.value = ""
        self.hourly_rate_field.value = "0.00"
        self.location_consent.value = False
        self.activity_consent.value = False
        
        self.dlg = ft.AlertDialog(
            title=ft.Text("Adicionar novo colaborador"),
            content=self.build_employee_form(),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dlg),
                ft.TextButton("Salvar", on_click=self.save_employee),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()

    def show_edit_dialog(self, e):
        """Show dialog to edit employee"""
        self.edited_employee = e.control.data
        self.username_field.value = self.edited_employee['username']
        self.username_field.disabled = True
        self.fullname_field.value = self.edited_employee['full_name']
        self.password_field.value = ""
        self.password_field.label = "Nova senha (deixe em branco para manter a atual)"
        self.hourly_rate_field.value = str(self.edited_employee['hourly_rate'] or 0)
        self.location_consent.value = bool(self.edited_employee['location_tracking_consent'])
        self.activity_consent.value = bool(self.edited_employee['activity_tracking_consent'])
        
        self.dlg = ft.AlertDialog(
            title=ft.Text("Editar colaborador"),
            content=self.build_employee_form(),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dlg),
                ft.TextButton("Salvar", on_click=self.save_employee),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()

    def show_delete_dialog(self, e):
        """Show confirmation dialog to delete employee"""
        self.employee_to_delete = e.control.data
        
        self.delete_dlg = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(
                f"Tem certeza que deseja excluir o colaborador {self.employee_to_delete['full_name']}? "
                "Esta ação não pode ser desfeita."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_delete_dlg),
                ft.TextButton("Excluir", on_click=self.delete_employee),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = self.delete_dlg
        self.delete_dlg.open = True
        self.page.update()

    def close_dlg(self, e):
        """Close employee form dialog"""
        self.dlg.open = False
        self.page.update()

    def close_delete_dlg(self, e):
        """Close delete confirmation dialog"""
        self.delete_dlg.open = False
        self.page.update()

    def build_employee_form(self):
        """Build employee form for add/edit dialog"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self.username_field,
                    self.fullname_field,
                    self.password_field,
                    self.hourly_rate_field,
                    ft.Divider(height=2, color=ft.Colors.SURFACE_VARIANT),
                    ft.Text("Consentimentos", size=16, weight=ft.FontWeight.BOLD),
                    self.location_consent,
                    self.activity_consent,
                ],
                spacing=20,
                width=350,
            ),
            padding=20,
        )