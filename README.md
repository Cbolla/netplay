# 🚀 Netplay RPA System

Sistema automatizado para migração de clientes da Netplay com interface web para revendedores e clientes.

## 📋 Funcionalidades

- **Painel do Revendedor**: Gerenciamento completo de clientes e migrações
- **Painel do Cliente**: Interface simplificada para auto-migração
- **Geração de Links**: Links personalizados para cada cliente
- **Migração em Lote**: Migração múltipla de clientes
- **API Integrada**: Comunicação direta com a API da Netplay

## 🛠️ Instalação Local (Desenvolvimento)

### Pré-requisitos
- Python 3.8+
- pip

### Passos

1. **Clone o repositório**
```bash
git clone <seu-repositorio>
cd netplay
```

2. **Configure as credenciais**
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais da Netplay
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Execute o servidor**
```bash
python -m uvicorn main:app --reload --port 8000
```

5. **Acesse a aplicação**
- Painel Admin: http://localhost:8000
- Painel Cliente: http://localhost:8000/client

## 🌐 Deploy em VPS (Produção)

### Método 1: Deploy Automatizado (Recomendado)

1. **Envie os arquivos para sua VPS**
```bash
# No seu computador local
scp -r . usuario@sua-vps:/home/usuario/netplay/
```

2. **Execute o script de deploy**
```bash
# Na sua VPS
cd /home/usuario/netplay
chmod +x deploy.sh
bash deploy.sh
```

3. **Configure seu domínio (opcional)**
```bash
# Edite o arquivo de configuração do Nginx
sudo nano /etc/nginx/sites-available/netplay
# Substitua "_" por seu domínio
```

4. **Configure HTTPS (opcional)**
```bash
sudo certbot --nginx -d seu-dominio.com
```

### Método 2: Deploy Manual

#### 1. Preparar o Sistema
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-pip python3-venv nginx git curl ufw
```

#### 2. Configurar o Projeto
```bash
# Criar diretório
sudo mkdir -p /opt/netplay
sudo chown $USER:$USER /opt/netplay

# Copiar arquivos
cp -r . /opt/netplay/
cd /opt/netplay

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configurar Nginx
```bash
# Copiar configuração
sudo cp nginx.conf /etc/nginx/sites-available/netplay
sudo ln -s /etc/nginx/sites-available/netplay /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Configurar Serviço
```bash
# Copiar arquivo de serviço
sudo cp netplay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable netplay
sudo systemctl start netplay
```

#### 5. Configurar Firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📁 Estrutura do Projeto

```
netplay/
├── main.py              # Aplicação FastAPI principal
├── database.py          # Gerenciamento do banco de dados
├── requirements.txt     # Dependências Python
├── gunicorn.conf.py     # Configuração do Gunicorn
├── nginx.conf           # Configuração do Nginx
├── netplay.service      # Arquivo de serviço systemd
├── deploy.sh            # Script de deploy automatizado
├── start.sh             # Script de inicialização
├── .env                 # Variáveis de ambiente
├── frontend/            # Arquivos da interface web
│   ├── index.html       # Painel do revendedor
│   ├── client.html      # Painel do cliente
│   ├── script.js        # JavaScript principal
│   ├── client-script.js # JavaScript do cliente
│   ├── style.css        # Estilos principais
│   └── client-style.css # Estilos do cliente
└── netplay.db           # Banco de dados SQLite
```

## 🔧 Comandos Úteis

### Gerenciamento do Serviço
```bash
# Ver status
sudo systemctl status netplay

# Reiniciar
sudo systemctl restart netplay

# Parar
sudo systemctl stop netplay

# Ver logs
sudo journalctl -u netplay -f
```

### Nginx
```bash
# Status
sudo systemctl status nginx

# Reiniciar
sudo systemctl restart nginx

# Testar configuração
sudo nginx -t
```

### Banco de Dados
```bash
# Verificar banco
python check_db.py

# Backup
cp netplay.db netplay.db.backup
```

## 🔒 Configurações de Segurança

### Firewall
```bash
# Ver status
sudo ufw status

# Permitir porta específica
sudo ufw allow 8080/tcp
```

### SSL/HTTPS
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Renovar automaticamente
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🐛 Solução de Problemas

### Serviço não inicia
```bash
# Verificar logs
sudo journalctl -u netplay -n 50

# Verificar permissões
sudo chown -R www-data:www-data /opt/netplay
```

### Nginx erro 502
```bash
# Verificar se o serviço está rodando
sudo systemctl status netplay

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

### Banco de dados
```bash
# Recriar banco
rm netplay.db
python -c "from database import db; print('Banco recriado!')"
```

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Verifique os logs: `sudo journalctl -u netplay -f`
- Teste a configuração: `sudo nginx -t`
- Verifique o status: `sudo systemctl status netplay nginx`

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.