#!/bin/bash

# Script para configurar Cloudflare Tunnel - Sistema Netplay
# Execute este script APÓS o deploy básico

set -e

echo "🌐 Configurando Cloudflare Tunnel para Sistema Netplay..."

# Configurações - ALTERE AQUI
DOMAIN="seu-dominio.com"  # SEU DOMÍNIO
TUNNEL_NAME="netplay"
APP_USER="netplay"
APP_DIR="/opt/netplay"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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
   print_error "Execute como root: sudo $0"
   exit 1
fi

# 1. Instalar cloudflared
print_status "Instalando cloudflared..."
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared.deb
rm cloudflared.deb

# 2. Criar diretório de configuração
print_status "Criando diretório de configuração..."
mkdir -p /home/$APP_USER/.cloudflared
chown -R $APP_USER:$APP_USER /home/$APP_USER/.cloudflared

# 3. Instruções para o usuário
print_warning "PRÓXIMOS PASSOS MANUAIS:"
echo ""
echo "1. Faça login no Cloudflare:"
echo "   sudo -u $APP_USER cloudflared tunnel login"
echo ""
echo "2. Crie o tunnel:"
echo "   sudo -u $APP_USER cloudflared tunnel create $TUNNEL_NAME"
echo ""
echo "3. Configure o DNS:"
echo "   sudo -u $APP_USER cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN"
echo ""
echo "4. Copie o arquivo de configuração:"
echo "   cp $APP_DIR/cloudflare-tunnel.yml /home/$APP_USER/.cloudflared/config.yml"
echo ""
echo "5. Edite o arquivo de configuração:"
echo "   nano /home/$APP_USER/.cloudflared/config.yml"
echo "   - Substitua SEU_TUNNEL_ID_AQUI pelo ID do tunnel criado"
echo "   - Substitua seu-dominio.com pelo seu domínio real"
echo ""
echo "6. Teste o tunnel:"
echo "   sudo -u $APP_USER cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "7. Criar serviço systemd:"
echo "   sudo cloudflared service install"
echo ""

# 4. Criar serviço systemd personalizado
print_status "Criando serviço systemd..."
cat > /etc/systemd/system/cloudflared-netplay.service << EOF
[Unit]
Description=Cloudflare Tunnel for Netplay
After=network.target

[Service]
Type=simple
User=$APP_USER
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/$APP_USER/.cloudflared/config.yml run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# 5. Atualizar configuração do app para Cloudflare
print_status "Atualizando configurações do app..."
if [ -f "$APP_DIR/.env" ]; then
    # Adicionar configurações específicas do Cloudflare
    echo "" >> $APP_DIR/.env
    echo "# Configurações Cloudflare Tunnel" >> $APP_DIR/.env
    echo "CLOUDFLARE_TUNNEL=true" >> $APP_DIR/.env
    echo "ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN" >> $APP_DIR/.env
    echo "CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN" >> $APP_DIR/.env
    
    chown $APP_USER:$APP_USER $APP_DIR/.env
fi

print_status "Configuração inicial concluída! ✅"
print_warning "Execute os passos manuais listados acima para finalizar."
print_status "Após configurar, inicie o serviço: systemctl enable cloudflared-netplay && systemctl start cloudflared-netplay"