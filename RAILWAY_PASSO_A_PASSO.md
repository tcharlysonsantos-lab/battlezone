# 🚂 GUIA COMPLETO: Deploy BattleZone no Railway

## Passo 1️⃣: Criar Conta no Railway

1. Abra: https://railway.app
2. Clique em **"Get Started"** (canto superior direito)
3. **Clique em "GitHub"** para conectar sua conta GitHub
4. Autorize Railway a acessar suas repositórios
5. ✅ Pronto! Você está logado

---

## Passo 2️⃣: Criar Novo Projeto

1. Clique em **"New Project"** (canto superior esquerdo)
2. Escolha **"Deploy from GitHub Repo"**

### Problema: Repositório não aparece?

Se `battlezone_flask` não aparecer na lista:

**Solução A - Sincronizar manualmente:**
1. Em Railway: Clique em seu perfil (canto superior direito)
2. Vá para **"Integrations"**
3. Clique no ícone do GitHub
4. Clique em **"Disconnect"**
5. Clique em **"Connect"** novamente
6. Autorize novamente
7. Volte para **"New Project"**

**Solução B - Usar URL diretamente:**
1. Clique em **"Deploy from GitHub Repo"**
2. Em **"Search repositories"**, cole:
   ```
   https://github.com/tcharlysonsantos-lab/battlezone_flask
   ```
3. Se ainda não aparecer, Railway pode estar sincronizando (aguarde 5 minutos)

---

## Passo 3️⃣: Configurar Variáveis de Ambiente

1. Após conectar o repositório, Railway vai criar um novo projeto
2. Clique no projeto criado
3. Vá na aba **"Variables"**
4. Clique em **"New Variable"**
5. Adicione:

### Variável 1:
- **Name:** `FLASK_ENV`
- **Value:** `production`
- Clique em **"Add"**

### Variável 2:
- **Name:** `SECRET_KEY`
- **Value:** (Cole o valor de `SECRET_KEY` do seu arquivo `seguranca.env`)
  
  *Para encontrar: Abra `seguranca.env` na sua máquina, copie o valor de `SECRET_KEY=...`*
- Clique em **"Add"**

---

## Passo 4️⃣: Deploy

1. Railway vai detectar automaticamente:
   - `Procfile` ✅
   - `requirements.txt` ✅
   - Python app ✅

2. Clique em **"Deploy"** ou aguarde deploy automático
3. Acompanhe os logs:
   - Se ver erros, Railway mostra no painel
   - Aguarde "Deployment completed" ✅

---

## Passo 5️⃣: Acessar sua App

Após deploy bem-sucedido:

1. Em Railway, clique em **"Deployments"**
2. Procure por **"Domains"** ou **"URL"**
3. Você terá uma URL como:
   ```
   https://battlezone-flask-xxxx.railway.app
   ```

4. Acesse no navegador! 🎉

---

## 🚨 Troubleshooting

### ❌ "Build failed"
- Verifique os logs em Railway
- Procure por mensagens de erro
- Pode ser `SECRET_KEY` ausente ou inválido

### ❌ "Application error"
- Verifique se `FLASK_ENV=production` está configurado
- Verifique se `SECRET_KEY` foi preenchido corretamente

### ❌ "Banco de dados Vazio"
- Isso é normal no primeiro deploy
- Depois você pode runnar `init_db.py` em produção via shell do Railway

---

## ✅ Quando tudo funcionar

Você terá:
- ✅ URL pública (https://...)
- ✅ HTTPS automático
- ✅ Deploy automático (quando fizer git push)
- ✅ Uptime 24/7 (mesmo no free tier)
- ✅ Pronto para upgrade a PostgreSQL depois

---

## 📝 Próximos Passos (Quando quiser)

1. **Adicionar PostgreSQL:** Railway → "Add Service" → PostgreSQL
2. **Backup automático:** Railway tem snapshots
3. **Custom Domain:** Railway → "Settings" → "Domains"
