# ANÁLISE DE PERFORMANCE E GARGALOS

## 🔴 PROBLEMAS CRÍTICOS ENCONTRADOS

### 1. N+1 QUERIES PROBLEM (CRÍTICO)

**`calendario_publico()` - app.py linha 214**
```python
# ❌ PROBLEMA: Busca TODAS as partidas, depois filtra em Python
todas_partidas = Partida.query.filter_by(finalizada=False).all()
for p in todas_partidas:
    len(p.participantes)  # Causa QUERY separada para cada partida!
```

**`dashboard()` - app.py linha 272**
```python
# ❌ PROBLEMA: Múltiplas queries separadas
total_operadores = Operador.query.count()      # Query 1
total_equipes = Equipe.query.count()           # Query 2
partidas_hoje = Partida.query.filter(...).count()  # Query 3
itens_baixo = Estoque.query.filter(...).all()     # Query 4
```

### 2. PROCESSAMENTO PESADO EM PYTHON

**`sort_eventos_by_proximity()` - app.py linha 310**
- Processa TODOS os eventos em Python
- Separa em 2 arrays depois ordena
- Deveria ser feito no SQL com `ORDER BY`

### 3. IMPORTS DESNECESSÁRIOS DENTRO DE FUNÇÕES

```python
import calendar        # Em cada request!
import json            # Em cada request!
import logging         # Em cada request!
from datetime import datetime  # Em cada request!
```

### 4. SESSION CHECK PESADO EM CADA REQUEST

`before_request()` - app.py linha 163
- Verifica `is_session_valid()` A CADA REQUEST
- Faz `update_activity()` com COMMIT a cada request
- Deveria ter threshold de 30s antes de atualizar

---

## 🟢 OTIMIZAÇÕES A FAZER

### 1. Filtrar Datas no SQL (não em Python)
- [ ] calendario_publico: Filtrar `data` com `Partida.data == hoje`
- [ ] Usar eager_loading para `participantes`

### 2. Consolidar Queries
- [ ] dashboard: Usar 1 query com count() agregado
- [ ] Usar joinedload() para relacionamentos

### 3. Cache de Dados Estáticos
- [ ] Cache 5 minutos: total de operadores, equipes
- [ ] Cache 10 minutos: eventos ativos
- [ ] Cache 1 minuto: itens de estoque com nível baixo

### 4. Lazy Loading Otimizado
- [ ] Operador.membros: usar `lazy='dynamic'` (já tem!)
- [ ] Partida.participantes: eagerly load quando necessário

### 5. Índices de Banco de Dados
- [ ] Partida.data: índice para buscas frequentes
- [ ] Operador.warname: índice (já é unique)
- [ ] Estoque.quantidade: índice para busca de itens baixos

### 6. Remover Imports Dentro de Funções
- [ ] Mover para imports globais no topo

---

## 📊 IMPACTO ESPERADO

| Otimização | Impacto | Por quê |
|------------|---------|--------|
| SQL Filtering | **-50% queries** | Não processar em Python |
| Cache | **-80% queries** | Não refazer dados invariáveis |
| Eager Loading | **-10 queries** | Carregar tudo de uma vez |
| Session Throttle | **-50% commits** | Não salvar a cada request |

---

## PRIORIDADE

1. **CRÍTICO**: Filtrar datas no SQL (calendario_publico)
2. **CRÍTICO**: Consolidar queries no dashboard
3. **ALTO**: Adicionar cache para dados estáticos
4. **MÉDIO**: Lazy loading otimizado
5. **BAIXO**: Índices no banco

