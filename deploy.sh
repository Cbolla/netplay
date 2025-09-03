#!/bin/bash

# Script de Deploy Automatizado - Sistema Netplay
# Para Ubuntu/Debian VPS

set -e  # Para em caso de erro

echo "🚀 Iniciando deploy do Sistema Netplay..."

# Configurações
APP_NAME="netplay"
APP_DIR="/opt/$APP_NAME"
USER="netplay"
SERVICE_NAME="netplay"
DOMAIN="seu-dominio.com"  # ALTERE AQUI

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se é root
if [[ $EUID -ne 0 ]]; then
   print_error "Este script deve ser executado como root (use sudo)"
   exit 1
fi

print_status "Atualizando sistema..."
apt update && apt upgrade -y

print_status "Instalando dependências do sistema..."
apt install -y python3 python3-pip python3-venv nginx supervisor git curl

# Criar usuário para a aplicação
print_status "Criando usuário $USER..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d $APP_DIR $USER
fi

# Criar diretório da aplicação
print_status "Criando diretório da aplicação..."
mkdir -p $APP_DIR
mkdir -p /var/log/$APP_NAME
chown -R $USER:$USER $APP_DIR
chown -R $USER:$USER /var/log/$APP_NAME

# Copiar arquivos da aplicação
print_status "Copiando arquivos da aplicação..."
cp -r . $APP_DIR/
chown -R $USER:$USER $APP_DIR

# Configurar ambiente virtual Python
print_status "Configurando ambiente virtual Python..."
cd $APP_DIR
sudo -u $USER python3 -m venv venv
sudo -u $USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $USER $APP_DIR/venv/bin/pip install -r requirements.txt

# Configurar arquivo .env para produção
print_status "Configurando arquivo de ambiente..."
if [ -f ".env.production" ]; then
    cp .env.production .env
    print_warning "IMPORTANTE: Configure as credenciais no arquivo $APP_DIR/.env"
else
    print_error "Arquivo .env.production não encontrado!"
    exit 1
fi

# Configurar banco de dados
print_status "Configurando banco de dados..."
sudo -u $USER $APP_DIR/venv/bin/python check_db.py

print_status "Deploy concluído com sucesso! ✅"
print_warning "Próximos passos:"
echo "1. Configure as credenciais em $APP_DIR/.env"
echo "2. Configure o domínio no nginx: $APP_DIR/nginx.conf"
echo "3. Execute: systemctl enable $SERVICE_NAME && systemctl start $SERVICE_NAME"
echo "4. Execute: systemctl reload nginx"
echo "5. Configure SSL com certbot se necessário"

print_status "Logs da aplicação: /var/log/$APP_NAME/"
print_status "Status do serviço: systemctl status $SERVICE_NAME"