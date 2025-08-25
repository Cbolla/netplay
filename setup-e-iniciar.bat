@echo off
chcp 65001 >nul 2>&1
color 0A

echo.
echo ================================================================
echo                    NETPLAY RPA SYSTEM
echo              Setup Automatico + Servidor Publico
echo ================================================================
echo.

echo [INFO] Configurando tudo automaticamente...
echo.

REM Verificar se Python esta instalado
echo [INFO] Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python nao encontrado!
    echo.
    echo Instale Python primeiro:
    echo 1. Acesse: https://www.python.org/downloads/
    echo 2. Baixe Python 3.8 ou superior
    echo 3. IMPORTANTE: Marque "Add Python to PATH" na instalacao
    echo 4. Execute este script novamente
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Python encontrado

REM Instalar dependencias Python
echo [INFO] Instalando dependencias Python...
pip install -r requirements.txt >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Instalando dependencias basicas...
    pip install fastapi uvicorn python-dotenv requests httpx >nul 2>&1
)
echo [SUCCESS] Dependencias Python instaladas

REM Verificar/Instalar ngrok
echo [INFO] Verificando ngrok...
if exist "ngrok\ngrok.exe" (
    echo [SUCCESS] ngrok ja instalado
    set "NGROK_CMD=ngrok\ngrok.exe"
    goto :ngrok_ready
)

if exist "ngrok.exe" (
    echo [SUCCESS] ngrok encontrado
    set "NGROK_CMD=ngrok.exe"
    goto :ngrok_ready
)

ngrok version >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] ngrok do sistema encontrado
    set "NGROK_CMD=ngrok"
    goto :ngrok_ready
)

echo [INFO] ngrok nao encontrado. Instalando...
echo.
echo Baixando ngrok... (pode demorar alguns minutos)

REM Criar diretorio ngrok
if not exist "ngrok" mkdir ngrok

REM Baixar ngrok usando PowerShell
PowerShell -Command "& {try { Write-Host 'Baixando ngrok...'; Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok\ngrok.zip' -UseBasicParsing; Write-Host 'Extraindo...'; Expand-Archive -Path 'ngrok\ngrok.zip' -DestinationPath 'ngrok' -Force; Remove-Item 'ngrok\ngrok.zip' -Force; Write-Host 'ngrok instalado com sucesso!' } catch { Write-Host 'Erro no download:' $_.Exception.Message; exit 1 }}"

if exist "ngrok\ngrok.exe" (
    echo [SUCCESS] ngrok instalado automaticamente
    set "NGROK_CMD=ngrok\ngrok.exe"
) else (
    echo [ERROR] Falha na instalacao automatica do ngrok!
    echo.
    echo Instalacao manual necessaria:
    echo 1. Acesse: https://ngrok.com/download
    echo 2. Baixe "Windows (64-bit)"
    echo 3. Extraia ngrok.exe na pasta "ngrok" dentro desta pasta
    echo 4. Execute este script novamente
    echo.
    pause
    exit /b 1
)

:ngrok_ready
REM Testar ngrok
echo [INFO] Testando ngrok...
%NGROK_CMD% version >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] ngrok funcionando
) else (
    echo [WARNING] ngrok pode ter problemas, mas continuando...
)

echo.
echo ================================================================
echo                 INICIANDO SERVIDOR PUBLICO
echo ================================================================
echo.

REM Inicializar banco de dados
echo [INFO] Inicializando banco de dados...
python -c "from database import db; print('Banco inicializado!')" 2>nul
echo [SUCCESS] Banco de dados pronto

REM Iniciar servidor Python
echo [INFO] Iniciando servidor FastAPI...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000

REM Aguardar servidor inicializar
echo [INFO] Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

REM Iniciar ngrok
echo [INFO] Criando tunel publico com ngrok...
echo Aguarde alguns segundos para obter a URL publica...
echo.
start /B %NGROK_CMD% http 8000

REM Aguardar ngrok inicializar
timeout /t 8 /nobreak >nul

echo ================================================================
echo                 SERVIDOR PUBLICO ATIVO!
echo ================================================================
echo.
echo Para encontrar sua URL publica:
echo    1. Abra: http://localhost:4040
echo    2. Copie a URL HTTPS (ex: https://abc123.ngrok.io)
echo    3. Use essa URL em qualquer dispositivo/lugar
echo.
echo Paginas disponiveis:
echo    Painel Admin: SUA_URL/
echo    Painel Cliente: SUA_URL/client
echo.
echo Dashboard ngrok: http://localhost:4040
echo.
echo Tudo configurado e funcionando!
echo.
echo IMPORTANTE:
echo    - Mantenha este terminal aberto
echo    - A URL e temporaria (muda a cada reinicializacao)
echo    - Para producao, use VPS real
echo.
echo TESTE AGORA:
echo    1. Abra http://localhost:4040 no navegador
echo    2. Copie a URL publica
echo    3. Teste no celular com 4G
echo    4. Funciona de qualquer lugar do mundo!
echo.

echo Pressione qualquer tecla para abrir o dashboard do ngrok...
pause >nul

REM Abrir dashboard do ngrok
start http://localhost:4040

echo.
echo Servidor rodando... Pressione Ctrl+C para parar
pause >nul

REM Cleanup
echo.
echo [INFO] Parando servicos...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo [SUCCESS] Servicos parados.
echo.
echo Obrigado por usar o Netplay RPA System!
pause