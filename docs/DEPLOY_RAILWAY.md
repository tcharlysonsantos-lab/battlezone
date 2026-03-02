# 🚂 Deploy no Railway - Guia Completo

## Visão Geral
BattleZone está pronto para deploy em produção via Railway.app.

## Pré-requisitos
- Conta no GitHub (seu projeto sincronizado)
- Conta no Railway.app (grátis)
- SECRET_KEY do arquivo `seguranca.env`

## Passos para Deploy

### 1. Criar Conta no Railway
1. Acesse: https://railway.app
2. Clique "Get Started" → "GitHub"
3. Autorize e confirme

### 2. Novo Projeto
1. Clique "New Project"
2. Escolha "Deploy from GitHub repo"
3. Selecione `battlezone_flask`

### 3. Configurar Variáveis
No painel, vá em "Variables" e adicione:

```
FLASK_ENV=production
SECRET_KEY=<seu_valor_do_seguranca.env>
```

### 4. Deploy
- Railway detecta `Procfile` automaticamente
- Clique "Deploy" ou aguarde automático
- Logs disponíveis em "Deployments"

### 5. Acessar
URL será: `https://seu-app.railway.app`

## Troubleshooting

### Build falhou?
- Verifique `SECRET_KEY` em Variables
- Verifique logs em Deployments

### App não inicia?
- `FLASK_ENV` deve ser `production`
- Banco de dados é SQLite (gratuito)

### Banco de dados vazio?
Normal no primeiro deploy. Use shell do Railway para executar `init_db.py` depois.

## Próximos Passos
- **PostgreSQL**: Railway → "Add Service" → PostgreSQL
- **Custom Domain**: Railway → Settings → Domains
- **Auto Deploy**: Automático ao fazer `git push`

📌 **Documentação completa**: Ver [RAILWAY_PASSO_A_PASSO.md]
