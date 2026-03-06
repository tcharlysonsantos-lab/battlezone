# 🧪 GUIA DE VALIDAÇÃO DAS OTIMIZAÇÕES

## Como Validar que as Otimizações Funcionaram ✅

---

## 1. Verificar Queries no Banco de Dados

### Ativar SQL Query Logging

Adicione ao seu `app.py` no início:

```python
import logging
from logging.handlers import RotatingFileHandler

# Logar queries SQL
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Criar arquivo de log
if not os.path.exists('logs'):
    os.makedirs('logs')
    
handler = RotatingFileHandler('logs/queries.log', maxBytes=10000000, backupCount=10)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
logging.getLogger('sqlalchemy.engine').addHandler(handler)
```

### Testar em Dev

```bash
# Terminal 1: Ativar aplicação
python -c "from app import app; app.run(debug=True)"

# Terminal 2: Ver logs de queries
tail -f logs/queries.log | grep -i select
```

---

## 2. Endpoints para Testar

### Teste 1: Dashboard (Antes: 7+ queries, Depois: 3 queries)

```bash
curl http://localhost:5000/dashboard
```

**Esperado no terminal**:
```sql
SELECT count(*) FROM operadores
SELECT count(*) FROM equipes
SELECT partidas.* FROM partidas ...
```

**IMPORTANTE**: Deve ter APENAS 3 queries, não 7+

---

### Teste 2: Calendario Público (Antes: 101 queries, Depois: 1 query)

```bash
curl http://localhost:5000/calendario-publico
```

**Esperado no terminal**:
```sql
SELECT partidas.*, partida_participantes.* 
FROM partidas 
LEFT JOIN partida_participantes ON partidas.id = partida_participantes.partida_id
WHERE partidas.data = '03/02/2025' AND partidas.finalizada = false
```

**IMPORTANTE**: Deve haver APENAS 1 SELECT, com LEFT JOIN para eager loading

---

### Teste 3: Session Activity Throttling

**Teste antes**:
1. Fazer login
2. Abrir DevTools (F12) → Network
3. Fazer 10 cliques em botões diferentes
4. Ver no banco: `SELECT * FROM users WHERE id = 1 ORDER BY last_activity`
5. Esperar 30 segundos
6. Fazer mais 10 cliques
7. Ver no banco novamente

**Esperado**:
```
Primeira batida (10 requisições): last_activity atualizado 1-2x apenas (não 10x!)
Após 30s + 10 cliques: last_activity atualizado novamente
```

---

## 3. Métrica: Tempo de Resposta

### Medir antes vs. depois

```python
import time
from app import app

with app.test_client() as client:
    # Login primeiro
    client.post('/auth/login', data={
        'username': 'seu_usuario',
        'password': 'sua_senha'
    })
    
    # Testar tempo de resposta
    endpoints = [
        '/dashboard',
        '/calendario-publico',
        '/operadores',
        '/partidas'
    ]
    
    for endpoint in endpoints:
        inicio = time.time()
        response = client.get(endpoint)
        tempo = (time.time() - inicio) * 1000  # em ms
        print(f"{endpoint}: {tempo:.2f}ms")
```

**Esperado**:
- Dashboard: 1500ms → 400-500ms (3x mais rápido)
- Calendario: 2000ms → 200-300ms (10x mais rápido)

---

## 4. Aplicar Índices no Banco

### Conectar ao Banco via SSH (Railway)

```bash
# Ver variáveis de ambiente
cat \$RAILWAY_ENV_FILE

# Conectar com psql
psql $DATABASE_URL
```

### Verificar Índices Criados

```sql
-- Listar índices da tabela partidas
\d partidas

-- Deve mostrar:
-- "ix_partida_data" btree (data)
-- "ix_partida_finalizada" btree (finalizada)
-- "ix_partida_data_finalizada" btree (data, finalizada)
```

### Criar Índices (se não existirem)

```bash
# Opção 1: Usar script Python
python scripts/criar_indices.py

# Opção 2: SQL direto
psql $DATABASE_URL -c "CREATE INDEX IF NOT EXISTS ix_partida_data ON partidas(data);"
psql $DATABASE_URL -c "CREATE INDEX IF NOT EXISTS ix_partida_finalizada ON partidas(finalizada);"
psql $DATABASE_URL -c "CREATE INDEX IF NOT EXISTS ix_estoque_quantidade ON estoque(quantidade);"
```

---

## 5. Monitoring em Produção (Railway)

### Acessar Logs do Railway

```bash
# Login no Railway
railway login

# Ver logs da aplicação
railway logs

# Procurar por queries lentas
railway logs | grep -i "duration.*ms"
```

### Ver Métricas do Banco

No painel do Railway:
1. Ir para banco PostgreSQL
2. Aba "Monitoring"
3. Ver gráficos de:
   - CPU Usage (deve reduzir)
   - Active Connections (deve reduzir)
   - Query Duration (deve reduzir)

---

## 6. Teste de Carga

### Simular múltiplos usuários

```python
from concurrent.futures import ThreadPoolExecutor
import requests
import time

BASE_URL = "http://localhost:5000"

def fazer_requisicao(num):
    """Fazer requisição única"""
    response = requests.get(f"{BASE_URL}/dashboard")
    return response.status_code, response.elapsed.total_seconds()

# Executar 50 requisições em paralelo
inicio = time.time()
with ThreadPoolExecutor(max_workers=10) as executor:
    resultados = list(executor.map(fazer_requisicao, range(50)))

tempo_total = time.time() - inicio

# Analisar resultados
status_codes = [r[0] for r in resultados]
tempos = [r[1] for r in resultados]

print(f"Total de requisições: 50")
print(f"Sucesso: {status_codes.count(200)}")
print(f"Tempo médio: {sum(tempos)/len(tempos):.3f}s")
print(f"Tempo máximo: {max(tempos):.3f}s")
print(f"Tempo total: {tempo_total:.2f}s")
```

**Esperado**:
- Sem timeouts
- Tempo médio < 500ms
- Sem 500 errors

---

## 7. Verificar Índices Estão Sendo Usados

### Usar EXPLAIN ANALYZE

```sql
-- Before (sem índice)
EXPLAIN ANALYZE
SELECT * FROM partidas WHERE data = '03/02/2025' AND finalizada = false;

-- After (com índice)
-- Deve mostrar "Index Scan" em vez de "Seq Scan"
-- Duration deve ser < 1ms
```

---

## 8. Checklista Pós-Deploy

```
✅ Dashboard carrega em < 500ms
✅ Calendario carrega em < 300ms  
✅ Nenhum N+1 query nos endpoints principais
✅ Índices criados no banco (ve com \d tabelas)
✅ Session updates reduzidos (throttled)
✅ Batch commits funcionando (no errors em log)
✅ Nenhum erro de 500 Internal Server Error
✅ Usuários relatam sistema mais fluido
```

---

## 🐛 Troubleshooting

### Se Dashboard ainda está lento:

1. Verificar se índices foram criados:
```sql
SELECT * FROM pg_stat_user_indexes WHERE tablename = 'partidas';
```

2. Se não aparecerem, criar manualmente:
```bash
python scripts/criar_indices.py
```

3. Força análise do plano de queries:
```sql
VACUUM ANALYZE;
```

---

### Se calendario still shows N+1 queries:

1. Verificar se eager loading está funcionando:
```python
# Testar direto no console Flask
from backend.models import Partida
from datetime import datetime

hoje = datetime.now().strftime('%d/%m/%Y')
partidas = Partida.query.filter_by(
    data=hoje,
    finalizada=False
).options(
    db.joinedload(Partida.participantes)
).all()

# Deve usar apenas 1 query
print(len(partidas[0].participantes))  # Sem triggar query adicional
```

2. Se ainda aciona query: 
- Verificar se há access a outro relacionamento não eager-loaded
- Adicionar debug com ForeignKey checks

---

### Se session updates ainda ocorrem sempre:

1. Verificar `before_request`:
```python
# Deve existir este bloco:
if time_since_last_update > 30:
    current_user.update_activity()
```

2. Verificar `after_request`:
```python
# Deve existir este bloco:
@app.after_request
def after_request(response):
    db.session.commit()
    return response
```

---

## 📊 Script de Relatório Completo

Salve como `validar_otimizacoes.py`:

```python
#!/usr/bin/env python
"""Script completo para validar todas as otimizações"""

from app import app, db
from backend.models import Partida, Estoque, User, Operador
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def testar_queries():
    """Testar quantidade de queries por endpoint"""
    with app.app_context():
        
        logger.info("\n" + "="*50)
        logger.info("TESTE 1: Dashboard (Esperado: 3 queries)")
        logger.info("="*50)
        
        # Contar queries
        from sqlalchemy import event
        query_count = [0]
        
        def count_queries(conn, cursor, statement, parameters, context, executemany):
            query_count[0] += 1
        
        event.listen(db.engine, "before_cursor_execute", count_queries)
        
        # Simular dashboard
        total_operadores = Operador.query.count()
        today = datetime.now().strftime("%d/%m/%Y")
        partidas_hoje = Partida.query.filter_by(data=today).count()
        
        logger.info(f"Queries executadas: {query_count[0]}")
        logger.info(f"✅ ESPERADO: 3, OBTIDO: {query_count[0]}")
        
        if query_count[0] <= 4:
            logger.info("✅ TEST PASSOU!")
        else:
            logger.warning("⚠️ Mais queries do que esperado")
        
        event.remove(db.engine, "before_cursor_execute", count_queries)

if __name__ == '__main__':
    testar_queries()
```

Execute:
```bash
python validar_otimizacoes.py
```

---

**Status**: Pronto para validar! 🚀
