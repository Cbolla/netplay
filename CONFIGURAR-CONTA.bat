@echo off
title 🔗 CONFIGURAR TUNNEL
color 0B

echo.
echo ==========================================
echo   🔗 CONFIGURAR TUNNEL CLOUDFLARE
echo ==========================================
echo.

echo Este script configura o tipo de tunnel que você quer usar.
echo.

:MENU
echo ==========================================
echo   ESCOLHA UMA OPÇÃO:
echo ==========================================
echo.
echo [1] 🔄 Usar tunnel temporário (RECOMENDADO)
echo [2] 📖 Ver instruções para tunnel fixo
echo [3] ⚙️  Configurar tunnel fixo manualmente
echo [4] ❌ Sair
echo.
set /p opcao="Digite sua opção (1-4): "

if "%opcao%"=="1" goto TEMP_MODE
if "%opcao%"=="2" goto INSTRUCTIONS
if "%opcao%"=="3" goto MANUAL_CONFIG
if "%opcao%"=="4" goto EXIT
goto MENU

:TEMP_MODE
echo.
echo 🔄 Configurando tunnel temporário...
echo MODO_TUNNEL=TEMPORARIO > tunnel-config.txt
echo TUNNEL_NAME=meu-netplay-tunnel >> tunnel-config.txt
echo TUNNEL_HOSTNAME=netplay.seudominio.com >> tunnel-config.txt
echo.
echo ✅ Tunnel temporário configurado!
echo 🔗 Cada vez que rodar será um link diferente
echo 🚀 Execute RODAR-VPS.bat para usar
echo.
pause
goto MENU

:INSTRUCTIONS
echo.
echo 📖 INSTRUÇÕES PARA TUNNEL FIXO:
echo.
echo Para ter um link fixo, você precisa:
echo.
echo 1. Ter uma conta no Cloudflare (gratuita)
echo 2. Ter um domínio próprio
echo 3. Configurar DNS no painel Cloudflare
echo.
echo 📋 PASSOS DETALHADOS:
echo.
echo 1. Acesse: https://dash.cloudflare.com
echo 2. Faça login ou crie conta gratuita
echo 3. Adicione seu domínio
echo 4. Configure os nameservers
echo 5. Volte aqui e use opção 3
echo.
echo 💡 DICA: Se não tem domínio, use opção 1 (temporário)
echo.
pause
goto MENU

:MANUAL_CONFIG
echo.
echo ⚙️ CONFIGURAÇÃO MANUAL DE TUNNEL FIXO
echo.
echo ⚠️  ATENÇÃO: Só funciona se você já configurou sua conta Cloudflare!
echo.
set /p continuar="Você já configurou sua conta Cloudflare? (s/n): "

if /i "%continuar%"=="n" goto INSTRUCTIONS
if /i "%continuar%"=="nao" goto INSTRUCTIONS

echo.
set /p tunnel_name="Nome do seu tunnel: "
set /p hostname="Seu domínio completo (ex: netplay.meusite.com): "

if "%tunnel_name%"=="" (
    echo ❌ Nome do tunnel não pode estar vazio!
    pause
    goto MENU
)

if "%hostname%"=="" (
    echo ❌ Domínio não pode estar vazio!
    pause
    goto MENU
)

echo MODO_TUNNEL=NOMEADO > tunnel-config.txt
echo TUNNEL_NAME=%tunnel_name% >> tunnel-config.txt
echo TUNNEL_HOSTNAME=%hostname% >> tunnel-config.txt

echo.
echo ✅ Configuração salva!
echo 🔗 Seu link será: https://%hostname%
echo 🚀 Execute RODAR-VPS.bat para usar
echo.
echo ⚠️  Se der erro, volte para opção 1 (temporário)
pause
goto MENU

:EXIT
echo.
echo 👋 Até logo!
echo.
pause
exit