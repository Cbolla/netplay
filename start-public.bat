@echo off
chcp 65001 >nul
color 0E

echo.
echo ████████████████████████████████████████████████████████████████
echo █                    NETPLAY RPA SYSTEM                       █
echo █                   Acesso Público (Internet)                 █
echo ████████████████████████████████████████████████████████████████
echo.

echo [INFO] Configurando acesso público via ngrok...
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python não encontrado!
    echo.
    echo Por favor, instale Python 3.8+ primeiro:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Python encontrado ✓

:: Verificar se ngrok está instalado
ngrok version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] ngrok não encontrado!
    echo [INFO] Tentando instalar automaticamente...
    echo.
    
    :: Tentar usar ngrok local se existir
    if exist "ngrok\ngrok.exe" (
        echo [SUCCESS] Encontrado ngrok local ✓
        set "NGROK_CMD=ngrok\ngrok.exe"
    ) else if exist "ngrok.exe" (
        echo [SUCCESS] Encontrado ngrok.exe ✓
        set "NGROK_CMD=ngrok.exe"
    ) else (
        echo [INFO] Executando instalação automática...
        PowerShell -ExecutionPolicy Bypass -File "install-ngrok.ps1"
        
        :: Verificar se instalação foi bem-sucedida
        if exist "ngrok\ngrok.exe" (
            echo [SUCCESS] ngrok instalado automaticamente ✓
            set "NGROK_CMD=ngrok\ngrok.exe"
        ) else (
            echo [ERROR] Falha na instalação automática!
            echo.
            echo 📋 Instalação manual:
            echo 1. Acesse: https://ngrok.com/download
            echo 2. Baixe "Windows (64-bit)"
            echo 3. Extraia ngrok.exe nesta pasta
            echo 4. Execute este script novamente
            echo.
            pause
            exit /b 1
        )
    )
) else (
    set "NGROK_CMD=ngrok"
)

echo [SUCCESS] ngrok encontrado ✓

:: Verificar autenticação ngrok
echo [INFO] Verificando autenticação ngrok...
ngrok config check >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] ngrok pode não estar autenticado!
    echo.
    echo Para melhor experiência:
    echo 1. Acesse: https://ngrok.com/signup
    echo 2. Crie conta gratuita
    echo 3. Execute: ngrok config add-authtoken SEU_TOKEN
    echo.
    echo Pressione qualquer tecla para continuar...
    pause >nul
)

:: Instalar dependências Python
echo [INFO] Verificando dependências Python...
pip install -r requirements.txt >nul 2>&1

echo.
echo ================================================
echo 🚀 INICIANDO SERVIDOR PÚBLICO
echo ================================================
echo.

echo [INFO] Iniciando servidor FastAPI...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000

:: Aguardar servidor inicializar
echo [INFO] Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

echo [INFO] Criando túnel público com ngrok...
echo.
echo ⏳ Aguarde alguns segundos para obter a URL pública...
echo.

:: Iniciar ngrok
start /B %NGROK_CMD% http 8000

:: Aguardar ngrok inicializar
timeout /t 8 /nobreak >nul

:: Tentar obter URL pública
echo [INFO] Obtendo URL pública...
for /f "tokens=*" %%i in ('curl -s http://localhost:4040/api/tunnels 2^>nul ^| findstr "public_url"') do (
    set "ngrok_response=%%i"
)

echo.
echo ================================================
echo 🌍 SERVIDOR PÚBLICO ATIVO!
echo ================================================
echo.
echo 🌐 Acesse de qualquer lugar do mundo:
echo    Verifique a interface do ngrok em: http://localhost:4040
echo.
echo 📋 Como encontrar sua URL:
echo    1. Abra: http://localhost:4040
echo    2. Copie a URL que aparece (ex: https://abc123.ngrok.io)
echo    3. Use essa URL em qualquer dispositivo
echo.
echo 📱 Páginas disponíveis:
echo    Painel Admin: SUA_URL/
echo    Painel Cliente: SUA_URL/client
echo.
echo ⚠️  IMPORTANTE:
echo    - Esta URL é temporária
echo    - Válida apenas enquanto este script estiver rodando
echo    - Para produção, use VPS real
echo.
echo 🔧 Controles:
echo    - Pressione Ctrl+C para parar
echo    - Mantenha este terminal aberto
echo.

echo Servidor rodando... Pressione Ctrl+C para parar
pause >nul

echo.
echo [INFO] Parando serviços...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo [SUCCESS] Serviços parados.
pause