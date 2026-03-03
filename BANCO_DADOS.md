# 🗄️ CONFIGURAÇÃO DE BANCO DE DADOS PERSISTENTE

## Opções Disponíveis para Railway

### 1️⃣ **PostgreSQL** ⭐ RECOMENDADO
- **Tipo:** Banco relacional SQL
- **Custo:** Gratuito (no Railway)
- **Persistência:** ✅ Sim (dados voltam entre deploys)
- **Melhor para:** Produção profissional
- **Status:** Mais confiável e robusto

### 2️⃣ **MySQL**
- **Tipo:** Banco relacional SQL
- **Custo:** Gratuito (no Railway)
- **Persistência:** ✅ Sim
- **Melhor para:** Compatibilidade geral
- **Status:** Funciona bem também

### 3️⃣ **MongoDB**
- **Tipo:** NoSQL (documento)
- **Custo:** Gratuito (no Railway)
- **Persistência:** ✅ Sim
- **Melhor para:** Dados não-estruturados
- **Status:** Requer mudanças no código

### ❌ SQLite Local (ATUAL)
- **Problema:** Dados perdidos a cada redeploy
- **Por que:** Arquivo local não persiste no Railway
- **Solução:** Migrar para PostgreSQL/MySQL

---

## 🚀 COMO ADICIONAR POSTGRESQL NO RAILWAY

### Passo 1: Adicionar PostgreSQL no Railway
```bash
# No dashboard do Railway:
1. Vá para seu projeto
2. Clique em "Create" ou "Add Service"
3. Selecione "PostgreSQL"
4. Pronto! Railway configura automaticamente
```

### Passo 2: Railway Configura Automaticamente
Quando você adiciona PostgreSQL:
- ✅ Cria a instância do banco
- ✅ Define variável `DATABASE_URL` automaticamente
- ✅ Sua app Flask já detecta e usa!

### Passo 3: Verificar Conexão
```bash
# O arquivo config.py JÁ há código para detectar:
if _database_url:
    # Railway PostgreSQL
    SQLALCHEMY_DATABASE_URI = _database_url
else:
    # SQLite local
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_file}'
```

---

## 📋 COMPARAÇÃO RÁPIDA

| Feature | SQLite | PostgreSQL | MySQL |
|---------|--------|-----------|-------|
| Persistência | ❌ Não | ✅ Sim | ✅ Sim |
| Perfil Múltiplo | ❌ Não | ✅ Sim | ✅ Sim |
| Custo | Grátis | Grátis* | Grátis* |
| Produção | ❌ Não | ✅ Sim | ✅ Sim |
| Backup | Manual | Automático | Automático |
| Complexidade | Fácil | Média | Média |

---

## ✅ PRÓXIMOS PASSOS

1. Adicionar PostgreSQL no Railway
2. Fazer primeiro deploy (banco será migrado automaticamente)
3. Testar se os dados persistem entre deploys
4. Configurar backups automáticos (opcional)

---

## 🔗 DOCUMENTAÇÃO OFICIAL
- Railway PostgreSQL: https://docs.railway.app/databases/postgresql
- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/

---

## 💡 RESUMO
**USE POSTGRESQL NO RAILWAY!** 🎯
- Melhor performance
- Dados persistem
- Gratuito
- Automático
