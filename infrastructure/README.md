# 🏗️ Infrastructure - Deployment & Database

Sistema de deployment e gerenciamento de banco de dados para BattleZone Flask.

---

## 📂 Estrutura

```
infrastructure/
├── ngrok/                  ← Exposição local na internet
├── railway/                ← Deploy em produção
├── database/               ← Gerenciamento de banco de dados
└── README.md              ← Você está aqui
```

---

## 🚀 Escolha Seu Caminho

### 🔥 Desenvolvimento Local

Use **NGROK** para expor sua aplicação local na internet com URL pública.

**Quando usar:**
- ✅ Desenvolvimento local
- ✅ Testes antes de produção
- ✅ Compartilhar URL com amigos
- ✅ Debugging remoto

**Como começar:**
```powershell
cd infrastructure/ngrok
python setup_ngrok.py
python start_with_ngrok.py
```

Veja: [infrastructure/ngrok/README.md](ngrok/README.md)

---

### 🚂 Produção na Nuvem

Use **RAILWAY** para deploy profissional automático com PostgreSQL.

**Quando usar:**
- ✅ Produção segura
- ✅ Performance garantida
- ✅ Auto-scaling
- ✅ SSL automático
- ✅ PostgreSQL grátis
- ✅ Deploy automático com git push

**Como começar:**
1. Commit suas mudanças: `git push origin main`
2. Vá para https://railway.app
3. Conecte seu GitHub
4. Siga guia em [infrastructure/railway/README.md](railway/README.md)

Veja: [infrastructure/railway/README.md](railway/README.md)

---

### 🗄️ Banco de Dados

Gerenciar e inicializar banco de dados.

**Desenvolvimento:** SQLite automático em `instance/database.db`  
**Produção:** PostgreSQL automático via Railway

**Comandos:**
```powershell
# Primeira execução
python infrastructure/database/init_db.py

# Atualizar schema
python ../scripts/update_db.py
```

Veja: [infrastructure/database/README.md](database/README.md)

---

## 📋 Migrações Rápidas

### Railway com PostgreSQL
```powershell
# 1. Fazer git push
git push origin main

# 2. Adicionar PostgreSQL em Railway
# Dashboard → Add Database → PostgreSQL

# 3. Deploy automático
# Railway detecta e faz deploy automaticamente

# 4. Acessar em
https://battlezone-flask-xxxx.railway.app
```

### NGROK Local
```powershell
# 1. Setup (primeira vez)
cd infrastructure/ngrok
python setup_ngrok.py

# 2. Iniciar
python start_with_ngrok.py

# 3. Acessar em
https://seu-token.ngrok.io
```

---

## 🔄 Workflow Recomendado

### Desenvolvimento
```
1. Editar código localmente
2. Testar em http://localhost:5000
3. Usar NGROK para teste compartilhado
4. Git push para GitHub
```

### Produção
```
1. Verificar tudo funciona localmente
2. Git push para main
3. Railway faz deploy automático
4. Verificar em https://seu-app.railway.app
5. Se erro, Railway mostra logs
6. Git push fix → Auto-deploy novamente
```

---

## 🛠️ Arquivos Importantes

| Arquivo | Localização | Propósito |
|---------|-------------|----------|
| `setup_ngrok.py` | `ngrok/` | Configurar ngrok (1ª vez) |
| `start_with_ngrok.py` | `ngrok/` | Iniciar servidor com ngrok |
| `Procfile` | `railway/` | Instrui Railway como rodar |
| `init_db.py` | `database/` | Inicializar banco de dados |
| `.env.ngrok` | `ngrok/` | Token ngrok (gerado) |
| `.ngrok/config.json` | `ngrok/` | Config avançada (gerado) |

---

## 📊 Comparação

| Aspecto | NGROK | Railway |
|--------|-------|---------|
| **Setup** | Rápido (5 min) | Muito fácil |
| **Deploy** | Manual | Automático |
| **Database** | SQLite local | PostgreSQL |
| **SSL** | Sim | Sim |
| **Custo** | Grátis | Grátis (com créditos) |
| **Downtime** | Quando reinicia | Nunca |
| **Escalabilidade** | Não | Sim |
| **Use para** | Desenvolvimento | Produção |

---

## ❓ FAQ

**P: Qual devo usar primeiro?**  
R: NGROK para desenvolvimento, Railway para produção.

**P: Posso testar Railway localmente?**  
R: Sim! Railway tem CLI local. Consulte docs.railway.app

**P: E se Railway cair?**  
R: Railway é enterprise-grade. Mas você pode ter backup em NGROK.

**P: Posso mudar de NGROK para Railway depois?**  
R: Sim! São independentes. Só fazer git push.

**P: Onde ficam os logs?**  
R: NGROK: `logs/` | Railway: Dashboard → Logs

---

## 🔗 Recursos Úteis

- **ngrok.com**: https://ngrok.com
- **railway.app**: https://railway.app
- **Flask**: https://flask.palletsprojects.com
- **SQLAlchemy**: https://www.sqlalchemy.org
- **PostgreSQL**: https://www.postgresql.org

---

## 🎯 Próximos Passos

1. Escolha seu caminho: NGROK ou Railway
2. Leia o README correspondente
3. Siga passo a passo
4. Teste funcionalidades importante (login, admin, etc)
5. Commit suas mudanças

---

**Última atualização**: 2026-03-02  
**Versão BattleZone**: 3.1.3  
**Próxima versão**: Kubernetes support
