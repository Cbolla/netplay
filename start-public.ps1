# Script para criar acesso público usando ngrok
# Execute: PowerShell -ExecutionPolicy Bypass -File start-public.ps1

Write-Host "🌐 Netplay RPA - Acesso Público (Internet)" -ForegroundColor Green
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
    
    # Verificar se ngrok está instalado
    Write-Info "Verificando ngrok..."
    $ngrokVersion = & ngrok version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "ngrok não encontrado. Instalando..."
        
        # Tentar instalar via Chocolatey
        $chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue
        if ($chocoInstalled) {
            Write-Info "Instalando ngrok via Chocolatey..."
            & choco install ngrok -y
        } else {
            Write-Info "Baixando ngrok manualmente..."
            
            # Criar diretório para ngrok
            $ngrokDir = "$env:USERPROFILE\ngrok"
            if (!(Test-Path $ngrokDir)) {
                New-Item -ItemType Directory -Path $ngrokDir -Force | Out-Null
            }
            
            # Baixar ngrok
            $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
            $ngrokZip = "$ngrokDir\ngrok.zip"
            
            Write-Info "Baixando ngrok..."
            try {
                Invoke-WebRequest -Uri $ngrokUrl -OutFile $ngrokZip -UseBasicParsing
                
                # Extrair
                Write-Info "Extraindo ngrok..."
                Expand-Archive -Path $ngrokZip -DestinationPath $ngrokDir -Force
                Remove-Item $ngrokZip -Force
                
                # Adicionar ao PATH temporariamente
                $env:PATH += ";$ngrokDir"
                
                Write-Success "ngrok instalado com sucesso!"
            } catch {
                Write-Error "Falha ao baixar ngrok: $($_.Exception.Message)"
                Write-Info "Por favor, instale manualmente de: https://ngrok.com/download"
                Read-Host "Pressione Enter para sair"
                exit 1
            }
        }
    } else {
        Write-Success "ngrok encontrado: $ngrokVersion"
    }
    
    # Verificar se ngrok está autenticado
    Write-Info "Verificando autenticação do ngrok..."
    $ngrokConfig = & ngrok config check 2>&1
    if ($ngrokConfig -like "*authtoken*" -or $ngrokConfig -like "*not found*") {
        Write-Warning "ngrok não está autenticado!"
        Write-Host ""
        Write-Host "📋 Para usar ngrok gratuitamente:" -ForegroundColor Yellow
        Write-Host "1. Acesse: https://ngrok.com/signup" -ForegroundColor White
        Write-Host "2. Crie uma conta gratuita" -ForegroundColor White
        Write-Host "3. Copie seu authtoken" -ForegroundColor White
        Write-Host "4. Execute: ngrok config add-authtoken SEU_TOKEN" -ForegroundColor White
        Write-Host ""
        $token = Read-Host "Cole seu authtoken aqui (ou Enter para continuar sem autenticação)"
        
        if ($token -and $token.Trim() -ne "") {
            Write-Info "Configurando authtoken..."
            & ngrok config add-authtoken $token.Trim()
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Authtoken configurado!"
            } else {
                Write-Warning "Falha ao configurar authtoken, continuando sem autenticação..."
            }
        } else {
            Write-Warning "Continuando sem autenticação (limitações aplicam-se)"
        }
    }
    
    # Instalar dependências Python
    Write-Info "Verificando dependências Python..."
    & pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Instalando dependências básicas..."
        & pip install fastapi uvicorn python-dotenv requests httpx --quiet
    }
    Write-Success "Dependências verificadas ✓"
    
    # Inicializar banco de dados
    Write-Info "Inicializando banco de dados..."
    & python -c "from database import db; print('Banco inicializado!')"
    
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "🚀 INICIANDO SERVIDOR PÚBLICO" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Iniciar servidor Python em background
    Write-Info "Iniciando servidor FastAPI..."
    $serverJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        & python -m uvicorn main:app --host 127.0.0.1 --port 8000
    }
    
    # Aguardar servidor inicializar
    Write-Info "Aguardando servidor inicializar..."
    Start-Sleep -Seconds 5
    
    # Verificar se servidor está rodando
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -UseBasicParsing
        Write-Success "Servidor local iniciado ✓"
    } catch {
        Write-Error "Falha ao iniciar servidor local"
        Stop-Job $serverJob -Force
        Remove-Job $serverJob -Force
        exit 1
    }
    
    # Iniciar ngrok
    Write-Info "Criando túnel público com ngrok..."
    Write-Host "Aguarde alguns segundos..." -ForegroundColor Yellow
    
    $ngrokJob = Start-Job -ScriptBlock {
        & ngrok http 8000 --log stdout
    }
    
    # Aguardar ngrok inicializar
    Start-Sleep -Seconds 8
    
    # Obter URL pública do ngrok
    try {
        $ngrokApi = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 10
        $publicUrl = $ngrokApi.tunnels[0].public_url
        
        if ($publicUrl) {
            Write-Host ""
            Write-Host "================================================" -ForegroundColor Cyan
            Write-Host "🌍 ACESSO PÚBLICO ATIVO!" -ForegroundColor Green
            Write-Host "================================================" -ForegroundColor Cyan
            Write-Host ""
            
            Write-Host "🌐 URL Pública (Acesse de qualquer lugar):" -ForegroundColor Yellow
            Write-Host "   $publicUrl" -ForegroundColor White
            Write-Host ""
            Write-Host "📋 Páginas disponíveis:" -ForegroundColor Yellow
            Write-Host "   Painel Admin: $publicUrl/" -ForegroundColor Cyan
            Write-Host "   Painel Cliente: $publicUrl/client" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "📱 Teste em qualquer dispositivo:" -ForegroundColor Yellow
            Write-Host "   - Celular (4G/5G)" -ForegroundColor White
            Write-Host "   - Tablet (qualquer Wi-Fi)" -ForegroundColor White
            Write-Host "   - Computador (qualquer lugar)" -ForegroundColor White
            Write-Host ""
            Write-Host "⚠️  IMPORTANTE:" -ForegroundColor Red
            Write-Host "   - Esta URL é temporária" -ForegroundColor White
            Write-Host "   - Válida apenas enquanto este script estiver rodando" -ForegroundColor White
            Write-Host "   - Para produção, use VPS real" -ForegroundColor White
            Write-Host ""
            Write-Host "🔧 Controles:" -ForegroundColor Yellow
            Write-Host "   - Pressione Ctrl+C para parar" -ForegroundColor White
            Write-Host "   - Mantenha este terminal aberto" -ForegroundColor White
            Write-Host ""
            
            # Copiar URL para clipboard
            try {
                $publicUrl | Set-Clipboard
                Write-Success "URL copiada para área de transferência!"
            } catch {
                # Ignore clipboard errors
            }
            
            Write-Host "Servidor rodando... Pressione Ctrl+C para parar" -ForegroundColor Green
            
            # Manter rodando até Ctrl+C
            try {
                while ($true) {
                    Start-Sleep -Seconds 1
                    
                    # Verificar se jobs ainda estão rodando
                    if ($serverJob.State -ne "Running" -or $ngrokJob.State -ne "Running") {
                        Write-Warning "Um dos serviços parou. Reiniciando..."
                        break
                    }
                }
            } catch {
                Write-Info "Parando serviços..."
            }
        } else {
            Write-Error "Não foi possível obter URL pública do ngrok"
        }
    } catch {
        Write-Error "Falha ao conectar com ngrok API: $($_.Exception.Message)"
        Write-Info "Verifique se ngrok está rodando corretamente"
    }
    
} catch {
    Write-Error "Erro: $($_.Exception.Message)"
} finally {
    # Limpar jobs
    Write-Info "Parando serviços..."
    
    if ($serverJob) {
        Stop-Job $serverJob -Force -ErrorAction SilentlyContinue
        Remove-Job $serverJob -Force -ErrorAction SilentlyContinue
    }
    
    if ($ngrokJob) {
        Stop-Job $ngrokJob -Force -ErrorAction SilentlyContinue
        Remove-Job $ngrokJob -Force -ErrorAction SilentlyContinue
    }
    
    # Matar processos ngrok
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Info "Serviços parados."
    Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}