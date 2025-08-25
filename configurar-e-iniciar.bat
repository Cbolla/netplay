@echo off
setlocal enabledelayedexpansion
color 0A

echo.
echo ================================================================
echo                 CONFIGURACAO NGROK + SERVIDOR
echo ================================================================
echo.

REM Verificar se Python esta instalado
echo Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Instale Python de: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK: Python encontrado

REM Verificar se ngrok existe
if not exist "ngrok\ngrok.exe" (
    echo ERRO: ngrok nao encontrado!
    echo Execute primeiro: iniciar-simples.bat
    pause
    exit /b 1
)

REM Verificar configuracao do ngrok
echo Verificando configuracao do ngrok...
ngrok\ngrok.exe config check >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ================================================================
    echo                   CONFIGURACAO NECESSARIA
    echo ================================================================
    echo.
    echo O ngrok precisa de um authtoken para funcionar.
    echo Isso e GRATUITO e leva apenas 2 minutos!
    echo.
    echo PASSO 1: Criar conta gratuita
    echo   1. Abra: https://dashboard.ngrok.com/signup
    echo   2. Crie conta com seu email
    echo   3. Confirme o email
    echo.
    echo PASSO 2: Obter authtoken
    echo   1. Faca login em: https://dashboard.ngrok.com/
    echo   2. Acesse: https://dashboard.ngrok.com/get-started/your-authtoken
    echo   3. Copie o authtoken (algo como: 2abc123def456ghi789jkl)
    echo.
    echo PASSO 3: Cole o token aqui
    echo.
    set /p "token=Cole seu authtoken aqui e pressione Enter: "
    
    if "!token!"=="" (
        echo ERRO: Token nao fornecido
        echo.
        echo Sem o authtoken, o ngrok nao funciona.
        echo Execute este script novamente apos obter o token.
        pause
        exit /b 1
    )
    
    echo.
    echo Configurando authtoken...
    ngrok\ngrok.exe config add-authtoken !token!
    if %errorLevel% equ 0 (
        echo OK: Authtoken configurado com sucesso!
    ) else (
        echo ERRO: Falha ao configurar authtoken
        echo Verifique se o token esta correto.
        pause
        exit /b 1
    )
) else (
    echo OK: ngrok ja esta configurado
)

REM Instalar dependencias
echo Instalando dependencias...
pip install fastapi uvicorn python-dotenv requests httpx >nul 2>&1
echo OK: Dependencias instaladas

echo.
echo ================================================================
echo                   INICIANDO SERVIDOR
echo ================================================================
echo.

REM Inicializar banco
echo Inicializando banco de dados...
python -c "from database import db" 2>nul
echo OK: Banco pronto

REM Iniciar servidor
echo Iniciando servidor web...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000

echo Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

REM Testar servidor local
echo Testando servidor local...
curl -s http://localhost:8000/ >nul 2>&1
if %errorLevel% equ 0 (
    echo OK: Servidor local funcionando
) else (
    echo AVISO: Servidor pode estar inicializando ainda
)

REM Iniciar ngrok
echo Criando tunel publico com ngrok...
start /B ngrok\ngrok.exe http 8000

echo Aguardando ngrok inicializar...
timeout /t 8 /nobreak >nul

REM Verificar se ngrok esta funcionando
echo Verificando tunel publico...
curl -s http://localhost:4040/api/tunnels >nul 2>&1
if %errorLevel% equ 0 (
    echo OK: Tunel publico criado com sucesso!
) else (
    echo AVISO: Tunel pode estar inicializando ainda
)

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
echo   2. Copie a URL HTTPS (ex: https://abc123.ngrok.io)
echo   3. Use essa URL em qualquer lugar do mundo
echo.
echo PAGINAS DISPONIVEIS:
echo   Admin: SUA_URL/
echo   Cliente: SUA_URL/client
echo.
echo TESTE GLOBAL:
echo   - Abra http://localhost:4040 no navegador
echo   - Copie a URL HTTPS mostrada
echo   - Teste no celular com 4G
echo   - Funciona de qualquer lugar do mundo!
echo.
echo IMPORTANTE:
echo   - Mantenha este terminal aberto
echo   - A URL e temporaria (muda a cada reinicializacao)
echo   - Para producao, use VPS real
echo.
echo Pressione qualquer tecla para abrir dashboard do ngrok...
pause >nul

REM Abrir dashboard
start http://localhost:4040

echo.
echo Dashboard aberto! Copie a URL publica de la.
echo.
echo Servidor rodando... Pressione Ctrl+C para parar
pause >nul

REM Cleanup
echo.
echo Parando servicos...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo Servicos parados. Obrigado!
pause