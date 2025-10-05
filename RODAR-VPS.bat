@echo off
title 🚀 NETPLAY - SUPER SIMPLES
color 0A

echo.
echo ==========================================
echo   🎮 NETPLAY - INSTALACAO AUTOMATICA
echo ==========================================
echo.

echo ⏳ [1/3] Instalando dependencias Python...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

echo ✅ [2/3] Configurando ambiente...
if not exist .env (
    copy .env.example .env >nul
    echo    📝 Arquivo .env criado automaticamente
)

echo ✅ [3/3] Iniciando servidor...
echo.
echo ==========================================
echo   🎯 SERVIDOR RODANDO COM SUCESSO!
echo ==========================================
echo.
echo 📍 Local:  http://localhost:8000
echo 🌍 Global: Execute 'cloudflared.exe tunnel --url http://localhost:8000' em outro terminal
echo.
echo ⚠️  Para PARAR: Feche esta janela ou Ctrl+C
echo ==========================================
echo.

python main.py