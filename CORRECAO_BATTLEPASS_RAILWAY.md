# 🔨 CORREÇÃO CRÍTICA - Battlepass VARCHAR Truncation

## ⚠️ PROBLEMA IDENTIFICADO

```
StringDataRightTruncation: value too long for type character varying(10)
Campo 'battlepass' está VARCHAR(10) mas precisa de 13+ caracteres para 'ELITE_CAVEIRA'
```

**Status**: 🔴 CRÍTICO - Bloqueia 100% da funcionalidade de battlepass

---

## ✅ SOLUÇÃO - Execute UMA destas opções

### **OPÇÃO 1: Via Rota de Setup (Mais Fácil - RECOMENDADA)**

```bash
# 1. Obtenha sua SECRET_KEY
# Railway Dashboard → Variables → SECRET_KEY

# 2. Acesse via navegador:
https://battlezone-production.up.railway.app/setup/corrigir-colunas/<SECRET_KEY>

# 3. Substitua <SECRET_KEY> pela chave real
# Exemplo:
https://battlezone-production.up.railway.app/setup/corrigir-colunas-force/sk_live_abc123xyz789...
```

**Resultado esperado:**
```json
{
    "sucesso": true,
    "etapas": [
        {
            "etapa": 1,
            "descricao": "Alterar operadores.battlepass",
            "resultado": "✅ Sucesso"
        },
        {
            "etapa": 2,
            "descricao": "Alterar equipes.battlepass",
            "resultado": "✅ Sucesso"
        }
    ],
    "timestamp": "2026-03-07T21:30:45.123456"
}
```

---

### **OPÇÃO 2: Via Railway CLI**

```bash
# 1. Instalar Railway CLI (se não tiver)
npm install -g @railway/cli

# 2. Fazer login
railway login

# 3. Selecionar projeto
railway link

# 4. Executar fix
railway run python fix_battlepass_column.py
```

---

### **OPÇÃO 3: Via Script Local (Para Ambiente de Desenvolvimento)**

```bash
# 1. Ativar venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# 2. Executar script
python fix_battlepass_column.py
```

---

## 🧪 VERIFICAR CORREÇÃO

### **Checklist de Validação:**

- [ ] Acessar página de operador
- [ ] Ir para editar operador
- [ ] Campo "Battlepass" agora mostra 'ELITE_CAVEIRA'?
- [ ] Tentar salvar operador com 'ELITE_CAVEIRA'
- [ ] Verificar se salvou sem erro 500
- [ ] Acessar página de equipe
- [ ] Adicionar membro à equipe
- [ ] Verificar se edição de equipe funciona

---

## 🐛 SE AINDA NÃO FUNCIONAR

### **Troubleshooting:**

1. **Erro 403 - Invalid secret key**
   - Copie a SECRET_KEY exatamente como está
   - Remova espaços ou aspas extras

2. **Erro 500 ainda persiste**
   - Railway foi reiniciado após a correção?
   - Verifique o banco em Railway dashboard → Postgres
   - Rode: `SELECT * FROM information_schema.columns WHERE table_name='operadores' AND column_name='battlepass'`

3. **Imagens ainda 404**
   - Verifique conexão HTTPS
   - URLs devem estar como: `/static/uploads/upload_XXXXXX.png`
   - Não: `static/uploads/...`

---

## 📊 MUDANÇAS IMPLEMENTADAS

### **Arquivo config.py**
```python
# ANTES:
UPLOAD_FOLDER = 'static/uploads'

# DEPOIS:
# Em produção (Railway), usar caminho ABSOLUTO
if os.environ.get('FLASK_ENV') == 'production':
    UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, 'frontend/static/uploads'))
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'frontend/static/uploads')
```

### **Schema PostgreSQL**
```sql
-- ANTES (Erro):
ALTER TABLE operadores ALTER COLUMN battlepass TYPE character varying(10);
ALTER TABLE equipes ALTER COLUMN battlepass TYPE character varying(10);

-- DEPOIS (Correto):
ALTER TABLE operadores ALTER COLUMN battlepass TYPE character varying(50);
ALTER TABLE equipes ALTER COLUMN battlepass TYPE character varying(50);
```

---

## 📝 PRÓXIMAS AÇÕES

1. **Executar uma das opções acima** ✅
2. **Validar com checklist** ✅
3. **Testar operador ELITE_CAVEIRA** ✅
4. **Testar edição de equipe** ✅
5. **Verificar imagens de equipes** ✅

---

## 🆘 SUPORTE

Se persistir erro após seguir todas as etapas:
- Verifique logs em Railway
- Confirme que DATABASE_URL está apontando para PostgreSQL
- Execute: `psql $DATABASE_URL -c "SELECT battlepass FROM operadores LIMIT 1;"`

