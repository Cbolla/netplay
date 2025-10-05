@echo off
title NETPLAY - TUNNEL FIXO
color 0A
echo.
echo ==========================================
echo   🚀 NETPLAY - TUNNEL FIXO
echo ==========================================
echo.
echo 🔗 URL: https://servidormigrarcliente.io
echo.
echo [1/2] Iniciando servidor Python...

REM Inicia o servidor Python em background
start /B python main.py

REM Aguarda 3 segundos para o servidor inicializar
timeout /t 3 /nobreak >nul

echo ✅ Servidor iniciado na porta 8000
echo.
echo [2/2] Conectando tunnel fixo...
echo.
echo ==========================================
echo   🌍 TUNNEL FIXO ATIVO
echo ==========================================
echo.
echo 🔗 Acesse: https://servidormigrarcliente.io
echo 📍 Local:  http://localhost:8000
echo.
echo ⚠️  MANTENHA ESTA JANELA ABERTA!
echo ⚠️  Para PARAR: Feche esta janela ou Ctrl+C
echo.

REM Inicia o tunnel fixo usando config.yml
.\cloudflared.exe tunnel --config config.yml run

echo.
echo ❌ Tunnel desconectado!
pause