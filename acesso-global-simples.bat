@echo off
title Netplay - Acesso Global GRATUITO (Cloudflare)
color 0B

echo.
echo ========================================
echo    NETPLAY - ACESSO GLOBAL GRATUITO
echo ========================================
echo.

REM Verificar se o servidor esta rodando
echo [INFO] Verificando servidor local...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000' -TimeoutSec 5 | Out-Null; Write-Host '[OK] Servidor rodando!' } catch { Write-Host '[ERRO] Servidor nao esta rodando! Execute primeiro: instalar-e-rodar.bat'; pause; exit 1 }"

echo.
echo ========================================
echo    OPCOES DE ACESSO GLOBAL
echo ========================================
echo.
echo 1. Cloudflare Tunnel (Recomendado)
echo 2. Usar serveo.net (Alternativo)
echo 3. Usar localhost.run (Alternativo)
echo.
set /p opcao="Escolha uma opcao (1-3): "

if "%opcao%"=="1" goto cloudflare
if "%opcao%"=="2" goto serveo
if "%opcao%"=="3" goto localhostrun

:cloudflare
echo.
echo [INFO] Tentando Cloudflare Tunnel...
echo.
echo Se o Windows Defender bloquear, permita o acesso!
echo.
cloudflared.exe tunnel --url http://localhost:8000
goto fim

:serveo
echo.
echo [INFO] Usando serveo.net...
echo [INFO] Baixando cliente SSH...
powershell -Command "if (!(Test-Path 'plink.exe')) { Invoke-WebRequest -Uri 'https://the.earth.li/~sgtatham/putty/latest/w64/plink.exe' -OutFile 'plink.exe' }"
echo.
echo URL sera: https://netplay.serveo.net
echo.
plink.exe -ssh -R netplay.serveo.net:80:localhost:8000 serveo.net
goto fim

:localhostrun
echo.
echo [INFO] Usando localhost.run...
echo [INFO] Baixando cliente SSH...
powershell -Command "if (!(Test-Path 'plink.exe')) { Invoke-WebRequest -Uri 'https://the.earth.li/~sgtatham/putty/latest/w64/plink.exe' -OutFile 'plink.exe' }"
echo.
echo Conectando...
plink.exe -ssh -R 80:localhost:8000 localhost.run
goto fim

:fim
echo.
echo ========================================
echo    TUNNEL FINALIZADO
echo ========================================
echo.
pause