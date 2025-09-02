@echo off
color 0A

echo.
echo ================================================================
echo           NETPLAY RPA - ACESSO GLOBAL SIMPLES
echo ================================================================
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Instale Python de: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK: Python encontrado

REM Instalar dependencias
echo Instalando dependencias...
pip install fastapi uvicorn python-dotenv requests >nul 2>&1
echo OK: Dependencias instaladas

REM Verificar ngrok
echo Verificando ngrok...
if exist "ngrok.exe" (
    echo OK: ngrok encontrado
    set "NGROK=ngrok.exe"
    goto start_server
)

if exist "ngrok\ngrok.exe" (
    echo OK: ngrok encontrado
    set "NGROK=ngrok\ngrok.exe"
    goto start_server
)

ngrok version >nul 2>&1
if %errorLevel% equ 0 (
    echo OK: ngrok do sistema encontrado
    set "NGROK=ngrok"
    goto start_server
)

echo AVISO: ngrok nao encontrado
echo.
echo Baixando ngrok...
if not exist "ngrok" mkdir ngrok

PowerShell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok.zip'; Expand-Archive -Path 'ngrok.zip' -DestinationPath 'ngrok' -Force; Remove-Item 'ngrok.zip'"

if exist "ngrok\ngrok.exe" (
    echo OK: ngrok instalado
    set "NGROK=ngrok\ngrok.exe"
) else (
    echo ERRO: Falha ao instalar ngrok
    echo.
    echo Instalacao manual:
    echo 1. Acesse: https://ngrok.com/download
    echo 2. Baixe Windows 64-bit
    echo 3. Extraia ngrok.exe nesta pasta
    echo.
    pause
    exit /b 1
)

:start_server
echo.
echo ================================================================
echo                   INICIANDO SERVIDOR GLOBAL
echo ================================================================
echo.

echo Inicializando banco...
python -c "from database import db" 2>nul
echo OK: Banco pronto

echo Iniciando servidor...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000

echo Aguardando servidor...
timeout /t 5 /nobreak >nul

echo Criando tunel publico...
start /B %NGROK% http 8000

echo Aguardando ngrok...
timeout /t 8 /nobreak >nul

echo.
echo ================================================================
echo                   SERVIDOR GLOBAL ATIVO!
echo ================================================================
echo.
echo COMO ACESSAR DE QUALQUER LUGAR:
echo.
echo 1. Abra no navegador: http://localhost:4040
echo 2. Copie a URL HTTPS (ex: https://abc123.ngrok.io)
echo 3. Use essa URL em qualquer lugar do mundo!
echo.
echo PAGINAS:
echo   Revendedor: SUA_URL/
echo   Admin: SUA_URL/admin
echo   Cliente: SUA_URL/client
echo.
echo LOGIN ADMIN:
echo   Usuario: futuro.noob@gmail.com
echo   Senha: Psw141611@@
echo.
echo TESTE:
echo   - Celular com 4G: Funciona!
echo   - Outro computador: Funciona!
echo   - Qualquer lugar: Funciona!
echo.
echo Pressione ENTER para abrir dashboard...
pause >nul

start http://localhost:4040

echo.
echo Dashboard aberto!
echo Copie a URL HTTPS de la e use em qualquer lugar.
echo.
echo Servidor rodando... Feche esta janela para parar.
pause >nul

echo Parando servicos...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo Servicos parados!
pause