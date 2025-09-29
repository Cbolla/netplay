@echo off
chcp 65001 >nul
title Netplay RPA - Acesso Público Mundial

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                🌍 NETPLAY RPA - ACESSO PÚBLICO               ║
echo ║              Permitindo acesso mundial para a turma         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🚀 Iniciando servidor local...
echo.

REM Verificar se o servidor já está rodando
netstat -an | find "8000" >nul
if %errorlevel% == 0 (
    echo ✅ Servidor já está rodando na porta 8000
) else (
    echo 📡 Iniciando servidor netplay...
    start /min "Netplay Server" cmd /c "netplay-server.exe"
    timeout /t 5 /nobreak >nul
)

echo.
echo 🌐 Criando túnel público com Cloudflare...
echo.
echo ⏳ Aguarde alguns segundos para o túnel ser criado...
echo.

REM Criar túnel público
cloudflared.exe tunnel --url http://localhost:8000

echo.
echo 🛑 Túnel público encerrado.
echo 📝 Para usar novamente, execute este arquivo.
echo.
pause