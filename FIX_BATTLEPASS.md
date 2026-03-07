# 🔨 Corrigir Erro do Battlepass - Guide

## ❌ Erro
```
StringDataRightTruncation: value too long for type character varying(10)
Tentando guardar: 'ELITE_CAVEIRA' (13 caracteres)
Coluna permite: 10 caracteres
```

---

## ✅ Solução Rápida (Railway)

### **Opção 1: Via Railway CLI (Recomendado)**

```bash
# 1. Instalar Railway CLI se não tiver:
# npm install -g @railway/cli

# 2. Fazer login:
railway login

# 3. Selecionar o projeto:
railway link

# 4. Executar o script de fix:
railway run python fix_battlepass_column.py
```

**Resultado esperado:**
```
[INFO] 🔨 Corrigindo tamanho da coluna 'battlepass'...
============================================================
Banco de dados: postgresql

[INFO] Executando alterações para PostgreSQL...
  - Alterando operadores.battlepass (10 → 50)...
  - Alterando equipes.battlepass (10 → 50)...

✅ Colunas corrigidas com sucesso!
============================================================

Agora você pode:
  ✓ Atualizar operadores com battlepass 'ELITE_CAVEIRA'
  ✓ Atualizar equipes com battlepass 'EQUIPE_BASICA'

Tamanho anterior: 10 caracteres
Tamanho novo: 50 caracteres
```

---

### **Opção 2: Via Railway Dashboard**

1. Acesse: https://railway.app
2. Selecione seu projeto "Battlezone Production"
3. Clique em "CLI" ou "Terminal"
4. Copie e cole:
```bash
python fix_battlepass_column.py
```

---

## ✅ Solução Alternativa (URL com SECRET_KEY)

Acesse no navegador:
```
https://battlezone-production.up.railway.app/setup/corrigir-colunas/SUA_SECRET_KEY
```

Substitua `SUA_SECRET_KEY` pela SECRET_KEY do seu Railway.

---

## ✅ Verificar se Funcionou

Após executar o fix:

1. Acesse a página de um operador
2. Tente atualizar o campo "Battlepass" 
3. Selecione "ELITE_CAVEIRA"
4. Salve

Se funcionar sem erro → ✅ Tudo correto!

---

## 📋 O que o Script Faz

```sql
-- Corrige a coluna de operadores
ALTER TABLE operadores 
ALTER COLUMN battlepass 
TYPE character varying(50);

-- Corrige a coluna de equipes
ALTER TABLE equipes 
ALTER COLUMN battlepass 
TYPE character varying(50);
```

**Antes:** `VARCHAR(10)` - máximo 10 caracteres  
**Depois:** `VARCHAR(50)` - máximo 50 caracteres

---

## 🚀 Battlepass Values Suportados Agora

| Valor | Tamanho | Tipo |
|-------|---------|------|
| `NAO` | 3 chars | Sem battlepass |
| `OPERADOR` | 9 chars | Operador básico |
| `ELITE_CAVEIRA` | 13 chars ✅ | Elite com caveira |
| `EQUIPE_BASICA` | 14 chars ✅ | Equipe básica |

---

## 🆘 Se Não Funcionar

### Erro: "Permission denied"
- Certifique-se de ter acesso PostgreSQL
- Verifique as credenciais de banco de dados no Railway

### Erro: "Table doesn't exist"
- Execute primeiro: `/setup/criar-todas-tabelas/SECRET_KEY`
- Depois execute este fix

### Erro: "Column already VARCHAR(50)"
- Significa que já foi corrigido!
- Tente atualizar um operador com ELITE_CAVEIRA para confirmar

---

## 📝 Script Criado

**Arquivo:** `fix_battlepass_column.py`  
**Localização:** Raiz do projeto  
**Commit:** Latest

---

**Status:** ✅ Ready to Deploy  
**Data:** 07/03/2026
