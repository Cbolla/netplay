@echo off
title Resolver Windows Defender - Cloudflare
color 0C

echo.
echo ========================================
echo    RESOLVER WINDOWS DEFENDER
echo ========================================
echo.

echo [INFO] Este arquivo vai te ajudar a resolver o bloqueio do Windows Defender
echo.

echo PASSO 1: Adicionar excecao manualmente
echo ========================================
echo.
echo 1. Pressione Windows + I (Configuracoes)
echo 2. Va em "Atualizacao e Seguranca"
echo 3. Clique em "Seguranca do Windows"
echo 4. Clique em "Protecao contra virus e ameacas"
echo 5. Em "Configuracoes de protecao contra virus e ameacas", clique em "Gerenciar configuracoes"
echo 6. Role para baixo e clique em "Adicionar ou remover exclusoes"
echo 7. Clique em "Adicionar uma exclusao" e escolha "Arquivo"
echo 8. Navegue ate: %CD%
echo 9. Selecione o arquivo: cloudflared.exe
echo 10. Clique em "Abrir"
echo.

echo PASSO 2: Executar como Administrador
echo ========================================
echo.
echo 1. Clique com botao direito em "cloudflare-fixo.bat"
echo 2. Escolha "Executar como administrador"
echo 3. Clique em "Sim" quando pedir permissao
echo.

echo PASSO 3: Alternativa - Desabilitar temporariamente
echo ========================================
echo.
echo 1. Abra Windows Security
echo 2. Va em "Protecao contra virus e ameacas"
echo 3. Em "Configuracoes de protecao em tempo real"
echo 4. Desative temporariamente a "Protecao em tempo real"
echo 5. Execute: cloudflare-fixo.bat
echo 6. IMPORTANTE: Reative a protecao depois!
echo.

echo ========================================
echo    TESTANDO CLOUDFLARE AGORA
echo ========================================
echo.

echo Pressione qualquer tecla para tentar executar o Cloudflare...
pause

REM Tentar executar diretamente
echo [INFO] Tentando executar cloudflared...
cloudflared.exe tunnel --url http://localhost:8000

echo.
echo Se funcionou, sua URL sera mostrada acima!
echo Se nao funcionou, siga os passos manuais acima.
echo.
pause