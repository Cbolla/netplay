# Script para iniciar servidor local com acesso Wi-Fi
# Execute: PowerShell -ExecutionPolicy Bypass -File start-local.ps1

Write-Host "🚀 Iniciando Netplay RPA - Servidor Local" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Função para log colorido
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

try {
    # Verificar Python
    Write-Info "Verificando Python..."
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python não encontrado!"
        Write-Info "Instale Python 3.8+ de: https://www.python.org/downloads/"
        Read-Host "Pressione Enter para sair"
        exit 1
    }
    Write-Success "Python encontrado: $pythonVersion"
    
    # Instalar dependências
    Write-Info "Verificando dependências..."
    & pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Instalando dependências básicas..."
        & pip install fastapi uvicorn python-dotenv requests httpx --quiet
    }
    Write-Success "Dependências verificadas ✓"
    
    # Configurar Windows Firewall
    Write-Info "Configurando Windows Firewall..."
    try {
        # Remover regra existente se houver
        netsh advfirewall firewall delete rule name="Netplay RPA Local" 2>$null
        
        # Adicionar nova regra
        $firewallResult = netsh advfirewall firewall add rule name="Netplay RPA Local" dir=in action=allow protocol=TCP localport=8000
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Firewall configurado ✓"
        } else {
            Write-Warning "Firewall não configurado - Execute como administrador para melhor resultado"
        }
    } catch {
        Write-Warning "Não foi possível configurar o firewall automaticamente"
    }
    
    # Obter IPs locais
    Write-Info "Detectando endereços de rede..."
    $LocalIPs = @()
    
    # Buscar IPs IPv4 válidos
    $networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -ne '127.0.0.1' -and 
        $_.IPAddress -notlike '169.254.*' -and
        $_.IPAddress -notlike '172.16.*' -and
        $_.PrefixOrigin -eq 'Dhcp'
    }
    
    foreach ($adapter in $networkAdapters) {
        $LocalIPs += $adapter.IPAddress
    }
    
    # Se não encontrou, tentar método alternativo
    if ($LocalIPs.Count -eq 0) {
        $ipconfig = ipconfig | Select-String "IPv4" | Where-Object { $_ -like "*192.168.*" -or $_ -like "*10.*" }
        foreach ($line in $ipconfig) {
            if ($line -match "(\d+\.\d+\.\d+\.\d+)") {
                $LocalIPs += $matches[1]
            }
        }
    }
    
    # Verificar se a porta está livre
    Write-Info "Verificando porta 8000..."
    $portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Warning "Porta 8000 já está em uso. Tentando liberar..."
        $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" }
        foreach ($proc in $processes) {
            Write-Info "Finalizando processo Python: PID $($proc.Id)"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    
    # Mostrar informações de acesso
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "🌐 INFORMAÇÕES DE ACESSO" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "💻 No seu computador:" -ForegroundColor Yellow
    Write-Host "   http://localhost:8000/" -ForegroundColor White
    Write-Host ""
    
    if ($LocalIPs.Count -gt 0) {
        Write-Host "📱 Em outros dispositivos da rede Wi-Fi:" -ForegroundColor Yellow
        foreach ($ip in $LocalIPs) {
            Write-Host "   http://$ip:8000/" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "📋 Páginas disponíveis:" -ForegroundColor Yellow
        foreach ($ip in $LocalIPs) {
            Write-Host "   Painel Admin: http://$ip:8000/" -ForegroundColor Cyan
            Write-Host "   Painel Cliente: http://$ip:8000/client" -ForegroundColor Cyan
        }
    } else {
        Write-Warning "Não foi possível detectar IP local automaticamente"
        Write-Info "Execute 'ipconfig' para ver seu IP manualmente"
    }
    
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "🔧 INSTRUÇÕES PARA TESTE" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 📶 Conecte outros dispositivos na mesma rede Wi-Fi" -ForegroundColor White
    Write-Host "2. 📱 Use um dos IPs mostrados acima no celular/tablet" -ForegroundColor White
    Write-Host "3. 🖥️  Mantenha este terminal aberto enquanto testar" -ForegroundColor White
    Write-Host "4. ⏹️  Pressione Ctrl+C para parar o servidor" -ForegroundColor White
    Write-Host ""
    Write-Host "🔥 Dica: Teste primeiro no seu navegador com localhost" -ForegroundColor Yellow
    Write-Host ""
    
    # Inicializar banco de dados
    Write-Info "Inicializando banco de dados..."
    & python -c "from database import db; print('Banco inicializado!')"
    
    Write-Host "🚀 Iniciando servidor..." -ForegroundColor Green
    Write-Host "Aguarde alguns segundos para o servidor inicializar..." -ForegroundColor Yellow
    Write-Host ""
    
    # Iniciar servidor
    & python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    
} catch {
    Write-Error "Erro: $($_.Exception.Message)"
    Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
} finally {
    Write-Host ""
    Write-Info "Servidor parado."
    Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}