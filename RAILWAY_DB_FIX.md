# Railway Database Fix - Forçar Inicialização do PostgreSQL

## 🔴 Problema
As tabelas do PostgreSQL não estão sendo criadas automaticamente no Railway, causando erros:
- `ERRO: a relação "eventos" não existe` 
- `ERRO: a relação "battlepasses" não existe`

## ✅ Solução Implementada

### 1. **Auto-Inicialização no Startup** (AUTOMÁTICO)
- `run.py`: Modificado para SEMPRE chamar `db.create_all()` em startup
- `app.py`: Adicionado verificação no `before_request` para detectar e criar tabelas faltantes
- `backend/init_db.py`: Melhorado com retry logic e verificação de tabelas críticas
- `wsgi.py`: Já chamava `init_database()` - funciona com Railway

### 2. **Modelos Registrados Corretamente**
- `app.py` linha 22: Importados `Sorteio, Battlepass`
- `backend/init_db.py` linha 5: Importados `Evento, Sorteio, Battlepass`
- Garante que SQLAlchemy registre todos os modelos

### 3. **Endpoints de Emergência** (COM SECRET_KEY)
Se as tabelas ainda não estiverem criadas depois do deploy, use:

```bash
# 1. Verificar Status
curl https://seuapp.railway.app/setup/info

# 2. Forçar Inicialização (SUBSTITUA {{SECRET_KEY}} pela sua chave)
curl https://seuapp.railway.app/setup/init-database/{{SECRET_KEY}}

# 3. Ver Estatísticas
curl https://seuapp.railway.app/setup/db-stats
```

### 4. **Para Railway Console (SSH)**
Se conseguir acesso SSH ao Railway:

```bash
# Entrar no console
railway run bash

# Criar tabelas manualmente
flask init-db
```

## 📋 Checklist After Deploy

- [ ] Aguardar 30-60 segundos após deploy
- [ ] Verificar logs no Railway: `[DB] All critical tables exist`
- [ ] Testar `/setup/info` - deve listar tabelas
- [ ] Testar dashboard - deve carregar eventos e sorteios
- [ ] Verificar `/setup/db-stats` - deve mostrar contagens

## 🚨 Se Ainda Não Funcionar

1. **Logs do Railway**: Ver se há erros de conexão PostgreSQL
2. **Variáveis de Ambiente**: Verificar se `DATABASE_URL` está correto
3. **Memory Limit**: Railway pode estar matando processo por falta de memória
4. **Endpoint de Força**: Use `/setup/init-database/{{SECRET_KEY}}` com SECRET_KEY da env
5. **Reset Completo**: Deletar volume PostgreSQL e redeploy (perderá dados!)

## 📝 Nota Técnica

O problema ocorria porque `run.py` tinha verificação condicional:
```python
# ANTES (BUG):
if 'sqlite' in db_url:
    db.create_all()  # Só criava em SQLite!
else:
    print("Banco será inicializado depois")  # Nunca acontecia!
```

Agora é forçado:
```python
# DEPOIS (CORRETO):
db.create_all()  # SEMPRE cria, independente de SQLite ou PostgreSQL
# + Retry logic no before_request
```

## 🔑 Encontrar SECRET_KEY

A SECRET_KEY está em `RAILWAY_DEPLOYMENT.env` ou variáveis de ambiente da Railway.
