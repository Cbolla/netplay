#!/bin/bash

# Script de Deploy Automatizado para Netplay RPA
# Execute este script na sua VPS Ubuntu/Debian
# Usage: bash deploy.sh

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy automatizado do Netplay RPA..."
echo "================================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verificar se é root
if [[ $EUID -eq 0 ]]; then
   log_error "Este script não deve ser executado como root"
   exit 1
fi

# Definir variáveis
PROJECT_DIR="/opt/netplay"
VENV_DIR="$PROJECT_DIR/venv"
CURRENT_USER=$(whoami)

log_info "Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

log_info "Instalando dependências do sistema..."
sudo apt install -y python3 python3-pip python3-venv nginx git curl ufw

# Criar diretório do projeto
log_info "Criando diretório do projeto..."
sudo mkdir -p $PROJECT_DIR
sudo chown $CURRENT_USER:$CURRENT_USER $PROJECT_DIR

# Copiar arquivos do projeto (assumindo que estão no diretório atual)
log_info "Copiando arquivos do projeto..."
cp -r . $PROJECT_DIR/
cd $PROJECT_DIR

# Criar ambiente virtual
log_info "Criando ambiente virtual Python..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Instalar dependências Python
log_info "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar permissões
log_info "Configurando permissões..."
sudo chown -R www-data:www-data $PROJECT_DIR
sudo chmod +x $PROJECT_DIR/start.sh

# Criar diretórios de log
log_info "Criando diretórios de log..."
sudo mkdir -p /var/log/netplay
sudo chown www-data:www-data /var/log/netplay

# Configurar Nginx
log_info "Configurando Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/netplay
sudo ln -sf /etc/nginx/sites-available/netplay /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Testar configuração do Nginx
log_info "Testando configuração do Nginx..."
sudo nginx -t

# Configurar serviço systemd
log_info "Configurando serviço systemd..."
sudo cp netplay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable netplay

# Configurar firewall
log_info "Configurando firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Inicializar banco de dados
log_info "Inicializando banco de dados..."
sudo -u www-data $VENV_DIR/bin/python -c "from database import db; print('Banco inicializado!')"

# Iniciar serviços
log_info "Iniciando serviços..."
sudo systemctl restart nginx
sudo systemctl start netplay

# Verificar status
log_info "Verificando status dos serviços..."
if sudo systemctl is-active --quiet nginx; then
    log_success "Nginx está rodando"
else
    log_error "Nginx não está rodando"
fi

if sudo systemctl is-active --quiet netplay; then
    log_success "Netplay está rodando"
else
    log_error "Netplay não está rodando"
fi

# Obter IP público
PUBLIC_IP=$(curl -s ifconfig.me || echo "IP não detectado")

echo ""
echo "================================================"
log_success "Deploy concluído com sucesso!"
echo "================================================"
echo ""
echo "🌐 Acesse sua aplicação em:"
echo "   http://$PUBLIC_IP/"
echo "   http://$PUBLIC_IP/client"
echo ""
echo "📋 Comandos úteis:"
echo "   sudo systemctl status netplay    # Ver status"
echo "   sudo systemctl restart netplay  # Reiniciar"
echo "   sudo journalctl -u netplay -f   # Ver logs"
echo "   sudo systemctl status nginx     # Status Nginx"
echo ""
echo "🔒 Para configurar HTTPS:"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d seu-dominio.com"
echo ""
log_warning "Lembre-se de configurar seu domínio no arquivo .env!"
echo ""