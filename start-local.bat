@echo off
chcp 65001 >nul
color 0B

echo.
echo ████████████████████████████████████████████████████████████████
echo █                    NETPLAY RPA SYSTEM                       █
echo █                  Servidor Local - Teste                     █
echo ████████████████████████████████████████████████████████████████
echo.

echo [INFO] Configurando servidor para acesso na rede Wi-Fi...
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

:: Instalar dependências se necessário
echo [INFO] Verificando dependências...
pip install -r requirements.txt >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Algumas dependências podem estar faltando
    echo [INFO] Tentando instalar dependências...
    pip install fastapi uvicorn python-dotenv requests httpx
)

:: Configurar Windows Firewall
echo [INFO] Configurando Windows Firewall...
netsh advfirewall firewall delete rule name="Netplay RPA Local" >nul 2>&1
netsh advfirewall firewall add rule name="Netplay RPA Local" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] Firewall configurado ✓
) else (
    echo [WARNING] Não foi possível configurar o firewall automaticamente
    echo Execute como administrador para configurar o firewall
)

:: Obter IP local
echo [INFO] Obtendo informações de rede...
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    set "ip=%%i"
    set "ip=!ip: =!"
    if not "!ip!"=="127.0.0.1" (
        if not "!ip!"=="" (
            set "LOCAL_IP=!ip!"
        )
    )
)

setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "192.168"') do (
    set "temp=%%i"
    set "temp=!temp: =!"
    if not "!temp!"=="" (
        set "LOCAL_IP=!temp!"
    )
)

echo.
echo ================================================
echo 🌐 INFORMAÇÕES DE ACESSO:
echo ================================================
echo.
echo 💻 No seu computador:
echo    http://localhost:8000/
echo.
if defined LOCAL_IP (
    echo 📱 Em outros dispositivos da rede Wi-Fi:
    echo    http://!LOCAL_IP!:8000/
    echo.
    echo 📋 Páginas disponíveis:
    echo    Painel Admin: http://!LOCAL_IP!:8000/
    echo    Painel Cliente: http://!LOCAL_IP!:8000/client
) else (
    echo [WARNING] Não foi possível detectar o IP local
    echo Use: ipconfig para ver seu IP manualmente
)
echo.
echo ================================================
echo 🔧 INSTRUÇÕES:
echo ================================================
echo.
echo 1. Conecte outros dispositivos na mesma rede Wi-Fi
echo 2. Use o IP mostrado acima nos outros dispositivos
echo 3. Mantenha este terminal aberto enquanto usar
echo 4. Pressione Ctrl+C para parar o servidor
echo.
echo [INFO] Iniciando servidor...
echo.

:: Iniciar servidor
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo [INFO] Servidor parado.
pause