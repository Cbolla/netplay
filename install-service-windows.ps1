# Script para instalar Sistema Netplay como Serviço Windows
# Execute como Administrador

param(
    [string]$InstallPath = "C:\netplay",
    [string]$ServiceName = "NetplaySystem",
    [string]$ServiceDisplayName = "Sistema Netplay",
    [string]$ServiceDescription = "Sistema de automação para migração de clientes Netplay"
)

# Verificar se está executando como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Este script deve ser executado como Administrador!"
    exit 1
}

Write-Host "🔧 Instalando Sistema Netplay como Serviço Windows..." -ForegroundColor Green

# 1. Verificar se NSSM está disponível
$nssmPath = ""
try {
    $nssmPath = (Get-Command nssm -ErrorAction Stop).Source
    Write-Host "✅ NSSM encontrado: $nssmPath" -ForegroundColor Green
} catch {
    Write-Host "⚠️ NSSM não encontrado. Baixando..." -ForegroundColor Yellow
    
    # Baixar NSSM
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$env:TEMP\nssm.zip"
    $nssmDir = "$env:TEMP\nssm"
    
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath $nssmDir -Force
        
        # Copiar NSSM para System32
        $nssmExe = Get-ChildItem -Path $nssmDir -Name "nssm.exe" -Recurse | Select-Object -First 1
        if ($nssmExe) {
            $nssmSourcePath = (Get-ChildItem -Path $nssmDir -Name "nssm.exe" -Recurse | Select-Object -First 1).FullName
            $nssmPath = "C:\Windows\System32\nssm.exe"
            Copy-Item $nssmSourcePath $nssmPath
            Write-Host "✅ NSSM instalado em $nssmPath" -ForegroundColor Green
        } else {
            throw "NSSM não encontrado no arquivo baixado"
        }
        
        # Limpar arquivos temporários
        Remove-Item $nssmZip -Force -ErrorAction SilentlyContinue
        Remove-Item $nssmDir -Recurse -Force -ErrorAction SilentlyContinue
        
    } catch {
        Write-Error "❌ Erro ao baixar/instalar NSSM: $_"
        Write-Host "Baixe manualmente de: https://nssm.cc/download" -ForegroundColor Cyan
        exit 1
    }
}

# 2. Parar serviço se já existir
Write-Host "🛑 Verificando serviço existente..." -ForegroundColor Yellow
try {
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "⚠️ Serviço existente encontrado. Parando..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        & $nssmPath remove $ServiceName confirm
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "ℹ️ Nenhum serviço existente encontrado" -ForegroundColor Gray
}

# 3. Criar script de execução
Write-Host "📝 Criando script de execução..." -ForegroundColor Yellow
$runScript = @"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"@

$runScript | Out-File -FilePath "$InstallPath\run-netplay-service.bat" -Encoding ASCII

# 4. Instalar serviço com NSSM
Write-Host "🔧 Instalando serviço..." -ForegroundColor Yellow
try {
    # Instalar serviço
    & $nssmPath install $ServiceName "$InstallPath\run-netplay-service.bat"
    
    # Configurar serviço
    & $nssmPath set $ServiceName DisplayName "$ServiceDisplayName"
    & $nssmPath set $ServiceName Description "$ServiceDescription"
    & $nssmPath set $ServiceName Start SERVICE_AUTO_START
    & $nssmPath set $ServiceName AppDirectory "$InstallPath"
    & $nssmPath set $ServiceName AppStdout "$InstallPath\logs\service-output.log"
    & $nssmPath set $ServiceName AppStderr "$InstallPath\logs\service-error.log"
    & $nssmPath set $ServiceName AppRotateFiles 1
    & $nssmPath set $ServiceName AppRotateOnline 1
    & $nssmPath set $ServiceName AppRotateSeconds 86400
    & $nssmPath set $ServiceName AppRotateBytes 1048576
    
    Write-Host "✅ Serviço instalado com sucesso!" -ForegroundColor Green
    
} catch {
    Write-Error "❌ Erro ao instalar serviço: $_"
    exit 1
}

# 5. Criar diretório de logs
Write-Host "📁 Criando diretório de logs..." -ForegroundColor Yellow
$logsDir = "$InstallPath\logs"
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force
}

# 6. Configurar permissões (opcional)
Write-Host "🔐 Configurando permissões..." -ForegroundColor Yellow
try {
    # Dar permissões ao usuário NETWORK SERVICE
    icacls $InstallPath /grant "NETWORK SERVICE:(OI)(CI)F" /T
    Write-Host "✅ Permissões configuradas" -ForegroundColor Green
} catch {
    Write-Warning "⚠️ Erro ao configurar permissões: $_"
}

# 7. Criar scripts de gerenciamento
Write-Host "📋 Criando scripts de gerenciamento..." -ForegroundColor Yellow

# Script para iniciar serviço
$startScript = @"
@echo off
echo Iniciando Sistema Netplay...
net start $ServiceName
if %errorlevel% == 0 (
    echo ✅ Sistema Netplay iniciado com sucesso!
    echo 🌐 Acesse: http://localhost:8000
) else (
    echo ❌ Erro ao iniciar o serviço
)
pause
"@
$startScript | Out-File -FilePath "$InstallPath\start-service.bat" -Encoding ASCII

# Script para parar serviço
$stopScript = @"
@echo off
echo Parando Sistema Netplay...
net stop $ServiceName
if %errorlevel% == 0 (
    echo ✅ Sistema Netplay parado com sucesso!
) else (
    echo ❌ Erro ao parar o serviço
)
pause
"@
$stopScript | Out-File -FilePath "$InstallPath\stop-service.bat" -Encoding ASCII

# Script para status do serviço
$statusScript = @"
@echo off
echo 📊 Status do Sistema Netplay:
sc query $ServiceName
echo.
echo 📁 Logs do serviço:
echo - Output: $InstallPath\logs\service-output.log
echo - Errors: $InstallPath\logs\service-error.log
echo.
echo 🔧 Comandos úteis:
echo - Iniciar: net start $ServiceName
echo - Parar: net stop $ServiceName
echo - Reiniciar: net stop $ServiceName && net start $ServiceName
pause
"@
$statusScript | Out-File -FilePath "$InstallPath\service-status.bat" -Encoding ASCII

Write-Host ""
Write-Host "🎉 Serviço Windows instalado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Comandos disponíveis:" -ForegroundColor Cyan
Write-Host "- Iniciar: Start-Service $ServiceName" -ForegroundColor White
Write-Host "- Parar: Stop-Service $ServiceName" -ForegroundColor White
Write-Host "- Status: Get-Service $ServiceName" -ForegroundColor White
Write-Host ""
Write-Host "📁 Scripts de gerenciamento:" -ForegroundColor Yellow
Write-Host "- $InstallPath\start-service.bat" -ForegroundColor White
Write-Host "- $InstallPath\stop-service.bat" -ForegroundColor White
Write-Host "- $InstallPath\service-status.bat" -ForegroundColor White
Write-Host ""
Write-Host "📊 Logs do serviço:" -ForegroundColor Yellow
Write-Host "- $InstallPath\logs\service-output.log" -ForegroundColor White
Write-Host "- $InstallPath\logs\service-error.log" -ForegroundColor White
Write-Host ""
Write-Host "▶️ Para iniciar agora: Start-Service $ServiceName" -ForegroundColor Green