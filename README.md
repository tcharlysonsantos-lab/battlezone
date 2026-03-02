# 🎮 BattleZone Flask - Sistema Completo

**Plataforma web para gerenciamento de equipes, partidas e operadores em Warfield e Redline**

---

## 📂 Estrutura do Projeto

```
battlezone_flask/
├── backend/                    ← Lógica de negócio
│   ├── models.py              ← Banco de dados
│   ├── auth.py                ← Autenticação
│   ├── forms.py               ← Validação
│   ├── utils.py               ← Utilitários
│   ├── decorators.py          ← Decoradores
│   ├── security_utils.py      ← Segurança
│   ├── auth_security.py       ← 2FA TOTP
│   ├── cloud_manager.py       ← Google Drive
│   ├── validators.py          ← Validadores
│   └── delete_partidas.py     ← Limpeza
├── frontend/                   ← Interface web
│   ├── templates/             ← HTML (40+ arquivos)
│   └── static/                ← CSS, JS, Images
├── infrastructure/             ← 🌐 Sistema de Deployment
│   ├── ngrok/                 ← Expor local na internet
│   ├── railway/               ← Deploy em produção
│   ├── database/              ← Banco de dados
│   └── README.md              ← Guide completo
├── scripts/                    ← Scripts auxiliares
│   ├── sync_stats.py          ← Sincronizar stats
│   ├── update_db.py           ← Atualizar schema
│   └── migrate_2fa.py         ← Migração 2FA
├── docs/                       ← 📚 Documentação
│   ├── ARQUITETURA.md         ← Visão técnica
│   ├── SEGURANCA.md           ← Segurança
│   ├── SINCRONIZACAO_STATS.md ← Sync de dados
│   └── README.md              ← Índice
├── app.py                      ← Flask app (3000+ linhas)
├── config.py                   ← Configuração
├── run.py                      ← Launcher
└── requirements.txt            ← Dependências
```

---

## 🚀 Quick Start

### 1️⃣ Instalar Dependências
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2️⃣ Inicializar Banco de Dados
```powershell
python infrastructure/database/init_db.py
```

### 3️⃣ Rodar Localmente
```powershell
python run.py
```

Acesse: **http://localhost:5000**

### 4️⃣ Login
```
Username: admin
Password: [veja em ADMIN_CREDENTIALS.json]
```

---

## 🌐 Deployment

### 🔥 Desenvolvimento (NGROK)
Expose sua app local com URL pública para testes.

```powershell
cd infrastructure/ngrok
python setup_ngrok.py
python start_with_ngrok.py
```

[📖 Guia completo](infrastructure/ngrok/README.md)

### 🚂 Produção (Railway)
Deploy automático com PostgreSQL, SSL, scaling infinito.

```powershell
git push origin main
# Railway faz deploy automático
```

[📖 Guia completo](infrastructure/railway/README.md)

---

## 📚 Documentação

### 🏗️ [Infrastructure Guide](infrastructure/README.md)
Deployment, NGROK, Railway, Database - **COMECE AQUI**

### 🔧 [Backend](docs/ARQUITETURA.md)
Arquitetura, models, rotas, fluxo de dados

### 🔒 [Segurança](docs/SEGURANCA.md)
CSRF, 2FA, Rate Limiting, Autenticação, Tokens

### 📊 [Stats Sync](docs/SINCRONIZACAO_STATS.md)
Sincronização de estatísticas entre operadores

### 💾 [Database](infrastructure/database/README.md)
Schema, migrations, backup, PostgreSQL

---

## ✨ Features

### 👥 Gerenciamento
- ✅ Usuários e Operadores
- ✅ Equipes e Times
- ✅ Partidas e Matches
- ✅ Vendas e Estoque

### 🔐 Segurança
- ✅ 2FA com TOTP (Google Authenticator)
- ✅ Senha com hash bcrypt
- ✅ CSRF Protection
- ✅ Rate Limiting
- ✅ Security Headers (CSP, X-Frame-Options)
- ✅ SQL Injection Prevention
- ✅ Access Control (RBAC)

### 📱 Interface
- ✅ Dashboard admin
- ✅ Página pública
- ✅ Responsivo mobile
- ✅ Calendário de partidas
- ✅ Estatísticas em tempo real

### ☁️ Integração
- ✅ Google Drive Backup automático
- ✅ NGROK para desenvolvimento
- ✅ Railway para produção
- ✅ PostgreSQL suportado

---

## 🏗️ Arquitetura

### Camadas
1. **Presentation** (`frontend/templates/`)
2. **Application** (`app.py` - rotas e lógica)
3. **Business Logic** (`backend/utils.py`)
4. **Data Access** (`backend/models.py` - SQLAlchemy)
5. **Database** (`instance/database.db` ou PostgreSQL)

### Stack Técnico
- **Framework**: Flask 3.1.3
- **ORM**: SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Authentication**: Flask-Login + 2FA
- **Forms**: WTForms
- **Security**: Talisman, Flask-Limiter
- **Server**: Gunicorn (produção)

---

## 🔑 Credenciais Padrão

Após rodar `infrastructure/database/init_db.py`:

```
Username: admin
Password: [gerado aleatoriamente em ADMIN_CREDENTIALS.json]
```

---

## 📊 Banco de Dados

### Tabelas
- `user` - Usuários do sistema
- `operador` - Jogadores/Staff
- `equipe` - Times
- `partida` - Matches
- `venda` - Transações
- `estoque` - Inventário
- `log` - Audit trail
- `solicitacao` - Requests de acesso

---

## 🛠️ Desenvolvimento

### Environment Setup
```powershell
# Copiar variáveis de ambiente
copy seguranca.env.example seguranca.env

# Ativar venv
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### Testes
```powershell
# Testar imports
python test_imports.py

# Testar estrutura
python verify_structure.py
```

### Git Workflow
```powershell
# Ver status
git status

# Commit
git add .
git commit -m "🎯 Descrição da mudança"

# Push automático faz deploy
git push origin main
```

---

## 🔍 Troubleshooting

### ❌ Port 5000 em uso
```powershell
Get-NetTCPConnection -LocalPort 5000 | Stop-Process -Force
```

### ❌ Database locked
```powershell
Get-Process python | Stop-Process -Force
Start-Sleep -Seconds 2
python run.py
```

### ❌ Import error
```powershell
# Verificar estrutura
python verify_structure.py

# Verificar venv ativo
python -c "import sys; print(sys.executable)"
```

### ❌ HTTPS certificate error
Use `http://` ao invés de `https://` em dev

---

## 📈 Performance

- ✅ Admin dashboard carrega em <500ms
- ✅ List operadores: <200ms
- ✅ Criar partida: <300ms
- ✅ Upload de videos: Handled

---

## 🤝 Contribuindo

1. Fork o repositório
2. Cria branch: `git checkout -b feature/sua-feature`
3. Commit: `git commit -am "Adicionado feature"`
4. Push: `git push origin feature/sua-feature`
5. Pull Request

---

## 📋 Checklist Pré-Deploy

- [ ] Código testado localmente
- [ ] Variáveis de ambiente configuradas
- [ ] Database inicializado
- [ ] Login funcionando
- [ ] Admin dashboard acessível
- [ ] Git push para main
- [ ] Railway mostra "deployed successfully"
- [ ] HTTPS acessível em app.railway.app

---

## 🔗 Links Úteis

- 📖 **Documentação**: Ver pasta `docs/`
- 🌐 **Infrastructure**: Ver pasta `infrastructure/`
- 🐍 **Python 3.14+**: https://python.org
- 🏗️ **Flask**: https://flask.palletsprojects.com
- 🚂 **Railway**: https://railway.app
- 🌍 **NGROK**: https://ngrok.com

---

## 📄 Licença

MIT License - Veja arquivo LICENSE

---

## 👤 Autor

**BattleZone Team**  
Plataforma de Warfield & Redline

---

## 🎯 Status

- ✅ Backend: Completo
- ✅ Frontend: Completo
- ✅ Autenticação: Completo (com 2FA)
- ✅ Database: Completo
- ✅ Deployment: Completo (NGROK + Railway)
- 🔄 Próximo: Kubernetes orchestration

---

**Última atualização**: 2026-03-02  
**Versão**: 3.1.3  
**Status**: Production Ready ✅