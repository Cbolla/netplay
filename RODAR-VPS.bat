@echo off
title 🚀 NETPLAY - SUPER SIMPLES
color 0A

echo.
echo ==========================================
echo   🎮 NETPLAY - INSTALACAO AUTOMATICA
echo ==========================================
echo.

echo ⏳ [1/4] Instalando dependencias Python...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

echo ✅ [2/4] Configurando ambiente...
if not exist .env (
    copy .env.example .env >nul
    echo    📝 Arquivo .env criado automaticamente
)

echo ✅ [3/4] Configurando Cloudflare Tunnel...
REM Ler configuração do tunnel
set MODO_TUNNEL=TEMPORARIO
set TUNNEL_NAME=
set TUNNEL_HOSTNAME=

if exist tunnel-config.txt (
    for /f "tokens=1,2 delims==" %%a in ('findstr /v "^#" tunnel-config.txt') do (
        if "%%a"=="MODO_TUNNEL" set MODO_TUNNEL=%%b
        if "%%a"=="TUNNEL_NAME" set TUNNEL_NAME=%%b
        if "%%a"=="TUNNEL_HOSTNAME" set TUNNEL_HOSTNAME=%%b
    )
)

echo ✅ [4/4] Iniciando servidor e tunnel...
echo.
echo ==========================================
echo   🎯 SERVIDOR RODANDO COM SUCESSO!
echo ==========================================
echo.
echo 📍 Local:  http://localhost:8000

REM Inicia o servidor Python em background
start /b python main.py

REM Aguarda o servidor iniciar
timeout /t 3 /nobreak >nul

REM Inicia o tunnel baseado na configuração
if "%MODO_TUNNEL%"=="NOMEADO" (
    echo 🌍 Global: Usando tunnel fixo '%TUNNEL_NAME%'...
    if not "%TUNNEL_HOSTNAME%"=="" (
        echo 🔗 URL:    https://%TUNNEL_HOSTNAME%
    )
    cloudflared.exe tunnel --config config.yml run
) else (
    echo 🌍 Global: Criando tunnel temporário...
    cloudflared.exe tunnel --url http://localhost:8000 --no-autoupdate
)

echo.
echo ⚠️  Para PARAR: Feche esta janela ou Ctrl+C
echo ==========================================