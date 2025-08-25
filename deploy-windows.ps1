# Script de Deploy para Windows Server
# Execute como Administrador: PowerShell -ExecutionPolicy Bypass -File deploy-windows.ps1

Write-Host "🚀 Iniciando deploy do Netplay RPA no Windows Server..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan

# Verificar se está executando como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Este script deve ser executado como Administrador!" -ForegroundColor Red
    Write-Host "Clique com botão direito no PowerShell e selecione 'Executar como administrador'" -ForegroundColor Yellow
    pause
    exit 1
}

# Função para log colorido
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

try {
    # Definir variáveis
    $ProjectDir = "C:\inetpub\netplay"
    $PythonPath = "python"
    $Port = 8000
    
    Write-Info "Verificando Python..."
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python não encontrado! Instale Python 3.8+ primeiro."
        Write-Info "Download: https://www.python.org/downloads/"
        pause
        exit 1
    }
    Write-Success "Python encontrado: $pythonVersion"
    
    # Criar diretório do projeto
    Write-Info "Criando diretório do projeto..."
    if (!(Test-Path $ProjectDir)) {
        New-Item -ItemType Directory -Path $ProjectDir -Force | Out-Null
    }
    
    # Copiar arquivos do projeto
    Write-Info "Copiando arquivos do projeto..."
    Copy-Item -Path ".\*" -Destination $ProjectDir -Recurse -Force
    Set-Location $ProjectDir
    
    # Criar ambiente virtual
    Write-Info "Criando ambiente virtual Python..."
    & python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao criar ambiente virtual"
        exit 1
    }
    
    # Ativar ambiente virtual e instalar dependências
    Write-Info "Instalando dependências Python..."
    & .\venv\Scripts\activate.ps1
    & .\venv\Scripts\pip install --upgrade pip
    & .\venv\Scripts\pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao instalar dependências"
        exit 1
    }
    
    # Verificar se a porta está disponível
    Write-Info "Verificando porta $Port..."
    $portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Warning "Porta $Port já está em uso. Tentando liberar..."
        $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*" }
        foreach ($proc in $processes) {
            Write-Info "Finalizando processo: $($proc.ProcessName) (PID: $($proc.Id))"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Configurar Windows Firewall
    Write-Info "Configurando Windows Firewall..."
    New-NetFirewallRule -DisplayName "Netplay RPA HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "Netplay RPA HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "Netplay RPA App" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -ErrorAction SilentlyContinue
    
    # Inicializar banco de dados
    Write-Info "Inicializando banco de dados..."
    & .\venv\Scripts\python -c "from database import db; print('Banco inicializado!')"
    
    # Obter IP público
    Write-Info "Obtendo IP público..."
    try {
        $PublicIP = Invoke-RestMethod -Uri "http://ifconfig.me/ip" -TimeoutSec 10
        $PublicIP = $PublicIP.Trim()
    } catch {
        $PublicIP = "IP não detectado"
    }
    
    # Obter IP local
    $LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress | Select-Object -First 1
    
    Write-Success "Deploy concluído com sucesso!"
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌐 Acesse sua aplicação em:" -ForegroundColor Green
    Write-Host "   http://$PublicIP:$Port/" -ForegroundColor White
    Write-Host "   http://$LocalIP:$Port/" -ForegroundColor White
    Write-Host "   http://localhost:$Port/" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Páginas disponíveis:" -ForegroundColor Yellow
    Write-Host "   Painel Revendedor: /" -ForegroundColor White
    Write-Host "   Painel Cliente: /client" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 Iniciando servidor..." -ForegroundColor Green
    Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
    Write-Host ""
    
    # Iniciar servidor
    & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port $Port --reload
    
} catch {
    Write-Error "Erro durante o deploy: $($_.Exception.Message)"
    Write-Host "Pressione qualquer tecla para sair..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}