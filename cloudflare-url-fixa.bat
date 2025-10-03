@echo off
chcp 65001 >nul
title Cloudflare Tunnel - URL Fixa Permanente

echo.
echo ========================================
echo    CLOUDFLARE TUNNEL - URL FIXA
echo ========================================
echo.
echo [INFO] Para ter URL que NUNCA muda, voce precisa:
echo.
echo OPCAO 1 - CRIAR CONTA GRATUITA no Cloudflare:
echo    Link: https://dash.cloudflare.com/sign-up
echo.
echo OPCAO 2 - EXECUTAR os comandos abaixo:
echo.

echo [PASSO 1] Login no Cloudflare:
echo cloudflared.exe tunnel login
echo.

echo [PASSO 2] Criar tunnel nomeado:
echo cloudflared.exe tunnel create netplay-server
echo.

echo [PASSO 3] Configurar DNS:
echo cloudflared.exe tunnel route dns netplay-server SEU-DOMINIO.com
echo.

echo [PASSO 4] Rodar com URL fixa:
echo cloudflared.exe tunnel run netplay-server
echo.

echo ========================================
echo    OPCAO AUTOMATICA (SEM CONTA)
echo ========================================
echo.
echo Se nao quiser criar conta, posso tentar:
echo - Usar sempre o mesmo nome de tunnel
echo - Salvar a URL gerada em arquivo
echo - Reutilizar quando possivel
echo.

set /p opcao="Escolha: [1] Criar conta Cloudflare [2] Tentar automatico [3] Cancelar: "

if "%opcao%"=="1" (
    echo.
    echo [INFO] Abrindo pagina de cadastro...
    start https://dash.cloudflare.com/sign-up
    echo.
    echo Apos criar conta, execute:
    echo cloudflared.exe tunnel login
    pause
    goto :eof
)

if "%opcao%"=="2" (
    echo.
    echo [INFO] Tentando metodo automatico...
    goto :automatico
)

echo [INFO] Cancelado pelo usuario.
pause
goto :eof

:automatico
echo.
echo ========================================
echo    METODO AUTOMATICO - URL CONSISTENTE
echo ========================================
echo.

REM Verificar se servidor local esta rodando
echo [INFO] Verificando servidor local...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 5 | Out-Null; Write-Host '[OK] Servidor local rodando!' -ForegroundColor Green } catch { Write-Host '[ERRO] Servidor local nao esta rodando!' -ForegroundColor Red; Write-Host 'Execute primeiro: instalar-e-rodar.bat'; exit 1 }"

if errorlevel 1 (
    echo.
    echo [ERRO] Execute primeiro: instalar-e-rodar.bat
    pause
    goto :eof
)

REM Tentar usar nome fixo para gerar URL mais consistente
echo.
echo [INFO] Iniciando tunnel com nome consistente...
echo [INFO] Tentando manter URL similar...

REM Usar hostname fixo para tentar gerar URL similar
set TUNNEL_NAME=netplay-server-fixo

echo [INFO] Executando: cloudflared.exe tunnel --hostname %TUNNEL_NAME% --url http://localhost:8000
echo.

cloudflared.exe tunnel --hostname %TUNNEL_NAME% --url http://localhost:8000

if errorlevel 1 (
    echo.
    echo [AVISO] Metodo com hostname nao funcionou.
    echo [INFO] Tentando metodo padrao...
    echo.
    cloudflared.exe tunnel --url http://localhost:8000
)

echo.
echo [INFO] Tunnel finalizado.
pause