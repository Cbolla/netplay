#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para consultar usuários diretamente na API da Netplay
"""

import requests
import sys
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações da API Netplay
NETPLAY_API_BASE_URL = "https://netplay.mplll.com/api"
NETPLAY_HEADERS = {
    "accept": "application/json", 
    "user-agent": "Mozilla/5.0", 
    "origin": "https://netplay.mplll.com", 
    "referer": "https://netplay.mplll.com/",
    "content-type": "application/json"
}

# Credenciais administrativas
NETPLAY_USERNAME = os.getenv("NETPLAY_USERNAME", "seu_usuario_admin")
NETPLAY_PASSWORD = os.getenv("NETPLAY_PASSWORD", "sua_senha_admin")

def autenticar_admin():
    """Autentica com credenciais de administrador"""
    try:
        response = requests.post(f"{NETPLAY_API_BASE_URL}/auth/login", 
                               headers=NETPLAY_HEADERS, 
                               json={
                                   "username": NETPLAY_USERNAME,
                                   "password": NETPLAY_PASSWORD
                               })
        
        if response.status_code == 200:
            token = response.json().get("token") or response.json().get("access_token")
            if token:
                print(f"✅ Autenticado como administrador: {NETPLAY_USERNAME}")
                return token
        
        print(f"❌ Erro na autenticação administrativa. Status: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return None

def consultar_usuario(username=None, admin_token=None):
    """Consulta um usuário específico ou lista todos os usuários na Netplay"""
    if not admin_token:
        print("❌ Token de administrador necessário.")
        return
    
    try:
        headers = {**NETPLAY_HEADERS, "authorization": f"Bearer {admin_token}"}
        
        if username:
            # Busca usuário específico
            print(f"\n🔍 Buscando usuário {username} na Netplay...")
            
            response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers)
            
            if response.status_code == 200:
                customers = response.json().get("data", [])
                user_found = None
                
                for customer in customers:
                    if str(customer.get("username")) == str(username):
                        user_found = customer
                        break
                
                if user_found:
                     client_id = user_found.get('id')
                     print(f"\n✅ USUÁRIO ENCONTRADO NA NETPLAY: {username}")
                     print("="*60)
                     print(f"📧 ID: {client_id}")
                     
                     # Busca dados completos do cliente incluindo senha
                     print(f"🔍 Buscando dados completos do cliente...")
                     
                     try:
                          detail_response = requests.get(f"{NETPLAY_API_BASE_URL}/customers/{client_id}", headers=headers)
                          
                          print(f"🔍 Status da resposta: {detail_response.status_code}")
                          
                          if detail_response.status_code == 200:
                              response_data = detail_response.json()
                              print(f"📋 DEBUG - Estrutura da resposta: {list(response_data.keys()) if isinstance(response_data, dict) else 'Não é dict'}")
                              
                              # Tenta diferentes estruturas de resposta
                              client_details = response_data
                              if 'data' in response_data:
                                  client_details = response_data['data']
                              elif 'customer' in response_data:
                                  client_details = response_data['customer']
                              
                              print(f"👤 Username: {client_details.get('username', user_found.get('username', 'N/A'))}")
                              print(f"🔐 SENHA: {client_details.get('password', 'Não disponível')}")
                              print(f"📧 Email: {client_details.get('email', user_found.get('email', 'N/A'))}")
                              
                              # Servidor - usa dados da listagem se não estiver nos detalhes
                              server = client_details.get('server', user_found.get('server', {}))
                              if isinstance(server, dict):
                                  print(f"🖥️ Servidor: {server.get('name', 'N/A')} (ID: {server.get('id', 'N/A')})")
                              else:
                                  print(f"🖥️ Servidor: {server}")
                              
                              # Pacote - usa dados da listagem se não estiver nos detalhes
                              package = client_details.get('package', user_found.get('package', {}))
                              if isinstance(package, dict):
                                  print(f"📦 Pacote: {package.get('name', 'N/A')} (ID: {package.get('id', 'N/A')})")
                              else:
                                  print(f"📦 Pacote: {package}")
                              
                              print(f"📅 Criado: {client_details.get('created_at', user_found.get('created_at', 'N/A'))}")
                              print(f"🔄 Atualizado: {client_details.get('updated_at', user_found.get('updated_at', 'N/A'))}")
                              print(f"✅ Status: {client_details.get('status', user_found.get('status', 'N/A'))}")
                              
                              # Informações adicionais se disponíveis
                              if client_details.get('phone'):
                                  print(f"📱 Telefone: {client_details.get('phone')}")
                              if client_details.get('cpf'):
                                  print(f"🆔 CPF: {client_details.get('cpf')}")
                              
                              # Mostra todos os campos disponíveis para debug
                              print(f"\n🔍 DEBUG - Campos disponíveis: {list(client_details.keys()) if isinstance(client_details, dict) else 'N/A'}")
                              
                              print(f"\n🔗 Link de edição: https://netplay.mplll.com/#/customers/edit/{client_id}")
                              
                          else:
                              print(f"⚠️ Erro ao buscar detalhes completos. Status: {detail_response.status_code}")
                              print(f"📋 Resposta: {detail_response.text[:200]}...")
                              
                              # Mostra dados básicos da listagem
                              print(f"👤 Username: {user_found.get('username', 'N/A')}")
                              print(f"📧 Email: {user_found.get('email', 'N/A')}")
                              
                              server = user_found.get('server', {})
                              if isinstance(server, dict):
                                  print(f"🖥️ Servidor: {server.get('name', 'N/A')}")
                              else:
                                  print(f"🖥️ Servidor: {server}")
                              
                              package = user_found.get('package', {})
                              if isinstance(package, dict):
                                  print(f"📦 Pacote: {package.get('name', 'N/A')}")
                              else:
                                  print(f"📦 Pacote: {package}")
                      
                     except Exception as detail_error:
                         print(f"⚠️ Erro ao buscar detalhes: {detail_error}")
                         # Mostra dados básicos da listagem
                         print(f"👤 Username: {user_found.get('username', 'N/A')}")
                         print(f"📧 Email: {user_found.get('email', 'N/A')}")
                         
                         server = user_found.get('server', {})
                         if isinstance(server, dict):
                             print(f"🖥️ Servidor: {server.get('name', 'N/A')}")
                         else:
                             print(f"🖥️ Servidor: {server}")
                         
                         package = user_found.get('package', {})
                         if isinstance(package, dict):
                             print(f"📦 Pacote: {package.get('name', 'N/A')}")
                         else:
                             print(f"📦 Pacote: {package}")
                     
                     print("="*60)
                else:
                    print(f"\n❌ Usuário {username} NÃO encontrado na Netplay.")
                    print("💡 Verifique se o número está correto ou se o usuário existe.")
            else:
                print(f"❌ Erro ao buscar usuários. Status: {response.status_code}")
                print(f"Resposta: {response.text}")
        
        else:
            # Lista todos os usuários (primeiros 50)
            print("\n📋 Buscando todos os usuários na Netplay...")
            
            response = requests.get(f"{NETPLAY_API_BASE_URL}/customers", headers=headers)
            
            if response.status_code == 200:
                customers = response.json().get("data", [])
                
                if customers:
                    print(f"\n📋 USUÁRIOS NA NETPLAY ({len(customers)} encontrados):")
                    print("="*80)
                    for i, customer in enumerate(customers[:50], 1):  # Limita a 50 para não sobrecarregar
                        username = customer.get('username', 'N/A')
                        server = customer.get('server', {})
                        server_name = server.get('name', 'N/A') if isinstance(server, dict) else str(server)
                        package = customer.get('package', {})
                        package_name = package.get('name', 'N/A') if isinstance(package, dict) else str(package)
                        
                        print(f"{i:2d}. 👤 {username} | 🖥️ {server_name} | 📦 {package_name}")
                    
                    if len(customers) > 50:
                        print(f"\n... e mais {len(customers) - 50} usuários (mostrando apenas os primeiros 50)")
                    
                    print("="*80)
                else:
                    print("\n📭 Nenhum usuário encontrado na Netplay.")
            else:
                print(f"❌ Erro ao buscar usuários. Status: {response.status_code}")
                print(f"Resposta: {response.text}")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")

def main():
    """Função principal"""
    print("🔍 CONSULTOR DE USUÁRIOS - NETPLAY API")
    print("="*50)
    
    # Autentica como administrador
    print("\n🔐 Autenticando como administrador...")
    admin_token = autenticar_admin()
    
    if not admin_token:
        print("❌ Falha na autenticação. Verifique suas credenciais no arquivo .env")
        print("💡 Configure NETPLAY_USERNAME e NETPLAY_PASSWORD no arquivo .env")
        return
    
    if len(sys.argv) > 1:
        # Usuário específico fornecido como argumento
        username = sys.argv[1]
        consultar_usuario(username, admin_token)
    else:
        # Modo interativo
        while True:
            print("\n📋 OPÇÕES:")
            print("1. 🔍 Consultar usuário específico")
            print("2. 📋 Listar todos os usuários (primeiros 50)")
            print("3. 🚪 Sair")
            
            escolha = input("\n👉 Escolha uma opção (1-3): ").strip()
            
            if escolha == "1":
                username = input("👤 Digite o username: ").strip()
                if username:
                    consultar_usuario(username, admin_token)
                else:
                    print("❌ Username não pode estar vazio.")
            
            elif escolha == "2":
                consultar_usuario(None, admin_token)
            
            elif escolha == "3":
                print("👋 Saindo...")
                break
            
            else:
                print("❌ Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()