import bcrypt

class AuthManager:
    def __init__(self, db):
        self.db = db
        self.current_user = None
        
    def login(self, username, password):
        """Autentica usuário"""
        query = "SELECT * FROM users WHERE username = %s"
        users = self.db.execute_query(query, (username,))
        
        if users and len(users) > 0:
            user = users[0]
            stored_password = user['password'].encode('utf-8')
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                self.current_user = user
                return user
        return None
        
    def logout(self):
        """Desloga usuário atual"""
        self.current_user = None
        
    def register_user(self, username, password, full_name, role='colaborador'):
        """Registra novo usuário (apenas admin)"""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        query = """
            INSERT INTO users (username, password, full_name, role)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.execute_query(query, (username, hashed_password.decode('utf-8'), full_name, role))
        
    def is_admin(self, user=None):
        """Verifica se usuário é admin"""
        if user is None:
            user = self.current_user
        return user and user.get('role') == 'admin'