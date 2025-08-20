# Sistema de Migração Netplay

Sistema para revendedores gerarem links de migração para clientes da Netplay.

## Configuração

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciais

**Opção A: Arquivo .env (Recomendado)**
1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```
2. Edite o arquivo `.env` com suas credenciais reais da Netplay:
   ```
   NETPLAY_USERNAME=seu_usuario_netplay
   NETPLAY_PASSWORD=sua_senha_netplay
   ```

**Opção B: Editar diretamente o código**
Edite as linhas 40-41 do arquivo `main.py`:
```python
NETPLAY_USERNAME = "seu_usuario_real"
NETPLAY_PASSWORD = "sua_senha_real"
```

### 3. Executar o Sistema
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Acessar o Sistema
Abra seu navegador em: http://localhost:8000

## Como Usar

1. **Login do Revendedor**: Faça login com suas credenciais da Netplay
2. **Gerar Link**: Crie links únicos para seus clientes
3. **Cliente Acessa**: Cliente usa o link para migrar servidores
4. **Migração Transparente**: Sistema usa suas credenciais automaticamente

## Solução de Problemas

### Erro de Conexão com netplay.sigma.vin
- Verifique se suas credenciais estão corretas no arquivo `.env`
- Certifique-se de que tem acesso à internet
- Confirme que suas credenciais têm permissões administrativas na Netplay