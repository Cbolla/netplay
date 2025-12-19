from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import asyncio
import httpx
import unicodedata
import re
import sqlite3
import os
from dotenv import load_dotenv
from database import db

app = FastAPI(
    title="Netplay RPA System",
    description="Sistema de automação para migração de clientes Netplay",
    version="1.0.0"
)

# Configurar CORS para permitir acesso externo
# Configurações de CORS para produção
cors_origins = os.getenv("CORS_ORIGINS", "*")
allowed_origins = cors_origins.split(",") if cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"!!! ERRO DE VALIDAÇÃO 422: {exc.errors()} !!!")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- Variáveis de Configuração e Cabeçalhos ---
NETPLAY_API_BASE_URL = "https://netplay.mplll.com/api"
AUTH_TOKEN = None
CURRENT_RESELLER = None
ALL_NETPLAY_PACKAGES = []
NETPLAY_HEADERS = {"accept": "application/json", "user-agent": "Mozilla/5.0", "origin": "https://netplay.mplll.com", "referer": "https://netplay.mplll.com/"}

# --- Configuração MaxPlayer ---
MAXPLAYER_API_BASE_URL = "https://api.maxplayer.tv/v3/api/panel"
MAXPLAYER_AUTH_TOKEN = None
MAXPLAYER_CREDENTIALS = {
    "email": "futuro.noob@icloud.com",
    "password": "William2025@"
}
MAXPLAYER_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0",
    "origin": "https://my.maxplayer.tv",
    "referer": "https://my.maxplayer.tv/"
}

# Mapa de Servidores NetPlay → MaxPlayer domain_id
SERVER_MAP = {
    "☀️ NETPLAY SOLAR ☀️": "1750385133185114283",
    "☄️ NETPLAY ANDRÔMEDA ☄️": "1750385543431130630",
    "⚡ NETPLAY SPEED ⚡": "1750384873990823788",
    "🌑 NETPLAY LUNAR 🌑": "1753657859890202256",
    "🌠 NETPLAY FLASH 🌠": "1756345548755066123",
    "🌬️ NETPLAY VÊNUS 🌬️": "1750385433321950245",
    "🏛️ NETPLAY ATENA 🏛️": "1750385235476264855",
    "👺 NETPLAY TITÃ 👺": "1750385578271894993",
    "💎 NETPLAY HADES 💎": "1750385472254248136",
    "💣 EXPLOSION 💣": "1755362642846269320",
    "📡 NETPLAY SKY 📡": "1750385204630190352",
    "🔥 NETPLAY FIRE 🔥": "1756378841114454295",
    "🛸 NETPLAY GALAXY 🛸": "1750385171559926175",
    "🧿 NETPLAY SEVEN 🧿": "1750384954579088880",
    "🪐 NETPLAY URANO 🪐": "1750385502428005340",
    # Servidores adicionais do MaxPlayer
    "ALPSYNC": "1764111505708068572",
    "StarPlay4": "1764334750403735279",
    "⭐️ StarPlay 1 ⭐️": "1762974282561465612",
    "⭐️ StarPlay 2 ⭐️": "1762974308988184556",
    "⭐️ StarPlay 3 ⭐️": "1762974556593364213",
    "🟣🟣🟣🟣": "1765801295763130892"
}

# Credenciais administrativas (configure com suas credenciais reais)
# Você pode configurar através de variáveis de ambiente ou diretamente aqui
# Carrega variáveis do arquivo .env se existir
load_dotenv()

NETPLAY_USERNAME = os.getenv("NETPLAY_USERNAME", "seu_usuario_admin")  # Configure sua credencial administrativa
NETPLAY_PASSWORD = os.getenv("NETPLAY_PASSWORD", "sua_senha_admin")    # Configure sua credencial administrativa

# Validação das credenciais
if NETPLAY_USERNAME == "seu_usuario_admin" or NETPLAY_PASSWORD == "sua_senha_admin":
    print("⚠️  ATENÇÃO: Credenciais da Netplay não configuradas!")
    print("📝 Configure suas credenciais reais no arquivo .env ou diretamente no código.")
    print("📖 Consulte o README.md para instruções detalhadas.")
    print("")

# --- Modelos Pydantic ---
class LoginRequest(BaseModel): username: str; password: str
class CustomerInfo(BaseModel): id: str; username: str; package_name: str
class BatchMigrateRequest(BaseModel): customers: list[CustomerInfo]; server_id: str; server_name: str; include_maxplayer: bool = False
class ClientLoginRequest(BaseModel): username: str; password: str
class ClientMigrateRequest(BaseModel): server_id: str; password: str = None; client_username: str = None; include_maxplayer: bool = False
class CreateClientLinkRequest(BaseModel): client_username: str; client_password: str
class ClientTokenLoginRequest(BaseModel): token: str
class ClientAuthRequest(BaseModel): 
    token: str = None
    username: str = None
    password: str = None
    reseller_id: int = None

# --- Modelos para Painel Admin ---
class AdminLoginRequest(BaseModel): username: str; password: str
class BlockResellerRequest(BaseModel): reseller_ids: list[int]; reason: str = None
class UnblockResellerRequest(BaseModel): reseller_id: int
class SaveMaxPlayerCredentialsRequest(BaseModel): email: str; password: str

# Função para detectar URL base (ngrok ou localhost)
async def get_base_url(request: Request) -> str:
    """Detecta automaticamente se está rodando com ngrok ou localhost"""
    try:
        # Verifica se há ngrok rodando
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                # Tenta acessar API do ngrok
                response = await client.get("http://localhost:4040/api/tunnels", timeout=2.0)
                if response.status_code == 200:
                    tunnels = response.json().get("tunnels", [])
                    # Procura por túnel HTTPS
                    for tunnel in tunnels:
                        if tunnel.get("proto") == "https":
                            return tunnel.get("public_url", "http://localhost:8000")
                    # Se não encontrou HTTPS, usa HTTP
                    for tunnel in tunnels:
                        if tunnel.get("proto") == "http":
                            return tunnel.get("public_url", "http://localhost:8000")
            except:
                pass
        
        # Se não conseguiu detectar ngrok, usa host do request
        host = request.headers.get("host", "localhost:8000")
        
        # Se o host contém ngrok, usa HTTPS
        if "ngrok" in host:
            return f"https://{host}"
        
        # Caso contrário, usa HTTP com localhost
        return "http://localhost:8000"
        
    except Exception:
        # Em caso de erro, retorna localhost
        return "http://localhost:8000"

# (NOVO) Função para normalizar nomes de planos de forma mais inteligente
def normalize_string(s: str) -> str:
    s = str(s).lower().strip()
    # Substitui abreviações comuns ANTES de remover caracteres
    s = s.replace('s/', 'sem')
    s = s.replace('c/', 'com')
    # Remove acentos
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    # Remove todos os outros caracteres não alfanuméricos
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

# --- Funções MaxPlayer ---
async def login_maxplayer(client: httpx.AsyncClient, credentials: dict = None):
    """Autentica na API MaxPlayer e armazena o token globalmente"""
    global MAXPLAYER_AUTH_TOKEN
    if MAXPLAYER_AUTH_TOKEN:
        return  # Já autenticado
    
    # Usar credenciais fornecidas ou fallback para as hardcoded
    creds = credentials if credentials else MAXPLAYER_CREDENTIALS
    
    headers = {**MAXPLAYER_HEADERS, "content-type": "application/json"}
    try:
        resp = await client.post(
            f"{MAXPLAYER_API_BASE_URL}/login",
            headers=headers,
            json=creds
        )
        resp.raise_for_status()
        token = resp.json().get("token")
        if not token:
            raise Exception("Token da Maxplayer não encontrado.")
        MAXPLAYER_AUTH_TOKEN = token
        print(f"✅ Autenticado no MaxPlayer com sucesso (email: {creds.get('email')})")
    except Exception as e:
        print(f"❌ Erro ao autenticar no MaxPlayer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível autenticar na Maxplayer: {e}"
        )

async def migrate_customer_on_maxplayer(
    username: str,
    server_name: str,
    client: httpx.AsyncClient
) -> str:
    """Migra um cliente no MaxPlayer para um novo servidor"""
    if not MAXPLAYER_AUTH_TOKEN:
        raise Exception("Autenticação da Maxplayer perdida.")
    
    headers = {**MAXPLAYER_HEADERS, "Authorization": f"Bearer {MAXPLAYER_AUTH_TOKEN}"}
    
    try:
        # 1. Buscar cliente
        params = {"search": username, "limit": 1, "agent": "false"}
        resp_search = await client.get(
            f"{MAXPLAYER_API_BASE_URL}/view/reseller/search-users",
            headers=headers,
            params=params
        )
        resp_search.raise_for_status()
        users = resp_search.json().get("users", [])
        if not users:
            return "Não encontrado"
        
        # 2. Obter detalhes da lista
        customer_id = users[0].get("id")
        resp_details = await client.get(
            f"{MAXPLAYER_API_BASE_URL}/view/reseller/user/{customer_id}",
            headers=headers
        )
        resp_details.raise_for_status()
        lists = resp_details.json().get("lists", [])
        if not lists:
            return "Erro: Nenhuma lista para editar."
        
        # 3. Atualizar servidor
        list_info = lists[0]
        iptv_info = list_info.get("iptv_info", {})
        new_domain_id = SERVER_MAP.get(server_name)
        if not new_domain_id:
            return f"Erro: Servidor '{server_name}' não mapeado."
        
        payload = {
            "list_id": list_info.get("id"),
            "domain_id": new_domain_id,
            "new_list_name": list_info.get("name"),
            "iptv_username": iptv_info.get("username"),
            "iptv_password": iptv_info.get("password"),
        }
        if not all(payload.values()):
            return "Erro: Dados da lista incompletos."
        
        resp_edit = await client.post(
            f"{MAXPLAYER_API_BASE_URL}/actions/reseller/edit-list",
            headers=headers,
            json=payload
        )
        resp_edit.raise_for_status()
        success = resp_edit.json().get("success")
        if success:
            print(f"✅ MaxPlayer: Cliente '{username}' migrado para {server_name}")
            
            # Verificar servidor atual após migração
            try:
                resp_verify = await client.get(
                    f"{MAXPLAYER_API_BASE_URL}/view/reseller/user/{customer_id}",
                    headers=headers
                )
                resp_verify.raise_for_status()
                verify_lists = resp_verify.json().get("lists", [])
                
                if verify_lists:
                    current_domain_id = verify_lists[0].get("domain_id")
                    # Buscar nome do servidor pelo domain_id
                    current_server_name = None
                    for srv_name, srv_id in SERVER_MAP.items():
                        if srv_id == current_domain_id:
                            current_server_name = srv_name
                            break
                    
                    if current_server_name:
                        print(f"📍 MaxPlayer: Servidor CONFIRMADO do cliente '{username}': {current_server_name} (domain_id: {current_domain_id})")
                        if current_domain_id == new_domain_id:
                            print(f"✅ VERIFICAÇÃO: Migração confirmada! Cliente está no servidor correto.")
                        else:
                            print(f"⚠️  VERIFICAÇÃO: ATENÇÃO! Cliente NÃO está no servidor esperado!")
                            print(f"   Esperado: {server_name} ({new_domain_id})")
                            print(f"   Atual: {current_server_name} ({current_domain_id})")
                    else:
                        print(f"📍 MaxPlayer: Cliente '{username}' está no domain_id: {current_domain_id}")
            except Exception as verify_error:
                print(f"⚠️  Não foi possível verificar servidor atual: {verify_error}")
            
            print(f"📍 MaxPlayer: Servidor esperado: {server_name} (domain_id: {new_domain_id})")
            return "Migrado com sucesso"
        else:
            return "Falha na API"
    
    except Exception as e:
        print(f"❌ Erro ao migrar '{username}' na Maxplayer: {e}")
        return "Erro na migração"

# --- Rotas do Backend ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/client.html")
async def read_client():
    with open("frontend/client.html", "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())


@app.get("/client", response_class=HTMLResponse)
async def client_page():
    """Página do cliente"""
    with open("frontend/client.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/servidores", response_class=HTMLResponse)
async def servers_page():
    """Página de monitoramento de servidores"""
    with open("frontend/servers.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/r{reseller_id}/client", response_class=HTMLResponse)
async def client_page_reseller(reseller_id: int):
    """Página do cliente para um revendedor específico usando ID"""
    # Verifica se o revendedor existe pelo ID
    try:
        conn = sqlite3.connect("netplay.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM resellers WHERE id = ?", (reseller_id,))
        reseller = cursor.fetchone()
        conn.close()
        
        if not reseller:
            raise HTTPException(status_code=404, detail="Revendedor não encontrado")
        
        # Lê o HTML do cliente e injeta o reseller_id
        with open("frontend/client.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            
        # Injeta o reseller_id no HTML
        html_content = html_content.replace(
            '<body>',
            f'<body data-reseller-id="{reseller[0]}" data-reseller-name="{reseller[1]}">')
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/login")
async def login(request: LoginRequest, req: Request):
    global AUTH_TOKEN, CURRENT_RESELLER
    
    # Primeiro, autentica na Netplay para verificar se as credenciais são válidas
    headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
    try:
        response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", headers=headers, json=request.dict())
        response.raise_for_status()
        login_body = response.json()
        token = login_body.get("token") or login_body.get("access_token")
        if not token: raise HTTPException(status_code=401, detail="Token não encontrado.")
        AUTH_TOKEN = token
        
        # Captura netplay_user_id da resposta de login, se disponível
        netplay_uid = None
        try:
            netplay_uid = (login_body.get("user", {}) or {}).get("id")
            if not netplay_uid:
                netplay_uid = login_body.get("userId") or login_body.get("user_id")
            if not netplay_uid and isinstance(login_body, dict):
                data = login_body.get("data")
                if isinstance(data, dict):
                    netplay_uid = data.get("id") or data.get("userId") or data.get("user_id")
        except Exception:
            pass
        
        # Verifica se o revendedor já existe no banco local
        reseller = db.authenticate_reseller(request.username, request.password)
        
        if not reseller:
            # Se não existe, cria o revendedor no banco local
            success = db.create_reseller(
                username=request.username,
                password=request.password,
                email=request.username,  # Usando username como email
                netplay_username=request.username,
                netplay_password=request.password
            )
            if not success:
                raise HTTPException(status_code=500, detail="Erro ao criar revendedor no sistema.")
            
            # Busca novamente após criar
            reseller = db.authenticate_reseller(request.username, request.password)
        
        # Verificar se o revendedor está bloqueado
        if reseller and db.get_all_resellers():
            reseller_info = next((r for r in db.get_all_resellers() if r["id"] == reseller["id"]), None)
            if reseller_info and reseller_info["is_blocked"]:
                db.log_activity(reseller["id"], "LOGIN_BLOCKED", f"Tentativa de login bloqueada: {reseller_info['blocked_reason']}", req.client.host)
                raise HTTPException(status_code=403, detail=f"Conta bloqueada: {reseller_info['blocked_reason']}")
        
        # Se obtivemos netplay_uid, persistir no banco e no objeto reseller
        if 'netplay_uid' in locals() and netplay_uid:
            try:
                db.update_reseller_netplay_user_id(reseller["id"], netplay_uid)
                reseller["netplay_user_id"] = netplay_uid
            except Exception:
                pass
        else:
            # Tentar pegar via /auth/me como fallback
            try:
                me_headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {token}"}
                for url in [f"{NETPLAY_API_BASE_URL}/auth/me", f"{NETPLAY_API_BASE_URL}/users/me", f"{NETPLAY_API_BASE_URL}/me"]:
                    me_resp = requests.get(url, headers=me_headers)
                    if me_resp.status_code == 200:
                        body = me_resp.json()
                        uid = body.get("id") or body.get("userId") or body.get("user_id")
                        if not uid and isinstance(body, dict):
                            data = body.get("data") or body
                            uid = (data.get("id") if isinstance(data, dict) else None) or (data.get("userId") if isinstance(data, dict) else None) or (data.get("user_id") if isinstance(data, dict) else None)
                        if uid:
                            db.update_reseller_netplay_user_id(reseller["id"], uid)
                            reseller["netplay_user_id"] = uid
                            break
            except Exception:
                pass
        
        # Criar sessão ativa
        session_token = db.create_session(reseller["id"])
        
        # Log da atividade
        db.log_activity(reseller["id"], "LOGIN", "Login realizado com sucesso", req.client.host)
        
        # Armazena o revendedor autenticado
        CURRENT_RESELLER = reseller
        
        return {
            "token": token,
            "session_token": session_token,
            "reseller_id": reseller["id"],
            "username": reseller["username"],
            "netplay_user_id": reseller.get("netplay_user_id")
        }
    except HTTPException:
        raise
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            raise HTTPException(status_code=401, detail="Credenciais inválidas na Netplay.")
        else:
            raise HTTPException(status_code=500, detail=f"Erro na API da Netplay: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Erro de conexão com a Netplay.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no login: {e}")

@app.post("/api/save_maxplayer_credentials")
async def save_maxplayer_credentials(request: SaveMaxPlayerCredentialsRequest):
    """Salva as credenciais MaxPlayer do usuário logado"""
    if not CURRENT_RESELLER or not CURRENT_RESELLER.get("id"):
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")
    
    try:
        db.update_reseller_maxplayer_credentials(
            CURRENT_RESELLER["id"],
            request.email,
            request.password
        )
        return {"success": True, "message": "Credenciais MaxPlayer salvas com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar credenciais: {e}")

@app.get("/api/servidores_e_planos")
async def get_servidores_e_planos():
    global ALL_NETPLAY_PACKAGES
    if not AUTH_TOKEN: raise HTTPException(status_code=401, detail="Não autenticado.")
    headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {AUTH_TOKEN}"}
    try:
        response = requests.get(f"{NETPLAY_API_BASE_URL}/servers", headers=headers)
        response.raise_for_status()
        servers_data = response.json().get("data", [])
        servers_list = [{"id": s.get("id"), "name": s.get("name")} for s in servers_data]
        
        packages_list = []
        seen_ids = set()
        for server in servers_data:
            for pkg in server.get("packages", []):
                if pkg.get("id") not in seen_ids:
                    pkg_info = {"id": pkg.get("id"), "name": pkg.get("name"), "server_id": server.get("id")}
                    packages_list.append(pkg_info)
                    seen_ids.add(pkg.get("id"))
        ALL_NETPLAY_PACKAGES = packages_list

        return {"servers": servers_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {e}")

@app.get("/api/servers/status")
async def check_servers_status():
    """Verifica o status online/offline dos servidores Netplay"""
    servers = [
        {"name": "SEVEN", "url": "http://vr766.com:80"},
        {"name": "GALAXY", "url": "http://galaxy.netpl4y.com"},
        {"name": "LUNAR", "url": "http://lunar.netpl4y.com"},
        {"name": "SPEED", "url": "http://obix.fun"},
        {"name": "OLYMPUS", "url": "http://olympus.netpl4y.com"},
        {"name": "EXPLOSION", "url": "http://explosion.netpl4y.com"},
        {"name": "TITA", "url": "http://tita.netpl4y.com"},
        {"name": "SKY", "url": "http://facilita.fun:80"},
        {"name": "SOLAR", "url": "http://solar.netpl4y.com"},
        {"name": "URANO", "url": "http://cdn.ofmp.site"},
        {"name": "ATENA", "url": "http://dns.whsv.top:80"},
        {"name": "ANDROMEDA", "url": "http://socio.gp4.fun"},
        {"name": "HADES", "url": "http://hades.netpl4y.com"},
        {"name": "VENUS", "url": "http://venus.netpl4y.com"},
        {"name": "FIRE", "url": "http://fire.netpl4y.com"}
    ]
    
    async def check_server(client, server, retry=False):
        """Verifica um servidor individual"""
        try:
            response = await client.get(server["url"])
            return server["name"], {
                "online": response.status_code < 500,
                "status_code": response.status_code,
                "url": server["url"],
                "verified": retry  # Indica se foi verificado duas vezes
            }
        except Exception as e:
            return server["name"], {
                "online": False,
                "error": str(e),
                "url": server["url"],
                "verified": retry
            }
    
    # Primeira verificação - todos os servidores em paralelo
    async with httpx.AsyncClient(timeout=3.0) as client:
        tasks = [check_server(client, server) for server in servers]
        results_list = await asyncio.gather(*tasks)
    
    # Converter lista de resultados para dicionário
    results = {name: status for name, status in results_list}
    
    # Segunda verificação - apenas para servidores offline
    offline_servers = [
        server for server in servers 
        if not results[server["name"]]["online"]
    ]
    
    if offline_servers:
        async with httpx.AsyncClient(timeout=3.0) as client:
            retry_tasks = [check_server(client, server, retry=True) for server in offline_servers]
            retry_results = await asyncio.gather(*retry_tasks)
        
        # Atualizar resultados com a segunda verificação
        for name, status in retry_results:
            results[name] = status
    
    return {"success": True, "servers": results}

@app.get("/api/client/servers")
async def get_client_servers():
    """Retorna lista de servidores disponíveis para clientes"""
    try:
        # Verificar se as credenciais estão configuradas
        if NETPLAY_USERNAME == "seu_usuario_admin" or NETPLAY_PASSWORD == "sua_senha_admin":
            raise HTTPException(status_code=500, detail="Credenciais da Netplay não configuradas. Configure no arquivo .env ou diretamente no código.")
        
        # Usar credenciais administrativas para obter servidores
        admin_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
        admin_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                     headers=admin_headers, 
                                     json={"username": NETPLAY_USERNAME, "password": NETPLAY_PASSWORD},
                                     timeout=10)
        admin_response.raise_for_status()
        admin_token = admin_response.json().get("token") or admin_response.json().get("access_token")
        
        if not admin_token:
            raise HTTPException(status_code=500, detail="Erro de autenticação administrativa. Verifique suas credenciais.")
        
        headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
        servers_response = requests.get(f"{NETPLAY_API_BASE_URL}/servers", headers=headers)
        servers_response.raise_for_status()
        servers_data = servers_response.json()
        
        servers = []
        # Verificar se servers_data é uma lista ou tem uma estrutura diferente
        if isinstance(servers_data, dict) and "data" in servers_data:
            server_list = servers_data["data"]
        elif isinstance(servers_data, dict) and "servers" in servers_data:
            server_list = servers_data["servers"]
        elif isinstance(servers_data, list):
            server_list = servers_data
        else:
            server_list = []
        
        for server in server_list:
            if isinstance(server, dict):
                servers.append({
                    "id": str(server.get("id", "unknown")),
                    "name": server.get("name", "Unknown Server")
                })
        return {"servers": servers}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            raise HTTPException(status_code=401, detail="Credenciais administrativas inválidas na Netplay.")
        else:
            raise HTTPException(status_code=500, detail=f"Erro na API da Netplay: {e.response.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"Erro de conexão com a API da Netplay: {e}")
        raise HTTPException(status_code=500, detail="Erro de conexão com a API da Netplay. Verifique sua conexão com a internet.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição com a API da Netplay: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão com a API da Netplay: {str(e)}")
    except Exception as e:
        print(f"Erro inesperado ao obter servidores: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.get("/api/client/{client_id}")
async def get_client_data(client_id: str):
    """Busca dados de um cliente específico"""
    try:
        # Por enquanto, vamos simular os dados do cliente
        # Em uma implementação real, isso viria do banco de dados ou API da Netplay
        
        # Simular busca de dados do cliente
        # Aqui você pode implementar a lógica para buscar os dados reais do cliente
        client_data = {
            "id": client_id,
            "username": client_id,  # Assumindo que o ID é o username
            "password": "senha_padrao",  # Em produção, isso viria do banco ou seria solicitado
            "name": f"Cliente {client_id}",
            "server": "Servidor Atual"
        }
        
        return {"success": True, "client": client_data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/create_client_link")
async def create_client_link(request: CreateClientLinkRequest, req: Request):
    """Cria um link de acesso para um cliente"""
    try:
        # Verifica se há um revendedor autenticado
        if not CURRENT_RESELLER:
            raise HTTPException(status_code=401, detail="Nenhum revendedor autenticado. Faça login primeiro.")
        
        reseller_id = CURRENT_RESELLER["id"]
        
        # Cria o link no banco de dados
        link_token = db.create_client_link(
            reseller_id=reseller_id,
            client_username=request.client_username,
            client_password=request.client_password
        )
        
        # Detecta a URL base (ngrok ou localhost)
        base_url = await get_base_url(req)
        
        # Gera a URL completa do link
        link_url = f"{base_url}/client?token={link_token}"
        
        return {
            "success": True,
            "link_token": link_token,
            "link_url": link_url,
            "client_username": request.client_username
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar link: {e}")

@app.get("/api/reseller_clients")
async def get_reseller_clients(reseller_id: int, req: Request):
    """Lista todos os clientes de um revendedor"""
    try:
        clients = db.get_reseller_clients(reseller_id)
        
        # Detecta a URL base
        base_url = await get_base_url(req)
        
        # Adiciona a URL completa para cada cliente
        for client in clients:
            client["link_url"] = f"{base_url}/client?token={client['link_token']}"
        
        return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar clientes: {e}")

@app.get("/api/generated_links")
async def get_generated_links(req: Request):
    """Lista todos os links gerados pelo revendedor atual"""
    try:
        # Verifica se há um revendedor autenticado
        if not CURRENT_RESELLER:
            raise HTTPException(status_code=401, detail="Nenhum revendedor autenticado. Faça login primeiro.")
        
        reseller_id = CURRENT_RESELLER["id"]
        
        # Detecta a URL base
        base_url = await get_base_url(req)
        
        conn = sqlite3.connect("netplay.db")
        cursor = conn.cursor()
        
        # Buscar todos os links gerados por este revendedor
        cursor.execute("""
            SELECT id, client_username, link_token, created_at, last_accessed, is_active
            FROM client_links 
            WHERE reseller_id = ?
            ORDER BY created_at DESC
        """, (reseller_id,))
        
        links = []
        for row in cursor.fetchall():
            link_data = {
                "id": row[0],
                "client_username": row[1],
                "link_token": row[2],
                "link_url": f"{base_url}/client?token={row[2]}",
                "created_at": row[3],
                "last_access": row[4],
                "is_active": bool(row[5])
            }
            links.append(link_data)
        
        conn.close()
        return {"success": True, "links": links}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/generated_links/{link_id}")
async def delete_generated_link(link_id: int):
    """Exclui um link gerado"""
    try:
        # Verifica se há um revendedor autenticado
        if not CURRENT_RESELLER:
            raise HTTPException(status_code=401, detail="Nenhum revendedor autenticado. Faça login primeiro.")
        
        reseller_id = CURRENT_RESELLER["id"]
        
        conn = sqlite3.connect("netplay.db")
        cursor = conn.cursor()
        
        # Verificar se o link pertence ao revendedor atual
        cursor.execute("""
            SELECT id FROM client_links 
            WHERE id = ? AND reseller_id = ?
        """, (link_id, reseller_id))
        
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Link não encontrado ou não pertence a este revendedor.")
        
        # Excluir o link
        cursor.execute("DELETE FROM client_links WHERE id = ?", (link_id,))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Link excluído com sucesso."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/test_credentials")
async def test_credentials(request: ClientLoginRequest):
    """Testa se as credenciais são válidas na Netplay (apenas para debug)"""
    try:
        client_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
        client_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                       headers=client_headers, 
                                       json={
                                           "username": request.username,
                                           "password": request.password
                                       })
        
        if client_response.status_code == 200:
            client_token = client_response.json().get("token") or client_response.json().get("access_token")
            if client_token:
                return {
                    "success": True,
                    "message": "Credenciais válidas na Netplay",
                    "token_exists": bool(client_token)
                }
        
        return {
            "success": False,
            "message": f"Erro na autenticação: Status {client_response.status_code}",
            "response": client_response.text[:200] if hasattr(client_response, 'text') else "N/A"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro na requisição: {str(e)}"
        }

@app.get("/api/search_customer")
async def search_customer(account_number: str = None, server_id: str = None, perPage: int | None = None, status: str | None = None, reseller_id: int | None = None, userId: str | None = None, packageId: str | None = None, expiryFrom: str | None = None, expiryTo: str | None = None, isTrial: str | None = None, connections: str | None = None):
    global AUTH_TOKEN
    if not AUTH_TOKEN and not reseller_id:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    
    params = {}
    if account_number: params["username"] = account_number
    if server_id: params["serverId"] = server_id
    if packageId: params["packageId"] = packageId
    if expiryFrom: params["expiryFrom"] = expiryFrom
    if expiryTo: params["expiryTo"] = expiryTo
    if isTrial: params["isTrial"] = isTrial
    if connections: params["connections"] = connections
    params["status"] = status or "ACTIVE"
    if perPage:
        params["perPage"] = perPage
    if userId:
        params["userId"] = userId
    else:
        # Se não foi informado userId explicitamente e não há reseller_id, usar o netplay_user_id do usuário logado
        if not reseller_id:
            if CURRENT_RESELLER and CURRENT_RESELLER.get("netplay_user_id"):
                params["userId"] = CURRENT_RESELLER["netplay_user_id"]
            else:
                # Tentativa de obter via /auth/me e persistir
                try:
                    me_headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {AUTH_TOKEN}"}
                    for url in [f"{NETPLAY_API_BASE_URL}/auth/me", f"{NETPLAY_API_BASE_URL}/users/me", f"{NETPLAY_API_BASE_URL}/me"]:
                        me_resp = requests.get(url, headers=me_headers)
                        if me_resp.status_code == 200:
                            body = me_resp.json()
                            uid = body.get("id") or body.get("userId") or body.get("user_id")
                            if not uid and isinstance(body, dict):
                                data = body.get("data") or body
                                uid = (data.get("id") if isinstance(data, dict) else None) or (data.get("userId") if isinstance(data, dict) else None) or (data.get("user_id") if isinstance(data, dict) else None)
                            if uid:
                                params["userId"] = uid
                                if CURRENT_RESELLER:
                                    db.update_reseller_netplay_user_id(CURRENT_RESELLER["id"], uid)
                                    CURRENT_RESELLER["netplay_user_id"] = uid
                                break
                except Exception:
                    pass
    
    try:
        # Se foi informada uma revenda específica, usar credenciais dela
        if reseller_id:
            reseller = db.get_reseller_by_id(reseller_id)
            if not reseller or not reseller.get("netplay_username") or not reseller.get("netplay_password"):
                raise HTTPException(status_code=404, detail="Credenciais da revenda não encontradas")
            login_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
            login_resp = requests.post(
                f"{NETPLAY_API_BASE_URL}/auth/login",
                headers=login_headers,
                json={"username": reseller["netplay_username"], "password": reseller["netplay_password"]}
            )
            login_resp.raise_for_status()
            reseller_token = login_resp.json().get("token") or login_resp.json().get("access_token")
            if not reseller_token:
                raise HTTPException(status_code=500, detail="Falha ao autenticar revenda na Netplay")
            headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {reseller_token}"}
        else:
            if not AUTH_TOKEN:
                raise HTTPException(status_code=401, detail="Não autenticado.")
            headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {AUTH_TOKEN}"}
        
        response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
        if response.status_code == 401:
            # Tenta reautenticar e refazer a requisição
            try:
                if reseller_id:
                    reseller = db.get_reseller_by_id(reseller_id)
                    if reseller and reseller.get("netplay_username") and reseller.get("netplay_password"):
                        login_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
                        login_resp = requests.post(
                            f"{NETPLAY_API_BASE_URL}/auth/login",
                            headers=login_headers,
                            json={"username": reseller["netplay_username"], "password": reseller["netplay_password"]}
                        )
                        login_resp.raise_for_status()
                        reseller_token = login_resp.json().get("token") or login_resp.json().get("access_token")
                        headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {reseller_token}"}
                        response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
                else:
                    # Reautentica usando credenciais da revenda atual
                    if CURRENT_RESELLER:
                        reseller = db.get_reseller_by_id(CURRENT_RESELLER["id"]) if CURRENT_RESELLER.get("id") else None
                        if reseller and reseller.get("netplay_username") and reseller.get("netplay_password"):
                            login_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
                            login_resp = requests.post(
                                f"{NETPLAY_API_BASE_URL}/auth/login",
                                headers=login_headers,
                                json={"username": reseller["netplay_username"], "password": reseller["netplay_password"]}
                            )
                            login_resp.raise_for_status()
                            AUTH_TOKEN = login_resp.json().get("token") or login_resp.json().get("access_token")
                            headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {AUTH_TOKEN}"}
                            response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
            except Exception:
                pass
        response.raise_for_status()
        clientes = response.json().get("data", [])
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao pesquisar cliente: {e}")

@app.post("/api/client/login")
async def client_login(request: ClientAuthRequest):
    """Autentica um cliente usando token do link gerado pelo revendedor ou credenciais diretas da Netplay"""
    try:
        # Verifica se é login por token
        if request.token:
            # Busca o cliente pelo token
            client_data = db.get_client_by_token(request.token)
            
            if not client_data:
                raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
            
            # Usa as credenciais do revendedor para buscar informações do cliente na Netplay
            admin_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
            admin_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                         headers=admin_headers, 
                                         json={
                                             "username": client_data["reseller_netplay_username"],
                                             "password": client_data["reseller_netplay_password"]
                                         })
            admin_response.raise_for_status()
            admin_token = admin_response.json().get("token") or admin_response.json().get("access_token")
            
            if not admin_token:
                raise HTTPException(status_code=500, detail="Erro de autenticação com revendedor.")
            
            # Busca o cliente usando token do revendedor
            headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
            params = {"username": client_data["client_username"]}
            response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
            response.raise_for_status()
            customers = response.json().get("data", [])
            
            # Verifica se o cliente existe
            client_found = None
            for customer in customers:
                if customer.get("username") == client_data["client_username"]:
                    client_found = customer
                    break
            
            if not client_found:
                raise HTTPException(status_code=404, detail="Cliente não encontrado na Netplay.")
            
            # Extrai informações do servidor e pacote
            server_info = client_found.get("server", {})
            server_name = server_info.get("name") if isinstance(server_info, dict) else server_info
            server_id = server_info.get("id") if isinstance(server_info, dict) else None
            
            package_info = client_found.get("package", {})
            package_name = package_info.get("name") if isinstance(package_info, dict) else package_info
            
            return {
                "success": True,
                "client_info": {
                    "id": client_found.get("id"),
                    "username": client_found.get("username"),
                    "server_name": server_name,
                    "server_id": server_id,
                    "package_name": package_name
                },
                "token": request.token,
                "auth_method": "token"
            }
        
        # Verifica se é login por credenciais (apenas username ou username + password)
        elif request.username:
            # Se há um token ou reseller_id junto com credenciais, valida se o cliente pertence ao revendedor
            if request.token or request.reseller_id:
                # Busca informações do revendedor (por token ou reseller_id)
                reseller_data = None
                
                if request.token:
                    # Busca por token
                    token_data = db.get_client_by_token(request.token)
                    if not token_data:
                        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
                    reseller_data = {
                        "netplay_username": token_data["reseller_netplay_username"],
                        "netplay_password": token_data["reseller_netplay_password"]
                    }
                elif request.reseller_id:
                    # Busca por reseller_id
                    conn = sqlite3.connect("netplay.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT netplay_username, netplay_password FROM resellers WHERE id = ?", (request.reseller_id,))
                    reseller_row = cursor.fetchone()
                    conn.close()
                    
                    if not reseller_row:
                        raise HTTPException(status_code=404, detail="Revendedor não encontrado.")
                    
                    reseller_data = {
                        "netplay_username": reseller_row[0],
                        "netplay_password": reseller_row[1]
                    }
                
                if not reseller_data:
                    raise HTTPException(status_code=400, detail="Dados do revendedor não encontrados.")
                
                # Autentica com credenciais do revendedor para buscar clientes
                admin_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
                admin_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                             headers=admin_headers, 
                                             json={
                                                 "username": reseller_data["netplay_username"],
                                                 "password": reseller_data["netplay_password"]
                                             })
                admin_response.raise_for_status()
                admin_token = admin_response.json().get("token") or admin_response.json().get("access_token")
                
                if not admin_token:
                    raise HTTPException(status_code=500, detail="Erro de autenticação com revendedor.")
                
                # Busca o cliente nas listas do revendedor
                headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
                params = {"username": request.username}
                response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
                response.raise_for_status()
                customers = response.json().get("data", [])
                
                # Verifica se o cliente existe na lista do revendedor
                client_found = None
                for customer in customers:
                    if customer.get("username") == request.username:
                        client_found = customer
                        break
                
                if not client_found:
                    raise HTTPException(status_code=403, detail="Cliente não encontrado na lista deste revendedor.")
                
                # Cliente encontrado na lista do revendedor - login apenas com username
                server_info = client_found.get("server", {})
                server_name = server_info.get("name") if isinstance(server_info, dict) else server_info
                server_id = server_info.get("id") if isinstance(server_info, dict) else None
                
                package_info = client_found.get("package", {})
                package_name = package_info.get("name") if isinstance(package_info, dict) else package_info
                
                return {
                    "success": True,
                    "client_info": {
                        "id": client_found.get("id"),
                        "username": client_found.get("username"),
                        "server_name": server_name,
                        "server_id": server_id,
                        "package_name": package_name
                    },
                    "system_token": request.token,
                    "reseller_id": request.reseller_id,
                    "auth_method": "username_only_reseller" if request.reseller_id else "username_only"
                }
            
            else:
                 # Login direto sem token - busca usando credenciais de admin
                 admin_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
                 admin_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                              headers=admin_headers, 
                                              json={
                                                  "username": NETPLAY_USERNAME,
                                                  "password": NETPLAY_PASSWORD
                                              })
                 admin_response.raise_for_status()
                 admin_token = admin_response.json().get("token") or admin_response.json().get("access_token")
                 
                 if not admin_token:
                     raise HTTPException(status_code=500, detail="Erro de autenticação com administrador.")
                 
                 # Busca o cliente usando credenciais de admin
                 headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
                 params = {"username": request.username}
                 response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
                 response.raise_for_status()
                 customers = response.json().get("data", [])
                 
                 # Verifica se o cliente existe
                 client_found = None
                 for customer in customers:
                     if customer.get("username") == request.username:
                         client_found = customer
                         break
                 
                 if not client_found:
                     raise HTTPException(status_code=404, detail="Cliente não encontrado.")
                 
                 # Cliente encontrado - login apenas com username
                 server_info = client_found.get("server", {})
                 server_name = server_info.get("name") if isinstance(server_info, dict) else server_info
                 server_id = server_info.get("id") if isinstance(server_info, dict) else None
                 
                 package_info = client_found.get("package", {})
                 package_name = package_info.get("name") if isinstance(package_info, dict) else package_info
                 
                 return {
                     "success": True,
                     "client_info": {
                         "id": client_found.get("id"),
                         "username": client_found.get("username"),
                         "server_name": server_name,
                         "server_id": server_id,
                         "package_name": package_name
                     },
                     "auth_method": "username_only_admin"
                 }
            
            # Se não conseguiu autenticar diretamente, tenta buscar nas credenciais salvas
            client_data = db.get_client_by_credentials(request.username, request.password)
            
            if not client_data:
                raise HTTPException(status_code=401, detail="Credenciais inválidas. Verifique seu usuário e senha da Netplay.")
            
            # Usa as credenciais do revendedor para buscar informações do cliente
            admin_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
            admin_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                         headers=admin_headers, 
                                         json={
                                             "username": client_data["reseller_netplay_username"],
                                             "password": client_data["reseller_netplay_password"]
                                         })
            admin_response.raise_for_status()
            admin_token = admin_response.json().get("token") or admin_response.json().get("access_token")
            
            if not admin_token:
                raise HTTPException(status_code=500, detail="Erro de autenticação com revendedor.")
            
            # Busca o cliente usando token do revendedor
            headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
            params = {"username": client_data["client_username"]}
            response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
            response.raise_for_status()
            customers = response.json().get("data", [])
            
            # Verifica se o cliente existe
            client_found = None
            for customer in customers:
                if customer.get("username") == client_data["client_username"]:
                    client_found = customer
                    break
            
            if not client_found:
                raise HTTPException(status_code=404, detail="Cliente não encontrado na Netplay.")
            
            # Extrai informações do servidor e pacote
            server_info = client_found.get("server", {})
            server_name = server_info.get("name") if isinstance(server_info, dict) else server_info
            server_id = server_info.get("id") if isinstance(server_info, dict) else None
            
            package_info = client_found.get("package", {})
            package_name = package_info.get("name") if isinstance(package_info, dict) else package_info
            
            return {
                "success": True,
                "client_info": {
                    "id": client_found.get("id"),
                    "username": client_found.get("username"),
                    "server_name": server_name,
                    "server_id": server_id,
                    "package_name": package_name
                },
                "token": client_data.get("link_token"),
                "auth_method": "saved_credentials"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Forneça token ou credenciais (username e password).")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na autenticação: {e}")

@app.post("/api/client/migrate")
async def client_migrate(request: ClientMigrateRequest, token: str = None, netplay_token: str = None, reseller_id: int = None):
    """Permite que um cliente migre seu próprio servidor"""
    global ALL_NETPLAY_PACKAGES
    
    admin_token = None
    client_username = None
    
    try:
        # Verifica se é um token direto da Netplay
        if netplay_token:
            # Usa o token direto da Netplay para migração
            admin_token = netplay_token
            
            # Busca informações do perfil do cliente
            headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
            profile_response = requests.get(f"{NETPLAY_API_BASE_URL}/profile", headers=headers)
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            client_username = profile_data.get("username")
            
        elif token or reseller_id:
            # Busca credenciais do revendedor (por token ou reseller_id)
            reseller_data = None
            
            if token:
                # Busca o cliente pelo token do sistema
                client_data = db.get_client_by_token(token)
                
                if not client_data:
                    raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
                
                client_username = client_data["client_username"]
                reseller_data = {
                    "netplay_username": client_data["reseller_netplay_username"],
                    "netplay_password": client_data["reseller_netplay_password"]
                }
            elif reseller_id:
                # Busca credenciais do revendedor pelo ID
                conn = sqlite3.connect("netplay.db")
                cursor = conn.cursor()
                cursor.execute("SELECT netplay_username, netplay_password FROM resellers WHERE id = ?", (reseller_id,))
                reseller_row = cursor.fetchone()
                conn.close()
                
                if not reseller_row:
                    raise HTTPException(status_code=404, detail="Revendedor não encontrado.")
                
                reseller_data = {
                    "netplay_username": reseller_row[0],
                    "netplay_password": reseller_row[1]
                }
                
                # Para reseller_id, usa o client_username do request
                if request.client_username:
                    client_username = request.client_username
                else:
                    raise HTTPException(status_code=400, detail="Username do cliente é obrigatório para migração via reseller_id.")
            
            # Usa as credenciais do revendedor para realizar a migração
            admin_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
            admin_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                         headers=admin_headers, 
                                         json={
                                             "username": reseller_data["netplay_username"],
                                             "password": reseller_data["netplay_password"]
                                         })
            admin_response.raise_for_status()
            admin_token = admin_response.json().get("token") or admin_response.json().get("access_token")
            
            if not admin_token:
                raise HTTPException(status_code=500, detail="Erro de autenticação com revendedor.")
        else:
            raise HTTPException(status_code=400, detail="Forneça token do sistema ou netplay_token.")
            
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="Erro de autenticação.")
    
    headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
    
    try:
        # Primeiro, busca o cliente para obter suas informações
        if netplay_token:
            # Para token direto da Netplay, busca o perfil
            response = requests.get(f"{NETPLAY_API_BASE_URL}/profile", headers=headers)
            response.raise_for_status()
            client_found = response.json()
        else:
            # Para token do sistema, busca na lista de clientes
            params = {"username": client_username}
            response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
            response.raise_for_status()
            customers = response.json().get("data", [])
            
            client_found = None
            for customer in customers:
                if customer.get("username") == client_username:
                    client_found = customer
                    break
            
            if not client_found:
                raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        
        # Busca o plano equivalente no servidor de destino
        package_info = client_found.get("package", {})
        current_package_name = package_info.get("name") if isinstance(package_info, dict) else package_info
        if not current_package_name:
            raise HTTPException(status_code=400, detail="Plano atual não identificado.")
        
        # Garante que os pacotes estejam carregados
        if not ALL_NETPLAY_PACKAGES:
            # Usa o token do cliente autenticado ou obtém um novo token usando as credenciais do revendedor
            token_to_use = None
            if "authorization" in headers:
                token_to_use = headers["authorization"].replace("Bearer ", "")
            elif reseller_id:
                # Obtém as credenciais do revendedor do banco de dados
                reseller_data = db.get_reseller_by_id(reseller_id)
                if reseller_data and reseller_data.get("netplay_username") and reseller_data.get("netplay_password"):
                    # Autentica usando as credenciais do revendedor
                    auth_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
                    auth_response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                                                headers=auth_headers, 
                                                json={"username": reseller_data["netplay_username"], 
                                                     "password": reseller_data["netplay_password"]})
                    auth_response.raise_for_status()
                    token_to_use = auth_response.json().get("token") or auth_response.json().get("access_token")
            
            if not token_to_use:
                raise HTTPException(status_code=401, detail="Token de autenticação não disponível para carregar pacotes.")
            
            headers_temp = {**NETPLAY_HEADERS, "authorization": f"Bearer {token_to_use}"}
            response = requests.get(f"{NETPLAY_API_BASE_URL}/servers", headers=headers_temp)
            response.raise_for_status()
            servers_data = response.json().get("data", [])
            
            packages_list = []
            seen_ids = set()
            for server in servers_data:
                for pkg in server.get("packages", []):
                    if pkg.get("id") not in seen_ids:
                        pkg_info = {"id": pkg.get("id"), "name": pkg.get("name"), "server_id": server.get("id")}
                        packages_list.append(pkg_info)
                        seen_ids.add(pkg.get("id"))
            ALL_NETPLAY_PACKAGES = packages_list
        
        new_package_id = None
        normalized_current_package_name = normalize_string(current_package_name)
        
        # Primeiro, tenta correspondência exata
        for pkg in ALL_NETPLAY_PACKAGES:
            if pkg.get("server_id") == request.server_id:
                normalized_pkg_name = normalize_string(pkg.get("name", ""))
                if normalized_pkg_name == normalized_current_package_name:
                    new_package_id = pkg.get("id")
                    break
        
        # Se não encontrou correspondência exata, tenta correspondência parcial
        if not new_package_id:
            # Busca por correspondência parcial baseada em características principais
            for pkg in ALL_NETPLAY_PACKAGES:
                if pkg.get("server_id") == request.server_id:
                    normalized_pkg_name = normalize_string(pkg.get("name", ""))
                    
                    # Verifica se contém 'semadulto' (característica principal)
                    if 'semadulto' in normalized_current_package_name and 'semadulto' in normalized_pkg_name:
                        new_package_id = pkg.get("id")
                        break
        
        if not new_package_id:
            raise HTTPException(status_code=400, detail=f"Plano '{current_package_name}' não encontrado no servidor de destino.")
        
        # Executa a migração
        payload = {"server_id": request.server_id, "package_id": new_package_id}
        headers["content-type"] = "application/json"
        
        url = f"{NETPLAY_API_BASE_URL}/customers/{client_found.get('id')}/server-migration"
        migration_response = requests.put(url, headers=headers, json=payload)
        migration_response.raise_for_status()
        
        # Se incluir MaxPlayer, migrar também
        maxplayer_result = None
        if request.include_maxplayer:
            print(f"🔄 [CLIENTE] Iniciando migração MaxPlayer para cliente '{client_username}'...")
            
            # Buscar credenciais MaxPlayer do revendedor
            maxplayer_creds = None
            if reseller_id:
                print(f"🔍 [CLIENTE] Buscando credenciais MaxPlayer do reseller_id={reseller_id}")
                maxplayer_creds = db.get_reseller_maxplayer_credentials(reseller_id)
                print(f"🔍 [CLIENTE] Credenciais encontradas: {maxplayer_creds}")
            
            # Buscar nome do servidor
            server_name = None
            if hasattr(request, 'server_name') and request.server_name:
                server_name = request.server_name
            else:
                for pkg in ALL_NETPLAY_PACKAGES:
                    if pkg.get("server_id") == request.server_id:
                        server_name = pkg.get("server_name", "")
                        break
            
            # Se não encontrou, tentar recarregar a lista de servidores
            if not server_name:
                print(f"⚠️  [CLIENTE] Servidor não encontrado inicialmente (ID: {request.server_id}). Recarregando lista...")
                try:
                    # Usar token disponível (admin_token já foi definido antes)
                    if not admin_token:
                         print(f"❌ [CLIENTE] Sem token administrativo para recarregar servidores")
                    else:
                        reload_headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
                        response = requests.get(f"{NETPLAY_API_BASE_URL}/servers", headers=reload_headers)
                        if response.ok:
                            data = response.json()
                            servers = data.get("data", [])
                            print(f"🔄 [CLIENTE] Lista recarregada com {len(servers)} servidores")
                            
                            # Atualizar globalmente e tentar buscar novamente
                            updated_packages = []
                            for s in servers:
                                s_id = s.get("id")
                                s_name = s.get("name")
                                # Verificar se é o servidor procurado
                                if str(s_id) == str(request.server_id):
                                    server_name = s_name
                                    print(f"✅ [CLIENTE] Servidor encontrado após recarregar: {server_name}")
                                
                                if s.get("plans"):
                                    for p in s.get("plans"):
                                        updated_packages.append({
                                            "id": p.get("id"),
                                            "name": p.get("name"),
                                            "server_id": s_id,
                                            "server_name": s_name
                                        })
                            
                            if updated_packages:
                                 ALL_NETPLAY_PACKAGES = updated_packages
                        else:
                            print(f"❌ [CLIENTE] Falha ao recarregar servidores: {response.status_code}")
                except Exception as e:
                    print(f"❌ [CLIENTE] Erro ao recarregar servidores: {e}")
            
            print(f"🔍 [CLIENTE] Nome do servidor encontrado: '{server_name}'")
            
            if server_name and maxplayer_creds:
                try:
                    async with httpx.AsyncClient() as mp_client:
                        # Login no MaxPlayer
                        print(f"✅ [CLIENTE] Usando credenciais MaxPlayer: {maxplayer_creds['email']}")
                        await login_maxplayer(mp_client, maxplayer_creds)
                        
                        # Migrar no MaxPlayer
                        print(f"🔄 [CLIENTE] Chamando migrate_customer_on_maxplayer...")
                        maxplayer_result = await migrate_customer_on_maxplayer(
                            client_username,
                            server_name,
                            mp_client
                        )
                        print(f"📊 [CLIENTE] Resultado MaxPlayer: {maxplayer_result}")
                except Exception as e:
                    print(f"❌ [CLIENTE] Erro EXCEPCIONAL na migração MaxPlayer: {e}")
                    import traceback
                    traceback.print_exc()
                    maxplayer_result = f"Erro técnico: {e}"
            elif not server_name:
                print(f"⚠️  [CLIENTE] Nome do servidor não encontrado para ID: {request.server_id}")
                maxplayer_result = "Nome do servidor não encontrado"
            elif not maxplayer_creds:
                print(f"⚠️  [CLIENTE] Revendedor não tem credenciais MaxPlayer configuradas")
                maxplayer_result = "Revendedor sem credenciais MaxPlayer"
        
        result = {"success": True, "message": "Migração realizada com sucesso!"}
        if maxplayer_result:
            result["maxplayer_status"] = maxplayer_result
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na migração: {e}")

@app.put("/api/batch_migrar")
async def batch_migrar_clientes(request: BatchMigrateRequest):
    if not AUTH_TOKEN: raise HTTPException(status_code=401, detail="Não autenticado na Netplay.")
    try:
        async with httpx.AsyncClient() as client:
            # Se incluir MaxPlayer, fazer login
            if request.include_maxplayer:
                print(f"🔄 Iniciando autenticação no MaxPlayer...")
                
                # Buscar credenciais MaxPlayer do usuário logado
                print(f"🔍 DEBUG: CURRENT_RESELLER = {CURRENT_RESELLER}")
                
                maxplayer_creds = None
                if CURRENT_RESELLER and CURRENT_RESELLER.get("id"):
                    print(f"🔍 DEBUG: Buscando credenciais MaxPlayer para reseller_id={CURRENT_RESELLER['id']}")
                    maxplayer_creds = db.get_reseller_maxplayer_credentials(CURRENT_RESELLER["id"])
                    print(f"🔍 DEBUG: Credenciais encontradas: {maxplayer_creds}")
                else:
                    print(f"⚠️  DEBUG: CURRENT_RESELLER não está definido ou não tem ID")
                
                if maxplayer_creds:
                    print(f"✅ Usando credenciais MaxPlayer do usuário: {maxplayer_creds['email']}")
                    await login_maxplayer(client, maxplayer_creds)
                else:
                    print(f"⚠️  Usuário não tem credenciais MaxPlayer salvas")
                    print(f"📧 Usando credenciais padrão: {MAXPLAYER_CREDENTIALS.get('email')}")
                    await login_maxplayer(client)
            
            tasks = [process_customer_migration(c, request, client) for c in request.customers]
            results = await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Processo de migração concluído.", "results": results}

# === ROTAS DO PAINEL ADMINISTRATIVO ===

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Página do painel administrativo"""
    with open("frontend/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/admin/login")
async def admin_login(request: AdminLoginRequest, req: Request):
    """Login do administrador"""
    try:
        if db.authenticate_admin(request.username, request.password):
            # Log da atividade
            db.log_activity(None, "ADMIN_LOGIN", "Administrador fez login", req.client.host)
            
            return {
                "success": True,
                "message": "Login administrativo realizado com sucesso",
                "is_admin": True
            }
        else:
            # Log da tentativa de login falhada
            db.log_activity(None, "ADMIN_LOGIN_FAILED", f"Tentativa de login admin falhada: {request.username}", req.client.host)
            raise HTTPException(status_code=401, detail="Credenciais administrativas inválidas")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no login administrativo: {e}")

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Obtém estatísticas gerais do sistema"""
    try:
        stats = db.get_admin_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {e}")

@app.get("/api/admin/resellers")
async def get_all_resellers():
    """Lista todos os revendedores para o painel admin (inclui netplay_user_id)"""
    try:
        basics = db.get_all_resellers()
        fulls = db.get_all_resellers_full()
        full_map = {r["id"]: r for r in fulls}
        merged = []
        for b in basics:
            f = full_map.get(b["id"], {})
            merged.append({
                "id": b["id"],
                "username": b["username"],
                "email": b.get("email"),
                "is_blocked": b.get("is_blocked"),
                "blocked_reason": b.get("blocked_reason"),
                "created_at": b.get("created_at"),
                "netplay_username": f.get("netplay_username"),
                "netplay_user_id": f.get("netplay_user_id")
            })
        return {"success": True, "resellers": merged}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter revendedores: {e}")

@app.get("/api/admin/netplay_user_ids")
async def get_netplay_user_ids():
    """Lista distintos user_ids observados no NetPlay (a partir de /customers)"""
    try:
        if NETPLAY_USERNAME == "seu_usuario_admin" or NETPLAY_PASSWORD == "sua_senha_admin":
            raise HTTPException(status_code=400, detail="Credenciais NetPlay não configuradas")
        # Autentica no NetPlay com credenciais administrativas
        auth_headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
        login_resp = requests.post(
            f"{NETPLAY_API_BASE_URL}/auth/login",
            headers=auth_headers,
            json={"username": NETPLAY_USERNAME, "password": NETPLAY_PASSWORD}
        )
        if login_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Falha ao autenticar no NetPlay: {login_resp.text}")
        token = login_resp.json().get("token") or login_resp.json().get("access_token")
        headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {token}"}
        
        user_ids = set()
        page = 1
        last_page = None
        max_pages = 10
        
        while True:
            customers_resp = requests.get(
                f"{NETPLAY_API_BASE_URL}/customers",
                headers=headers,
                params={"page": page}
            )
            if customers_resp.status_code != 200:
                break
            body = customers_resp.json()
            items = body.get("data") or body.get("clientes") or []
            for item in items:
                uid = item.get("user_id") or item.get("userId")
                if uid:
                    user_ids.add(uid)
            links = body.get("links") or {}
            if last_page is None and links.get("last"):
                try:
                    from urllib.parse import urlparse, parse_qs
                    q = parse_qs(urlparse(links["last"]).query)
                    last_page = int(q.get("page", [page])[0])
                except Exception:
                    last_page = None
            if last_page is not None:
                if page >= last_page:
                    break
            else:
                # Sem informação de última página: para evitar loops infinitos, limita a 10 páginas ou para quando não houver próximo
                if page >= max_pages or not links.get("next"):
                    break
            page += 1
        
        return {"success": True, "user_ids": sorted(list(user_ids))}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter user_ids do NetPlay: {e}")

@app.post("/api/admin/block")
async def block_resellers(request: BlockResellerRequest, req: Request):
    """Bloqueia um ou múltiplos revendedores"""
    try:
        if len(request.reseller_ids) == 1:
            success = db.block_reseller(request.reseller_ids[0], request.reason)
            if success:
                db.log_activity(None, "ADMIN_BLOCK", f"Admin bloqueou revendedor ID {request.reseller_ids[0]}: {request.reason}", req.client.host)
                return {"success": True, "message": "Revendedor bloqueado com sucesso"}
            else:
                return {"success": False, "message": "Erro ao bloquear revendedor"}
        else:
            blocked_count = db.block_multiple_resellers(request.reseller_ids, request.reason)
            db.log_activity(None, "ADMIN_BLOCK_MULTIPLE", f"Admin bloqueou {blocked_count} revendedores: {request.reason}", req.client.host)
            return {
                "success": True, 
                "message": f"{blocked_count} revendedores bloqueados com sucesso",
                "blocked_count": blocked_count
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao bloquear revendedores: {e}")

@app.post("/api/admin/unblock")
async def unblock_reseller(request: UnblockResellerRequest, req: Request):
    """Desbloqueia um revendedor"""
    try:
        success = db.unblock_reseller(request.reseller_id)
        if success:
            db.log_activity(None, "ADMIN_UNBLOCK", f"Admin desbloqueou revendedor ID {request.reseller_id}", req.client.host)
            return {"success": True, "message": "Revendedor desbloqueado com sucesso"}
        else:
            return {"success": False, "message": "Erro ao desbloquear revendedor"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desbloquear revendedor: {e}")

@app.get("/api/admin/logs")
async def get_activity_logs(limit: int = 100):
    """Obtém logs de atividade recentes"""
    try:
        logs = db.get_activity_logs(limit)
        return {"success": True, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs: {e}")

@app.get("/api/admin/reseller/{reseller_id}/customers")
async def get_reseller_customers_admin(reseller_id: int):
    """Obtém clientes de um revendedor específico (admin)"""
    try:
        # Buscar revendedor
        resellers = db.get_all_resellers()
        reseller = next((r for r in resellers if r["id"] == reseller_id), None)
        
        if not reseller:
            raise HTTPException(status_code=404, detail="Revendedor não encontrado")
        
        # Buscar clientes na API da Netplay usando credenciais do revendedor
        headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
        
        # Buscar credenciais completas do revendedor
        reseller_full = db.authenticate_reseller(reseller["username"], "temp")
        if not reseller_full:
            # Buscar diretamente do banco
            conn = sqlite3.connect("netplay.db")
            cursor = conn.cursor()
            cursor.execute("SELECT netplay_password FROM resellers WHERE id = ?", (reseller_id,))
            result = cursor.fetchone()
            conn.close()
            netplay_password = result[0] if result else None
        else:
            netplay_password = reseller_full.get("netplay_password")
        
        if not netplay_password:
            return {"success": False, "message": "Credenciais do revendedor não encontradas"}
        
        # Fazer login na Netplay com credenciais do revendedor
        login_response = requests.post(
            f"{NETPLAY_API_BASE_URL}/auth/login", 
            headers=headers, 
            json={
                "username": reseller["netplay_username"], 
                "password": netplay_password
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            if token:
                # Buscar clientes
                customers_headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {token}"}
                customers_response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=customers_headers)
                
                if customers_response.status_code == 200:
                    customers = customers_response.json().get("data", [])
                    
                    # Atualizar cache no banco
                    db.update_reseller_customers(reseller_id, customers)
                    
                    return {"success": True, "customers": customers, "total": len(customers)}
        
        return {"success": False, "message": "Erro ao obter clientes do revendedor"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter clientes: {e}")

# --- Funções Auxiliares ---
def handle_netplay_api_error(e):
    """Padroniza o tratamento de erros da API da Netplay"""
    if isinstance(e, requests.exceptions.HTTPError):
        if e.response.status_code == 422:
            raise HTTPException(status_code=401, detail="Credenciais inválidas na Netplay.")
        else:
            raise HTTPException(status_code=500, detail=f"Erro na API da Netplay: {e.response.status_code}")
    elif isinstance(e, requests.exceptions.ConnectionError):
        raise HTTPException(status_code=500, detail="Erro de conexão com a API da Netplay. Verifique sua conexão com a internet.")
    elif isinstance(e, requests.exceptions.RequestException):
        raise HTTPException(status_code=500, detail="Erro de conexão com a Netplay.")
    else:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

async def process_customer_migration(customer: CustomerInfo, request: BatchMigrateRequest, client: httpx.AsyncClient):
    result = {
        "username": customer.username,
        "migration_status": "Pendente",
        "maxplayer_status": "Não solicitado"  # Status padrão
    }
    headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {AUTH_TOKEN}", "content-type": "application/json"}
    
    try:
        new_package_id = None
        normalized_current_package_name = normalize_string(customer.package_name)

        for pkg in ALL_NETPLAY_PACKAGES:
            if pkg.get("server_id") == request.server_id:
                normalized_pkg_name = normalize_string(pkg.get("name", ""))
                if normalized_pkg_name == normalized_current_package_name:
                    new_package_id = pkg.get("id")
                    break
        
        if not new_package_id:
            raise Exception(f"Plano '{customer.package_name}' não encontrado no servidor de destino.")

        payload = {"server_id": request.server_id, "package_id": new_package_id}
        
        url = f"{NETPLAY_API_BASE_URL}/customers/{customer.id}/server-migration"
        resp_netplay = await client.put(url, headers=headers, json=payload, timeout=30.0)
        resp_netplay.raise_for_status()
        result["migration_status"] = "Migrado com sucesso"
        
        # Se incluir MaxPlayer, migrar também
        if request.include_maxplayer:
            print(f"🔄 Migrando '{customer.username}' no MaxPlayer...")
            result["maxplayer_status"] = await migrate_customer_on_maxplayer(
                customer.username,
                request.server_name,
                client
            )
        
    except httpx.HTTPStatusError as e:
        error = e.response.json().get("message", e.response.text)
        result["migration_status"] = f"Falha: {error}"
        if request.include_maxplayer:
            result["maxplayer_status"] = "Não executado"
    except Exception as e:
        result["migration_status"] = f"Erro: {e}"
        if request.include_maxplayer:
            result["maxplayer_status"] = "Não executado"
    return result

# Endpoint público para status dos servidores
@app.get("/api/servers/status")
async def public_server_status():
    """Retorna lista de servidores para o frontend verificar status"""
    # Lista fixa de servidores para monitoramento
    servers = [
        {"id": "1750385133185114283", "name": "NETPLAY SOLAR", "url": "http://solar.netplay.tv"},
        {"id": "1750385543431130630", "name": "NETPLAY ANDRÔMEDA", "url": "http://andromeda.netplay.tv"},
        {"id": "1750384873990823788", "name": "NETPLAY SPEED", "url": "http://speed.netplay.tv"},
        {"id": "1753657859890202256", "name": "NETPLAY LUNAR", "url": "http://lunar.netplay.tv"},
        {"id": "1756345548755066123", "name": "NETPLAY FLASH", "url": "http://flash.netplay.tv"},
        {"id": "1750385433321950245", "name": "NETPLAY VÊNUS", "url": "http://venus.netplay.tv"},
        {"id": "1750385235476264855", "name": "NETPLAY ATENA", "url": "http://atena.netplay.tv"},
        {"id": "1750385578271894993", "name": "NETPLAY TITÃ", "url": "http://tita.netplay.tv"},
        {"id": "1750385472254248136", "name": "NETPLAY HADES", "url": "http://hades.netplay.tv"},
        {"id": "1755362642846269320", "name": "EXPLOSION", "url": "http://explosion.netplay.tv"},
        {"id": "1750385204630190352", "name": "NETPLAY SKY", "url": "http://sky.netplay.tv"},
        {"id": "1756378841114454295", "name": "NETPLAY FIRE", "url": "http://fire.netplay.tv"},
        {"id": "1750385171559926175", "name": "NETPLAY GALAXY", "url": "http://galaxy.netplay.tv"},
        {"id": "1750384954579088880", "name": "NETPLAY SEVEN", "url": "http://seven.netplay.tv"},
        {"id": "1750385502428005340", "name": "NETPLAY URANO", "url": "http://urano.netplay.tv"},
        {"id": "1764111505708068572", "name": "ALPSYNC", "url": "http://alpsync.netplay.tv"},
        {"id": "1764334750403735279", "name": "StarPlay4", "url": "http://starplay4.netplay.tv"},
        {"id": "1762974282561465612", "name": "StarPlay1", "url": "http://starplay1.netplay.tv"},
        {"id": "1762974308988184556", "name": "StarPlay2", "url": "http://starplay2.netplay.tv"},
        {"id": "1762974556593364213", "name": "StarPlay3", "url": "http://starplay3.netplay.tv"},
        {"id": "1765801295763130892", "name": "PURPLE", "url": "http://purple.netplay.tv"}
    ]
    
    # Retorna apenas a lista, frontend fará o ping
    return {"servers": servers, "client_side_check": True}

if __name__ == "__main__":
    import uvicorn
    
    # Configurações do servidor
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Configurações para produção
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,
            access_log=True,
            log_level="info"
        )
    else:
        # Configurações para desenvolvimento
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            access_log=True,
            log_level="debug" if debug else "info"
        )