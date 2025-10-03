@echo off
title Netplay - SERVIDOR + ACESSO GLOBAL
color 0A

echo.
echo ========================================
echo    NETPLAY - COMPLETO (LOCAL + GLOBAL)
echo ========================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.8+ primeiro
    pause
    exit /b 1
)

REM Criar ambiente virtual se nao existir
if not exist "venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual
echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo [INFO] Instalando dependencias...
pip install -r requirements.txt

REM Criar arquivo .env se nao existir
if not exist ".env" (
    echo [INFO] Criando arquivo de configuracao...
    copy .env.production .env
    echo.
    echo ========================================
    echo    CONFIGURE SUAS CREDENCIAIS
    echo ========================================
    echo.
    echo Abra o arquivo .env e configure:
    echo - NETPLAY_USERNAME=seu_usuario@netplay.com
    echo - NETPLAY_PASSWORD=sua_senha
    echo.
    echo Pressione qualquer tecla apos configurar...
    pause
)

REM Inicializar banco de dados
echo [INFO] Inicializando banco de dados...
python database.py

REM Baixar cloudflared se nao existir
if not exist "cloudflared.exe" (
    echo [INFO] Baixando Cloudflare Tunnel...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
)

echo.
echo ========================================
echo    INICIANDO SERVIDOR LOCAL
echo ========================================
echo.

REM Iniciar servidor em background
start /B python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM Aguardar servidor iniciar
echo [INFO] Aguardando servidor iniciar...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    INICIANDO ACESSO GLOBAL
echo ========================================
echo.
echo Tentando usar: https://midwest-thursday-seminar-mountain.trycloudflare.com
echo.

REM Iniciar tunnel
cloudflared.exe tunnel --url http://localhost:8000 --name midwest-thursday-seminar-mountain

echo.
echo ========================================
echo    SISTEMA FINALIZADO
echo ========================================
echo.
pause