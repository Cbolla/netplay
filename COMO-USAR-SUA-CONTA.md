# 🔗 Como Usar Sua Conta Cloudflare Existente

## 📋 Passo a Passo

### 1️⃣ **Fazer Login na Sua Conta Cloudflare**
```bash
cloudflared.exe tunnel login
```
- Isso abrirá seu navegador
- Faça login na sua conta Cloudflare
- Autorize o cloudflared

### 2️⃣ **Criar um Tunnel Nomeado** (se ainda não tiver)
```bash
cloudflared.exe tunnel create netplay-vps
```
- Substitua `netplay-vps` pelo nome que preferir
- Anote o nome do tunnel criado

### 3️⃣ **Configurar o DNS** (no painel Cloudflare)
- Acesse o painel do Cloudflare
- Vá em **DNS** > **Records**
- Adicione um registro CNAME:
  - **Name**: `netplay` (ou o subdomínio que preferir)
  - **Target**: `[TUNNEL-ID].cfargotunnel.com`
  - **Proxy status**: Proxied (laranja)

### 4️⃣ **Configurar o Sistema**
Edite o arquivo `tunnel-config.txt`:
```
MODO_TUNNEL=NOMEADO
TUNNEL_NAME=netplay-vps
TUNNEL_HOSTNAME=netplay.seudominio.com
```

### 5️⃣ **Executar**
Agora quando executar `RODAR-VPS.bat`, ele usará sua conta!

---

## 🔄 **Modo Atual vs Novo Modo**

### ❌ **Modo Atual (Temporário)**
- Link muda toda vez: `https://random-words.trycloudflare.com`
- Não precisa de conta
- Link expira

### ✅ **Novo Modo (Sua Conta)**
- Link fixo: `https://netplay.seudominio.com`
- Usa sua conta Cloudflare
- Link permanente

---

## 🛠️ **Comandos Úteis**

### Ver tunnels existentes:
```bash
cloudflared.exe tunnel list
```

### Deletar tunnel:
```bash
cloudflared.exe tunnel delete NOME-DO-TUNNEL
```

### Testar configuração:
```bash
cloudflared.exe tunnel run NOME-DO-TUNNEL
```

---

## 📞 **Precisa de Ajuda?**

Se tiver dúvidas, me chame que te ajudo a configurar! 🚀