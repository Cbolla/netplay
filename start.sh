#!/bin/bash

# Script de inicialização para o projeto Netplay RPA
# Execute este script na sua VPS para iniciar o servidor

echo "🚀 Iniciando Netplay RPA Server..."

# Definir diretório do projeto
PROJECT_DIR="/opt/netplay"
VENV_DIR="$PROJECT_DIR/venv"

# Criar diretório de logs se não existir
sudo mkdir -p /var/log/netplay
sudo chown www-data:www-data /var/log/netplay

# Navegar para o diretório do projeto
cd $PROJECT_DIR

# Ativar ambiente virtual
echo "📦 Ativando ambiente virtual..."
source $VENV_DIR/bin/activate

# Verificar se as dependências estão instaladas
echo "🔍 Verificando dependências..."
pip install -r requirements.txt

# Executar migrações do banco de dados se necessário
echo "🗄️ Inicializando banco de dados..."
python -c "from database import db; print('Banco de dados inicializado!')"

# Iniciar servidor com Gunicorn
echo "🌐 Iniciando servidor..."
echo "Acesse: http://seu-dominio.com ou http://$(curl -s ifconfig.me)"
echo "Painel Admin: /"
echo "Painel Cliente: /client"
echo ""
echo "Para parar o servidor: Ctrl+C"
echo ""

gunicorn main:app -c gunicorn.conf.py