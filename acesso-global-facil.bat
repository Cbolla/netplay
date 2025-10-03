@echo off
title Netplay - Acesso Global FACIL
color 0B

echo.
echo ========================================
echo    NETPLAY - ACESSO GLOBAL FACIL
echo ========================================
echo.

REM Verificar se o servidor esta rodando
echo [INFO] Verificando servidor local...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000' -TimeoutSec 5 | Out-Null; Write-Host '[OK] Servidor rodando em http://localhost:8000' } catch { Write-Host '[ERRO] Servidor nao esta rodando!'; Write-Host 'Execute primeiro: instalar-e-rodar.bat'; pause; exit 1 }"

echo.
echo ========================================
echo    BAIXANDO NGROK (GRATUITO)
echo ========================================
echo.

REM Baixar ngrok se nao existir
if not exist "ngrok.exe" (
    echo [INFO] Baixando ngrok...
    powershell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok.zip'"
    echo [INFO] Extraindo ngrok...
    powershell -Command "Expand-Archive -Path 'ngrok.zip' -DestinationPath '.' -Force"
    del ngrok.zip
    echo [OK] Ngrok instalado!
)

echo.
echo ========================================
echo    INICIANDO TUNNEL GLOBAL
echo ========================================
echo.
echo [INFO] Criando tunnel gratuito...
echo [INFO] Sua URL sera gerada automaticamente
echo [INFO] Para parar: Feche esta janela ou Ctrl+C
echo.

REM Iniciar ngrok
ngrok.exe http 8000

echo.
echo ========================================
echo    TUNNEL FINALIZADO
echo ========================================
echo.
pause