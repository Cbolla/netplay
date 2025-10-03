@echo off
chcp 65001 >nul
title Cloudflare Tunnel - URL Salva e Reutiliza

echo.
echo ========================================
echo    CLOUDFLARE - URL SALVA E REUTILIZA
echo ========================================
echo.

REM Arquivo para salvar a URL
set URL_FILE=cloudflare-url-salva.txt

REM Verificar se servidor local esta rodando
echo [INFO] Verificando servidor local...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 5 | Out-Null; Write-Host '[OK] Servidor local rodando!' -ForegroundColor Green } catch { Write-Host '[ERRO] Servidor local nao esta rodando!' -ForegroundColor Red; exit 1 }"

if errorlevel 1 (
    echo.
    echo [ERRO] Execute primeiro: instalar-e-rodar.bat
    pause
    goto :eof
)

REM Verificar se ja existe URL salva
if exist "%URL_FILE%" (
    echo.
    echo [INFO] URL anterior encontrada:
    type "%URL_FILE%"
    echo.
    set /p usar_anterior="Usar URL anterior? [S/n]: "
    if /i not "%usar_anterior%"=="n" (
        echo [INFO] Tentando reutilizar URL anterior...
        goto :reutilizar
    )
)

echo.
echo [INFO] Gerando nova URL...
echo [INFO] A URL sera salva em: %URL_FILE%
echo.

REM Executar cloudflared e capturar a URL
echo [INFO] Iniciando Cloudflare Tunnel...
echo [INFO] Aguarde a URL aparecer...
echo.

REM Criar arquivo temporario para capturar output
set TEMP_LOG=cloudflare-temp.log

REM Executar cloudflared em background e capturar output
start /b cmd /c "cloudflared.exe tunnel --url http://localhost:8000 > %TEMP_LOG% 2>&1"

REM Aguardar URL aparecer no log
echo [INFO] Aguardando URL ser gerada...
:wait_url
timeout /t 2 /nobreak >nul
if not exist "%TEMP_LOG%" goto :wait_url

REM Procurar pela URL no log
findstr /c:"trycloudflare.com" "%TEMP_LOG%" >nul
if errorlevel 1 goto :wait_url

REM Extrair e salvar a URL
for /f "tokens=*" %%i in ('findstr /c:"trycloudflare.com" "%TEMP_LOG%"') do (
    echo %%i | findstr /r "https://.*\.trycloudflare\.com" > "%URL_FILE%"
)

if exist "%URL_FILE%" (
    echo.
    echo ========================================
    echo    URL GERADA E SALVA!
    echo ========================================
    echo.
    echo Sua URL fixa:
    type "%URL_FILE%"
    echo.
    echo Salva em: %URL_FILE%
    echo Na proxima vez, sera reutilizada!
    echo.
) else (
    echo [ERRO] Nao foi possivel extrair a URL.
)

REM Manter tunnel rodando
echo [INFO] Tunnel rodando... Pressione Ctrl+C para parar.
type nul > nul
goto :eof

:reutilizar
echo [INFO] Tentando reutilizar URL salva...
set /p SAVED_URL=<"%URL_FILE%"
echo [INFO] URL: %SAVED_URL%
echo.

REM Tentar usar URL especifica (isso pode nao funcionar com quick tunnels)
echo [INFO] Iniciando tunnel...
cloudflared.exe tunnel --url http://localhost:8000

echo.
echo [INFO] Tunnel finalizado.
pause