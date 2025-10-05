@echo off
title NETPLAY - TUNNEL TEMPORARIO
color 0E
echo.
echo ==========================================
echo   ⚡ NETPLAY - TUNNEL TEMPORARIO
echo ==========================================
echo.
echo 🔄 Gerando URL temporária aleatória...
echo.
echo [1/2] Iniciando servidor Python...

REM Inicia o servidor Python em background
start /B python main.py

REM Aguarda 3 segundos para o servidor inicializar
timeout /t 3 /nobreak >nul

echo ✅ Servidor iniciado na porta 8000
echo.
echo [2/2] Criando tunnel temporário...
echo ⏳ Aguarde a URL aparecer...
echo.
echo ==========================================
echo   🌍 TUNNEL TEMPORARIO ATIVO
echo ==========================================
echo.
echo 📍 Local: http://localhost:8000
echo 🔗 Global: (aguarde aparecer abaixo)
echo.
echo ⚠️  MANTENHA ESTA JANELA ABERTA!
echo ⚠️  Para PARAR: Feche esta janela ou Ctrl+C
echo ⚠️  URL muda a cada execução!
echo.

REM Inicia tunnel temporário (URL aleatória)
.\cloudflared.exe tunnel --url http://localhost:8000

echo.
echo ❌ Tunnel desconectado!
pause