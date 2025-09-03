# 🚀 Guia de Deploy - Sistema Netplay VPS

Este guia contém instruções completas para fazer deploy do Sistema Netplay em uma VPS Ubuntu/Debian.

## 📋 Pré-requisitos

- VPS com Ubuntu 20.04+ ou Debian 11+
- Acesso root ou sudo
- Domínio configurado (opcional, mas recomendado)
- Credenciais da Netplay

## 🛠️ Deploy Automatizado

### 1. Preparar os arquivos

```bash
# No seu computador local, comprima os arquivos
tar -czf netplay-deploy.tar.gz .

# Envie para a VPS
scp netplay-deploy.tar.gz root@SEU_IP_VPS:/tmp/
```

### 2. Executar o deploy

```bash
# Conecte na VPS
ssh root@SEU_IP_VPS

# Extrair arquivos
cd /tmp
tar -xzf netplay-deploy.tar.gz
cd netplay-*

# Tornar o script executável
chmod +x deploy.sh

# Executar deploy
./deploy.sh
```

## ⚙️ Configuração Manual (Alternativa)

### 1. Instalar dependências do sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git curl
```

### 2. Criar usuário da aplicação

```bash
sudo useradd -r -s /bin/false -d /opt/netplay netplay
sudo mkdir -p /opt/netplay
sudo mkdir -p /var/log/netplay
sudo chown -R netplay:netplay /opt/netplay
sudo chown -R netplay:netplay /var/log/netplay
```

### 3. Configurar aplicação

```bash
# Copiar arquivos
sudo cp -r . /opt/netplay/
sudo chown -R netplay:netplay /opt/netplay

# Criar ambiente virtual
cd /opt/netplay
sudo -u netplay python3 -m venv venv
sudo -u netplay ./venv/bin/pip install --upgrade pip
sudo -u netplay ./venv/bin/pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
# Copiar arquivo de produção
sudo cp .env.production .env

# Editar configurações
sudo nano .env
```

**Configure as seguintes variáveis:**

```env
# Credenciais da Netplay (OBRIGATÓRIO)
NETPLAY_USERNAME=seu_usuario@netplay.com
NETPLAY_PASSWORD=sua_senha_segura

# Configurações do servidor
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
DEBUG=false

# Domínio (se tiver)
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,IP_DA_VPS
CORS_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
```

### 5. Configurar systemd service

```bash
# Copiar arquivo de serviço
sudo cp netplay.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar e iniciar serviço
sudo systemctl enable netplay
sudo systemctl start netplay

# Verificar status
sudo systemctl status netplay
```

### 6. Configurar Nginx

```bash
# Copiar configuração
sudo cp nginx.conf /etc/nginx/sites-available/netplay

# Editar domínio na configuração
sudo nano /etc/nginx/sites-available/netplay
# Altere 'seu-dominio.com' para seu domínio real

# Habilitar site
sudo ln -s /etc/nginx/sites-available/netplay /etc/nginx/sites-enabled/

# Remover site padrão (opcional)
sudo rm -f /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Reiniciar nginx
sudo systemctl restart nginx
```

## 🔒 Configurar SSL (Recomendado)

### Usando Let's Encrypt (Gratuito)

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Configurar renovação automática
sudo crontab -e
# Adicione a linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Comandos Úteis

### Gerenciar serviço

```bash
# Status
sudo systemctl status netplay

# Iniciar
sudo systemctl start netplay

# Parar
sudo systemctl stop netplay

# Reiniciar
sudo systemctl restart netplay

# Ver logs
sudo journalctl -u netplay -f
```

### Logs da aplicação

```bash
# Logs em tempo real
sudo tail -f /var/log/netplay/app.log

# Logs de erro
sudo tail -f /var/log/netplay/error.log
```

### Atualizar aplicação

```bash
# Parar serviço
sudo systemctl stop netplay

# Fazer backup do banco
sudo cp /opt/netplay/netplay.db /opt/netplay/netplay.db.backup

# Atualizar código
cd /opt/netplay
sudo -u netplay git pull  # se usando git
# ou copiar novos arquivos

# Atualizar dependências
sudo -u netplay ./venv/bin/pip install -r requirements.txt

# Reiniciar serviço
sudo systemctl start netplay
```

## 🔍 Verificação

### Testar aplicação

```bash
# Verificar se está rodando
curl http://localhost:8000

# Verificar com domínio
curl http://seu-dominio.com
```

### Verificar portas

```bash
# Ver portas abertas
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## 🛡️ Segurança

### Firewall básico

```bash
# Instalar ufw
sudo apt install -y ufw

# Configurar regras
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Ativar firewall
sudo ufw enable
```

### Backup automático

```bash
# Criar script de backup
sudo nano /opt/netplay/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/netplay/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /opt/netplay/netplay.db $BACKUP_DIR/netplay_$DATE.db

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "netplay_*.db" -mtime +7 -delete
```

```bash
# Tornar executável
sudo chmod +x /opt/netplay/backup.sh

# Adicionar ao cron (backup diário às 2h)
sudo crontab -e
# Adicione:
0 2 * * * /opt/netplay/backup.sh
```

## 🆘 Troubleshooting

### Problemas comuns

1. **Serviço não inicia**
   ```bash
   sudo journalctl -u netplay -n 50
   ```

2. **Erro de permissão**
   ```bash
   sudo chown -R netplay:netplay /opt/netplay
   ```

3. **Porta já em uso**
   ```bash
   sudo lsof -i :8000
   ```

4. **Nginx não funciona**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

### Logs importantes

- Aplicação: `/var/log/netplay/app.log`
- Erros: `/var/log/netplay/error.log`
- Nginx: `/var/log/nginx/netplay_access.log`
- Sistema: `sudo journalctl -u netplay`

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs
2. Confirme as configurações
3. Teste conectividade
4. Verifique permissões

---

✅ **Deploy concluído com sucesso!**

Sua aplicação deve estar rodando em:
- HTTP: `http://seu-dominio.com` ou `http://IP_DA_VPS`
- HTTPS: `https://seu-dominio.com` (se SSL configurado)