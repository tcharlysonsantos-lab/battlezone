# 🚂 Railway Deploy Guide

## Passo 1: Preparação Local
✅ Já feito! Criamos:
- `Procfile` - Instrui Railway como rodar o app
- `requirements.txt` - Com gunicorn (servidor WSGI)
- `config.py` - Compatível com SQLite (agora) e PostgreSQL (depois)

## Passo 2: Criar Conta no Railway
1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub (recomendado)
3. Clique em "New Project"

## Passo 3: Conectar GitHub
1. Em Railway: "Connect a Repository"
2. Autorize acesso ao seu GitHub
3. Selecione o repo `battlezone_flask`
4. Railway vai detectar automaticamente que é um projeto Python

## Passo 4: Configurar Environment Variables
Railway vai pedir as variáveis de ambiente. Você precisa adicionar:

```
FLASK_ENV=production
SECRET_KEY=seu_secret_key_aqui_copie_do_seguranca.env
```

Copie o `SECRET_KEY` do seu arquivo `seguranca.env` local.

## Passo 5: Deploy
1. Railway automaticamente faz deploy quando você da push
2. Ou clique em "Deploy" no painel

## Resultado
✅ Sua app estará em: `https://seu-app.railway.app`

---

## Depois: Adicionar PostgreSQL (quando pugar)

1. Em Railway: "Add Database" → PostgreSQL
2. Railway cria automaticamente a variável `DATABASE_URI`
3. Seu app vai detectar e usar PostgreSQL automaticamente
4. Backup do SQLite é automático na Railway

---

## Troubleshooting

**Build falhou?**
- Verifique se `requirements.txt` está no root
- Tente fazer `git push` novamente

**App não sobe?**
- Verifique logs em Railway → Deployments
- Procure por erros de SECRET_KEY

**Banco de dados vazio?**
- Isso é normal! Você precisa rodar `init_db.py` uma vez em produção
- Railway permite shell access para rodar scripts

