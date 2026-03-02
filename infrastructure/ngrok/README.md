# 🚀 NGROK - Exposição Local na Internet

Infraestrutura profissional para expor seu BattleZone Flask na internet com autenticação segura.

## 📋 Arquivos Disponíveis

### 🔧 Scripts (Execute na ordem)
- **`setup_ngrok.py`** - Setup inicial (gerar token, criar config)
- **`start_with_ngrok.py`** - Iniciar servidor com ngrok
- **`ngrok_security.py`** - Middleware de autenticação para proteção

### ⚙️ Configuração
- **`.env.ngrok`** - Token e configurações (auto-gerado)
- **`ngrok.exe`** - Executável do ngrok (Windows)
- **`.ngrok/config.json`** - Configuração avançada (auto-gerado)

---

## 🚀 Início Rápido

### 1️⃣ Setup (primeira vez)
```powershell
python setup_ngrok.py
```
- Solicita seu token ngrok
- Cria `.env.ngrok` e `.ngrok/config.json`
- Gera chave de segurança

### 2️⃣ Iniciar servidor
```powershell
python start_with_ngrok.py
```
- Inicia Flask em http://localhost:5000
- Inicia ngrok e gera URL pública (ex: https://abc123.ngrok.io)
- Ativa autenticação de segurança

### 3️⃣ Usar URL pública
```
https://seu-token.ngrok.io/auth/login
```

---

## 🔒 Segurança

A solução inclui **3 camadas de segurança**:

1. **Token ngrok** - Exigido para iniciar ngrok
2. **CSRF Protection** - Tokens Flask-WTF
3. **Rate Limiting** - Máximo 100 requisições por minuto
4. **Security Headers** - CSP, X-Frame-Options, etc.

---

## 📊 Configuração do ngrok

### Arquivo: `.ngrok/config.json`
```json
{
  "Version": "3",
  "Backends": {
    "default": {
      "Address": "http://localhost:5000"
    }
  },
  "Tunnels": {
    "default": {
      "Proto": "http",
      "Addr": "localhost:5000",
      "Auth": "seu-token-aqui",
      "BindTls": true
    }
  }
}
```

### Variáveis de ambiente (`.env.ngrok`)
```
NGROK_TOKEN=seu_token_aqui
NGROK_DOMAIN=seu-dominio.ngrok.io (opcional)
FLASK_SECRET_KEY=gerado-automaticamente
SECURITY_KEY=gerado-automaticamente
```

---

## 🛠️ Troubleshooting

### ❌ Erro: "Token inválido"
- Gerar novo token em https://dashboard.ngrok.com
- Rodar `python setup_ngrok.py` novamente

### ❌ Erro: "Porta 5000 já em uso"
```powershell
# Matar processo
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

### ❌ Erro: "ngrok.exe não encontrado"
- Baixar em https://ngrok.com/download
- Colocar em `infrastructure/ngrok/`

### ❌ Erro: "SSL certificate verify failed"
- Usar URL http:// ao invés de https://
- Ou desabilitar verificação de SSL em testes

---

## 📱 Usando em Produção (Railway)

Para produção, use [Railway.app](https://railway.app) ao invés de ngrok:

1. Git push para GitHub
2. Conectar Railway ao repositório
3. Deploy automático

Veja: `../railway/README.md`

---

## 🔗 URLs Úteis

- **Dashboard ngrok**: https://dashboard.ngrok.com
- **Documentação ngrok**: https://ngrok.com/docs
- **Inspiração**: https://github.com/ngrok/ngrok-examples

---

## 📅 Log de Conexões

Verifique logs em:
```
logs/ngrok_connections.log
logs/flask_security.log
```

---

## 💡 Dicas

1. **Admin**: usuario `admin` / senha no ADMIN_CREDENTIALS.json
2. **Compartilhar URL**: A URL muda quando reinicia ngrok (use domínio custom para fixar)
3. **Testar autenticação**: `python start_with_ngrok.py --test`
4. **Ver QR Code**: `python NGROK_QUICK_START.py`

---

**Última atualização**: 2026-03-02  
**Versão ngrok**: 3.x+
