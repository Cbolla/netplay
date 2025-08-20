from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import requests
import asyncio
import httpx
import unicodedata
import re
import sqlite3
from database import db

app = FastAPI()



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"!!! ERRO DE VALIDAÇÃO 422: {exc.errors()} !!!")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- Variáveis de Configuração e Cabeçalhos ---
NETPLAY_API_BASE_URL = "https://netplay.sigma.vin/api"
AUTH_TOKEN = None
CURRENT_RESELLER = None
ALL_NETPLAY_PACKAGES = []
NETPLAY_HEADERS = {"accept": "application/json", "user-agent": "Mozilla/5.0", "origin": "https://netplay.sigma.vin", "referer": "https://netplay.sigma.vin/"}

# Credenciais administrativas (configure com suas credenciais reais)
# Você pode configurar através de variáveis de ambiente ou diretamente aqui
import os
from dotenv import load_dotenv

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
class BatchMigrateRequest(BaseModel): customers: list[CustomerInfo]; server_id: str; server_name: str
class ClientLoginRequest(BaseModel): username: str; password: str
class ClientMigrateRequest(BaseModel): server_id: str; password: str
class CreateClientLinkRequest(BaseModel): client_username: str; client_password: str
class ClientTokenLoginRequest(BaseModel): token: str

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

# --- Rotas do Backend ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/client", response_class=HTMLResponse)
async def client_page():
    """Página para clientes individuais"""
    with open("frontend/client.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/login")
async def login(request: LoginRequest):
    global AUTH_TOKEN, CURRENT_RESELLER
    
    # Primeiro, autentica na Netplay para verificar se as credenciais são válidas
    headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
    try:
        response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", headers=headers, json=request.dict())
        response.raise_for_status()
        token = response.json().get("token") or response.json().get("access_token")
        if not token: raise HTTPException(status_code=401, detail="Token não encontrado.")
        AUTH_TOKEN = token
        
        # Verifica se o revendedor já existe no banco local
        reseller = db.authenticate_reseller(request.username, request.password)
        
        if not reseller:
            # Se não existe, cria o revendedor no banco local
            success = db.create_reseller(
                username=request.username,
                password=request.password,
                netplay_username=request.username,
                netplay_password=request.password
            )
            if not success:
                raise HTTPException(status_code=500, detail="Erro ao criar revendedor no sistema.")
            
            # Busca novamente após criar
        reseller = db.authenticate_reseller(request.username, request.password)
        
        # Armazena o revendedor autenticado
        CURRENT_RESELLER = reseller
        
        return {
            "token": token,
            "reseller_id": reseller["id"],
            "username": reseller["username"]
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=401, detail="Credenciais inválidas na Netplay.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no login: {e}")

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
                                     json={"username": NETPLAY_USERNAME, "password": NETPLAY_PASSWORD})
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
        if isinstance(servers_data, dict) and "servers" in servers_data:
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
    except requests.exceptions.ConnectionError as e:
        raise HTTPException(status_code=500, detail="Erro de conexão com a API da Netplay. Verifique sua conexão com a internet.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Erro ao carregar servidores. Verifique suas credenciais da Netplay.")
    except Exception as e:
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
async def create_client_link(request: CreateClientLinkRequest):
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
        
        # Gera a URL completa do link
        link_url = f"http://localhost:8000/client?token={link_token}"
        
        return {
            "success": True,
            "link_token": link_token,
            "link_url": link_url,
            "client_username": request.client_username
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar link: {e}")

@app.get("/api/reseller_clients")
async def get_reseller_clients(reseller_id: int):
    """Lista todos os clientes de um revendedor"""
    try:
        clients = db.get_reseller_clients(reseller_id)
        
        # Adiciona a URL completa para cada cliente
        for client in clients:
            client["link_url"] = f"http://localhost:8000/client?token={client['link_token']}"
        
        return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar clientes: {e}")

@app.get("/api/generated_links")
async def get_generated_links():
    """Lista todos os links gerados pelo revendedor atual"""
    try:
        # Verifica se há um revendedor autenticado
        if not CURRENT_RESELLER:
            raise HTTPException(status_code=401, detail="Nenhum revendedor autenticado. Faça login primeiro.")
        
        reseller_id = CURRENT_RESELLER["id"]
        
        conn = sqlite3.connect("netplay.db")
        cursor = conn.cursor()
        
        # Buscar todos os links gerados por este revendedor
        cursor.execute("""
            SELECT id, client_username, link_token, created_at, last_access, is_active
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
                "link_url": f"http://localhost:8000/client?token={row[2]}",
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

@app.get("/api/search_customer")
async def search_customer(account_number: str = None, server_id: str = None):
    if not AUTH_TOKEN: raise HTTPException(status_code=401, detail="Não autenticado.")
    headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {AUTH_TOKEN}"}
    params = {}
    if account_number: params["username"] = account_number
    if server_id: params["serverId"] = server_id
    if not account_number and not server_id:
        raise HTTPException(status_code=400, detail="Forneça um número de conta ou servidor.")
    try:
        response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
        response.raise_for_status()
        return {"clientes": response.json().get("data", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao pesquisar cliente: {e}")

@app.post("/api/client/login")
async def client_login(request: ClientTokenLoginRequest):
    """Autentica um cliente usando token do link gerado pelo revendedor"""
    try:
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
        
        # Extrai informações do servidor de forma segura
        server_info = client_found.get("server", {})
        server_name = server_info.get("name") if isinstance(server_info, dict) else server_info
        server_id = server_info.get("id") if isinstance(server_info, dict) else None
        
        # Extrai informações do pacote de forma segura
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
            "token": request.token  # Retorna o token para uso nas próximas requisições
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na autenticação: {e}")

@app.post("/api/client/migrate")
async def client_migrate(request: ClientMigrateRequest, token: str):
    """Permite que um cliente migre seu próprio servidor usando credenciais do revendedor"""
    try:
        # Busca o cliente pelo token
        client_data = db.get_client_by_token(token)
        
        if not client_data:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
        
        # Usa as credenciais do revendedor para realizar a migração
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
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="Erro de autenticação com revendedor.")
    
    headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
    
    try:
        # Primeiro, busca o cliente para obter suas informações
        params = {"username": username}
        response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers, params=params)
        response.raise_for_status()
        customers = response.json().get("data", [])
        
        client_found = None
        for customer in customers:
            if customer.get("username") == username:
                client_found = customer
                break
        
        if not client_found:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        
        # Busca o plano equivalente no servidor de destino
        package_info = client_found.get("package", {})
        current_package_name = package_info.get("name") if isinstance(package_info, dict) else package_info
        if not current_package_name:
            raise HTTPException(status_code=400, detail="Plano atual não identificado.")
        
        new_package_id = None
        normalized_current_package_name = normalize_string(current_package_name)
        
        for pkg in ALL_NETPLAY_PACKAGES:
            if pkg.get("server_id") == request.server_id:
                normalized_pkg_name = normalize_string(pkg.get("name", ""))
                if normalized_pkg_name == normalized_current_package_name:
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
        
        return {"success": True, "message": "Migração realizada com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na migração: {e}")

@app.put("/api/batch_migrar")
async def batch_migrar_clientes(request: BatchMigrateRequest):
    if not AUTH_TOKEN: raise HTTPException(status_code=401, detail="Não autenticado na Netplay.")
    try:
        async with httpx.AsyncClient() as client:
            tasks = [process_customer_migration(c, request, client) for c in request.customers]
            results = await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Processo de migração concluído.", "results": results}

# --- Funções Auxiliares ---
async def process_customer_migration(customer: CustomerInfo, request: BatchMigrateRequest, client: httpx.AsyncClient):
    result = {"username": customer.username, "migration_status": "Pendente"}
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
    except httpx.HTTPStatusError as e:
        error = e.response.json().get("message", e.response.text)
        result["migration_status"] = f"Falha: {error}"
    except Exception as e:
        result["migration_status"] = f"Erro: {e}"
    return result