import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
import os

class Database:
    def __init__(self, db_path="netplay.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de revendedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                netplay_username TEXT,
                netplay_password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT FALSE,
                blocked_reason TEXT,
                customers_data TEXT
            )
        ''')
        
        # Adicionar colunas se não existirem (para bancos existentes)
        try:
            cursor.execute('ALTER TABLE resellers ADD COLUMN netplay_username TEXT')
        except sqlite3.OperationalError:
            pass  # Coluna já existe
        
        try:
            cursor.execute('ALTER TABLE resellers ADD COLUMN netplay_password TEXT')
        except sqlite3.OperationalError:
            pass  # Coluna já existe
        
        # Tabela de sessões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES resellers (id)
            )
        ''')
        
        # Tabela de links de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                reseller_id INTEGER,
                client_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES resellers (id)
            )
        ''')
        
        # Tabela de logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER,
                action TEXT NOT NULL,
                description TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def authenticate_reseller(self, username, password):
        """Autentica um revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT id, username, email, is_blocked, blocked_reason, netplay_username, netplay_password FROM resellers WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "is_blocked": bool(result[3]),
                "blocked_reason": result[4],
                "netplay_username": result[5],
                "netplay_password": result[6]
            }
        return None
    
    def create_reseller(self, username, password, email=None, netplay_username=None, netplay_password=None):
        """Cria um novo revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute(
                "INSERT INTO resellers (username, password_hash, email, netplay_username, netplay_password) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, email, netplay_username, netplay_password)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def create_session(self, reseller_id, expires_hours=24):
        """Cria uma sessão para o revendedor"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO sessions (reseller_id, token, expires_at) VALUES (?, ?, ?)",
            (reseller_id, token, expires_at)
        )
        
        conn.commit()
        conn.close()
        
        return token
    
    def create_client_link(self, reseller_id, client_data, expires_hours=168):
        """Cria um link para cliente"""
        token = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO client_links (token, reseller_id, client_data, expires_at) VALUES (?, ?, ?, ?)",
            (token, reseller_id, json.dumps(client_data), expires_at)
        )
        
        conn.commit()
        conn.close()
        
        return token
    
    def get_client_by_token(self, token):
        """Busca dados do cliente pelo token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT client_data, expires_at FROM client_links WHERE token = ?",
            (token,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result and datetime.fromisoformat(result[1]) > datetime.now():
            return json.loads(result[0])
        return None
    
    def get_client_by_credentials(self, username, password):
        """Busca cliente por credenciais (mock)"""
        return {"username": username, "password": password}
    
    def get_reseller_clients(self, reseller_id):
        """Retorna clientes do revendedor"""
        return []
    
    def authenticate_admin(self, username, password):
        """Autentica administrador (credenciais fixas)"""
        return username == "admin" and password == "admin123"
    
    def get_admin_stats(self):
        """Retorna estatísticas do admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM resellers")
        total_resellers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resellers WHERE is_blocked = TRUE")
        blocked_resellers = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_resellers": total_resellers,
            "active_resellers": total_resellers - blocked_resellers,
            "blocked_resellers": blocked_resellers,
            "total_migrations": 0
        }
    
    def get_all_resellers(self):
        """Retorna todos os revendedores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, email, is_blocked, blocked_reason, created_at FROM resellers")
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "is_blocked": bool(row[3]),
                "blocked_reason": row[4],
                "created_at": row[5]
            }
            for row in results
        ]
    
    def block_reseller(self, reseller_id, reason):
        """Bloqueia um revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE resellers SET is_blocked = TRUE, blocked_reason = ? WHERE id = ?",
            (reason, reseller_id)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def block_multiple_resellers(self, reseller_ids, reason):
        """Bloqueia múltiplos revendedores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ",".join("?" * len(reseller_ids))
        cursor.execute(
            f"UPDATE resellers SET is_blocked = TRUE, blocked_reason = ? WHERE id IN ({placeholders})",
            [reason] + reseller_ids
        )
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return count
    
    def unblock_reseller(self, reseller_id):
        """Desbloqueia um revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE resellers SET is_blocked = FALSE, blocked_reason = NULL WHERE id = ?",
            (reseller_id,)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def log_activity(self, reseller_id, action, description, ip_address=None):
        """Registra atividade no log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO activity_logs (reseller_id, action, description, ip_address) VALUES (?, ?, ?, ?)",
            (reseller_id, action, description, ip_address)
        )
        
        conn.commit()
        conn.close()
    
    def get_activity_logs(self, limit=100):
        """Retorna logs de atividade"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT reseller_id, action, description, ip_address, created_at FROM activity_logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "reseller_id": row[0],
                "action": row[1],
                "description": row[2],
                "ip_address": row[3],
                "created_at": row[4]
            }
            for row in results
        ]
    
    def update_reseller_customers(self, reseller_id, customers):
        """Atualiza dados dos clientes do revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE resellers SET customers_data = ? WHERE id = ?",
            (json.dumps(customers), reseller_id)
        )
        
        conn.commit()
        conn.close()

# Instância global do banco de dados
db = Database()