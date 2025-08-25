# 🔑 Como Configurar ngrok - Resolver ERR_NGROK_4018

Guia passo a passo para configurar o authtoken do ngrok e resolver o erro de autenticação.

## ❌ Erro Atual

```
ERROR: authentication failed: Usage of ngrok requires a verified account and authtoken.
ERR_NGROK_4018
```

## ✅ Solução Completa

### Passo 1: Criar Conta Gratuita

1. **Acesse**: https://dashboard.ngrok.com/signup
2. **Crie conta** com email e senha
3. **Confirme** o email (verifique caixa de entrada)
4. **Faça login** em: https://dashboard.ngrok.com/

### Passo 2: Obter Authtoken

1. **Após login**, acesse: https://dashboard.ngrok.com/get-started/your-authtoken
2. **Copie** o authtoken (algo como: `2abc123def456ghi789jkl`)
3. **Guarde** esse token (você vai precisar)

### Passo 3: Configurar Authtoken

#### Método 1: Automático (Recomendado)
```batch
# Execute este comando (substitua SEU_TOKEN pelo token copiado)
ngrok\ngrok.exe config add-authtoken SEU_TOKEN
```

#### Método 2: Manual
1. Abra o terminal na pasta do projeto
2. Execute:
```batch
ngrok\ngrok.exe config add-authtoken 2abc123def456ghi789jkl
```
*(Substitua pelo seu token real)*

### Passo 4: Verificar Configuração

```batch
# Verificar se foi configurado corretamente
ngrok\ngrok.exe config check
```

Deve mostrar algo como:
```
Valid configuration file at C:\Users\Usuario\.ngrok2\ngrok.yml
```

### Passo 5: Testar

```batch
# Testar ngrok
ngrok\ngrok.exe http 8000
```

Agora deve funcionar sem erro!

## 🚀 Script Atualizado com Configuração

Criei um script que configura automaticamente:

### `configurar-e-iniciar.bat`

```batch
@echo off
color 0A

echo ================================================================
echo                 CONFIGURACAO NGROK + SERVIDOR
echo ================================================================
echo.

echo Verificando configuracao do ngrok...
ngrok\ngrok.exe config check >nul 2>&1
if %errorLevel% neq 0 (
    echo AVISO: ngrok nao esta configurado!
    echo.
    echo Para usar ngrok, voce precisa:
    echo 1. Criar conta gratuita em: https://dashboard.ngrok.com/signup
    echo 2. Obter authtoken em: https://dashboard.ngrok.com/get-started/your-authtoken
    echo 3. Configurar o token
    echo.
    set /p "token=Cole seu authtoken aqui: "
    
    if not "!token!"=="" (
        echo Configurando authtoken...
        ngrok\ngrok.exe config add-authtoken !token!
        if %errorLevel% equ 0 (
            echo OK: Authtoken configurado com sucesso!
        ) else (
            echo ERRO: Falha ao configurar authtoken
            pause
            exit /b 1
        )
    ) else (
        echo ERRO: Token nao fornecido
        pause
        exit /b 1
    )
) else (
    echo OK: ngrok ja esta configurado
)

echo.
echo Iniciando servidor...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000
timeout /t 5 /nobreak >nul

echo Iniciando ngrok...
start /B ngrok\ngrok.exe http 8000
timeout /t 8 /nobreak >nul

echo.
echo ================================================================
echo                   SERVIDOR ATIVO!
echo ================================================================
echo.
echo Abra: http://localhost:4040
echo Copie a URL publica e use em qualquer lugar!
echo.
pause
```

## 🔧 Comandos Úteis

### Configurar Token:
```batch
ngrok\ngrok.exe config add-authtoken SEU_TOKEN
```

### Verificar Configuração:
```batch
ngrok\ngrok.exe config check
```

### Ver Configuração Atual:
```batch
type %USERPROFILE%\.ngrok2\ngrok.yml
```

### Testar Conexão:
```batch
ngrok\ngrok.exe http 8000
```

### Remover Configuração:
```batch
del %USERPROFILE%\.ngrok2\ngrok.yml
```

## 📋 Planos ngrok

### Gratuito:
- ✅ 1 túnel simultâneo
- ✅ HTTPS automático
- ✅ Subdomínio aleatório
- ⚠️ URL muda a cada reinicialização

### Pago (Opcional):
- ✅ Múltiplos túneis
- ✅ Subdomínio personalizado
- ✅ URL fixa
- ✅ Mais recursos

## 🚨 Solução de Problemas

### Erro: "authtoken not found"
```batch
# Reconfigurar token
ngrok\ngrok.exe config add-authtoken SEU_TOKEN
```

### Erro: "invalid authtoken"
1. Verifique se copiou o token completo
2. Gere novo token em: https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure novamente

### Erro: "account limit exceeded"
1. Feche outros túneis ngrok
2. Ou upgrade para plano pago

### Erro: "tunnel not found"
1. Aguarde alguns segundos
2. Verifique se servidor local está rodando
3. Teste: http://localhost:8000

## 🎯 Próximos Passos

1. **Configure o authtoken** seguindo os passos acima
2. **Execute**: `iniciar-simples.bat` novamente
3. **Deve funcionar** sem erro ERR_NGROK_4018
4. **Teste** a URL pública gerada

## 📞 Links Úteis

- **Criar conta**: https://dashboard.ngrok.com/signup
- **Obter token**: https://dashboard.ngrok.com/get-started/your-authtoken
- **Documentação**: https://ngrok.com/docs
- **Suporte**: support@ngrok.com

---

**🔑 Após configurar o authtoken, tudo funcionará perfeitamente!**