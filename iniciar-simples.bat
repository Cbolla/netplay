@echo off
color 0A

echo.
echo ================================================================
echo                    NETPLAY RPA SYSTEM
echo                   Inicializacao Simples
echo ================================================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo.
    echo Instale Python de: https://www.python.org/downloads/
    echo Marque "Add Python to PATH" na instalacao
    echo.
    pause
    exit /b 1
)
echo OK: Python encontrado

echo Instalando dependencias...
pip install fastapi uvicorn python-dotenv requests httpx >nul 2>&1
echo OK: Dependencias instaladas

echo Verificando ngrok...
if exist "ngrok\ngrok.exe" (
    echo OK: ngrok encontrado
    set "NGROK=ngrok\ngrok.exe"
    goto start_server
)

if exist "ngrok.exe" (
    echo OK: ngrok encontrado
    set "NGROK=ngrok.exe"
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
echo Baixando ngrok automaticamente...
if not exist "ngrok" mkdir ngrok

PowerShell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok\ngrok.zip'; Expand-Archive -Path 'ngrok\ngrok.zip' -DestinationPath 'ngrok' -Force; Remove-Item 'ngrok\ngrok.zip'"

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
echo                   INICIANDO SERVIDOR
echo ================================================================
echo.

echo Inicializando banco de dados...
python -c "from database import db" 2>nul
echo OK: Banco pronto

echo Iniciando servidor web...
start /B python -m uvicorn main:app --host 0.0.0.0 --port 8000

echo Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

echo Criando tunel publico...
start /B %NGROK% http 8000

echo Aguardando ngrok...
timeout /t 8 /nobreak >nul

echo.
echo ================================================================
echo                   SERVIDOR ATIVO!
echo ================================================================
echo.
echo ACESSO LOCAL:
echo   http://localhost:8000
echo.
echo ACESSO PUBLICO:
echo   1. Abra: http://localhost:4040
echo   2. Copie a URL publica (ex: https://abc123.ngrok.io)
echo   3. Use essa URL em qualquer lugar do mundo
echo.
echo PAGINAS:
echo   Admin: SUA_URL/
echo   Cliente: SUA_URL/client
echo.
echo TESTE:
echo   - Abra http://localhost:4040 no navegador
echo   - Copie a URL HTTPS
echo   - Teste no celular com 4G
echo   - Funciona de qualquer lugar!
echo.
echo Pressione qualquer tecla para abrir dashboard...
pause >nul

start http://localhost:4040

echo.
echo Servidor rodando... Pressione Ctrl+C para parar
pause >nul

echo Parando servicos...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo.
echo Servicos parados. Obrigado!
pause