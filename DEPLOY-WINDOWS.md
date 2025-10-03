# 🚀 Guia de Deploy - Sistema Netplay Windows Server

Este guia contém instruções completas para fazer deploy do Sistema Netplay em uma VPS Windows Server.

## 📋 Pré-requisitos

- VPS com Windows Server 2019+ ou Windows 10/11
- Acesso de Administrador
- Python 3.8+ instalado
- Domínio configurado (opcional, mas recomendado)
- Credenciais da Netplay

## 🛠️ Deploy Automatizado

### 1. Preparar os arquivos na VPS

```powershell
# Conecte via RDP na VPS Windows
# Baixe os arquivos do projeto para C:\temp\netplay
# Ou use git clone se disponível
```

### 2. Executar o deploy

```powershell
# Abra PowerShell como Administrador
cd C:\temp\netplay

# Executar deploy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy-windows.ps1
```

## ⚙️ Configuração Manual (Alternativa)

### 1. Instalar Python

```powershell
# Baixe Python de https://www.python.org/downloads/windows/
# Certifique-se de marcar "Add Python to PATH"
python --version  # Verificar instalação
```

### 2. Configurar aplicação

```powershell
# Criar diretório
New-Item -ItemType Directory -Path "C:\netplay" -Force
cd C:\netplay

# Copiar arquivos do projeto
Copy-Item -Path "C:\temp\netplay\*" -Destination "C:\netplay" -Recurse -Force

# Criar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```powershell
# Copiar arquivo de produção
Copy-Item .env.production .env

# Editar configurações
notepad .env
```

**Configure as seguintes variáveis:**

```env
# Credenciais da Netplay (OBRIGATÓRIO)
NETPLAY_USERNAME=seu_usuario@netplay.com
NETPLAY_PASSWORD=sua_senha_segura

# Configurações do servidor
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
DEBUG=false

# Domínio (se tiver)
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,IP_DA_VPS
CORS_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
```

### 4. Configurar banco de dados

```powershell
python check_db.py
```

### 5. Instalar como serviço Windows

```powershell
# Executar script de instalação do serviço
.\install-service-windows.ps1
```

## 🌐 Configurar Cloudflare Tunnel

### 1. Executar configuração do Cloudflare

```powershell
# Executar script de configuração
.\setup-cloudflare-tunnel-windows.ps1 -Domain "seu-dominio.com"
```

### 2. Configuração manual do tunnel

```powershell
# 1. Login no Cloudflare
cloudflared tunnel login

# 2. Criar tunnel
cloudflared tunnel create netplay

# 3. Configurar DNS
cloudflared tunnel route dns netplay seu-dominio.com

# 4. Editar configuração
notepad "C:\Users\Administrator\.cloudflared\config.yml"
# Substitua SEU_TUNNEL_ID_AQUI pelo ID real do tunnel

# 5. Testar tunnel
cloudflared tunnel run netplay

# 6. Instalar como serviço
cloudflared service install

# 7. Iniciar serviço
Start-Service cloudflared
```

## 🔧 Gerenciamento do Sistema

### Comandos do Serviço Principal

```powershell
# Iniciar sistema
Start-Service NetplaySystem

# Parar sistema
Stop-Service NetplaySystem

# Status do sistema
Get-Service NetplaySystem

# Logs do sistema
Get-Content "C:\netplay\logs\service-output.log" -Tail 50
```

### Scripts de Gerenciamento

- **Iniciar**: `C:\netplay\start-service.bat`
- **Parar**: `C:\netplay\stop-service.bat`
- **Status**: `C:\netplay\service-status.bat`
- **Manual**: `C:\netplay\start-netplay.bat`

### Comandos do Cloudflare Tunnel

```powershell
# Status do tunnel
cloudflared tunnel info netplay

# Logs do tunnel
Get-EventLog -LogName Application -Source cloudflared -Newest 50

# Reiniciar tunnel
Restart-Service cloudflared
```

## 🔥 Configuração do Firewall

```powershell
# Permitir porta 8000 (se não usar Cloudflare Tunnel)
New-NetFirewallRule -DisplayName "Netplay HTTP" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Permitir Cloudflare Tunnel (já configurado automaticamente)
```

## 📊 Monitoramento

### Logs do Sistema

- **Aplicação**: `C:\netplay\logs\service-output.log`
- **Erros**: `C:\netplay\logs\service-error.log`
- **Windows Events**: Event Viewer > Windows Logs > Application

### URLs de Acesso

- **Local**: http://localhost:8000
- **IP Público**: http://SEU_IP_VPS:8000 (se firewall permitir)
- **Cloudflare Tunnel**: https://seu-dominio.com

## 🛠️ Solução de Problemas

### Serviço não inicia

```powershell
# Verificar logs
Get-Content "C:\netplay\logs\service-error.log" -Tail 20

# Testar manualmente
cd C:\netplay
.\start-netplay.bat
```

### Cloudflare Tunnel não funciona

```powershell
# Verificar configuração
cloudflared tunnel info netplay

# Testar manualmente
cloudflared tunnel --config "C:\Users\Administrator\.cloudflared\config.yml" run netplay

# Verificar DNS
nslookup seu-dominio.com
```

### Problemas de permissão

```powershell
# Dar permissões ao diretório
icacls "C:\netplay" /grant "Everyone:(OI)(CI)F" /T

# Executar como administrador
```

## 🔄 Atualizações

### Atualizar código

```powershell
# Parar serviços
Stop-Service NetplaySystem
Stop-Service cloudflared

# Atualizar arquivos
# (copiar novos arquivos)

# Reinstalar dependências se necessário
cd C:\netplay
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Reiniciar serviços
Start-Service NetplaySystem
Start-Service cloudflared
```

## 📞 Suporte

### Comandos úteis para diagnóstico

```powershell
# Status geral
Get-Service NetplaySystem, cloudflared
Get-Process python, cloudflared

# Teste de conectividade
Test-NetConnection -ComputerName seu-dominio.com -Port 443
Test-NetConnection -ComputerName localhost -Port 8000

# Informações do sistema
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion
python --version
```

### Estrutura de arquivos

```
C:\netplay\
├── main.py                          # Aplicação principal
├── requirements.txt                 # Dependências Python
├── .env                            # Configurações (CONFIGURE!)
├── venv\                           # Ambiente virtual Python
├── logs\                           # Logs do sistema
├── frontend\                       # Arquivos web
├── start-netplay.bat              # Iniciar manual
├── start-service.bat              # Iniciar serviço
├── stop-service.bat               # Parar serviço
├── service-status.bat             # Status do serviço
└── run-netplay-service.bat        # Script do serviço
```

---

## 🎉 Deploy Concluído!

Após seguir este guia, seu Sistema Netplay estará:

- ✅ Rodando como serviço Windows (auto-start)
- ✅ Acessível globalmente via Cloudflare Tunnel
- ✅ Com logs estruturados
- ✅ Com scripts de gerenciamento
- ✅ Configurado para produção

**Acesse seu sistema em**: https://seu-dominio.com