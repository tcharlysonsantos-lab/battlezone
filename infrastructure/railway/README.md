# 🚂 Railway Deploy Guide

Deploy seu BattleZone Flask em produção com PostgreSQL automático.

---

## 📋 O Que Você Precisa

- ✅ **Conta GitHub** (com repo `battlezone_flask`)
- ✅ **Procfile** (já existe aqui)
- ✅ **requirements.txt** (já configurado com gunicorn)
- ✅ **SECRET_KEY** (em `../../seguranca.env`)

---

## 🚀 Passo a Passo

### 1️⃣ Criar Conta e Conectar GitHub

1. Acesse: https://railway.app
2. Clique **"Get Started"**
3. Clique **"GitHub"** para conectar sua conta
4. Autorize acesso aos repositórios

### 2️⃣ Criar Novo Projeto

1. Clique **"New Project"**
2. Escolha **"Deploy from GitHub Repo"**
3. Procure por `battlezone_flask`
4. Se não aparecer, sincronize em **Settings → Integrations**

### 3️⃣ Configurar Environment Variables

Railway detecta `Procfile` e `requirements.txt` automaticamente.

Você precisa adicionar **2 variáveis**:

**Variável 1: FLASK_ENV**
```
Name:  FLASK_ENV
Value: production
```

**Variável 2: SECRET_KEY**
```
Name:  SECRET_KEY
Value: [copie de seguranca.env]
```

📝 Para encontrar `SECRET_KEY`:
- Abra o arquivo `../../seguranca.env`
- Copie o valor de `SECRET_KEY=...`
- Cole em Railway

### 4️⃣ Deploy

Railway automaticamente:
1. ✅ Detecta Python
2. ✅ Instala dependências do `requirements.txt`
3. ✅ Executa comando do `Procfile`
4. ✅ Inicia servidor gunicorn

Acompanhe os logs no painel de Railway.

### 5️⃣ Acessar Aplicação

Após deploy bem-sucedido, Railway cria URL como:
```
https://battlezone-flask-xxxx.railway.app
```

Acesse e faça login com:
```
Username: admin
Password: [veja em ADMIN_CREDENTIALS.json]
```

---

## 📦 PostgreSQL (Próximo Passo)

Quando estiver pronto para banco de dados profissional:

1. Em Railway: **"Add Database"**
2. Escolha **"PostgreSQL"**
3. Railway cria automaticamente `DATABASE_URI`
4. Seu app detecta e usa PostgreSQL
5. SQLite local é mantido para backup

---

## 🔍 Troubleshooting

### ❌ "Build failed"
- Verifique logs em Railway (aba Deployment)
- Procure por erro de interpretação Python
- Solução: Alguns erros podem ser de import

Veja também: `app.py` linhas 1-50 para verificar imports corretos.

### ❌ "Application error" (500)
- Verifique `SECRET_KEY` está configurado
- Certifique que `FLASK_ENV=production`
- Verifique logs: Railway → Logs

### ❌ "Cannot import backend"
- Isso ocorre se a reorganização não foi feita
- Veja: `../../backend/` deve existir
- E `app.py` deve ter `from backend.models import ...`

---

## 📋 Checklist Pré-Deploy

- [ ] GitHub repo atualizado
- [ ] `requirements.txt` tem `gunicorn`
- [ ] `Procfile` está em `infrastructure/railway/`
- [ ] `SECRET_KEY` está em `../../seguranca.env`
- [ ] `FLASK_ENV` será `production`
- [ ] Backend package existe em `../../backend/`

---

## 🔗 Recursos Úteis

- **Railway Dashboard**: https://railway.app
- **Documentação Railway**: https://docs.railway.app
- **Procfile Reference**: https://devcenter.heroku.com/articles/procfile

---

## 💡 Dicas

1. **Auto-deploy**: Railway faz deploy automático quando você faz `git push`
2. **Logs em tempo real**: Railway mostra todos os logs na interface
3. **Rollback**: Fácil voltar para versão anterior se algo quebrar
4. **SSL automático**: HTTPS já vem habilitado
5. **Domínio customizado**: Você pode adicionar seu próprio domínio

---

**Última atualização**: 2026-03-02  
**Versão gunicorn**: 23.0+  
**Versão Flask**: 3.1.3+
