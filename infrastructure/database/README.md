# 🗄️ Database Management

Gerenciamento de banco de dados e migrações para BattleZone Flask.

---

## 📋 Arquivos Disponíveis

- **`init_db.py`** - Inicializar banco de dados local
- **`migrations/`** - Scripts de migração (quando necessário)

---

## 🚀 Inicializar Banco de Dados (Primeira Vez)

### Local (SQLite)
```powershell
python infrastructure/database/init_db.py
```

Isso vai:
1. ✅ Criar `instance/database.db`
2. ✅ Criar todas as tabelas
3. ✅ Criar usuário admin padrão
4. ✅ Inicializar estrutura de dados

### Em Produção (Railway + PostgreSQL)

Railway automaticamente:
1. Fornece `DATABASE_URI` quando você adiciona PostgreSQL
2. `config.py` detecta e muda para PostgreSQL
3. Tabelas são criadas automaticamente
4. Seu app está pronto para usar

---

## 📊 Estrutura de Banco de Dados

### Tabelas Principais

#### `user` (Usuários do Sistema)
```
- id (PK)
- username (UNIQUE)
- email
- password_hash
- 2fa_secret
- 2fa_backup_codes
- is_admin
- created_at
- updated_at
```

#### `operador` (Jogadores/Staff)
```
- id (PK)
- user_id (FK → user)
- cpf (UNIQUE)
- nome
- whatsapp
- telegram
- plano (SILVER, GOLD, PLATINUM)
- equipe_id (FK → equipe)
- stats (JSON)
```

#### `equipe` (Times/Squads)
```
- id (PK)
- nome
- descricao
- criada_em
```

#### `partida` (Matches/Jogos)
```
- id (PK)
- equipe_id (FK → equipe)
- data
- resultado
- stats (JSON)
```

Mais tabelas: `venda`, `estoque`, `log`, `solicitacao`

---

## 🔄 Lidar com Mudanças de Schema

### Quando Adicionar Nova Coluna

1. **Edite `models.py`** (em `backend/models.py`)
   ```python
   class User(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       email = db.Column(db.String(120), unique=True)
       nova_coluna = db.Column(db.String(100))  # ← Novo
   ```

2. **Execute migração** (se houver dados)
   ```powershell
   python scripts/update_db.py
   ```

3. **Ou delete e reinicialize** (se não houver dados importantes)
   ```powershell
   rm instance/database.db
   python infrastructure/database/init_db.py
   ```

### Quando Mudar Tipo de Coluna

1. **Backup da database**
   ```powershell
   copy instance/database.db instance/database.db.backup
   ```

2. **Altere `models.py`**

3. **Recrie database**
   ```powershell
   rm instance/database.db
   python infrastructure/database/init_db.py
   ```

---

## 🐛 Troubleshooting

### ❌ "Database is locked"
```powershell
# Fecha processos Flask
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
# Aguarde alguns segundos
Start-Sleep -Seconds 2
python infrastructure/database/init_db.py
```

### ❌ "Table already exists"
- Delete `instance/database.db`
- Rode `init_db.py` novamente

### ❌ "Foreign key constraint failed"
- Verifique que `equipe` existe antes de criar `operador`
- Use `init_db.py` que cria na ordem correta

### ❌ "Migration failed"
1. Backup database
2. Delete `instance/database.db`
3. Rodeinit_db.py
4. Restaure dados manualmente se necessário

---

## 📦 Backup e Restore

### Fazer Backup
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
copy instance/database.db "backups/database_${timestamp}.db"
```

### Restaurar
```powershell
copy backups/database_[timestamp].db instance/database.db
```

### Backup Automático
Railway faz backup automático de PostgreSQL:
- Você pode restaurar versões anteriores
- Dados nunca são perdidos

---

## 🔍 Verificar Integridade

### Ver Tabelas
```powershell
python -c "from app import app; from backend.models import db; app.app_context().push(); print([table for table in db.metadata.tables])"
```

### Ver Registros
```powershell
python -c "from app import app; from backend.models import User; app.app_context().push(); print(f'Total users: {User.query.count()}')"
```

---

## 🗂️ Estrutura de Diretórios

```
infrastructure/database/
├── init_db.py              ← Use isto para criar database
├── migrations/             ← Scripts de migração (futura)
│   ├── migrate_session.py
│   ├── migrate_2fa.py
│   └── [outras]
└── README.md               ← Você está aqui
```

---

## 💡 Boas Práticas

1. **Sempre fazer backup** antes de alterações
2. **Testar localmente** antes de produção
3. **SQLite é para desenvolvimento**, PostgreSQL para produção
4. **Railway cuida de backups** automaticamente
5. **Logs de erro** ficam em `logs/database.log`

---

**Última atualização**: 2026-03-02  
**SQLite versão**: 3.x+  
**PostgreSQL suportado**: 12+
