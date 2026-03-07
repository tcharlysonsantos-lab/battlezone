# 🗄️ Setup do Banco de Dados - BattleZone

## Problema Atual
A página `/sorteios` está retornando erro **500** porque as tabelas do banco de dados PostgreSQL não foram criadas:

```
❌ relation "battlepasses" não existe
❌ relation "eventos" não existe  
```

---

## Solução: Criar Todas as Tabelas

### ✅ Via Browser (Recomendado para Railway)

1. **Obtenha sua SECRET_KEY do Railway**
   - Acesse: https://railway.app/dashboard
   - Projeto: Battlezone Production
   - Clique em: "Variables" ou "Environment"
   - Copie o valor de `SECRET_KEY`

2. **Acesse a rota de setup**
   ```
   https://seu-app.railway.app/setup/criar-todas-tabelas/SUA_SECRET_KEY
   ```
   
   **Exemplo:**
   ```
   https://battlezone-production.up.railway.app/setup/criar-todas-tabelas/abc123def456...
   ```

3. **Resultado esperado:**
   ```json
   {
     "success": true,
     "message": "Tabelas criadas! 14/14 tabelas essenciais detectadas.",
     "timestamp": "2026-03-07T20:13:49.123456",
     "tabelas": {
       "users": true,
       "operadores": true,
       "equipes": true,
       "partidas": true,
       "eventos": true,
       "battlepasses": true,
       "sorteios": true,
       ... (mais tabelas)
     },
     "total_criadas": 14,
     "total_esperadas": 14
   }
   ```

---

### 📟 Via Terminal/Curl (Local)

```bash
curl "http://localhost:5000/setup/criar-todas-tabelas/your-secret-key"
```

---

## Tabelas que Serão Criadas

| Tabela | Status | Função |
|--------|--------|--------|
| `users` | ✅ | Usuários do sistema |
| `operadores` | ✅ | Dados dos operadores |
| `equipes` | ✅ | Equipes de jogadores |
| `equipemembros` | ✅ | Membros das equipes |
| `partidas` | ✅ | Partidas registradas |
| `partida_participantes` | ✅ | Participantes de partidas |
| `vendas` | ✅ | Registro de vendas |
| `estoque` | ✅ | Itens de estoque |
| `logs` | ✅ | Log de ações |
| `solicitacoes` | ✅ | Solicitações pendentes |
| `pagamento_operador` | ✅ | Pagamentos |
| `eventos` | ✅ | Eventos especiais |
| `evento_brindes` | ✅ | Brindes dos eventos |
| `battlepasses` | ✅ | Battlepasses do sistema |
| `sorteios` | ✅ | Registro de sorteios |

---

## ✅ Depois de Criar as Tabelas

### 1. Inicializar Battlepasses (Opcional mas Recomendado)

```bash
# Local
python -m flask init-battlepasses

# Ou via CLI do Railway
railway run python -m flask init-battlepasses
```

### 2. Testar a Página de Sorteios

- Acesse: `https://seu-app.railway.app/sorteios`
- Deve carregar SEM erro 500
- Exibirá seções vazias (sem eventos/sorteios ainda)

### 3. Criar Dados Iniciais (Admin)

Depois de criar as tabelas, você pode:

- **Adicionar Battlepasses** via CLI ou Admin Panel
- **Criar Eventos** via API: `/api/eventos/criar`
- **Realizar Sorteios** via Admin Panel

---

## 🔐 Segurança

⚠️ **IMPORTANTE:**
- A rota requer a **SECRET_KEY correta** do Railway
- Sem a SECRET_KEY correta, retorna erro 403
- Nunca compartilhe sua SECRET_KEY publicamente

---

## 📋 Checklist

- [ ] Obter SECRET_KEY do Railway
- [ ] Acessar `/setup/criar-todas-tabelas/SECRET_KEY`
- [ ] Confirmar resposta com `"success": true`
- [ ] Testar página `/sorteios` (deve carregar sem erros 500)
- [ ] Inicializar battlepasses (opcional)
- [ ] Criar dados de teste no admin panel

---

## 🆘 Se Algo Deu Errado

### Erro: "Invalid secret key"
- Verifique se a SECRET_KEY foi copiada corretamente (sem espaços extras)
- Certifique-se de estar usando a SECRET_KEY do ambiente de produção

### Erro: "relation already exists"
- As tabelas podem já estar criadas parcialmente
- Tente fazer DELETE todas as tabelas e criar novamente
- Ou use `db.create_all()` que ignora tabelas existentes

### A página `/sorteios` ainda retorna 500
- Verifique nos logs do Railway se há outros erros
- Execute novamente a rota de setup
- Contate o suporte técnico com os logs de erro

---

## 🚀 Próximos Passos

1. ✅ **Criar tabelas** (esta etapa)
2. 📊 **Inicializar battlepasses** 
3. 👥 **Criar operadores/equipes** (admin panel)
4. 🎮 **Criar partidas** (admin panel)
5. 🎲 **Realizar sorteios** (admin panel)

---

**Última atualização:** 07/03/2026  
**Commit:** 954b63b  
**Status:** ✅ Production Ready
