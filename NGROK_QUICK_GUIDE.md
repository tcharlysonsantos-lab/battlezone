# 🎯 GUIA VISUAL - NGROK SETUP (2 minutos)

## ⚡ TL;DR - Os Essenciais

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Executar Setup                                           │
│    python setup_ngrok.py                                    │
│                                                              │
│ 2. Preencher Authtoken                                      │
│    Editar: .env.ngrok → NGROK_AUTH_TOKEN=ngrok_...        │
│                                                              │
│ 3. Validar                                                  │
│    python test_ngrok_security.py                            │
│                                                              │
│ 4. Iniciar                                                  │
│    python start_with_ngrok.py                               │
│                                                              │
│ 5. Acessar                                                  │
│    https://xxxxx-xxxxx.ngrok.io/auth/login                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 O QUE VOCÊ RECEBEU

```
╔═══════════════════════════════════════════╗
║ 🔧 SCRIPTS (Execute na ordem)            ║
╠═══════════════════════════════════════════╣
║ 1️⃣  setup_ngrok.py                        ║
║     └─ Gera API Key e configuração       ║
║                                           ║
║ 2️⃣  test_ngrok_security.py               ║
║     └─ Valida tudo funciona              ║
║                                           ║
║ 3️⃣  start_with_ngrok.py                  ║
║     └─ Inicia o servidor                 ║
║                                           ║
║ 4️⃣  NGROK_QUICK_START.py                 ║
║     └─ Ver status rápido                 ║
╚═══════════════════════════════════════════╝

╔═══════════════════════════════════════════╗
║ 📚 DOCUMENTAÇÃO (Leia conforme necessário)║
╠═══════════════════════════════════════════╣
║ 📖 README_NGROK.md                        ║
║    └─ Visão geral completa                ║
║                                           ║
║ 📖 NGROK_SETUP.md                         ║
║    └─ Passo a passo (5 passos)            ║
║                                           ║
║ 📖 NGROK_INTEGRATION.md                   ║
║    └─ Como usar no seu código             ║
║                                           ║
║ 📖 NGROK_CHECKLIST.md                     ║
║    └─ 10 fases com checks                 ║
║                                           ║
║ 📖 NGROK_INVENTORY.md                     ║
║    └─ Lista detalhada de tudo             ║
╚═══════════════════════════════════════════╝

╔═══════════════════════════════════════════╗
║ 🔐 CONFIGURAÇÃO (Auto-gerenciado)        ║
╠═══════════════════════════════════════════╣
║ .env.ngrok              [GITIGNORED]     ║
║ .ngrok/config.json      [GITIGNORED]     ║
║ logs/                   [GITIGNORED]     ║
╚═══════════════════════════════════════════╝
```

---

## 🚀 PASSO A PASSO (4 minutos)

### ✅ PASSO 1: Setup (1 min)

```powershell
cd d:\Backup_Sistema\Flask\battlezone_flask
python setup_ngrok.py
```

**O que acontece:**
```
✅ Ngrok detectado
✅ API Key gerada: YmQuUqtJ8HwpK...
✅ .env.ngrok criado
✅ .ngrok/config.json criado
✅ logs/ diretório criado
✅ .gitignore atualizado
```

**Tempo:** ~30 segundos

---

### ✅ PASSO 2: Preencher Token (1 min)

1. Abrir: https://dashboard.ngrok.com/auth
2. Copiar token (que começa com `ngrok_`)
3. Editar `.env.ngrok`:

```env
NGROK_AUTH_TOKEN=ngrok_seu_token_colado_aqui_1234567890abcdef
```

**❌ NÃO FAZER:**
```
NGROK_AUTH_TOKEN=COLOQUE_SEU_TOKEN_AQUI  ← Deixar como estava
NGROK_AUTH_TOKEN=ngrok_                  ← Incompleto
NGROK_AUTH_TOKEN=meu_token_1234          ← Sem "ngrok_"
```

**✅ CORRETO:**
```
NGROK_AUTH_TOKEN=ngrok_4LcKpJ7Yz9mK2bW5X8qL1NpO3GhE6RfT
```

**Tempo:** ~1 minuto

---

### ✅ PASSO 3: Validar (1 min)

```powershell
python test_ngrok_security.py
```

**Esperado:**
```
✅ Setup de arquivos
✅ Configuração .env.ngrok
✅ config.json
✅ Ngrok instalado
✅ Porta disponível
✅ Proteção .gitignore
✅ Diretório de logs
✅ Flask app
✅ Módulos de segurança
✅ Formato de API Key

🎉 TUDO PRONTO! Você pode executar:
  python start_with_ngrok.py
```

**Se falhar em algo:** Ver NGROK_CHECKLIST.md (troubleshooting)

**Tempo:** ~30 segundos

---

### ✅ PASSO 4: Iniciar (1 min)

```powershell
python start_with_ngrok.py
```

**Esperado:**
```
✅ VALIDANDO CONFIGURAÇÃO DE SEGURANÇA
✅ INICIANDO NGROK
✅ NGROK URL: https://1a2b3c-4d5e.ngrok.io
✅ INICIANDO FLASK COM SEGURANÇA

Seu servidor está ONLINE! 🎉
```

**Anotar:**
- 📍 URL: `https://1a2b3c-4d5e.ngrok.io`
- 🔑 API Key: `YmQuUqtJ8HwpK...` (em .env.ngrok)

**Tempo:** ~5 segundos

---

## 🧪 TESTAR (2 minutos)

### Teste 1: Login no Navegador ✅

```
1. Abrir: https://sua-url.ngrok.io/auth/login
2. Usuário: tcharlyson
3. Senha: 123456Ab
4. Entrar
5. Se abrir dashboard → ✅ Funciona!
```

---

### Teste 2: API com curl ✅

```powershell
# Nome da variável
$apiKey = "sua_chave_32_caracteres_aqui"
$url = "https://sua-url.ngrok.io/api/usuarios"

# Fazer requisição
$headers = @{ "Authorization" = "Bearer $apiKey" }
Invoke-WebRequest -Uri $url -Headers $headers

# Resultado esperado:
# StatusCode: 200
# Content: {...}
```

---

### Teste 3: Ver Logs ✅

```powershell
# Log de segurança
Get-Content logs/ngrok_security.log -Tail 5

# Saída esperada:
# 2025-02-... - INFO - Acesso autorizado de 192.168.x.x
```

---

## 📊 ARQUITETURA VISUAL

```
┌─────────────────────────────────────┐
│     SEU COMPUTADOR (Windows)        │
├─────────────────────────────────────┤
│ Flask App                           │
│ http://localhost:5000               │
└────────────────┬────────────────────┘
                 │
                 ↓
        ┌────────────────┐
        │     NGROK      │
        │  Expõe para    │
        │   Internet     │
        └────────┬───────┘
                 │
                 ↓
        ┌────────────────────┐
        │   INTERNET (HTTPS) │
        │ https://xxxx.nngrok│
        │      .io           │
        └────────┬───────────┘
                 │
                 ↓
        ┌────────────────────┐
        │   CLIENTE REMOTO   │
        │ (seu time em outro │
        │  lugar)            │
        └────────────────────┘
```

---

## 🔑 CREDENCIAIS

### API Key (Compartilhável)
```
✅ Compartilhável diretamente
✅ Regenerável a qualquer momento
✅ Específica da sua instalação
✅ Pode enviar por email/chat

Exemplo:
YmQuUqtJ8HwpK-Tzl9AzM7cXyZ3FvWjX
```

### Authtoken (NUNCA compartilhar)
```
❌ NUNCA compartilhar
❌ Mantenha em .env.ngrok
❌ Protegido em .gitignore
❌ É como sua senha do Ngrok

Exemplo:
NGROK_AUTH_TOKEN=ngrok_4LcKpJ7Yz9mK2bW5X8qL1NpO3GhE6RfT
```

---

## 📁 ESTRUTURA DE PASTAS

```
Antes:
battlezone_flask/
├── app.py
├── auth.py
├── models.py
└── ...

Depois:
battlezone_flask/
├── app.py
├── auth.py
├── models.py
│
├── 🆕 setup_ngrok.py              ← Execute aqui
├── 🆕 start_with_ngrok.py         ← Execute aqui para rodar
├── 🆕 test_ngrok_security.py      ← Execute para validar
├── 🆕 ngrok_security.py           ← Middleware
│
├── 🆕 README_NGROK.md             ← Leia isso
├── 🆕 NGROK_SETUP.md              ← E isso também
├── 🆕 NGROK_INTEGRATION.md
├── 🆕 NGROK_CHECKLIST.md
│
├── 🆕 .env.ngrok                  ← Editar (se necessário)
├── 🆕 .ngrok/                     ← Pasta de config
├── 🆕 logs/                       ← Logs de acesso
│
└── ...
```

---

## ⚡ COMANDOS MAIS USADOS

### Usar seu server
```powershell
python start_with_ngrok.py
```

### Validar funcionamento
```powershell
python test_ngrok_security.py
```

### Ver status rápido
```powershell
python NGROK_QUICK_START.py
```

### Ver logs em tempo real
```powershell
Get-Content logs/ngrok_security.log -Wait
```

### Regenerar API Key
```powershell
python setup_ngrok.py
```

---

## 🎯 URLS IMPORTANTES

```
Seu Servidor:
https://sua-url-aqui.ngrok.io/auth/login

Login:
User: tcharlyson
Pass: 123456Ab

Dashboard Ngrok (monitorar):
http://127.0.0.1:4040

Obter Authtoken:
https://dashboard.ngrok.com/auth

Ngrok Pricing:
https://ngrok.com/pricing
```

---

## ✅ CHECKLIST RÁPIDO

- [ ] Executei `python setup_ngrok.py`
- [ ] Copiei meu authtoken de https://dashboard.ngrok.com/auth
- [ ] Preenchi `NGROK_AUTH_TOKEN` em .env.ngrok
- [ ] Executei `python test_ngrok_security.py` (passou!)
- [ ] Executei `python start_with_ngrok.py`
- [ ] Acessei login no navegador (funcionou!)
- [ ] Testei API com curl (funcionou!)
- [ ] Vi logs sendo registrados

✅ = TUDO PRONTO!

---

## 🆘 ALGO DEU ERRADO?

### "ngrok not found"
```powershell
choco install ngrok
# ou
winget install ngrok.ngrok
```

### "NGROK_AUTH_TOKEN inválido"
```
1. Ir a https://dashboard.ngrok.com/auth
2. Copiar token exacto (começa com ngrok_)
3. Colar em .env.ngrok
4. Salvar arquivo
```

### "API Key rejected"
```powershell
# Verificar que está usando Bearer
curl -H "Authorization: Bearer sua_chave" https://url
# NÃO:
curl -H "Authorization: sua_chave" https://url  ← Falta "Bearer"
```

### "Port 5000 em uso"
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
# depois tentar novamente
```

### "Ngrok desconecta"
```powershell
# Reconectar:
python start_with_ngrok.py
```

---

## 🎓 APRENDER MAIS

```
Ler em ordem:
1. Este arquivo (visão geral)
2. NGROK_SETUP.md (como usar)
3. NGROK_INTEGRATION.md (integração)
4. NGROK_CHECKLIST.md (troubleshooting)

Se mais dúvidas:
5. README_NGROK.md (tudo em detalhe)
6. NGROK_INVENTORY.md (lista completa)
```

---

## 🎉 PRONTO!

Seu BattleZone está:
- ✅ **Online** (internet access)
- ✅ **Seguro** (API Key auth)
- ✅ **Monitorado** (logging)
- ✅ **Compartilhável** (team access)

**Próximo passo:** `python start_with_ngrok.py` 🚀

---

*Documento criado em Fevereiro 2025*  
*Versão: 1.0*
