# Script para configurar Cloudflare Tunnel no Windows Server
# Execute como Administrador APÓS o deploy básico

param(
    [string]$Domain = "seu-dominio.com",
    [string]$TunnelName = "netplay",
    [string]$InstallPath = "C:\netplay"
)

# Verificar se está executando como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Este script deve ser executado como Administrador!"
    exit 1
}

Write-Host "🌐 Configurando Cloudflare Tunnel para Sistema Netplay..." -ForegroundColor Green

# 1. Baixar e instalar cloudflared
Write-Host "📥 Baixando cloudflared..." -ForegroundColor Yellow
$cloudflaredUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$cloudflaredPath = "C:\Windows\System32\cloudflared.exe"

try {
    Invoke-WebRequest -Uri $cloudflaredUrl -OutFile $cloudflaredPath
    Write-Host "✅ cloudflared instalado em $cloudflaredPath" -ForegroundColor Green
} catch {
    Write-Error "❌ Erro ao baixar cloudflared: $_"
    exit 1
}

# 2. Criar diretório de configuração
Write-Host "📁 Criando diretório de configuração..." -ForegroundColor Yellow
$configDir = "$env:USERPROFILE\.cloudflared"
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force
}

# 3. Copiar arquivo de configuração
Write-Host "📋 Copiando arquivo de configuração..." -ForegroundColor Yellow
if (Test-Path "$InstallPath\cloudflare-tunnel.yml") {
    Copy-Item "$InstallPath\cloudflare-tunnel.yml" "$configDir\config.yml"
    Write-Host "✅ Arquivo de configuração copiado" -ForegroundColor Green
} else {
    Write-Error "❌ Arquivo cloudflare-tunnel.yml não encontrado em $InstallPath"
    exit 1
}

# 4. Criar script de configuração manual
$setupScript = @"
# Passos para configurar o Cloudflare Tunnel manualmente:

Write-Host "🔐 1. Faça login no Cloudflare:" -ForegroundColor Cyan
Write-Host "cloudflared tunnel login" -ForegroundColor White
Write-Host ""

Write-Host "🚇 2. Crie o tunnel:" -ForegroundColor Cyan
Write-Host "cloudflared tunnel create $TunnelName" -ForegroundColor White
Write-Host ""

Write-Host "🌐 3. Configure o DNS:" -ForegroundColor Cyan
Write-Host "cloudflared tunnel route dns $TunnelName $Domain" -ForegroundColor White
Write-Host ""

Write-Host "⚙️ 4. Edite o arquivo de configuração:" -ForegroundColor Cyan
Write-Host "notepad `"$configDir\config.yml`"" -ForegroundColor White
Write-Host "- Substitua SEU_TUNNEL_ID_AQUI pelo ID do tunnel criado" -ForegroundColor Yellow
Write-Host "- Substitua seu-dominio.com pelo seu domínio real" -ForegroundColor Yellow
Write-Host ""

Write-Host "🧪 5. Teste o tunnel:" -ForegroundColor Cyan
Write-Host "cloudflared tunnel run $TunnelName" -ForegroundColor White
Write-Host ""

Write-Host "🔧 6. Instale como serviço:" -ForegroundColor Cyan
Write-Host "cloudflared service install" -ForegroundColor White
Write-Host ""

Write-Host "▶️ 7. Inicie o serviço:" -ForegroundColor Cyan
Write-Host "Start-Service cloudflared" -ForegroundColor White
"@

$setupScript | Out-File -FilePath "$InstallPath\cloudflare-setup-manual.ps1" -Encoding UTF8

# 5. Criar serviço do Cloudflare Tunnel
Write-Host "🔧 Preparando serviço do Cloudflare Tunnel..." -ForegroundColor Yellow

$serviceScript = @"
# Script para executar Cloudflare Tunnel como serviço
cloudflared tunnel --config "$configDir\config.yml" run $TunnelName
"@

$serviceScript | Out-File -FilePath "$InstallPath\run-cloudflare-tunnel.ps1" -Encoding UTF8

# 6. Atualizar configurações do app
Write-Host "⚙️ Atualizando configurações do app..." -ForegroundColor Yellow
$envFile = "$InstallPath\.env"
if (Test-Path $envFile) {
    # Adicionar configurações específicas do Cloudflare
    Add-Content -Path $envFile -Value ""
    Add-Content -Path $envFile -Value "# Configurações Cloudflare Tunnel"
    Add-Content -Path $envFile -Value "CLOUDFLARE_TUNNEL=true"
    Add-Content -Path $envFile -Value "ALLOWED_HOSTS=$Domain,www.$Domain"
    Add-Content -Path $envFile -Value "CORS_ORIGINS=https://$Domain,https://www.$Domain"
    
    Write-Host "✅ Configurações do app atualizadas" -ForegroundColor Green
}

# 7. Configurar Firewall para Cloudflare
Write-Host "🔥 Configurando Firewall para Cloudflare..." -ForegroundColor Yellow
try {
    # Permitir cloudflared
    New-NetFirewallRule -DisplayName "Cloudflare Tunnel" -Direction Outbound -Program $cloudflaredPath -Action Allow
    Write-Host "✅ Regra de firewall criada para Cloudflare Tunnel" -ForegroundColor Green
} catch {
    Write-Warning "Erro ao configurar firewall: $_"
}

Write-Host ""
Write-Host "🎉 Configuração inicial do Cloudflare Tunnel concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos MANUAIS:" -ForegroundColor Cyan
Write-Host "1. Execute: $InstallPath\cloudflare-setup-manual.ps1" -ForegroundColor White
Write-Host "2. Siga as instruções para configurar o tunnel" -ForegroundColor White
Write-Host "3. Teste o acesso pelo seu domínio" -ForegroundColor White
Write-Host ""
Write-Host "📁 Arquivos importantes:" -ForegroundColor Yellow
Write-Host "- Configuração: $configDir\config.yml" -ForegroundColor White
Write-Host "- Setup manual: $InstallPath\cloudflare-setup-manual.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos úteis:" -ForegroundColor Yellow
Write-Host "- Status do tunnel: cloudflared tunnel info $TunnelName" -ForegroundColor White
Write-Host "- Logs: Get-EventLog -LogName Application -Source cloudflared" -ForegroundColor White