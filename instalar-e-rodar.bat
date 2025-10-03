@echo off
title Netplay - Instalacao e Execucao Automatica
color 0A

echo.
echo ========================================
echo    NETPLAY - INSTALACAO AUTOMATICA
echo ========================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.8+ primeiro
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado!

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

REM Configurar firewall
echo [INFO] Configurando firewall...
netsh advfirewall firewall add rule name="Netplay Server" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1

echo.
echo ========================================
echo    SERVIDOR INICIANDO...
echo ========================================
echo.
echo Acesse: http://localhost:8000
echo Para parar: Feche esta janela ou Ctrl+C
echo.

REM Iniciar servidor
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause