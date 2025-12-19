# 🚀 Como Rodar na VPS

## Arquivo Único para VPS

Use o arquivo **`RODAR-VPS-COMPLETO.bat`** para rodar tudo de uma vez na sua VPS.

### O que ele faz:

1. ✅ Inicia o servidor Python (FastAPI)
2. ✅ Inicia o Cloudflare Tunnel
3. ✅ Conecta ao seu domínio fixo: https://servidormigrarcliente.io

> **Nota:** As dependências Python devem estar instaladas previamente. Se precisar instalar, rode antes:
> ```
> python -m pip install -r requirements.txt
> ```

### Como usar:

1. **Na sua VPS**, abra o PowerShell ou CMD
2. Navegue até a pasta do projeto:
   ```
   cd C:\caminho\para\netplay
   ```
3. Execute o arquivo:
   ```
   .\RODAR-VPS-COMPLETO.bat
   ```
4. **Mantenha a janela aberta!** Fechar a janela para o servidor e o tunnel

### O que você verá:

```
==========================================
  🎮 NETPLAY VPS - INICIANDO TUDO
==========================================

⏳ [1/4] Instalando dependencias Python...
✅ [2/4] Configurando ambiente...
✅ [3/4] Iniciando servidor Python...
   📍 Local: http://localhost:8000
✅ [4/4] Iniciando Cloudflare Tunnel...
   🌍 Conectando ao Cloudflare...
   🔗 URL: https://servidormigrarcliente.io

==========================================
  ✅ TUDO RODANDO COM SUCESSO!
==========================================

⚠️  MANTENHA ESTA JANELA ABERTA!
```

### Acessando:

- **Local (na VPS):** http://localhost:8000
- **Público (de qualquer lugar):** https://servidormigrarcliente.io

### Para parar:

- Feche a janela do CMD/PowerShell
- Ou pressione `Ctrl+C`

---

## Arquivos Removidos

Os seguintes arquivos foram removidos pois não são mais necessários:

- ❌ `CONFIGURAR-CONTA.bat` (não usado)
- ❌ `TUNNEL-FIXO.bat` (integrado no completo)
- ❌ `TUNNEL-TEMPORARIO.bat` (não usado)
- ❌ `RODAR-VPS.bat` (substituído pelo completo)
- ❌ `CLOUDFLARE-TUNNEL.bat` (integrado no completo)

Agora você tem apenas **1 arquivo** para rodar tudo! 🎉
