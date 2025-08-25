# Script para instalar ngrok automaticamente
# Execute: PowerShell -ExecutionPolicy Bypass -File install-ngrok.ps1

Write-Host "📦 Instalando ngrok automaticamente..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Função para log colorido
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

try {
    # Verificar se ngrok já está instalado
    Write-Info "Verificando se ngrok já está instalado..."
    $ngrokExists = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($ngrokExists) {
        Write-Success "ngrok já está instalado: $($ngrokExists.Version)"
        Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 0
    }
    
    # Criar diretório para ngrok
    $ngrokDir = "$PWD\ngrok"
    Write-Info "Criando diretório: $ngrokDir"
    if (!(Test-Path $ngrokDir)) {
        New-Item -ItemType Directory -Path $ngrokDir -Force | Out-Null
    }
    
    # URL de download do ngrok
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $ngrokZip = "$ngrokDir\ngrok.zip"
    $ngrokExe = "$ngrokDir\ngrok.exe"
    
    Write-Info "Baixando ngrok de: $ngrokUrl"
    Write-Host "Aguarde, isso pode levar alguns minutos..." -ForegroundColor Yellow
    
    try {
        # Baixar ngrok
        Invoke-WebRequest -Uri $ngrokUrl -OutFile $ngrokZip -UseBasicParsing
        Write-Success "Download concluído!"
        
        # Extrair arquivo
        Write-Info "Extraindo ngrok..."
        Expand-Archive -Path $ngrokZip -DestinationPath $ngrokDir -Force
        
        # Remover arquivo zip
        Remove-Item $ngrokZip -Force
        
        # Verificar se foi extraído corretamente
        if (Test-Path $ngrokExe) {
            Write-Success "ngrok extraído com sucesso!"
        } else {
            throw "Arquivo ngrok.exe não encontrado após extração"
        }
        
    } catch {
        Write-Error "Falha ao baixar ngrok: $($_.Exception.Message)"
        Write-Info "Tentando método alternativo..."
        
        # Método alternativo - baixar diretamente o executável
        $ngrokDirectUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.exe"
        try {
            Write-Info "Baixando executável diretamente..."
            Invoke-WebRequest -Uri $ngrokDirectUrl -OutFile $ngrokExe -UseBasicParsing
            Write-Success "Download alternativo concluído!"
        } catch {
            Write-Error "Falha no download alternativo: $($_.Exception.Message)"
            Write-Host ""
            Write-Host "❌ Instalação automática falhou!" -ForegroundColor Red
            Write-Host ""
            Write-Host "📋 Instalação manual:" -ForegroundColor Yellow
            Write-Host "1. Acesse: https://ngrok.com/download" -ForegroundColor White
            Write-Host "2. Baixe 'Windows (64-bit)'" -ForegroundColor White
            Write-Host "3. Extraia ngrok.exe nesta pasta: $PWD" -ForegroundColor White
            Write-Host "4. Execute novamente: start-public.bat" -ForegroundColor White
            Write-Host ""
            Read-Host "Pressione Enter para sair"
            exit 1
        }
    }
    
    # Verificar se ngrok funciona
    Write-Info "Testando ngrok..."
    $ngrokVersion = & "$ngrokExe" version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "ngrok instalado com sucesso!"
        Write-Success "Versão: $ngrokVersion"
    } else {
        Write-Warning "ngrok instalado mas pode ter problemas"
    }
    
    # Adicionar ao PATH da sessão atual
    Write-Info "Adicionando ngrok ao PATH..."
    $env:PATH += ";$ngrokDir"
    
    # Criar script de atalho
    $shortcutScript = "@echo off`nset PATH=%PATH%;$ngrokDir`n$ngrokDir\ngrok.exe %*"
    $shortcutPath = "$PWD\ngrok.bat"
    $shortcutScript | Out-File -FilePath $shortcutPath -Encoding ASCII
    Write-Success "Atalho criado: ngrok.bat"
    
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "✅ INSTALAÇÃO CONCLUÍDA!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "📋 Como usar:" -ForegroundColor Yellow
    Write-Host "1. Execute: start-public.bat" -ForegroundColor White
    Write-Host "2. Ou use diretamente: .\ngrok\ngrok.exe http 8000" -ForegroundColor White
    Write-Host "3. Ou use o atalho: .\ngrok.bat http 8000" -ForegroundColor White
    Write-Host ""
    
    Write-Host "🔧 Configuração opcional (recomendada):" -ForegroundColor Yellow
    Write-Host "1. Acesse: https://ngrok.com/signup" -ForegroundColor White
    Write-Host "2. Crie conta gratuita" -ForegroundColor White
    Write-Host "3. Copie seu authtoken" -ForegroundColor White
    Write-Host "4. Execute: .\ngrok\ngrok.exe config add-authtoken SEU_TOKEN" -ForegroundColor White
    Write-Host ""
    
    Write-Host "🚀 Próximo passo:" -ForegroundColor Green
    Write-Host "Execute: start-public.bat" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Error "Erro durante instalação: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "📋 Instalação manual necessária:" -ForegroundColor Yellow
    Write-Host "1. Acesse: https://ngrok.com/download" -ForegroundColor White
    Write-Host "2. Baixe e extraia ngrok.exe" -ForegroundColor White
    Write-Host "3. Coloque ngrok.exe nesta pasta" -ForegroundColor White
    Write-Host ""
}

Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")