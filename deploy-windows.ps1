# Script de Deploy para Windows Server - Sistema Netplay
# Execute como Administrador

param(
    [string]$InstallPath = "C:\netplay",
    [string]$ServiceName = "NetplaySystem",
    [string]$Domain = "seu-dominio.com"
)

# Verificar se está executando como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Este script deve ser executado como Administrador!"
    exit 1
}

Write-Host "🚀 Iniciando deploy do Sistema Netplay no Windows Server..." -ForegroundColor Green

# 1. Verificar se Python está instalado
Write-Host "📋 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "❌ Python não encontrado! Instale Python 3.8+ primeiro."
    Write-Host "Download: https://www.python.org/downloads/windows/" -ForegroundColor Cyan
    exit 1
}

# 2. Criar diretório da aplicação
Write-Host "📁 Criando diretório da aplicação..." -ForegroundColor Yellow
if (!(Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force
}

# 3. Copiar arquivos
Write-Host "📋 Copiando arquivos da aplicação..." -ForegroundColor Yellow
Copy-Item -Path ".\*" -Destination $InstallPath -Recurse -Force -Exclude @("deploy-windows.ps1", ".git", "__pycache__", "*.pyc")

# 4. Criar ambiente virtual
Write-Host "🐍 Criando ambiente virtual Python..." -ForegroundColor Yellow
Set-Location $InstallPath
python -m venv venv
& ".\venv\Scripts\Activate.ps1"

# 5. Instalar dependências
Write-Host "📦 Instalando dependências..." -ForegroundColor Yellow
.\venv\Scripts\pip.exe install --upgrade pip
.\venv\Scripts\pip.exe install -r requirements.txt

# 6. Configurar arquivo .env
Write-Host "⚙️ Configurando arquivo de ambiente..." -ForegroundColor Yellow
if (Test-Path ".env.production") {
    Copy-Item ".env.production" ".env"
    Write-Host "⚠️ IMPORTANTE: Configure as credenciais no arquivo $InstallPath\.env" -ForegroundColor Red
} else {
    Write-Error "Arquivo .env.production não encontrado!"
}

# 7. Configurar banco de dados
Write-Host "🗄️ Configurando banco de dados..." -ForegroundColor Yellow
.\venv\Scripts\python.exe check_db.py

# 8. Criar serviço Windows
Write-Host "🔧 Criando serviço Windows..." -ForegroundColor Yellow

$serviceScript = @"
# Script para executar o Netplay como serviço
Set-Location "$InstallPath"
& ".\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"@

$serviceScript | Out-File -FilePath "$InstallPath\run-service.ps1" -Encoding UTF8

# Criar serviço usando NSSM (se disponível) ou sc
try {
    # Tentar usar NSSM primeiro (mais robusto)
    if (Get-Command nssm -ErrorAction SilentlyContinue) {
        nssm install $ServiceName powershell.exe
        nssm set $ServiceName Arguments "-ExecutionPolicy Bypass -File `"$InstallPath\run-service.ps1`""
        nssm set $ServiceName DisplayName "Sistema Netplay"
        nssm set $ServiceName Description "Sistema de automação Netplay"
        nssm set $ServiceName Start SERVICE_AUTO_START
        Write-Host "✅ Serviço criado com NSSM" -ForegroundColor Green
    } else {
        Write-Host "⚠️ NSSM não encontrado. Criando serviço básico..." -ForegroundColor Yellow
        sc.exe create $ServiceName binPath= "powershell.exe -ExecutionPolicy Bypass -File `"$InstallPath\run-service.ps1`"" start= auto
        Write-Host "✅ Serviço básico criado" -ForegroundColor Green
    }
} catch {
    Write-Warning "Erro ao criar serviço: $_"
}

# 9. Configurar Firewall
Write-Host "🔥 Configurando Firewall..." -ForegroundColor Yellow
try {
    New-NetFirewallRule -DisplayName "Netplay HTTP" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
    Write-Host "✅ Regra de firewall criada para porta 8000" -ForegroundColor Green
} catch {
    Write-Warning "Erro ao configurar firewall: $_"
}

# 10. Criar script de inicialização manual
$startScript = @"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
"@

$startScript | Out-File -FilePath "$InstallPath\start-netplay.bat" -Encoding ASCII

Write-Host ""
Write-Host "🎉 Deploy concluído com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Configure as credenciais em: $InstallPath\.env" -ForegroundColor White
Write-Host "2. Inicie o serviço: Start-Service $ServiceName" -ForegroundColor White
Write-Host "3. Ou execute manualmente: $InstallPath\start-netplay.bat" -ForegroundColor White
Write-Host "4. Acesse: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "📁 Logs do serviço: Event Viewer > Windows Logs > Application" -ForegroundColor Yellow
Write-Host "🔧 Gerenciar serviço: services.msc" -ForegroundColor Yellow