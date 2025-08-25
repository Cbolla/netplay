# 🌍 Guia de Acesso Público - Netplay RPA

Guia completo para acessar seu sistema de **qualquer lugar do mundo** usando seu PC como servidor.

## 🚀 Métodos de Acesso Público

### 🥇 Método 1: ngrok (Recomendado para Testes)

#### Vantagens:
- ✅ Gratuito
- ✅ Fácil de usar
- ✅ HTTPS automático
- ✅ Funciona atrás de NAT/Firewall

#### Limitações:
- ⚠️ URL muda a cada reinicialização
- ⚠️ Limitado a 1 túnel simultâneo (gratuito)
- ⚠️ Dependente de terceiros

### 🥈 Método 2: Cloudflare Tunnel

#### Vantagens:
- ✅ Gratuito
- ✅ URL fixa
- ✅ Múltiplos túneis
- ✅ Mais estável

### 🥉 Método 3: Port Forwarding + DDNS

#### Vantagens:
- ✅ Controle total
- ✅ Sem dependências
- ✅ Melhor performance

#### Desvantagens:
- ❌ Requer configuração do roteador
- ❌ Exposição direta à internet
- ❌ Mais complexo

## 🛠️ Configuração ngrok (Método Mais Fácil)

### Passo 1: Instalação Automática
```batch
# Clique duplo em:
start-public.bat

# Ou execute:
start-public.ps1
```

### Passo 2: Configuração Manual (se necessário)

#### 2.1 Baixar ngrok:
1. Acesse: https://ngrok.com/download
2. Baixe para Windows
3. Extraia `ngrok.exe` na pasta do projeto

#### 2.2 Criar conta (opcional mas recomendado):
1. Acesse: https://ngrok.com/signup
2. Crie conta gratuita
3. Copie seu authtoken
4. Execute: `ngrok config add-authtoken SEU_TOKEN`

### Passo 3: Iniciar Servidor
```batch
# Método 1: Script automático
start-public.bat

# Método 2: Manual
python -m uvicorn main:app --host 127.0.0.1 --port 8000
# Em outro terminal:
ngrok http 8000
```

### Passo 4: Obter URL Pública
1. Abra: http://localhost:4040
2. Copie a URL (ex: `https://abc123.ngrok.io`)
3. Use essa URL em qualquer dispositivo

## 🌐 URLs de Acesso

### Exemplo de URL ngrok:
```
https://abc123.ngrok.io/          # Painel Admin
https://abc123.ngrok.io/client    # Painel Cliente
```

### Interface de Monitoramento:
```
http://localhost:4040             # Dashboard ngrok
```

## 📱 Testando de Qualquer Lugar

### Cenários de Teste:

#### 1. **Celular (4G/5G)**
- Abra navegador no celular
- Digite: `https://abc123.ngrok.io`
- Teste login e funcionalidades

#### 2. **Outro Wi-Fi**
- Conecte em Wi-Fi diferente
- Acesse a URL pública
- Verifique se funciona normalmente

#### 3. **Computador Remoto**
- Use qualquer computador
- Acesse via navegador
- Teste todas as funcionalidades

#### 4. **Múltiplos Dispositivos**
- Teste vários dispositivos simultaneamente
- Verifique performance
- Teste diferentes navegadores

## 🔧 Configuração Cloudflare Tunnel

### Instalação:
```powershell
# Baixar cloudflared
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"

# Autenticar
.\cloudflared.exe tunnel login

# Criar túnel
.\cloudflared.exe tunnel create netplay

# Configurar
.\cloudflared.exe tunnel route dns netplay netplay.seudominio.com

# Iniciar
.\cloudflared.exe tunnel run netplay
```

### Arquivo de Configuração:
```yaml
# config.yml
tunnel: netplay
credentials-file: C:\Users\Usuario\.cloudflared\netplay.json

ingress:
  - hostname: netplay.seudominio.com
    service: http://localhost:8000
  - service: http_status:404
```

## 🏠 Port Forwarding + DDNS

### Configuração do Roteador:
1. Acesse interface do roteador (192.168.1.1)
2. Vá em "Port Forwarding" ou "Virtual Server"
3. Adicione regra:
   - **Porta Externa**: 8000
   - **IP Interno**: 192.168.1.8 (seu IP local)
   - **Porta Interna**: 8000
   - **Protocolo**: TCP

### DDNS (IP Dinâmico):
1. Registre em serviço DDNS (No-IP, DuckDNS, etc.)
2. Configure no roteador
3. Use domínio: `seudominio.ddns.net:8000`

## 🔒 Segurança

### Para ngrok:
- ✅ HTTPS automático
- ✅ Túnel criptografado
- ✅ Sem exposição direta
- ⚠️ Confie no provedor

### Para Port Forwarding:
- ❌ HTTP não criptografado
- ❌ Exposição direta
- ✅ Controle total
- 🔧 Configure HTTPS manualmente

### Recomendações:
1. **Use HTTPS sempre que possível**
2. **Configure autenticação forte**
3. **Monitore acessos**
4. **Use para testes apenas**
5. **Para produção, use VPS real**

## 🚨 Solução de Problemas

### ngrok não funciona:
```bash
# Verificar se está rodando
ngrok version

# Verificar túneis ativos
curl http://localhost:4040/api/tunnels

# Reiniciar
taskkill /f /im ngrok.exe
ngrok http 8000
```

### Servidor não responde:
```bash
# Verificar se está rodando
netstat -an | findstr :8000

# Testar localmente
curl http://localhost:8000

# Reiniciar servidor
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Firewall bloqueando:
```cmd
# Liberar porta
netsh advfirewall firewall add rule name="Netplay RPA" dir=in action=allow protocol=TCP localport=8000

# Verificar regras
netsh advfirewall firewall show rule name="Netplay RPA"
```

## 📊 Monitoramento

### ngrok Dashboard:
- **URL**: http://localhost:4040
- **Requests**: Ver todas as requisições
- **Status**: Verificar saúde do túnel
- **Logs**: Debug de problemas

### Logs do Servidor:
- Aparecem no terminal onde iniciou
- Use para debug de erros
- Monitore performance

## 🎯 Próximos Passos

### Para Testes:
1. ✅ Use ngrok (mais fácil)
2. ✅ Teste em vários dispositivos
3. ✅ Verifique todas as funcionalidades

### Para Produção:
1. 🚀 Migre para VPS real
2. 🔒 Configure HTTPS próprio
3. 📊 Configure monitoramento
4. 💾 Configure backup

## 📞 Comandos Úteis

```bash
# Iniciar servidor local
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Iniciar ngrok
ngrok http 8000

# Ver túneis ativos
ngrok tunnels list

# Parar tudo
taskkill /f /im python.exe
taskkill /f /im ngrok.exe

# Verificar porta
netstat -an | findstr :8000

# Testar conectividade
curl https://sua-url.ngrok.io
```

---

**🌍 Agora você pode acessar seu sistema de qualquer lugar do mundo!**

**⚠️ Lembre-se: Para uso profissional, migre para uma VPS real.**