# Railway Deployment Guide - BattleZone

## 🚀 Deployment em Railway

### Passo 1: Criar Secret Key

Gere uma chave segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Passo 2: Configurar Railway

No Dashboard Railway:

#### 1. **Banco de Dados PostgreSQL**
   - Clique em "Add Service" → PostgreSQL
   - Railway criará `DATABASE_URL` automaticamente

#### 2. **Variáveis de Ambiente** (Settings → Variables)

```env
SECRET_KEY=<sua-chave-secura-aqui>
FLASK_ENV=production
DEBUG=false

# Email (opcional, mas recomendado)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu.email@gmail.com
MAIL_PASSWORD=sua-app-password

# Logging
LOG_TO_FILE=true
LOG_LEVEL=INFO
```

### Passo 3: Conectar com GitHub

1. Clique em "Connect Repository"
2. Selecione seu repositório
3. Railway faz deploy automático a cada push

### Passo 4: Verificar Deployment

Após deploy, acesse: `https://seu-app.railway.app`

⚠️ **Importante**: Primeira vez pode levar 2-3 minutos para inicializar o banco de dados.

## 🔧 Troubleshooting

### Problema: "Já inicia em /auth/login"

**Causa**: Sessão/Cookie não persistindo entre requisições

**Solução** ✅: Já implementada!
- ProxyFix configurado (confia em headers de proxy)
- SESSION_COOKIE_SECURE = true em produção
- SESSION_COOKIE_SAMESITE = 'Lax' para HTTPS
- Sessão marcada como permanente

### Problema: "Páginas não carregam"

**Verificar**:
```bash
# Ver logs em Railway
railway logs -f

# Ou acesse Dashboard → Logs
```

### Problema: Emails não enviando

**Verificar**:
1. MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD configurados
2. Para Gmail: Use [App Password](https://myaccount.google.com/apppasswords), não senha normal
3. Se não configurado, sistema cria fallback (sem erro crítico)

## 📊 Monitoramento

### Verificar Status
```bash
railway status
```

### Ver Logs
```bash
railway logs -f  # Follow (atualiza em tempo real)
railway logs --tail 100  # Últimas 100 linhas
```

### Environment Variables
```bash
railway variables
```

## 🔐 Segurança em Produção

✅ HTTPS forçado (Talisman: `force_https=True`)
✅ Headers de segurança adicionados
✅ CSRF protection via Flask-WTF
✅ Cookies seguros (Secure, HttpOnly, SameSite)
✅ Rate limiting de 5 tentativas de login/15 min
✅ Sessions expiram após 30 minutos de inatividade

## 📱 Banco de Dados

Railway cria PostgreSQL automaticamente quando você adicionar via UI.

**DATABASE_URL é criado automaticamente** - não precisa configurar manualmente!

Para migrar dados locais para produção:
```bash
# Fazer backup local
python scripts/backup_db.py

# Restaurar em produção (após confirmar estrutura)
# Use o painel Railway ou ferramentas CLI
```

## 🆘 Suporte

Problemas mais comuns:

| Problema | Solução |
|----------|---------|
| "502 Bad Gateway" | Esperou deploy terminar? (pode levar 3 min) |
| Sessão sempre em /login | Verificar DATABASE_URL está configurada |
| Emails não enviando | Checar MAIL_* variables e credenciais |
| Banco vazio | PostgreSQL levou tempo para inicializar, aguarde |

## 📚 Documentos Úteis

- [Railway Docs](https://docs.railway.app)
- [Flask Deployment](https://flask.palletsprojects.com/deployment)
- [Gunicorn (WSGI Server)](https://gunicorn.org)
