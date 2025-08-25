# Script para verificar IP e status do servidor Netplay RPA
# Execute: PowerShell -ExecutionPolicy Bypass -File check-ip.ps1

Write-Host "🔍 Verificando informações do servidor Netplay RPA..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Função para log colorido
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Obter IP público
Write-Info "Obtendo IP público..."
try {
    $PublicIP = Invoke-RestMethod -Uri "http://ifconfig.me/ip" -TimeoutSec 10
    $PublicIP = $PublicIP.Trim()
    Write-Success "IP Público: $PublicIP"
} catch {
    Write-Warning "Não foi possível obter o IP público"
    $PublicIP = "Não detectado"
}

# Obter IP local
Write-Info "Obtendo IP local..."
try {
    $LocalIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
        $_.IPAddress -ne '127.0.0.1' -and 
        $_.IPAddress -ne '169.254.*' -and
        $_.PrefixOrigin -eq 'Dhcp' 
    } | Select-Object -ExpandProperty IPAddress
    
    if ($LocalIPs) {
        foreach ($ip in $LocalIPs) {
            Write-Success "IP Local: $ip"
        }
    } else {
        Write-Warning "IP local não detectado"
    }
} catch {
    Write-Warning "Erro ao obter IP local"
}

Write-Host ""
Write-Host "🌐 URLs de Acesso:" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan

$Port = 8000

if ($PublicIP -ne "Não detectado") {
    Write-Host "📡 Acesso Externo (Internet):" -ForegroundColor Green
    Write-Host "   Painel Admin: http://$PublicIP:$Port/" -ForegroundColor White
    Write-Host "   Painel Cliente: http://$PublicIP:$Port/client" -ForegroundColor White
    Write-Host ""
}

if ($LocalIPs) {
    Write-Host "🏠 Acesso Local (Rede):" -ForegroundColor Green
    foreach ($ip in $LocalIPs) {
        Write-Host "   Painel Admin: http://$ip:$Port/" -ForegroundColor White
        Write-Host "   Painel Cliente: http://$ip:$Port/client" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "💻 Acesso Localhost:" -ForegroundColor Green
Write-Host "   Painel Admin: http://localhost:$Port/" -ForegroundColor White
Write-Host "   Painel Cliente: http://localhost:$Port/client" -ForegroundColor White
Write-Host ""

# Verificar se o servidor está rodando
Write-Info "Verificando se o servidor está rodando..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port/" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "Servidor está rodando na porta $Port ✓"
    } else {
        Write-Warning "Servidor respondeu com código: $($response.StatusCode)"
    }
} catch {
    Write-Error "Servidor não está rodando na porta $Port"
    Write-Info "Para iniciar o servidor, execute: start-windows.bat"
}

# Verificar processos Python
Write-Info "Verificando processos Python..."
$pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" }
if ($pythonProcesses) {
    Write-Success "Processos Python encontrados:"
    foreach ($proc in $pythonProcesses) {
        Write-Host "   PID: $($proc.Id) - $($proc.ProcessName)" -ForegroundColor White
    }
} else {
    Write-Warning "Nenhum processo Python encontrado"
}

# Verificar porta em uso
Write-Info "Verificando porta $Port..."
$portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Success "Porta $Port está em uso"
    foreach ($conn in $portInUse) {
        Write-Host "   Estado: $($conn.State) - PID: $($conn.OwningProcess)" -ForegroundColor White
    }
} else {
    Write-Warning "Porta $Port não está em uso"
}

Write-Host ""
Write-Host "🔧 Comandos Úteis:" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Iniciar servidor: start-windows.bat" -ForegroundColor White
Write-Host "Verificar IP: check-ip.ps1" -ForegroundColor White
Write-Host "Parar servidor: Ctrl+C no terminal do servidor" -ForegroundColor White
Write-Host ""

Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")