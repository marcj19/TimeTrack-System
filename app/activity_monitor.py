from pynput import mouse, keyboard
import threading
import time
from datetime import datetime

class ActivityMonitor:
    def __init__(self, db, user_id, timetrack_id, log_interval=60):
        self.db = db
        self.user_id = user_id
        self.timetrack_id = timetrack_id
        self.log_interval = log_interval  # Intervalo de log em segundos
        
        self.mouse_events = 0
        self.keyboard_events = 0
        self.last_activity = time.time()
        self.is_monitoring = False
        
        # Lock para acesso seguro aos contadores
        self.lock = threading.Lock()
        
    def start(self):
        """Inicia o monitoramento de atividade"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        
        # Inicia listeners em threads separadas
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        # Inicia thread de logging
        self.log_thread = threading.Thread(target=self._log_activity_loop)
        self.log_thread.daemon = True
        self.log_thread.start()
        
    def stop(self):
        """Para o monitoramento de atividade"""
        self.is_monitoring = False
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
            
        # Registra última atividade antes de parar
        self._log_current_activity()
        
    def on_mouse_move(self, x, y):
        with self.lock:
            self.mouse_events += 1
            self.last_activity = time.time()
            
    def on_mouse_click(self, x, y, button, pressed):
        with self.lock:
            self.mouse_events += 1
            self.last_activity = time.time()
            
    def on_mouse_scroll(self, x, y, dx, dy):
        with self.lock:
            self.mouse_events += 1
            self.last_activity = time.time()
            
    def on_key_press(self, key):
        with self.lock:
            self.keyboard_events += 1
            self.last_activity = time.time()
            
    def on_key_release(self, key):
        with self.lock:
            self.keyboard_events += 1
            self.last_activity = time.time()
            
    def _log_activity_loop(self):
        """Loop principal para registro periódico de atividade"""
        while self.is_monitoring:
            time.sleep(self.log_interval)
            self._log_current_activity()
            
    def _log_current_activity(self):
        """Registra o nível atual de atividade no banco de dados"""
        with self.lock:
            # Calcula o nível de atividade (0-100)
            # Considera tanto eventos de mouse quanto teclado
            total_events = self.mouse_events + self.keyboard_events
            
            # Reseta contadores
            self.mouse_events = 0
            self.keyboard_events = 0
            
            # Calcula nível de atividade baseado em eventos por minuto
            # Assume que 60 eventos/minuto (1 por segundo) é atividade normal
            activity_level = min(100, int((total_events / self.log_interval) * 100 / 1))
            
            # Verifica inatividade
            if time.time() - self.last_activity > self.log_interval:
                activity_level = 0
                
        # Registra no banco de dados
        self.db.log_activity(self.timetrack_id, activity_level)
        
    def get_current_activity_level(self):
        """Retorna o nível atual de atividade (0-100)"""
        with self.lock:
            total_events = self.mouse_events + self.keyboard_events
            # Se inativo por mais de 1 minuto, retorna 0
            if time.time() - self.last_activity > 60:
                return 0
            # Calcula nível baseado em eventos do último minuto
            return min(100, int((total_events / 60) * 100))