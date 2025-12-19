@echo off
title 🚀 NETPLAY VPS - SERVIDOR + CLOUDFLARE TUNNEL
color 0A

echo.
echo ==========================================
echo   🎮 NETPLAY VPS - INICIANDO TUDO
echo ==========================================
echo.

echo ⏳ [1/4] Instalando dependencias Python...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

echo ✅ [2/4] Configurando ambiente...
if not exist .env (
    copy .env.example .env >nul 2>&1
    echo    📝 Arquivo .env criado automaticamente
)

echo ✅ [3/4] Iniciando servidor Python...
echo    📍 Local: http://localhost:8000
echo.

REM Inicia o servidor Python em background
start /b python main.py

REM Aguarda o servidor iniciar
timeout /t 3 /nobreak >nul

echo ✅ [4/4] Iniciando Cloudflare Tunnel...
echo    🌍 Conectando ao Cloudflare...
echo    🔗 URL: https://servidormigrarcliente.io
echo.
echo ==========================================
echo   ✅ TUDO RODANDO COM SUCESSO!
echo ==========================================
echo.
echo ⚠️  MANTENHA ESTA JANELA ABERTA!
echo ⚠️  Para PARAR: Feche esta janela ou Ctrl+C
echo ==========================================
echo.

REM Executa o tunnel fixo (isso mantém a janela aberta)
.\cloudflared.exe tunnel --config config.yml run

echo.
echo [INFO] Tunnel encerrado.
pause
