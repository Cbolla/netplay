@echo off
chcp 65001 >nul 2>&1
color 0A

echo.
echo ================================================================
echo           NETPLAY RPA - ACESSO GLOBAL DE QUALQUER LUGAR
echo ================================================================
echo.

echo [INFO] Configurando acesso publico global...
echo.

REM Verificar Python
echo [INFO] Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python nao encontrado!
    echo Instale Python de: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [SUCCESS] Python encontrado

REM Instalar dependencias
echo [INFO] Instalando dependencias...
pip install fastapi uvicorn python-dotenv requests httpx >nul 2>&1
echo [SUCCESS] Dependencias instaladas

REM Verificar ngrok
echo [INFO] Verificando ngrok...
if exist "ngrok\ngrok.exe" (
    echo [SUCCESS] ngrok encontrado
    set "NGROK_CMD=ngrok\ngrok.exe"
    goto ngrok_ready
)

if exist "ngrok.exe" (
    echo [SUCCESS] ngrok encontrado
    set "NGROK_CMD=ngrok.exe"
    goto ngrok_ready
)

ngrok version >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] ngrok do sistema encontrado
    set "NGROK_CMD=ngrok"
    goto ngrok_ready
)

echo [INFO] ngrok nao encontrado. Instalando...
if not exist "ngrok" mkdir ngrok

echo Baixando ngrok...
PowerShell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok\ngrok.zip'; Expand-Archive -Path 'ngrok\ngrok.zip' -DestinationPath 'ngrok' -Force; Remove-Item 'ngrok\ngrok.zip'"

if exist "ngrok\ngrok.exe" (
    echo [SUCCESS] ngrok instalado
    set "NGROK_CMD=ngrok\ngrok.exe"
) else (
    echo [ERROR] Falha ao instalar ngrok
    echo.
    echo Instalacao manual:
    echo 1. Acesse: https://ngrok.com/download
    echo 2. Baixe Windows 64-bit
    echo 3. Extraia ngrok.exe nesta pasta
    echo.
    pause
    exit /b 1
)

:ngrok_ready
echo [INFO] Testando ngrok...
%NGROK_CMD% version >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] ngrok funcionando
) else (
    echo [WARNING] ngrok pode ter problemas
)

echo.
echo ================================================================
echo              INICIANDO SERVIDOR GLOBAL
echo ================================================================
echo.

REM Inicializar banco
echo [INFO] Inicializando banco de dados...
python -c "from database import db" 2>nul
echo [SUCCESS] Banco pronto

REM Iniciar servidor
echo [INFO] Iniciando servidor FastAPI...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000

echo [INFO] Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

REM Iniciar ngrok
echo [INFO] Criando tunel publico...
start /B %NGROK_CMD% http 8000

echo [INFO] Aguardando ngrok...
timeout /t 8 /nobreak >nul

echo.
echo ================================================================
echo                 SERVIDOR GLOBAL ATIVO!
echo ================================================================
echo.
echo Para encontrar sua URL publica:
echo   1. Abra: http://localhost:4040
echo   2. Copie a URL HTTPS (ex: https://abc123.ngrok.io)
echo   3. Use essa URL em qualquer lugar do mundo
echo.
echo PAGINAS DISPONIVEIS:
echo   Painel Revendedor: SUA_URL/
echo   Painel Admin: SUA_URL/admin
echo   Painel Cliente: SUA_URL/client
echo.
echo CREDENCIAIS ADMIN:
echo   Usuario: futuro.noob@gmail.com
echo   Senha: Psw141611@@
echo.
echo ACESSO LOCAL:
echo   http://localhost:8000
echo   http://localhost:8000/admin
echo.
echo DASHBOARD NGROK:
echo   http://localhost:4040
echo.
echo ================================================================
echo                    TESTE AGORA!
echo ================================================================
echo.
echo 1. Abra http://localhost:4040 no navegador
echo 2. Copie a URL HTTPS mostrada
echo 3. Teste no celular com 4G
echo 4. Funciona de qualquer lugar do mundo!
echo.
echo IMPORTANTE:
echo   - Mantenha este terminal aberto
echo   - A URL e temporaria (muda a cada reinicializacao)
echo   - Para URL fixa, crie conta no ngrok.com
echo.
echo Pressione qualquer tecla para abrir dashboard...
pause >nul

start http://localhost:4040

echo.
echo Dashboard aberto! Copie a URL publica de la.
echo.
echo Servidor rodando globalmente...
echo Pressione Ctrl+C para parar ou feche esta janela
pause >nul

REM Cleanup
echo.
echo [INFO] Parando servicos...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo [SUCCESS] Servicos parados.
echo Obrigado!
pause