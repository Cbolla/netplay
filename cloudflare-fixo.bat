@echo off
title Netplay - Cloudflare Tunnel FIXO
color 0B

echo.
echo ========================================
echo    CLOUDFLARE TUNNEL - URL FIXA
echo ========================================
echo.

REM Verificar se o servidor esta rodando
echo [INFO] Verificando servidor local...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000' -TimeoutSec 5 | Out-Null; Write-Host '[OK] Servidor rodando!' } catch { Write-Host '[ERRO] Servidor nao esta rodando! Execute primeiro: instalar-e-rodar.bat'; pause; exit 1 }"

echo.
echo ========================================
echo    RESOLVENDO WINDOWS DEFENDER
echo ========================================
echo.

REM Verificar se cloudflared existe
if not exist "cloudflared.exe" (
    echo [ERRO] cloudflared.exe nao encontrado!
    echo Execute primeiro: rodar-completo.bat
    pause
    exit /b 1
)

echo [INFO] Tentando adicionar excecao no Windows Defender...
echo [INFO] Se pedir permissao de administrador, clique em SIM
echo.

REM Tentar adicionar exceção (pode falhar se não for admin)
powershell -Command "try { Add-MpPreference -ExclusionPath '%CD%\cloudflared.exe'; Write-Host '[OK] Excecao adicionada!' } catch { Write-Host '[AVISO] Execute como Administrador para melhor resultado' }" 2>nul

echo.
echo ========================================
echo    INICIANDO CLOUDFLARE TUNNEL
echo ========================================
echo.
echo [INFO] Tentando manter URL fixa...
echo [INFO] URL desejada: https://midwest-thursday-seminar-mountain.trycloudflare.com
echo.
echo Se o Windows Defender bloquear:
echo 1. Clique em "Mais informacoes"
echo 2. Clique em "Executar mesmo assim"
echo 3. Ou va em Windows Security e adicione excecao
echo.

REM Tentar diferentes métodos para executar
echo [INFO] Metodo 1: Execucao direta...
cloudflared.exe tunnel --url http://localhost:8000 --name midwest-thursday-seminar-mountain 2>nul
if errorlevel 1 (
    echo [INFO] Metodo 2: Execucao via PowerShell...
    powershell -Command "& '.\cloudflared.exe' tunnel --url http://localhost:8000 --name midwest-thursday-seminar-mountain" 2>nul
    if errorlevel 1 (
        echo [INFO] Metodo 3: Execucao sem nome fixo...
        cloudflared.exe tunnel --url http://localhost:8000
        if errorlevel 1 (
            echo.
            echo [ERRO] Nao foi possivel executar o cloudflared!
            echo.
            echo SOLUCOES:
            echo 1. Execute este arquivo como Administrador
            echo 2. Adicione excecao no Windows Defender manualmente:
            echo    - Abra Windows Security
            echo    - Va em Virus e protecao contra ameacas
            echo    - Configuracoes de protecao contra virus e ameacas
            echo    - Adicionar ou remover exclusoes
            echo    - Adicionar exclusao > Arquivo
            echo    - Selecione: %CD%\cloudflared.exe
            echo.
            pause
        )
    )
)

echo.
echo ========================================
echo    TUNNEL FINALIZADO
echo ========================================
echo.
pause