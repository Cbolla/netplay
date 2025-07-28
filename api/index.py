import os
import asyncio
import httpx
import requests
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Adicione esta importação para o CORS
from fastapi.middleware.cors import CORSMiddleware

# Carrega as variáveis de ambiente do .env
load_dotenv()

# --- Configurações da API Netplay (não mude, elas virão das suas variáveis de ambiente) ---
NETPLAY_API_BASE_URL = os.getenv("NETPLAY_API_BASE_URL", "https://api.netplay.sigma.vin")
NETPLAY_HEADERS = {
    "User-Agent": os.getenv("NETPLAY_USER_AGENT", "seu_user_agent_aqui"),
    "Accept": "application/json",
    "x-api-key": os.getenv("NETPLAY_API_KEY", "sua_api_key_aqui"),
    "x-api-secret": os.getenv("NETPLAY_API_SECRET", "seu_api_secret_aqui")
}

MAXPLAYER_API_BASE_URL = os.getenv("MAXPLAYER_API_BASE_URL", "https://api.maxplayer.tv")
MAXPLAYER_AUTH_HEADER = os.getenv("MAXPLAYER_AUTH_HEADER", "seu_auth_header_maxplayer_aqui")
MAXPLAYER_HEADERS = {
    "Authorization": MAXPLAYER_AUTH_HEADER,
    "Content-Type": "application/json"
}

app = FastAPI()

# Adicione este bloco de código para o CORS
# Ele permite que seu frontend, mesmo em um domínio Vercel,
# converse com sua API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens, pode restringir depois
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Variáveis Globais (ATENÇÃO: Requerem refatoração futura para serverless) ---
# Conforme discutimos, variáveis globais como AUTH_TOKEN não são ideais para
# serverless functions por causa do estado efêmero. No entanto, para fins
# de depuração e para manter a compatibilidade imediata com seu código,
# vamos manter por enquanto, mas lembre-se da discussão sobre passá-lo
# pelo frontend.
AUTH_TOKEN = None

# --- Modelos Pydantic para Validação de Dados ---
class LoginRequest(BaseModel):
    username: str
    password: str

class MigrationCustomer(BaseModel):
    id: str
    username: str
    package_name: str

class BatchMigrateRequest(BaseModel):
    customers: list[MigrationCustomer]
    server_id: str
    server_name: str

# --- Rotas da API ---

@app.post("/api/login")
async def login(request: LoginRequest):
    global AUTH_TOKEN
    headers = {**NETPLAY_HEADERS, "content-type": "application/json"}
    try:
        response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", headers=headers, json=request.dict())
        response.raise_for_status()
        token = response.json().get("token") or response.json().get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Token não encontrado na resposta da API.")

        AUTH_TOKEN = token
        return {"token": token}

    except Exception as e:
        # !!! ESTA É A PARTE NOVA E IMPORTANTE !!!
        # Se qualquer coisa na função falhar, este código será executado.
        print(f"!!!!!!!! ERRO CRÍTICO DENTRO DA FUNÇÃO DE LOGIN !!!!!!!!")
        print(f"Tipo de Erro: {type(e)}")
        print(f"Argumentos do Erro: {e.args}")
        print(f"Detalhes: {e}") # Adicionado para mais detalhes
        print(f"----------------------------------------------------")

        # Levanta o erro 500 para que o frontend saiba que falhou.
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor ao tentar logar: {e}")

@app.get("/api/servidores_e_planos")
async def get_servers_and_plans():
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")

    headers = {**NETPLAY_HEADERS, "Authorization": f"Bearer {AUTH_TOKEN}"}
    try:
        # Pega servidores
        servers_response = requests.get(f"{NETPLAY_API_BASE_URL}/admin/servers", headers=headers)
        servers_response.raise_for_status()
        servers_data = servers_response.json().get("data", [])

        # Pega planos
        plans_response = requests.get(f"{NETPLAY_API_BASE_URL}/admin/packages", headers=headers)
        plans_response.raise_for_status()
        plans_data = plans_response.json().get("data", [])

        # Processa os dados para o formato que você precisa
        processed_servers = [{"id": server["id"], "name": server["name"]} for server in servers_data if server.get("status") == "active"]
        processed_plans = [{"id": plan["id"], "name": plan["name"]} for plan in plans_data if plan.get("status") == "active"]

        return {"servers": processed_servers, "plans": processed_plans}
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar servidores/planos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao comunicar com a API Netplay: {e}")
    except Exception as e:
        print(f"Erro inesperado ao processar servidores/planos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao carregar dados: {e}")

@app.get("/api/search_customer")
async def search_customer(account_number: str = None, server_id: str = None):
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")

    headers = {**NETPLAY_HEADERS, "Authorization": f"Bearer {AUTH_TOKEN}"}
    params = {}
    if account_number:
        params["search"] = account_number
    if server_id:
        params["server_id"] = server_id

    try:
        response = requests.get(f"{NETPLAY_API_BASE_URL}/admin/clients", headers=headers, params=params)
        response.raise_for_status()
        clients_data = response.json().get("data", [])

        # Adapta o formato para o frontend
        processed_clients = []
        for client in clients_data:
            processed_clients.append({
                "id": client.get("id"),
                "username": client.get("username"),
                "name": client.get("name"),
                "server": client.get("server_name"), # Presumindo que a API retorna 'server_name'
                "package": client.get("package_name") # Presumindo que a API retorna 'package_name'
            })
        return {"clientes": processed_clients}
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar clientes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao comunicar com a API Netplay: {e}")
    except Exception as e:
        print(f"Erro inesperado ao processar busca de clientes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar clientes: {e}")

async def migrate_customer_netplay(client_id: str, new_server_id: str, auth_token: str):
    url = f"{NETPLAY_API_BASE_URL}/admin/clients/{client_id}/migrate"
    headers = {**NETPLAY_HEADERS, "Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    payload = {"server_id": new_server_id}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0) # Aumentar timeout
            response.raise_for_status()
            return {"status": "sucesso", "message": response.json().get("message", "Migrado com sucesso na Netplay.")}
    except httpx.HTTPStatusError as e:
        print(f"Erro HTTP na migração Netplay para {client_id}: {e.response.status_code} - {e.response.text}")
        return {"status": "falha", "message": f"Netplay: Erro HTTP {e.response.status_code} - {e.response.text}"}
    except httpx.RequestError as e:
        print(f"Erro de requisição na migração Netplay para {client_id}: {e}")
        return {"status": "falha", "message": f"Netplay: Erro de conexão - {e}"}
    except Exception as e:
        print(f"Erro inesperado na migração Netplay para {client_id}: {e}")
        return {"status": "falha", "message": f"Netplay: Erro inesperado - {e}"}

async def migrate_customer_maxplayer(username: str, package_name: str, new_server_name: str):
    # Lógica simplificada para Maxplayer, ajuste conforme a API real
    url = f"{MAXPLAYER_API_BASE_URL}/api/migrate" # Exemplo, ajuste o endpoint real
    headers = {**MAXPLAYER_HEADERS}
    payload = {
        "username": username,
        "package_name": package_name,
        "new_server_name": new_server_name
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            # Maxplayer pode retornar algo diferente, ajuste a leitura
            return {"status": "sucesso", "message": response.json().get("message", "Migrado com sucesso no Maxplayer.")}
    except httpx.HTTPStatusError as e:
        print(f"Erro HTTP na migração Maxplayer para {username}: {e.response.status_code} - {e.response.text}")
        return {"status": "falha", "message": f"Maxplayer: Erro HTTP {e.response.status_code} - {e.response.text}"}
    except httpx.RequestError as e:
        print(f"Erro de requisição na migração Maxplayer para {username}: {e}")
        return {"status": "falha", "message": f"Maxplayer: Erro de conexão - {e}"}
    except Exception as e:
        print(f"Erro inesperado na migração Maxplayer para {username}: {e}")
        return {"status": "falha", "message": f"Maxplayer: Erro inesperado - {e}"}


@app.put("/api/batch_migrar")
async def batch_migrate(request: BatchMigrateRequest):
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")

    results = []
    tasks = []

    for customer in request.customers:
        # Tarefa para Netplay
        tasks.append(
            asyncio.create_task(
                migrate_customer_netplay(customer.id, request.server_id, AUTH_TOKEN)
            )
        )
        # Tarefa para Maxplayer
        tasks.append(
            asyncio.create_task(
                migrate_customer_maxplayer(customer.username, customer.package_name, request.server_name)
            )
        )

    # Executa todas as migrações em paralelo
    responses = await asyncio.gather(*tasks, return_exceptions=True) # return_exceptions=True para não parar se uma falhar

    # Processa os resultados
    for i in range(0, len(responses), 2):
        netplay_result = responses[i]
        maxplayer_result = responses[i+1]
        customer = request.customers[i//2] # Pega o cliente correspondente

        netplay_status = netplay_result.get("message", "Erro desconhecido Netplay") if isinstance(netplay_result, dict) else str(netplay_result)
        maxplayer_status = maxplayer_result.get("message", "Erro desconhecido Maxplayer") if isinstance(maxplayer_result, dict) else str(maxplayer_result)

        results.append({
            "username": customer.username,
            "migration_status": netplay_status,
            "maxplayer_status": maxplayer_status
        })

    return {"message": "Processamento de migrações concluído.", "results": results}