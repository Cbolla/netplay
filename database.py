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
                is_blocked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                blocked_at TIMESTAMP,
                blocked_reason TEXT
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
        
        # Tabela de sessões ativas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (reseller_id) REFERENCES resellers (id)
            )
        """)
        
        # Tabela de logs de atividade
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES resellers (id)
            )
        """)
        
        # Tabela de clientes dos revendedores (cache da API Netplay)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reseller_customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER NOT NULL,
                customer_id TEXT NOT NULL,
                customer_username TEXT NOT NULL,
                customer_name TEXT,
                server_name TEXT,
                package_name TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES resellers (id),
                UNIQUE(reseller_id, customer_id)
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
    
    def get_client_by_credentials(self, username: str, password: str) -> Optional[Dict]:
        """Busca um cliente pelas credenciais username/password"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cl.client_username, cl.client_password, r.netplay_username, r.netplay_password, r.username, cl.link_token
            FROM client_links cl
            JOIN resellers r ON cl.reseller_id = r.id
            WHERE cl.client_username = ? AND cl.client_password = ?
        """, (username, password))
        
        result = cursor.fetchone()
        
        if result:
            # Atualiza o último acesso
            cursor.execute("""
                UPDATE client_links
                SET last_accessed = CURRENT_TIMESTAMP
                WHERE client_username = ? AND client_password = ?
            """, (username, password))
            conn.commit()
        
        conn.close()
        
        if result:
            return {
                "client_username": result[0],
                "client_password": result[1],
                "reseller_netplay_username": result[2],
                "reseller_netplay_password": result[3],
                "reseller_username": result[4],
                "link_token": result[5]
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
    
    # === MÉTODOS PARA PAINEL ADMINISTRATIVO ===
    
    def authenticate_admin(self, username: str, password: str) -> bool:
        """Autentica o administrador usando credenciais do .env"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        admin_username = os.getenv("NETPLAY_USERNAME")
        admin_password = os.getenv("NETPLAY_PASSWORD")
        
        return username == admin_username and password == admin_password
    
    def get_all_resellers(self) -> List[Dict]:
        """Lista todos os revendedores para o painel admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.id, r.username, r.netplay_username, r.is_blocked, r.created_at, r.blocked_at, r.blocked_reason,
                   COUNT(DISTINCT cl.id) as total_clients,
                   COUNT(DISTINCT CASE WHEN s.is_active = 1 THEN s.id END) as active_sessions,
                   MAX(s.last_activity) as last_activity
            FROM resellers r
            LEFT JOIN client_links cl ON r.id = cl.reseller_id
            LEFT JOIN active_sessions s ON r.id = s.reseller_id
            GROUP BY r.id
            ORDER BY r.created_at DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            "id": row[0],
            "username": row[1],
            "netplay_username": row[2],
            "is_blocked": bool(row[3]),
            "created_at": row[4],
            "blocked_at": row[5],
            "blocked_reason": row[6],
            "total_clients": row[7],
            "active_sessions": row[8],
            "last_activity": row[9],
            "is_online": bool(row[8] > 0)
        } for row in results]
    
    def block_reseller(self, reseller_id: int, reason: str = None) -> bool:
        """Bloqueia um revendedor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE resellers 
                SET is_blocked = 1, blocked_at = CURRENT_TIMESTAMP, blocked_reason = ?
                WHERE id = ?
            """, (reason, reseller_id))
            
            # Desativar todas as sessões ativas
            cursor.execute("""
                UPDATE active_sessions 
                SET is_active = 0 
                WHERE reseller_id = ?
            """, (reseller_id,))
            
            # Log da ação
            cursor.execute("""
                INSERT INTO activity_logs (reseller_id, action, details)
                VALUES (?, 'BLOCKED', ?)
            """, (reseller_id, f"Bloqueado: {reason or 'Sem motivo especificado'}"))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def unblock_reseller(self, reseller_id: int) -> bool:
        """Desbloqueia um revendedor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE resellers 
                SET is_blocked = 0, blocked_at = NULL, blocked_reason = NULL
                WHERE id = ?
            """, (reseller_id,))
            
            # Log da ação
            cursor.execute("""
                INSERT INTO activity_logs (reseller_id, action, details)
                VALUES (?, 'UNBLOCKED', 'Desbloqueado pelo administrador')
            """, (reseller_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def block_multiple_resellers(self, reseller_ids: List[int], reason: str = None) -> int:
        """Bloqueia múltiplos revendedores"""
        blocked_count = 0
        for reseller_id in reseller_ids:
            if self.block_reseller(reseller_id, reason):
                blocked_count += 1
        return blocked_count
    
    def create_session(self, reseller_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Cria uma nova sessão ativa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_token = secrets.token_urlsafe(32)
        
        cursor.execute("""
            INSERT INTO active_sessions (reseller_id, session_token, ip_address, user_agent)
            VALUES (?, ?, ?, ?)
        """, (reseller_id, session_token, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        return session_token
    
    def update_session_activity(self, session_token: str) -> bool:
        """Atualiza a última atividade de uma sessão"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE active_sessions 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE session_token = ? AND is_active = 1
            """, (session_token,))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def end_session(self, session_token: str) -> bool:
        """Encerra uma sessão"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE active_sessions 
                SET is_active = 0 
                WHERE session_token = ?
            """, (session_token,))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def log_activity(self, reseller_id: int, action: str, details: str = None, ip_address: str = None):
        """Registra uma atividade no log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO activity_logs (reseller_id, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        """, (reseller_id, action, details, ip_address))
        
        conn.commit()
        conn.close()
    
    def get_activity_logs(self, limit: int = 100) -> List[Dict]:
        """Obtém os logs de atividade recentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT al.timestamp, r.username, al.action, al.details, al.ip_address
            FROM activity_logs al
            LEFT JOIN resellers r ON al.reseller_id = r.id
            ORDER BY al.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            "timestamp": row[0],
            "username": row[1] or "Sistema",
            "action": row[2],
            "details": row[3],
            "ip_address": row[4]
        } for row in results]
    
    def update_reseller_customers(self, reseller_id: int, customers: List[Dict]):
        """Atualiza o cache de clientes de um revendedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Limpar clientes antigos
        cursor.execute("DELETE FROM reseller_customers WHERE reseller_id = ?", (reseller_id,))
        
        # Inserir novos clientes
        for customer in customers:
            cursor.execute("""
                INSERT INTO reseller_customers 
                (reseller_id, customer_id, customer_username, customer_name, server_name, package_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                reseller_id,
                customer.get("id", ""),
                customer.get("username", ""),
                customer.get("name", ""),
                customer.get("server", ""),
                customer.get("package", "")
            ))
        
        conn.commit()
        conn.close()
    
    def get_admin_stats(self) -> Dict:
        """Obtém estatísticas gerais para o painel admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de revendedores
        cursor.execute("SELECT COUNT(*) FROM resellers")
        total_resellers = cursor.fetchone()[0]
        
        # Revendedores bloqueados
        cursor.execute("SELECT COUNT(*) FROM resellers WHERE is_blocked = 1")
        blocked_resellers = cursor.fetchone()[0]
        
        # Sessões ativas
        cursor.execute("SELECT COUNT(*) FROM active_sessions WHERE is_active = 1")
        active_sessions = cursor.fetchone()[0]
        
        # Total de clientes
        cursor.execute("SELECT COUNT(*) FROM client_links")
        total_clients = cursor.fetchone()[0]
        
        # Atividade hoje
        cursor.execute("""
            SELECT COUNT(*) FROM activity_logs 
            WHERE DATE(timestamp) = DATE('now')
        """)
        today_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_resellers": total_resellers,
            "active_resellers": total_resellers - blocked_resellers,
            "blocked_resellers": blocked_resellers,
            "active_sessions": active_sessions,
            "total_clients": total_clients,
            "today_activity": today_activity
        }

# Instância global do banco de dados
db = Database()