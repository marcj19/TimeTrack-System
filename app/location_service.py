import requests
import threading
from datetime import datetime

class GeolocationService:
    def __init__(self):
        self.current_location = None
        self.last_update = None
        self._lock = threading.Lock()
        
    def get_current_location(self):
        """
        Obtém a localização atual do usuário usando o IP Geolocation API.
        Retorna um tuple (latitude, longitude) ou None em caso de erro.
        """
        try:
            # Usando ip-api.com (gratuito, sem necessidade de chave API)
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    with self._lock:
                        self.current_location = (data['lat'], data['lon'])
                        self.last_update = datetime.now()
                    return self.current_location
            return None
        except Exception as e:
            print(f"Erro ao obter localização: {e}")
            return None
            
    def get_cached_location(self):
        """
        Retorna a última localização conhecida e o timestamp da atualização.
        """
        with self._lock:
            return (self.current_location, self.last_update)
            
    def get_location_details(self, lat, lon):
        """
        Obtém detalhes de uma localização específica.
        Retorna um dicionário com informações como cidade, estado, país, etc.
        """
        try:
            response = requests.get(
                f'http://ip-api.com/json/{lat},{lon}',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return {
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'country': data.get('country'),
                        'timezone': data.get('timezone')
                    }
            return None
        except Exception as e:
            print(f"Erro ao obter detalhes da localização: {e}")
            return None