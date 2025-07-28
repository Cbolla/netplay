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

app = FastAPI()

# Mapa de Servidores
SERVER_MAP = {
    "☀️ NETPLAY SOLAR ☀️": "1750385133185114283", "☄️ NETPLAY ANDRÔMEDA ☄️": "1750385543431130630",
    "⚡ NETPLAY SPEED ⚡": "1750384873990823788", "🌑 NETPLAY LUNAR 🌑": "1753657859890202256",
    "🌬️ NETPLAY VÊNUS 🌬️": "1750385433321950245", "🏛️ NETPLAY ATENA 🏛️": "1750385235476264855",
    "👺 NETPLAY TITÃ 👺": "1750385578271894993", "💎 NETPLAY HADES 💎": "1750385472254248136",
    "📡 NETPLAY SKY 📡": "1750385204630190352", "🛸 NETPLAY GALAXY 🛸": "1750385171559926175",
    "🧿 NETPLAY SEVEN 🧿": "1750384954579088880", "🪐 NETPLAY URANO 🪐": "1750385502428005340"
}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"!!! ERRO DE VALIDAÇÃO 422: {exc.errors()} !!!")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- Variáveis de Configuração e Cabeçalhos ---
NETPLAY_API_BASE_URL = "https://netplay.sigma.vin/api"
MAXPLAYER_API_BASE_URL = "https://api.maxplayer.tv/v3/api/panel"
AUTH_TOKEN = None
MAXPLAYER_AUTH_TOKEN = None
ALL_NETPLAY_PACKAGES = []
MAXPLAYER_CREDENTIALS = {"email": "futuro.noob@icloud.com", "password": "William2025@"}
NETPLAY_HEADERS = {"accept": "application/json", "user-agent": "Mozilla/5.0", "origin": "https://netplay.sigma.vin", "referer": "https://netplay.sigma.vin/"}
MAXPLAYER_HEADERS = {"accept": "application/json, text/plain, */*", "user-agent": "Mozilla/5.0", "origin": "https://my.maxplayer.tv", "referer": "https://my.maxplayer.tv/"}

# --- Modelos Pydantic ---
class LoginRequest(BaseModel): username: str; password: str
class CustomerInfo(BaseModel): id: str; username: str; package_name: str
class BatchMigrateRequest(BaseModel): customers: list[CustomerInfo]; server_id: str; server_name: str

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

@app.post("/api/login")
async def login(request: LoginRequest):
    global AUTH_TOKEN
    headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
    try:
        response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", headers=headers, json=request.dict())
        response.raise_for_status()
        token = response.json().get("token") or response.json().get("access_token")
        if not token: raise HTTPException(status_code=401, detail="Token não encontrado.")
        AUTH_TOKEN = token
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no login da Netplay: {e}")

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

@app.put("/api/batch_migrar")
async def batch_migrar_clientes(request: BatchMigrateRequest):
    if not AUTH_TOKEN: raise HTTPException(status_code=401, detail="Não autenticado na Netplay.")
    try:
        async with httpx.AsyncClient() as client:
            await login_maxplayer(client)
            tasks = [process_customer_migration(c, request, client) for c in request.customers]
            results = await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Processo de migração concluído.", "results": results}

# --- Funções Auxiliares (ATUALIZADO) ---
async def process_customer_migration(customer: CustomerInfo, request: BatchMigrateRequest, client: httpx.AsyncClient):
    result = {"username": customer.username, "migration_status": "Pendente", "maxplayer_status": "Pendente"}
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
        result["maxplayer_status"] = await migrate_customer_on_maxplayer(customer.username, request.server_name, client)
    except httpx.HTTPStatusError as e:
        error = e.response.json().get("message", e.response.text)
        result["migration_status"] = f"Falha: {error}"
        result["maxplayer_status"] = "Não executado"
    except Exception as e:
        result["migration_status"] = f"Erro: {e}"
        result["maxplayer_status"] = "Não executado"
    return result

async def login_maxplayer(client: httpx.AsyncClient):
    global MAXPLAYER_AUTH_TOKEN
    if MAXPLAYER_AUTH_TOKEN: return
    headers = {**MAXPLAYER_HEADERS, "content-type": "application/json"}
    try:
        resp = await client.post(f"{MAXPLAYER_API_BASE_URL}/login", headers=headers, json=MAXPLAYER_CREDENTIALS)
        resp.raise_for_status()
        token = resp.json().get("token")
        if not token: raise Exception("Token da Maxplayer não encontrado.")
        MAXPLAYER_AUTH_TOKEN = token
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível autenticar na Maxplayer: {e}")

async def migrate_customer_on_maxplayer(username: str, server_name: str, client: httpx.AsyncClient):
    if not MAXPLAYER_AUTH_TOKEN: raise Exception("Autenticação da Maxplayer perdida.")
    headers = {**MAXPLAYER_HEADERS, "Authorization": f"Bearer {MAXPLAYER_AUTH_TOKEN}"}
    try:
        params = {"search": username, "limit": 1, "agent": "false"}
        resp_search = await client.get(f"{MAXPLAYER_API_BASE_URL}/view/reseller/search-users", headers=headers, params=params)
        resp_search.raise_for_status()
        users = resp_search.json().get("users", [])
        if not users: return "Não encontrado"
        
        customer_id = users[0].get("id")
        resp_details = await client.get(f"{MAXPLAYER_API_BASE_URL}/view/reseller/user/{customer_id}", headers=headers)
        resp_details.raise_for_status()
        lists = resp_details.json().get("lists", [])
        if not lists: return "Erro: Nenhuma lista para editar."
        
        list_info = lists[0]
        iptv_info = list_info.get("iptv_info", {})
        new_domain_id = SERVER_MAP.get(server_name)
        if not new_domain_id: return f"Erro: Servidor '{server_name}' não mapeado."
        
        payload = {
            "list_id": list_info.get("id"), "domain_id": new_domain_id,
            "new_list_name": list_info.get("name"), "iptv_username": iptv_info.get("username"),
            "iptv_password": iptv_info.get("password"),
        }
        if not all(payload.values()): return "Erro: Dados da lista incompletos."
        
        resp_edit = await client.post(f"{MAXPLAYER_API_BASE_URL}/actions/reseller/edit-list", headers=headers, json=payload)
        resp_edit.raise_for_status()
        return "Migrado com sucesso" if resp_edit.json().get("success") else "Falha na API"
    except Exception as e:
        print(f"Erro ao migrar '{username}' na Maxplayer: {e}")
        return "Erro na migração"