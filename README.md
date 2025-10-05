# 🎮 NETPLAY - SUPER SIMPLES

## 🚀 COMO USAR (1 CLIQUE)

1. **Baixe TODOS os arquivos** para sua VPS Windows
2. **Clique 2x em**: `RODAR-VPS.bat`
3. **PRONTO!** ✅

## 🔗 OPÇÕES DE LINK:

### 🔄 **Link Temporário** (Padrão - SEM LOGIN)
- Funciona sem configuração
- Link muda toda vez: `https://random-words.trycloudflare.com`
- **Mais fácil e rápido!**

### 🆕 **Link Fixo** (Permanente - COM LOGIN)
- **Clique 2x em**: `CONFIGURAR-CONTA.bat`
- Configure sua conta Cloudflare uma vez
- Tenha sempre o mesmo link: `https://netplay.seusite.com`
- **Requer conta Cloudflare**

## 📁 Arquivos

```
netplay/
├── frontend/              # Interface web
├── main.py               # Servidor principal
├── requirements.txt      # Dependências Python
├── cloudflared.exe       # Cloudflare Tunnel
├── .env.example         # Configuração
├── RODAR-VPS.bat        # ⭐ SCRIPT PRINCIPAL
├── CONFIGURAR-CONTA.bat # 🔗 Configurar conta Cloudflare
├── tunnel-config.txt    # ⚙️ Configuração do tunnel
└── COMO-USAR-SUA-CONTA.md # 📖 Instruções detalhadas
```

## 🌐 Acesso

- **Local**: http://localhost:8000
- **Global**: 
  - Link temporário: `https://random-words.trycloudflare.com` (padrão)
  - Link fixo: `https://netplay.seusite.com` (com sua conta)

## 🌐 Acesso Global

Você pode acessar seu servidor de qualquer lugar do mundo através do Cloudflare Tunnel:

### 🔄 Link Temporário (RECOMENDADO)
- Execute `CONFIGURAR-CONTA.bat` e escolha opção 1
- Depois execute `RODAR-VPS.bat` 
- Exemplo: `https://abc-def-ghi.trycloudflare.com`
- ✅ Funciona imediatamente, sem configuração
- ✅ Não precisa de conta Cloudflare
- ⚠️ Link muda a cada execução

### 🔗 Link Fixo (Para Usuários Avançados)
- Execute `CONFIGURAR-CONTA.bat` e veja as instruções (opção 2)
- Configure sua conta Cloudflare primeiro
- Use opção 3 para configurar manualmente
- Exemplo: `https://meunetplay.meudominio.com`
- ✅ Link sempre o mesmo
- ⚠️ Requer conta Cloudflare e domínio próprio

## ⚙️ O que acontece quando roda:

1. ✅ Instala dependências Python automaticamente
2. ✅ Configura ambiente (.env)
3. ✅ Configura Cloudflare Tunnel
4. ✅ Inicia servidor e tunnel automaticamente

## 🔧 Requisitos

- **Windows** com Python instalado
- **Internet** para baixar dependências
- **Conta Cloudflare** (opcional, para link fixo)

## 🆘 Problemas?

Se der erro, instale Python:
1. Baixe do site oficial: python.org
2. **IMPORTANTE**: Marque "Add to PATH" na instalação
3. Rode o script novamente

**É isso! Simples assim! 🎯**