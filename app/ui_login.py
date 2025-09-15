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
            prefix_icon=ft.Icons.PERSON,
            border_radius=10,
            width=300
        )
        
        self.password_field = ft.TextField(
            label="Senha",
            prefix_icon=ft.Icons.LOCK,
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
            icon=ft.Icons.BRIGHTNESS_6,
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
                    ft.Icon(ft.Icons.ACCESS_TIME, size=60, color=ft.Colors.BLUE),
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
                        color=ft.Colors.GREY
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.username_field,
                    self.password_field,
                    self.error_text,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    login_btn,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Login padrão: admin / admin123",
                        size=12,
                        color=ft.Colors.GREY,
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
                ft.Colors.BLUE_50,
                ft.Colors.INDIGO_100
            ])
        )
