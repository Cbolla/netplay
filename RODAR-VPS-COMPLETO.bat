@echo off
title 🚀 NETPLAY VPS - SERVIDOR + CLOUDFLARE TUNNEL
color 0A

echo.
echo ==========================================
echo   🎮 NETPLAY VPS - INICIANDO TUDO
echo ==========================================
echo.

echo ✅ [1/2] Iniciando servidor Python...
echo    📍 Local: http://localhost:8000
echo.

REM Inicia o servidor Python em background
start /b python main.py

REM Aguarda o servidor iniciar
timeout /t 3 /nobreak >nul

echo ✅ [2/2] Iniciando Cloudflare Tunnel...
echo    🌍 Conectando ao Cloudflare...
echo    ⏳ Aguarde a URL aparecer abaixo...
echo.
echo ==========================================
echo   ✅ SERVIDOR RODANDO!
echo ==========================================
echo.
echo ⚠️  MANTENHA ESTA JANELA ABERTA!
echo ⚠️  Para PARAR: Feche esta janela ou Ctrl+C
echo ==========================================
echo.

REM Executa o tunnel temporário (não precisa de login)
.\cloudflared.exe tunnel --url http://localhost:8000 --no-autoupdate

echo.
echo [INFO] Tunnel encerrado.
pause
