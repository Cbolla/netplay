from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# load_dotenv() # Mantenha esta linha se você tiver outras variáveis de ambiente (além das credenciais de login) que precise carregar do arquivo .env. Se não, pode deixá-la comentada ou remover o .env.

app = FastAPI()

# --- Configuração de Pastas Estáticas ---
# Monta a pasta 'frontend' para servir os arquivos estáticos (HTML, CSS, JS).
# Qualquer requisição para '/static/...' será mapeada para a pasta 'frontend'.
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- Variáveis de Configuração da API Externa Netplay ---
# Base da URL da API externa Netplay.
NETPLAY_API_BASE_URL = "https://netplay.sigma.vin/api"
# URLs específicas para login, busca de clientes e servidores.
NETPLAY_LOGIN_URL = f"{NETPLAY_API_BASE_URL}/auth/login"
NETPLAY_CUSTOMER_SEARCH_URL = f"{NETPLAY_API_BASE_URL}/customers"
NETPLAY_SERVERS_URL = f"{NETPLAY_API_BASE_URL}/servers" # Usamos esta rota para obter servidores E planos

# Variável global para armazenar o token de autenticação.
# Em uma aplicação de produção, considere um gerenciamento de sessão mais robusto.
AUTH_TOKEN = None

# --- Cabeçalhos Comuns para Requisições à API Externa ---
# Estes cabeçalhos ajudam a simular uma requisição de navegador,
# o que pode ser importante para a API externa aceitar a chamada.
COMMON_HEADERS = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "origin": "https://netplay.sigma.vin",
    "referer": "https://netplay.sigma.vin/",
}

# --- Modelos Pydantic para validação de dados de requisição ---
# Define a estrutura esperada para o corpo da requisição de login.
class LoginRequest(BaseModel):
    username: str
    password: str

# Define a estrutura esperada para o corpo da requisição de migração.
# server_id e package_id são opcionais (podem ser None se não forem fornecidos).
class MigrateRequest(BaseModel):
    customer_id: str
    server_id: str = None
    package_id: str = None

# --- Rotas do Backend ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Rota principal que serve o arquivo HTML do frontend.
    Esta é a primeira página que o usuário verá ao acessar o servidor.
    """
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/login") # Rota para lidar com o login do usuário. Espera um método POST.
async def login(request: LoginRequest):
    """
    Realiza o login na API netplay.sigma.vin usando as credenciais fornecidas
    pelo frontend. Obtém e armazena o token de autenticação para uso futuro.
    """
    global AUTH_TOKEN # Declara que estamos usando a variável global AUTH_TOKEN

    headers = {
        **COMMON_HEADERS, # Inclui os cabeçalhos comuns definidos acima
        "content-type": "application/json", # Especifica que o corpo da requisição que enviamos é JSON
    }

    # Constrói o payload (corpo da requisição) com as credenciais recebidas do frontend.
    payload = {
        "username": request.username,
        "password": request.password
    }

    try:
        # Envia a requisição POST para a URL de login da API externa.
        response = requests.post(NETPLAY_LOGIN_URL, headers=headers, json=payload)
        response.raise_for_status()  # Lança uma exceção se a resposta for um erro (4xx ou 5xx)

        data = response.json() # Tenta converter a resposta da API externa para JSON
        
        # Tenta extrair o token de autenticação de diferentes campos possíveis na resposta (flexibilidade).
        token = data.get("token") or data.get("access_token") or data.get("data", {}).get("token")
        
        if token:
            AUTH_TOKEN = token # Armazena o token globalmente
            return {"message": "Login bem-sucedido!", "token": token}
        else:
            # Se nenhum token for encontrado, levanta um erro de autenticação.
            raise HTTPException(status_code=401, detail="Token de autenticação não encontrado na resposta da API externa.")
    except requests.exceptions.RequestException as e:
        # Captura erros que ocorrem durante a requisição HTTP (ex: falha de rede, timeout).
        print(f"Erro de requisição para API de login: {e}")
        error_message = f"Erro ao conectar com a API de login: {e}. Verifique se a API está online ou se há problemas de rede."
        if response is not None and response.content:
            try:
                error_data = response.json()
                error_message = error_data.get("message", error_message)
            except ValueError:
                error_message = response.text
        raise HTTPException(status_code=response.status_code if response is not None and response.status_code >= 400 else 500, detail=error_message)
    except Exception as e:
        # Captura outros erros inesperados (ex: JSON inválido, problemas de lógica).
        print(f"Erro inesperado no login: {e}")
        raise HTTPException(status_code=401, detail=f"Credenciais inválidas ou erro inesperado: {e}")

@app.get("/api/search_customer")
async def search_customer(account_number: str):
    """
    Pesquisa um cliente na API netplay.sigma.vin pelo número da conta.
    Requer um token de autenticação válido.
    Retorna dados filtrados e formatados do cliente.
    """
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Por favor, faça login primeiro.")

    headers = {
        **COMMON_HEADERS,
        "authorization": f"Bearer {AUTH_TOKEN}", # Inclui o token de autenticação nas requisições subsequentes
    }

    # Parâmetros de consulta para a API de busca de clientes.
    params = {
        "page": 1,
        "username": account_number, # O número da conta do cliente é mapeado para 'username' na API
        "perPage": 100 # Número de resultados por página
    }

    try:
        # Envia a requisição GET para buscar clientes na API externa.
        response = requests.get(NETPLAY_CUSTOMER_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status() # Verifica por erros HTTP na resposta
        full_data = response.json() # Converte a resposta para JSON
        
        # Processa e filtra os dados para enviar apenas as informações relevantes para o frontend.
        filtered_data = []
        for client in full_data.get("data", []):
            vencimento = "Desconhecido"
            # Tenta extrair a data de vencimento de um campo de template, se disponível.
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
        raise HTTPException(status_code=500, detail=f"Erro ao pesquisar cliente na API externa: {e}. Verifique se a API está online ou o token.")
    except Exception as e:
        print(f"Erro inesperado ao processar pesquisa de cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar pesquisa: {e}")

@app.get("/api/servidores_e_planos") # Rota UNIFICADA para obter servidores E planos
async def get_servidores_e_planos():
    """
    Obtém a lista de servidores e extrai todos os planos (packages) disponíveis
    da API netplay.sigma.vin. Esta rota substitui a antiga rota '/api/planos'.
    """
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")
    
    headers = {
        **COMMON_HEADERS,
        "authorization": f"Bearer {AUTH_TOKEN}",
    }
    
    try:
        # Chama a API de servidores. A resposta desta API contém os planos aninhados dentro de cada servidor.
        response = requests.get(NETPLAY_SERVERS_URL, headers=headers)
        response.raise_for_status()
        servers_data = response.json().get("data", []) # Extrai a lista de servidores do campo 'data'

        servers_list = []
        packages_list = []
        seen_package_ids = set() # Usado para garantir que não haja planos duplicados na lista final

        for server in servers_data:
            servers_list.append({
                "id": server.get("id"),
                "name": server.get("name")
            })
            
            # Percorre a lista de pacotes (planos) dentro de cada servidor.
            for pkg in server.get("packages", []):
                # Adiciona o plano à lista de planos se ele ainda não tiver sido adicionado (pelo ID).
                if pkg.get("id") not in seen_package_ids:
                    packages_list.append({
                        "id": pkg.get("id"),
                        "name": pkg.get("name"),
                        "server_id": pkg.get("server_id"), # ID do servidor associado ao plano
                        "server_name": pkg.get("server") # Nome do servidor associado ao plano
                    })
                    seen_package_ids.add(pkg.get("id"))

        # Retorna ambas as listas (servidores e planos únicos) ao frontend.
        return {"servers": servers_list, "packages": packages_list}

    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição ao obter servidores e planos: {e}")
        error_detail = "Erro desconhecido ao obter servidores e planos."
        response_status_code = 500
        if response is not None:
            response_status_code = response.status_code
            try:
                error_json = response.json()
                error_detail = error_json.get("message", error_detail)
            except ValueError:
                error_detail = response.text
        raise HTTPException(status_code=response_status_code, detail=f"Erro ao obter servidores e planos da API externa: {error_detail} (Detalhes: {e})")
    except Exception as e:
        print(f"Erro inesperado ao processar servidores e planos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar servidores e planos: {e}")


@app.put("/api/migrar") # Rota para migrar um cliente. Espera um método PUT.
async def migrar_cliente(request: MigrateRequest):
    """
    Migra um cliente para um novo servidor e/ou plano na API netplay.sigma.vin.
    Recebe o ID do cliente e os IDs do novo servidor e/ou plano via JSON.
    """
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")
    
    # Validação: Pelo menos um server_id ou package_id deve ser fornecido para a migração.
    if not request.server_id and not request.package_id:
        raise HTTPException(status_code=400, detail="Pelo menos um 'server_id' ou 'package_id' deve ser fornecido para a migração.")

    headers = {
        **COMMON_HEADERS,
        "authorization": f"Bearer {AUTH_TOKEN}",
        "content-type": "application/json", # Indica que o corpo da requisição que enviamos é JSON
    }
    
    # Constrói o payload apenas com os campos que foram realmente fornecidos na requisição.
    payload = {}
    if request.server_id:
        payload["server_id"] = request.server_id
    if request.package_id:
        payload["package_id"] = request.package_id
    
    # --- NOVOS PRINTS DE DEBUG PARA CAPTURAR A RESPOSTA 400 ---
    print(f"DEBUG: Payload enviado para migração: {payload}")
    migration_url_external = f"{NETPLAY_API_BASE_URL}/customers/{request.customer_id}/server-migration"
    print(f"DEBUG: Tentando migrar cliente para URL externa: {migration_url_external}")
    # --- FIM DOS NOVOS PRINTS ---

    try:
        # Envia a requisição PUT para a API externa para migrar o cliente.
        response = requests.put(
            migration_url_external,
            headers=headers,
            json=payload # Envia o payload como JSON
        )

        # --- MAIS PRINTS DE DEBUG APÓS RECEBER A RESPOSTA, ANTES DE VERIFICAR O STATUS ---
        print(f"DEBUG: Status code da resposta da API externa: {response.status_code}")
        print(f"DEBUG: Texto bruto da resposta da API externa: {response.text}")
        # --- FIM DOS PRINTS ---

        response.raise_for_status() # Esta linha irá levantar a exceção HTTPError se o status for 4xx ou 5xx

        # Se a resposta for bem-sucedida, retorna uma mensagem de sucesso.
        return {"message": "Migração realizada com sucesso!"}
    except requests.exceptions.RequestException as e:
        # Captura erros que ocorrem durante a requisição HTTP (ex: falha de rede, timeout, ou 4xx/5xx).
        print(f"Erro de requisição ao migrar cliente: {e}")
        
        error_detail_from_response = "Nenhuma resposta detalhada da API externa (corpo vazio ou não parseável)."
        response_status_code = 500

        # Tenta extrair a resposta detalhada da exceção, se disponível.
        if e.response is not None: # Verifica se um objeto de resposta está anexado à exceção
            response_status_code = e.response.status_code
            try:
                error_json = e.response.json() # Tenta parsear como JSON
                # Pega a mensagem do JSON, ou o texto bruto se 'message' não existir
                error_detail_from_response = error_json.get("message", str(e.response.text))
            except ValueError: # Se não for JSON, pega o texto bruto
                error_detail_from_response = e.response.text
        
        print(f"DEBUG: Detalhe do erro da API externa (capturado via exceção): {error_detail_from_response}")
        
        raise HTTPException(status_code=response_status_code, detail=f"Erro na migração: {error_detail_from_response} (Detalhes: {e})")
    except Exception as e:
        print(f"Erro inesperado ao processar migração: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar migração: {e}")
    """
    Migra um cliente para um novo servidor e/ou plano na API netplay.sigma.vin.
    Recebe o ID do cliente e os IDs do novo servidor e/ou plano via JSON.
    """
    if not AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login primeiro.")
    
    # Validação: Pelo menos um server_id ou package_id deve ser fornecido para a migração.
    if not request.server_id and not request.package_id:
        raise HTTPException(status_code=400, detail="Pelo menos um 'server_id' ou 'package_id' deve ser fornecido para a migração.")

    headers = {
        **COMMON_HEADERS,
        "authorization": f"Bearer {AUTH_TOKEN}",
        "content-type": "application/json", # Indica que o corpo da requisição que enviamos é JSON
    }
    
    # Constrói o payload apenas com os campos que foram realmente fornecidos na requisição.
    payload = {}
    if request.server_id:
        payload["server_id"] = request.server_id
    if request.package_id:
        payload["package_id"] = request.package_id
    
    try:
        # Envia a requisição PUT para a API externa para migrar o cliente.
        # A URL inclui o customer_id para identificar qual cliente será migrado.
        print(f"DEBUG: Tentando migrar cliente para URL externa: {NETPLAY_API_BASE_URL}/customers/{request.customer_id}/server-migration")

        response = requests.put(
            f"{NETPLAY_API_BASE_URL}/customers/{request.customer_id}/server-migration", # <--- AQUI A URL FOI CORRIGIDA
            headers=headers,
            json=payload # Seu payload atual é {"server_id": "...", "package_id": "..."}
        )
        response.raise_for_status() # Verifica por erros HTTP na resposta

        # Se a resposta for bem-sucedida, retorna uma mensagem de sucesso.
        return {"message": "Migração realizada com sucesso!"}
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição ao migrar cliente: {e}")
        # Tenta extrair detalhes do erro do corpo da resposta da API externa, se disponível.
        error_detail = "Erro desconhecido na migração."
        response_status_code = 500
        if response is not None:
            response_status_code = response.status_code
            try:
                error_json = response.json()
                error_detail = error_json.get("message", error_detail) # Adapte este campo se a API externa usar outro nome
            except ValueError:
                error_detail = response.text # Se a resposta não for JSON, pega o texto puro
        raise HTTPException(status_code=response_status_code, detail=f"Erro na migração: {error_detail} (Detalhes: {e})")
    except Exception as e:
        print(f"Erro inesperado ao processar migração: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao processar migração: {e}")