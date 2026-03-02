# 🔄 Sincronização de Estatísticas - Implementação Completa

## Problema Identificado
- Quando você **deleta partidas diretamente no banco de dados** (sem usar o sistema), as estatísticas dos operadores ficam **inconsistentes**
- As estatísticas já foram somadas ao operador, mas a partida foi deletada
- Ficam registros órfãos de `PartidaParticipante` sem `partida_id` válido

## Solução Implementada

### 1️⃣ Função de Sincronização (`utils.py`)

#### `sincronizar_estatisticas_operadores()`
```python
def sincronizar_estatisticas_operadores():
    """
    Sincroniza as estatísticas dos operadores removendo registros órfãos
    e recalculando as estatísticas baseado no que existe de verdade.
    """
```

**O que faz:**
1. Remove todos os `PartidaParticipante` órfãos (cujas partidas foram deletadas)
2. Reseta as estatísticas de TODOS os operadores
3. Recalcula as estatísticas varrendo cada participação válida
4. Procura (precautoriamente) por mais registros órfãos durante o cálculo

**Campos recalculados:**
- `total_kills`, `total_deaths`
- `total_vitorias`, `total_derrotas`
- `total_mvps`
- `total_capturas`, `total_plantas_bomba`, `total_desarmes_bomba`
- `total_refens`, `total_cacos`
- `total_partidas`

---

#### `remover_estadisticas_partida(partida)`
```python
def remover_estadisticas_partida(partida):
    """
    Remove as estatísticas de uma partida das estatísticas dos operadores.
    Deve ser chamado ANTES de deletar a partida.
    """
```

**O que faz:**
- Remove as stats de cada participação da partida do operador
- Usa `max(0, ...)` para evitar valores negativos
- Chamada automaticamente quando deletar via sistema

---

### 2️⃣ Atualização da Função `deletar_partida()` (`app.py`)

**Novo fluxo:**
```
1. Remover as estatísticas DOS OPERADORES (se finalizada)
   ↓
2. Devolver BBs ao estoque
   ↓
3. Remover vendas associadas
   ↓
4. Deletar a partida (cascade deleta participantes)
```

**Antes:**
- ❌ Não removia as estatísticas do operador
- ❌ Deixava dados inconsistentes se partida tinha sido finalizada

**Depois:**
- ✅ Remove as stats ANTES de deletar
- ✅ Garante integridade dos dados

---

### 3️⃣ Rota Admin (`app.py`)

**Endpoint:** `/admin/sincronizar-estatisticas`

```python
@app.route('/admin/sincronizar-estatisticas', methods=['GET', 'POST'])
@login_required
@admin_required
def sincronizar_estatisticas_admin():
    """
    GET: Mostra página de confirmação
    POST: Executa sincronização
    """
```

**Fluxo:**
1. Admin clica no botão
2. Vai para página de confirmação
3. Confirma a ação
4. Sincronização executa
5. Mostra resultado (sucesso/erro)

---

### 4️⃣ Script Standalone (`sync_stats.py`)

Pode rodar manualmente do terminal sem precisar da interface web:

```bash
python sync_stats.py
```

**Output:**
```
======================================================================
🔄 SINCRONIZAÇÃO DE ESTATÍSTICAS DOS OPERADORES
======================================================================

📍 Etapa 1: Procurando por registros órfãos...
   ✅ Nenhum registro órfão encontrado

📍 Etapa 2: Recalculando estatísticas dos operadores...
   [  1/3] Keno            -  2 partida(s) - K/D: 10/2
   [  2/3] teste           -  2 partida(s) - K/D: 1/8
   [  3/3] 222             -  2 partida(s) - K/D: 1/2

   ✅ 3 operador(es) recalculado(s)

======================================================================
✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!
======================================================================
```

---

### 5️⃣ Interface Web (`templates/admin/usuarios.html`)

Adicionado novo **Card de Sincronização** na página de admin de usuários:

```html
<!-- Card de Sincronização -->
<div class="card mt-4 border-warning">
    <div class="card-header bg-warning text-dark">
        <h6 class="mb-0">
            <i class="fas fa-sync-alt me-2"></i>Ferramentas de Sincronização
        </h6>
    </div>
    <div class="card-body">
        <p class="text-muted mb-3">Use essa ferramenta se você deletou partidas...</p>
        
        <a href="{{ url_for('sincronizar_estatisticas_admin') }}" class="btn btn-warning">
            <i class="fas fa-refresh me-2"></i>Sincronizar Estatísticas dos Operadores
        </a>
    </div>
</div>
```

**Acessível em:** `/admin/usuarios`

---

## Como Usar

### Opção 1: Via Interface Web (Recomendado)
1. Acesse `/admin/usuarios`
2. Scroll até "Ferramentas de Sincronização"
3. Clique em "Sincronizar Estatísticas dos Operadores"
4. Confirme a ação
5. Resultado é exibido com mensagem de sucesso/erro

### Opção 2: Via Terminal (Rápido)
```bash
# Ativar venv
.\.venv\Scripts\Activate.ps1

# Rodar script
python sync_stats.py
```

---

## Quando Usar?

✅ **Use se:**
- Deletou partidas diretamente no banco via SQL
- Estatísticas dos operadores estão erradas/inconsistentes
- Vencedor/derrotas não batem com o esperado

❌ **NÃO precisa usar se:**
- Deletou partidas via sistema (Web UI)
- Sistema nunca foi acessado diretamente no banco

---

## Segurança

- ✅ Requer autenticação (`@login_required`)
- ✅ Requer nível admin (`@admin_required`)
- ✅ Usa `max(0, ...)` para evitar overflow
- ✅ Transações ACID com rollback em caso de erro

---

## Tratamento de Erros

Se algo der errado:
1. Todas as mudanças são **revertidas** (rollback)
2. Mensagem de erro é exibida
3. Log é registrado no servidor
4. Dados ficam em estado consistente

---

## Arquivos Modificados

1. **`utils.py`** (+105 linhas)
   - Adicionadas 2 funções de sincronização

2. **`app.py`** (+25 linhas)
   - Atualizada função `deletar_partida()`
   - Adicionada rota `/admin/sincronizar-estatisticas`

3. **`sync_stats.py`** (novo, 160 linhas)
   - Script standalone para sincronização

4. **`templates/admin/sincronizar_estatisticas.html`** (novo, 52 linhas)
   - Página de confirmação

5. **`templates/admin/usuarios.html`** (+18 linhas)
   - Adicionado card de sincronização

---

## Próximos Passos (Opcional)

- [ ] Adicionar agendamento automático de sincronização (semanal/diário)
- [ ] Criar logs detalhados de sincronizações
- [ ] Adicionar filtros de sincronização (por operador, data range, etc)
- [ ] Dashboard mostrando status das sincronizações

