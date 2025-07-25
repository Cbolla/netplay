from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# load_dotenv() # Manter se tiver outras variáveis de ambiente necessárias

app = FastAPI()

# --- Configuração de Pastas Estáticas ---
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- Variáveis de Configuração da API Externa Netplay ---
NETPLAY_API_BASE_URL = "https://netplay.sigma.vin/api"
NETPLAY_LOGIN_URL = f"{NETPLAY_API_BASE_URL}/auth/login"
NETPLAY_CUSTOMER_SEARCH_URL = f"{NETPLAY_API_BASE_URL}/customers"
NETPLAY_SERVERS_URL = f"{NETPLAY_API_BASE_URL}/servers" # Nova variável para clareza

# Armazena o token de autenticação
AUTH_TOKEN = None

# --- Cabeçalhos Comuns para Requisições à API Externa ---
COMMON_HEADERS = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "origin": "https://netplay.sigma.vin",
    "referer": "https://netplay.sigma.vin/",
}

# --- Modelos Pydantic para validação de requisições ---
class LoginRequest(BaseModel):
    username: str
    password: str

class MigrateRequest(BaseModel):
    customer_id: str
    server_id: str = None
    package_id: str = None

# --- Rotas do Backend ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve o arquivo HTML principal do frontend."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/login")
async def login(request: LoginRequest):
    """Realiza o login na API netplay.sigma.vin e obtém o token."""
    global AUTH_TOKEN

    headers = {
        **COMMON_HEADERS,
        "content-type": "application/json",
    }

    payload = {
        "username": request.username,
        "password": request.password
    }

    try:
        response = requests.post(NETPLAY_LOGIN_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        token = data.get("token") or data.get("access_token") or data.get("data", {}).get("token")
        
        if token:
            AUTH_TOKEN = token
            return {"message": "Login bem-sucedido!", "token": token}
        else:
            raise HTTPException(status_code=401, detail="Token de autenticação não encontrado na resposta da API externa.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição para API de login: {e}")
        error_message = f"Erro ao conectar com a API de login: {e}."
        if response is not None and response.content:
            try:
                error_data = response.json()
                error_message = error_data.get("message", error_message)
            except ValueError:
                error_message = response.text
        raise HTTPException(status_code=response.status_code if response is not None and response.status_code >= 400 else 500, detail=error_message)
    except Exception as e:
        print(f"Erro inesperado no login: {e}")
        raise HTTPException(status_code=401, detail=f"Credenciais inválidas ou erro inesperado: {e}")

@app.get("/api/search_customer")
async def search_customer(account_number: str):
    """Pesquisa um cliente na API netplay.sigma.vin."""
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Por favor, faça login primeiro.")

    headers = {
        **COMMON_HEADERS,
        "authorization": f"Bearer {AUTH_TOKEN}",
    }

    params = {
        "page": 1,
        "username": account_number,
        "perPage": 100
    }

    try:
        response = requests.get(NETPLAY_CUSTOMER_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        full_data = response.json()
        
        filtered_data = []
        for client in full_data.get("data", []):
            vencimento = "Desconhecido"
            template = client.get("customer_renew_confirmation_template", "")
            if "🗓️ Próximo Vencimento: " in template:
                vencimento = template.split("🗓️ Próximo Vencimento: ")[-1].strip()
            
            filtered_data.append({
                "id": client.get("id"),
                "name": client.get("name"),
                "server": client.get("server"),
                "package": client.get("package"),
                "vencimento": vencimento,
                "username": client.get("username"),
                "status": client.get("status")
            })
        return {"clientes": filtered_data}
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição ao buscar cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao pesquisar cliente na API externa: {e}")
    except Exception as e:
        print(f"Erro inesperado ao processar pesquisa de cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar pesquisa: {e}")

@app.get("/api/servidores_e_planos") # Rota UNIFICADA para obter servidores E planos
async def get_servidores_e_planos():
    """
    Obtém a lista de servidores E extrai todos os planos (packages) de cada servidor
    da API netplay.sigma.vin.
    """
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")
    
    headers = {
        **COMMON_HEADERS,
        "authorization": f"Bearer {AUTH_TOKEN}",
    }
    
    try:
        # Chama a API de servidores, que já contém os planos aninhados
        response = requests.get(NETPLAY_SERVERS_URL, headers=headers)
        response.raise_for_status()
        servers_data = response.json().get("data", []) # Pega a lista de servidores

        servers_list = []
        packages_list = []
        seen_package_ids = set() # Para garantir que os planos sejam únicos

        for server in servers_data:
            servers_list.append({
                "id": server.get("id"),
                "name": server.get("name")
            })
            
            # Extrai os planos deste servidor
            for pkg in server.get("packages", []):
                if pkg.get("id") not in seen_package_ids:
                    packages_list.append({
                        "id": pkg.get("id"),
                        "name": pkg.get("name"),
                        "server_id": pkg.get("server_id"), # Pode ser útil para depuração
                        "server_name": pkg.get("server") # Nome do servidor associado ao plano
                    })
                    seen_package_ids.add(pkg.get("id"))

        # Retorna ambas as listas: servidores e planos (únicos)
        return {"servers": servers_list, "packages": packages_list}

    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição ao obter servidores e planos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter servidores e planos da API externa: {e}")
    except Exception as e:
        print(f"Erro inesperado ao processar servidores e planos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar servidores e planos: {e}")

# A rota /api/planos foi REMOVIDA, pois a função get_servidores_e_planos a substitui.


@app.put("/api/migrar")
async def migrar_cliente(request: MigrateRequest):
    """Migra um cliente para um novo servidor e/ou plano na API netplay.sigma.vin."""
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")
    
    if not request.server_id and not request.package_id:
        raise HTTPException(status_code=400, detail="Pelo menos um 'server_id' ou 'package_id' deve ser fornecido para a migração.")

    headers = {
        **COMMON_HEADERS,
        "authorization": f"Bearer {AUTH_TOKEN}",
        "content-type": "application/json",
    }
    
    payload = {}
    if request.server_id:
        payload["server_id"] = request.server_id
    if request.package_id:
        payload["package_id"] = request.package_id
    
    try:
        # A API de migração (PUT) deve ser chamada com o customer_id
        response = requests.put(
            f"{NETPLAY_API_BASE_URL}/customers/{request.customer_id}/migrate",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return {"message": "Migração realizada com sucesso!"}
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição ao migrar cliente: {e}")
        error_detail = "Erro desconhecido na migração."
        response_status_code = 500
        if response is not None:
            response_status_code = response.status_code
            try:
                error_json = response.json()
                error_detail = error_json.get("message", error_detail)
            except ValueError:
                error_detail = response.text
        raise HTTPException(status_code=response_status_code, detail=f"Erro na migração: {error_detail} (Detalhes: {e})")
    except Exception as e:
        print(f"Erro inesperado ao processar migração: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar migração: {e}")