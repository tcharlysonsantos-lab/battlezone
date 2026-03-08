# 🔧 VERIFICAÇÃO - Página de Eventos

## Status das Seções em Eventos

### ✅ Seções que devem estar presentes:

1. **Seção 1: Eventos - Warfield**
   - Mostra eventos cadastrados para o campo Warfield
   - Ordenados: próximos primeiro, depois passados
   - Location: `frontend/templates/eventos.html` linhas ~50-150

2. **Seção 2: Eventos - Redline**
   - Mostra eventos cadastrados para o campo Redline
   - Ordenados: próximos primeiro, depois passados
   - Location: `frontend/templates/eventos.html` linhas ~150-250

3. **Seção 3: Eventos - Geral**
   - Mostra eventos genéricos (campo GERAL)
   - Ordenados: próximos primeiro, depois passados
   - Location: `frontend/templates/eventos.html` linhas ~250-300

4. **Seção 4: Sorteios & Resultados**
   - Sorteios de operadores (semanais)
   - Sorteios de equipes (mensais)
   - Location: `frontend/templates/eventos.html` linhas ~250-1000

---

## 🔍 Como Verificar se está Funcionando

### Passo 1: Verificar Backend (app.py)
```python
@app.route('/eventos')
def eventos():
    # Deve ter:
    ✅ Queries de eventos (Warfield, Redline, GERAL)
    ✅ Queries de battlepasses (operador, equipe)
    ✅ Preenchimento de sorteios_data
    ✅ render_template(..., sorteios_data=sorteios_data, ...)
```

**Status:** ✅ Verificado - app.py tem tudo

### Passo 2: Verificar Template (eventos.html)
```html
<!-- Deve ter: -->
✅ Seção de eventos Warfield
✅ Seção de eventos Redline
✅ Seção de eventos Geral
✅ Seção de sorteios com {% if sorteios_data %}
✅ Loop por battlepasses_operador
✅ Loop por battlepasses_equipe
```

**Status:** ✅ Verificado - eventos.html tem tudo

---

## 🚨 Possíveis Problemas

### Problema 1: Nenhum battlepass cadastrado
**Sintoma:** Seção de sorteios aparece vazia
**Causa:** Nenhum registro em `battlepass` table
**Solução:** Criar battlepasses via admin

### Problema 2: Nenhum sorteio realizado
**Sintoma:** Sorteios mostram "Nenhum sorteio realizado"
**Causa:** Nenhum registro em `sorteio` table para esta semana/mês
**Solução:** Executar um sorteio via página de sorteios

### Problema 3: Template não renderiza
**Sintoma:** Página não carrega ou erro 500
**Causa:** Erro de sintaxe Jinja2 ou variável indefinida
**Solução:** Verificar logs do Railway

### Problema 4: Dados antigos sendo mostrados
**Sintoma:** Vê sorteios de mês/semana anterior
**Causa:** Dados casuais não resetando corretamente
**Solução:** Verificar se mês/ano/semana estão corretos no código

---

## 📋 Checklist de Deploy

After commit `0210ec7` deployado:

- [ ] Railway rebuild completo (~60 segundos)
- [ ] Página /eventos carrega sem erros
- [ ] Seções de eventos aparecem
- [ ] Seção de sorteios aparece
- [ ] Dados de sorteios exibem corretamente

---

## 🔗 Relacionados

- Commit com correção de sorteios no dashboard: `fab8e6d`
- Commit com análise de desincronização: `743c118`
- Commit com limpeza de arquivos: `0210ec7`

---

## 📞 Se Eventos Ainda Não Aparecer

1. Verificar logs do Railway para erros
2. Confirmar que battlepasses existem no BD
3. Confirmar que sorteios foram criados
4. Fazer test login e navegar para /eventos manualmente
5. Verificar elementos no browser DevTools (F12)

O backend está preparado. Se ainda não aparecer, é problema no frontend ou dados faltando no banco.
