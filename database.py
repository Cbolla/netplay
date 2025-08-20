import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_path: str = "netplay.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de revendedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                netplay_username TEXT NOT NULL,
                netplay_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de links de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER NOT NULL,
                client_username TEXT NOT NULL,
                client_password TEXT NOT NULL,
                link_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES resellers (id),
                UNIQUE(reseller_id, client_username)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_reseller(self, username: str, password: str, netplay_username: str, netplay_password: str) -> bool:
        """Cria um novo revendedor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO resellers (username, password_hash, netplay_username, netplay_password)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, netplay_username, netplay_password))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_reseller(self, username: str, password: str) -> Optional[Dict]:
        """Autentica um revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT id, username, netplay_username, netplay_password
            FROM resellers
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "netplay_username": result[2],
                "netplay_password": result[3]
            }
        return None
    
    def create_client_link(self, reseller_id: int, client_username: str, client_password: str) -> str:
        """Cria um link para um cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Gera um token único para o link
        link_token = secrets.token_urlsafe(32)
        
        # Verifica se já existe um link para este cliente deste revendedor
        cursor.execute("""
            SELECT link_token FROM client_links
            WHERE reseller_id = ? AND client_username = ?
        """, (reseller_id, client_username))
        
        existing = cursor.fetchone()
        
        if existing:
            # Atualiza o link existente
            cursor.execute("""
                UPDATE client_links
                SET client_password = ?, link_token = ?, created_at = CURRENT_TIMESTAMP
                WHERE reseller_id = ? AND client_username = ?
            """, (client_password, link_token, reseller_id, client_username))
        else:
            # Cria um novo link
            cursor.execute("""
                INSERT INTO client_links (reseller_id, client_username, client_password, link_token)
                VALUES (?, ?, ?, ?)
            """, (reseller_id, client_username, client_password, link_token))
        
        conn.commit()
        conn.close()
        
        return link_token
    
    def get_client_by_token(self, token: str) -> Optional[Dict]:
        """Busca um cliente pelo token do link"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cl.client_username, cl.client_password, r.netplay_username, r.netplay_password, r.username
            FROM client_links cl
            JOIN resellers r ON cl.reseller_id = r.id
            WHERE cl.link_token = ?
        """, (token,))
        
        result = cursor.fetchone()
        
        if result:
            # Atualiza o último acesso
            cursor.execute("""
                UPDATE client_links
                SET last_accessed = CURRENT_TIMESTAMP
                WHERE link_token = ?
            """, (token,))
            conn.commit()
        
        conn.close()
        
        if result:
            return {
                "client_username": result[0],
                "client_password": result[1],
                "reseller_netplay_username": result[2],
                "reseller_netplay_password": result[3],
                "reseller_username": result[4]
            }
        return None
    
    def get_reseller_clients(self, reseller_id: int) -> List[Dict]:
        """Lista todos os clientes de um revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT client_username, link_token, created_at, last_accessed
            FROM client_links
            WHERE reseller_id = ?
            ORDER BY created_at DESC
        """, (reseller_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            "client_username": row[0],
            "link_token": row[1],
            "created_at": row[2],
            "last_accessed": row[3]
        } for row in results]

# Instância global do banco de dados
db = Database()