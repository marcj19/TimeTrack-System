import flet as ft
import bcrypt
from datetime import datetime

class CollaboratorsScreen:
    def __init__(self, user, db, on_back):
        self.user = user
        self.db = db
        self.on_back = on_back
        self.selected_collaborator = None
        
        # Campos do formulário
        self.full_name_field = ft.TextField(
            label="Nome Completo",
            width=300,
            text_size=14
        )
        self.email_field = ft.TextField(
            label="E-mail",
            width=300,
            text_size=14
        )
        self.username_field = ft.TextField(
            label="Nome de Usuário",
            width=300,
            text_size=14
        )
        self.password_field = ft.TextField(
            label="Senha",
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=14
        )
        self.hourly_rate_field = ft.TextField(
            label="Valor/Hora (R$)",
            width=150,
            text_size=14,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        self.status_dropdown = ft.Dropdown(
            label="Status",
            width=150,
            text_size=14,
            options=[
                ft.dropdown.Option("active", "Ativo"),
                ft.dropdown.Option("inactive", "Inativo")
            ],
            value="active"
        )
        
        # Lista de colaboradores
        self.collaborators_list = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("E-mail")),
                ft.DataColumn(ft.Text("Usuário")),
                ft.DataColumn(ft.Text("Valor/Hora")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            vertical_lines=ft.BorderSide(1, ft.colors.OUTLINE),
            horizontal_lines=ft.BorderSide(1, ft.colors.OUTLINE),
            sort_column_index=0,
            width=900
        )

    def _load_collaborators(self):
        """Carrega a lista de colaboradores do banco de dados."""
        collaborators = self.db.execute_query("""
            SELECT id, full_name, email, username, hourly_rate, status
            FROM users
            WHERE role = 'colaborador'
            ORDER BY full_name
        """)
        
        self.collaborators_list.rows = []
        
        for collab in collaborators:
            self.collaborators_list.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(collab['full_name'])),
                        ft.DataCell(ft.Text(collab['email'])),
                        ft.DataCell(ft.Text(collab['username'])),
                        ft.DataCell(ft.Text(f"R$ {float(collab['hourly_rate']):.2f}")),
                        ft.DataCell(ft.Text("Ativo" if collab['status'] == 'active' else "Inativo")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, c=collab: self._edit_collaborator(c)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    tooltip="Excluir",
                                    on_click=lambda e, c=collab: self._confirm_delete(c)
                                )
                            ])
                        )
                    ]
                )
            )
        
        self.collaborators_list.update()

    def _clear_form(self):
        """Limpa os campos do formulário."""
        self.full_name_field.value = ""
        self.email_field.value = ""
        self.username_field.value = ""
        self.password_field.value = ""
        self.hourly_rate_field.value = ""
        self.status_dropdown.value = "active"
        self.selected_collaborator = None
        
        for field in [self.full_name_field, self.email_field, self.username_field,
                     self.password_field, self.hourly_rate_field, self.status_dropdown]:
            field.error_text = None
            field.update()

    def _validate_form(self):
        """Valida os campos do formulário."""
        is_valid = True
        
        if not self.full_name_field.value:
            self.full_name_field.error_text = "Nome é obrigatório"
            is_valid = False
        
        if not self.email_field.value:
            self.email_field.error_text = "E-mail é obrigatório"
            is_valid = False
        elif not '@' in self.email_field.value:
            self.email_field.error_text = "E-mail inválido"
            is_valid = False
            
        if not self.username_field.value:
            self.username_field.error_text = "Nome de usuário é obrigatório"
            is_valid = False
            
        if not self.selected_collaborator and not self.password_field.value:
            self.password_field.error_text = "Senha é obrigatória"
            is_valid = False
            
        if not self.hourly_rate_field.value:
            self.hourly_rate_field.error_text = "Valor/hora é obrigatório"
            is_valid = False
        
        return is_valid

    def _save_collaborator(self, e):
        """Salva ou atualiza um colaborador."""
        if not self._validate_form():
            return
            
        try:
            # Prepara os dados comuns
            data = {
                'full_name': self.full_name_field.value,
                'email': self.email_field.value,
                'username': self.username_field.value,
                'hourly_rate': float(self.hourly_rate_field.value),
                'status': self.status_dropdown.value,
                'role': 'colaborador'
            }
            
            if self.selected_collaborator:
                # Atualização
                if self.password_field.value:
                    # Só atualiza a senha se foi fornecida uma nova
                    hashed = bcrypt.hashpw(self.password_field.value.encode('utf-8'), bcrypt.gensalt())
                    data['password_hash'] = hashed
                    
                self.db.execute_query("""
                    UPDATE users
                    SET full_name = %(full_name)s,
                        email = %(email)s,
                        username = %(username)s,
                        hourly_rate = %(hourly_rate)s,
                        status = %(status)s
                        """ + (", password_hash = %(password_hash)s" if 'password_hash' in data else "") + """
                    WHERE id = %(id)s
                """, {**data, 'id': self.selected_collaborator['id']})
                
                message = "Colaborador atualizado com sucesso!"
            else:
                # Novo cadastro
                hashed = bcrypt.hashpw(self.password_field.value.encode('utf-8'), bcrypt.gensalt())
                data['password_hash'] = hashed
                data['created_at'] = datetime.now()
                
                self.db.execute_query("""
                    INSERT INTO users (full_name, email, username, password_hash, 
                                     hourly_rate, status, role, created_at)
                    VALUES (%(full_name)s, %(email)s, %(username)s, %(password_hash)s,
                           %(hourly_rate)s, %(status)s, %(role)s, %(created_at)s)
                """, data)
                
                message = "Colaborador cadastrado com sucesso!"
            
            # Limpa o formulário e recarrega a lista
            self._clear_form()
            self._load_collaborators()
            
            # Mostra mensagem de sucesso
            if self.content.page:
                self.content.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(message))
                )
                
        except Exception as error:
            if self.content.page:
                self.content.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Erro ao salvar: {str(error)}"))
                )

    def _edit_collaborator(self, collaborator):
        """Carrega os dados do colaborador para edição."""
        self.selected_collaborator = collaborator
        
        self.full_name_field.value = collaborator['full_name']
        self.email_field.value = collaborator['email']
        self.username_field.value = collaborator['username']
        self.password_field.value = ""  # Não carrega a senha
        self.hourly_rate_field.value = str(float(collaborator['hourly_rate']))
        self.status_dropdown.value = collaborator['status']
        
        for field in [self.full_name_field, self.email_field, self.username_field,
                     self.password_field, self.hourly_rate_field, self.status_dropdown]:
            field.update()

    def _confirm_delete(self, collaborator):
        """Mostra diálogo de confirmação para excluir colaborador."""
        def close_dlg(e):
            dialog.open = False
            self.content.page.update()
            
        def delete_confirmed(e):
            close_dlg(e)
            self._delete_collaborator(collaborator)
            
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Excluir {collaborator['full_name']}?"),
            content=ft.Text("Esta ação não pode ser desfeita."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Excluir", on_click=delete_confirmed),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        if self.content.page:
            self.content.page.dialog = dialog
            dialog.open = True
            self.content.page.update()

    def _delete_collaborator(self, collaborator):
        """Exclui um colaborador."""
        try:
            # Primeiro verifica se há registros associados
            has_records = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM timetrack
                WHERE user_id = %s
            """, (collaborator['id'],))[0]['count'] > 0
            
            if has_records:
                # Se houver registros, apenas inativa
                self.db.execute_query("""
                    UPDATE users
                    SET status = 'inactive'
                    WHERE id = %s
                """, (collaborator['id'],))
                message = "Colaborador inativado pois possui registros de tempo."
            else:
                # Se não houver registros, exclui
                self.db.execute_query("""
                    DELETE FROM users
                    WHERE id = %s
                """, (collaborator['id'],))
                message = "Colaborador excluído com sucesso!"
            
            self._load_collaborators()
            
            if self.content.page:
                self.content.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(message))
                )
                
        except Exception as error:
            if self.content.page:
                self.content.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Erro ao excluir: {str(error)}"))
                )

    def build(self, page: ft.Page):
        """Constrói a tela de gerenciamento de colaboradores."""
        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK,
                            tooltip="Voltar",
                            on_click=self.on_back
                        ),
                        ft.Text(
                            "Gerenciar Colaboradores",
                            size=24,
                            weight=ft.FontWeight.BOLD
                        )
                    ]),
                    padding=ft.padding.only(bottom=20)
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Novo Colaborador" if not self.selected_collaborator else "Editar Colaborador",
                                size=20,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Row([
                                self.full_name_field,
                                self.email_field,
                            ], wrap=True),
                            ft.Row([
                                self.username_field,
                                self.password_field,
                            ], wrap=True),
                            ft.Row([
                                self.hourly_rate_field,
                                self.status_dropdown,
                            ], wrap=True),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Salvar",
                                    on_click=self._save_collaborator
                                ),
                                ft.OutlinedButton(
                                    "Limpar",
                                    on_click=lambda _: self._clear_form()
                                )
                            ])
                        ], spacing=20),
                        padding=20
                    )
                ),
                ft.Container(height=20),
                self.collaborators_list
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            expand=True
        )
        
        # Carrega a lista inicial de colaboradores
        self._load_collaborators()
        
        return self.content