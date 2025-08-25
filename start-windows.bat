@echo off
chcp 65001 >nul
color 0A

echo.
echo ████████████████████████████████████████████████████████████████
echo █                    NETPLAY RPA SYSTEM                       █
echo █                   Deploy para Windows                       █
echo ████████████████████████████████████████████████████████████████
echo.

echo [INFO] Verificando privilégios de administrador...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [SUCCESS] Executando como administrador ✓
) else (
    echo [ERROR] Este script precisa ser executado como administrador!
    echo.
    echo Como executar como administrador:
    echo 1. Clique com botão direito no arquivo start-windows.bat
    echo 2. Selecione "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Iniciando deploy automatizado...
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python não encontrado!
    echo.
    echo Por favor, instale Python 3.8+ primeiro:
    echo https://www.python.org/downloads/
    echo.
    echo Certifique-se de marcar "Add Python to PATH" durante a instalação
    pause
    exit /b 1
)

echo [SUCCESS] Python encontrado ✓

:: Executar script PowerShell
echo [INFO] Executando script de deploy...
echo.
PowerShell -ExecutionPolicy Bypass -File "%~dp0deploy-windows.ps1"

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Falha no deploy!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Deploy concluído!
pause