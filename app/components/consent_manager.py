import flet as ft

class ConsentManager:
    def __init__(self, db, user, on_update=None):
        self.db = db
        self.user = user
        self.on_update = on_update
        
        self.activity_consent_switch = ft.Switch(
            label="Monitoramento de Atividade",
            value=user.get('activity_tracking_consent', False),
            on_change=self.handle_activity_consent
        )
        
        self.location_consent_switch = ft.Switch(
            label="Rastreamento de Localização",
            value=user.get('location_tracking_consent', False),
            on_change=self.handle_location_consent
        )
        
        self.consent_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Configurações de Privacidade"),
            content=ft.Column([
                ft.Text(
                    "Configure suas preferências de privacidade abaixo. "
                    "Você pode alterar essas configurações a qualquer momento.",
                    size=14
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Monitoramento de Atividade", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Quando ativado, monitora eventos de teclado e mouse para calcular "
                            "seu nível de atividade. Nenhum dado específico sobre teclas ou "
                            "cliques é registrado.",
                            size=14,
                            color=ft.Colors.GREY_700
                        ),
                        self.activity_consent_switch
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=10,
                    margin=ft.margin.only(bottom=10)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Rastreamento de Localização", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Quando ativado, registra sua localização apenas no momento do "
                            "check-in e check-out. A localização não é monitorada continuamente.",
                            size=14,
                            color=ft.Colors.GREY_700
                        ),
                        self.location_consent_switch
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=10
                )
            ], scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Fechar", on_click=self.close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def handle_activity_consent(self, e):
        """Atualiza o consentimento para monitoramento de atividade"""
        consent = e.control.value
        if self.db.update_user_consent(self.user['id'], activity_consent=consent):
            self.user['activity_tracking_consent'] = consent
            if self.on_update:
                self.on_update()

    def handle_location_consent(self, e):
        """Atualiza o consentimento para rastreamento de localização"""
        consent = e.control.value
        if self.db.update_user_consent(self.user['id'], location_consent=consent):
            self.user['location_tracking_consent'] = consent
            if self.on_update:
                self.on_update()

    def show(self, page):
        """Exibe o diálogo de gerenciamento de consentimento"""
        page.dialog = self.consent_dialog
        self.consent_dialog.open = True
        page.update()

    def close_dialog(self, e):
        """Fecha o diálogo"""
        self.consent_dialog.open = False
        self.consent_dialog.page.update()