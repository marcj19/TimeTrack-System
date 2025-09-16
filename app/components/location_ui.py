import flet as ft
from datetime import datetime

class LocationCard:
    def __init__(self, lat=None, lon=None, details=None, last_update=None):
        self.lat = lat
        self.lon = lon
        self.details = details or {}
        self.last_update = last_update
        
    def build(self):
        """Constrói o card de localização"""
        status_icon = ft.Icon(
            ft.Icons.LOCATION_ON if self.lat and self.lon else ft.Icons.LOCATION_OFF,
            color=ft.Colors.GREEN if self.lat and self.lon else ft.Colors.GREY
        )
        
        status_row = ft.Row([
            status_icon,
            ft.Text(
                "Localização Disponível" if self.lat and self.lon else "Localização Indisponível",
                color=ft.Colors.GREEN if self.lat and self.lon else ft.Colors.GREY
            )
        ])
        
        content_column = [status_row]
        
        if self.lat and self.lon:
            location_text = f"Lat: {self.lat:.6f}, Lon: {self.lon:.6f}"
            
            if self.details:
                if self.details.get('city') and self.details.get('region'):
                    location_text = f"{self.details['city']}, {self.details['region']}"
                    if self.details.get('country'):
                        location_text += f" - {self.details['country']}"
                        
            content_column.extend([
                ft.Text(location_text, size=14),
                ft.Text(
                    f"Última atualização: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'N/A'}",
                    size=12,
                    color=ft.Colors.GREY_600
                )
            ])
            
            if self.lat and self.lon:
                maps_url = f"https://www.google.com/maps?q={self.lat},{self.lon}"
                content_column.append(
                    ft.TextButton(
                        "Ver no Google Maps",
                        icon=ft.icons.MAP,
                        url=maps_url
                    )
                )
                
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    content_column,
                    spacing=10
                ),
                padding=15
            )
        )
        
class LocationHistoryTable:
    def __init__(self, history_data):
        self.history_data = history_data or []
        
    def build(self):
        """Constrói a tabela de histórico de localizações"""
        if not self.history_data:
            return ft.Text("Nenhum histórico de localização disponível.")
            
        columns = [
            ft.DataColumn(ft.Text("Data/Hora")),
            ft.DataColumn(ft.Text("Local")),
            ft.DataColumn(ft.Text("Projeto")),
            ft.DataColumn(ft.Text("Tipo"))
        ]
        
        rows = []
        for entry in self.history_data:
            timestamp = datetime.strptime(str(entry['timestamp']), '%Y-%m-%d %H:%M:%S')
            location = f"{entry['city']}, {entry['region']}" if entry.get('city') and entry.get('region') else \
                      f"{entry['latitude']:.6f}, {entry['longitude']:.6f}"
                      
            event_type = "Check-in" if abs((timestamp - entry['check_in']).total_seconds()) < 300 else "Check-out"
            
            rows.append(
                ft.DataRow([
                    ft.DataCell(ft.Text(timestamp.strftime('%d/%m/%Y %H:%M'))),
                    ft.DataCell(ft.Text(location)),
                    ft.DataCell(ft.Text(entry.get('project_name', 'N/A'))),
                    ft.DataCell(ft.Text(event_type))
                ])
            )
            
        return ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_400),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_400),
            column_spacing=50
        )