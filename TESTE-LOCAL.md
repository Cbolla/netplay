# 📱 Guia de Teste Local - Netplay RPA

Guia completo para testar o sistema na sua rede Wi-Fi local antes de colocar em uma VPS.

## 🚀 Início Rápido

### Método 1: Super Simples
1. **Clique duplo** em `start-local.bat`
2. **Aguarde** o servidor inicializar
3. **Copie** um dos IPs mostrados
4. **Teste** no celular/tablet

### Método 2: PowerShell (Mais Detalhado)
1. **Clique duplo** em `start-local.ps1`
2. **Veja** informações detalhadas de rede
3. **Use** os IPs mostrados para testar

## 📋 Pré-requisitos

- ✅ Python 3.8+ instalado
- ✅ Todos os dispositivos na mesma rede Wi-Fi
- ✅ Windows Firewall configurado (automático nos scripts)

## 🌐 Como Acessar

### No Seu Computador:
```
http://localhost:8000/
```

### Em Outros Dispositivos (Celular, Tablet, etc.):
```
http://192.168.1.8:8000/     (exemplo - use seu IP real)
```

### Páginas Disponíveis:
- **Painel Admin**: `http://SEU-IP:8000/`
- **Painel Cliente**: `http://SEU-IP:8000/client`

## 🔧 Configuração Automática

Os scripts fazem automaticamente:

### Windows Firewall:
```cmd
netsh advfirewall firewall add rule name="Netplay RPA Local" dir=in action=allow protocol=TCP localport=8000
```

### Detecção de IP:
- Detecta automaticamente seu IP da rede Wi-Fi
- Mostra todos os IPs disponíveis
- Filtra IPs inválidos (127.0.0.1, 169.254.*, etc.)

### Dependências:
- Instala automaticamente se necessário
- Verifica Python
- Inicializa banco de dados

## 📱 Testando em Dispositivos Móveis

### Passo a Passo:

1. **Inicie o servidor** no PC:
   ```
   Clique duplo em: start-local.bat
   ```

2. **Anote o IP** mostrado na tela:
   ```
   Exemplo: http://192.168.1.8:8000/
   ```

3. **No celular/tablet**:
   - Conecte na mesma rede Wi-Fi
   - Abra o navegador
   - Digite o IP: `http://192.168.1.8:8000`

4. **Teste as funcionalidades**:
   - Login do revendedor
   - Geração de links
   - Acesso do cliente
   - Migração de servidores

## 🔍 Descobrindo seu IP Manualmente

### Método 1: Comando
```cmd
ipconfig | findstr "IPv4"
```

### Método 2: PowerShell
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}
```

### Método 3: Interface Gráfica
1. Windows + R
2. Digite: `ncpa.cpl`
3. Clique duplo na conexão Wi-Fi
4. Clique em "Detalhes"
5. Procure por "Endereço IPv4"

## 🛠️ Solução de Problemas

### Problema: "Não consigo acessar do celular"
**Soluções:**
1. Verifique se estão na mesma rede Wi-Fi
2. Execute como administrador para configurar firewall
3. Desative temporariamente antivírus
4. Use IP correto (não localhost)

### Problema: "Porta 8000 em uso"
**Soluções:**
```cmd
# Ver processos usando a porta
netstat -ano | findstr :8000

# Matar processo (substitua PID)
taskkill /PID 1234 /F
```

### Problema: "Python não encontrado"
**Solução:**
1. Instale Python: https://www.python.org/downloads/
2. Marque "Add Python to PATH" na instalação
3. Reinicie o terminal

### Problema: "Firewall bloqueando"
**Soluções:**
1. Execute script como administrador
2. Ou configure manualmente:
   - Painel de Controle > Firewall do Windows
   - Configurações Avançadas
   - Regras de Entrada > Nova Regra
   - Porta TCP 8000

## 📊 Monitoramento

### Ver Logs do Servidor:
Os logs aparecem no terminal onde você executou o script.

### Verificar Conexões:
```cmd
netstat -an | findstr :8000
```

### Processos Python:
```cmd
tasklist | findstr python
```

## 🔒 Segurança Local

### Para Teste:
- ✅ Rede Wi-Fi doméstica é segura
- ✅ Firewall configurado apenas para porta 8000
- ✅ Acesso limitado à rede local

### Para Produção:
- ❌ NÃO use para produção real
- ❌ NÃO exponha para internet
- ❌ NÃO deixe rodando 24/7 no PC pessoal

## 🎯 Próximos Passos

Após testar localmente:

1. **Funcionou bem?** → Migre para VPS real
2. **Precisa ajustes?** → Modifique e teste novamente
3. **Quer acesso externo?** → Use ngrok ou VPS

### Para VPS Real:
- Use os scripts `deploy.sh` (Linux) ou `deploy-windows.ps1` (Windows Server)
- Configure domínio próprio
- Configure HTTPS/SSL
- Configure backup automático

## 📞 Comandos Úteis

```cmd
# Parar servidor
Ctrl + C (no terminal do servidor)

# Ver IP atual
ipconfig

# Testar conectividade
ping 192.168.1.8

# Ver portas abertas
netstat -an | findstr LISTEN

# Limpar cache DNS
ipconfig /flushdns
```

---

**🎉 Agora você pode testar seu sistema localmente antes de colocar em produção!**