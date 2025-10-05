@echo off
title CLOUDFLARE TUNNEL - NETPLAY VPS
color 0A
echo.
echo ========================================
echo    CLOUDFLARE TUNNEL - NETPLAY VPS
echo ========================================
echo.
echo [INFO] Iniciando Cloudflare Tunnel...
echo [INFO] Aguarde o link publico aparecer...
echo.
echo ----------------------------------------
echo  MANTENHA ESTA JANELA ABERTA!
echo ----------------------------------------
echo.

REM Verifica se o cloudflared.exe existe
if not exist "cloudflared.exe" (
    echo [ERRO] cloudflared.exe nao encontrado!
    echo [INFO] Baixando cloudflared.exe...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe' -UseBasicParsing"
    echo [OK] Download concluido!
    echo.
)

REM Executa o tunnel fixo
echo [INFO] Conectando ao Cloudflare...
echo [INFO] Usando seu dominio fixo: https://servidormigrarcliente.io
echo.
echo ========================================
.\cloudflared.exe tunnel --config config.yml run

echo.
echo [INFO] Tunnel encerrado.
pause