# 🚀 NGROK SETUP - GUIA COMPLETO

## 📋 Pré-requisitos

- ✅ `setup_ngrok.py` executado (gera as configurações)
- ✅ Ngrok instalado: `choco install ngrok` ou `brew install ngrok`
- ✅ Conta Ngrok criada (https://ngrok.com/signup)

---

## 🔧 Passo 1: Executar Setup

```powershell
cd d:\Backup_Sistema\Flask\battlezone_flask
python setup_ngrok.py
```

**Saída esperada:**
```
✅ Ngrok detectado
✅ Configuração de segurança criada
✅ Arquivos gerados:
   - .ngrok/config.json
   - .env.ngrok
   - logs/
```

---

## 🔑 Passo 2: Configurar Ngrok Authtoken

### Obter token:
1. Ir para https://dashboard.ngrok.com/auth
2. Copiar o token (começa com `ngrok_...`)

### Preencher em `.env.ngrok`:
```env
NGROK_AUTH_TOKEN=ngrok_seu_token_aqui_1234567890abcdef
NGROK_API_KEY=gerado_automaticamente_no_setup
NGROK_REGION=sa
NGROK_PORT=5000
```

**Nota:** Cada próxima execução do setup irá gerar uma nova `NGROK_API_KEY`

---

## ▶️ Passo 3: Iniciar Servidor

```powershell
python start_with_ngrok.py
```

**Saída esperada:**
```
✅ NGROK URL: https://xxxx-xxxx.ngrok.io
✅ API Key: sua_chave_de_32_caracteres
```

---

## 🔐 AUTENTICAÇÃO POR API KEY

Toda requisição para o servidor via Ngrok **EXIGE** header `Authorization`:

### ✅ Acessar no navegador
Para login normal, use a URL do Ngrok normalmente:
```
https://xxxx-xxxx.ngrok.io/auth/login
```
O navegador gerenciará cookies de sessão automaticamente.

### ✅ Requisições via curl/API
Para requisições de API, inclua a chave no header:

```bash
# GET request
curl -H "Authorization: Bearer sua_chave_aqui" \
     https://xxxxx-xxxxx.ngrok.io/api/usuarios

# POST request
curl -X POST \
     -H "Authorization: Bearer sua_chave_aqui" \
     -H "Content-Type: application/json" \
     -d '{"dados": "valor"}' \
     https://xxxxx-xxxxx.ngrok.io/api/criar
```

### ✅ Requisições Python
```python
import requests

headers = {
    'Authorization': 'Bearer sua_chave_de_api',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://xxxxx-xxxxx.ngrok.io/api/dados',
    headers=headers
)
```

### ✅ JavaScript/Fetch
```javascript
const apiKey = 'sua_chave_aqui';
const response = await fetch('https://xxxxx-xxxxx.ngrok.io/api/dados', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
  }
});
```

---

## 📊 Monitorar Acessos

### Dashboard Ngrok (tempo real)
```
http://127.0.0.1:4040
```
Mostra todas as requisições, headers, responses.

### Logs de Segurança
```powershell
# Seguir logs em tempo real (PowerShell)
Get-Content logs/ngrok_security.log -Wait

# Ou ver últimos 50 acessos
Get-Content logs/ngrok_access.json | Measure-Object -Line
```

### Arquivo de Acessos
- **logs/ngrok_security.log** - Log legível (autenticações, erros)
- **logs/ngrok_access.json** - Todos os acessos em JSON (análise)

---

## ⚠️ Segurança

### Rate Limiting
- **60 requisições/minuto** por IP
- **10 requisições** burst permitidas
- Espaçar requisições para evitar limite

### Authorization Header
```
✅ Correto:  Authorization: Bearer abc123xyz789
❌ Errado:   Authorization abc123xyz789
❌ Errado:   Bearer abc123xyz789 (sem Authorization:)
❌ Errado:   Api-Key abc123xyz789
```

### Proteger a API Key
- ✅ Armazenar em `.env.ngrok` (já em `.gitignore`)
- ✅ Nunca compartilhar em código público
- ✅ Regenerar se comprometida (executar setup_ngrok.py novamente)
- ✅ Usar diferentes chaves por ambiente

### HTTPS Automático
- Ngrok fornece certificado SSL/TLS automático
- Todos os acessos via `https://` (seguro)
- ✅ CSP, HSTS e outros headers ativados

---

## 🐛 Troubleshooting

### "Erro: NGROK_AUTH_TOKEN não foi preenchido"
```powershell
# Solução:
# 1. Ir a https://dashboard.ngrok.com/auth
# 2. Copiar token
# 3. Editar .env.ngrok
# 4. Substituir NGROK_AUTH_TOKEN=ngrok_seu_token_aqui
```

### "Acesso Negado - API Key Inválida"
Verificar:
- Header `Authorization` está incluído?
- Formato é `Bearer <api_key>`?
- API Key matches a chave em `.env.ngrok`?

```bash
# Debug
echo "API Key de .env.ngrok:"
Select-String "NGROK_API_KEY=" .env.ngrok
```

### "Port 5000 já está em uso"
```powershell
# Liberar porta ou usar diferente
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Ou mude em .env.ngrok
NGROK_PORT=5001
```

### Ngrok não inicializa
```powershell
# Verificar se está instalado
ngrok --version

# Instalar se necessário
choco install ngrok
# ou
winget install ngrok.ngrok
```

---

## 📊 Exemplo de Uso Completo

### 1. Terminal 1 - Iniciar servidor
```powershell
python start_with_ngrok.py
# Output: https://1a2b3c4d-5e6f.ngrok.io
#        API Key: abcd1234efgh5678ijkl9012mnop3456
```

### 2. Terminal 2 - Teste de requisição
```powershell
$apiKey = "abcd1234efgh5678ijkl9012mnop3456"
$url = "https://1a2b3c4d-5e6f.ngrok.io/api/status"

$headers = @{
    "Authorization" = "Bearer $apiKey"
}

Invoke-WebRequest -Uri $url -Headers $headers
```

### 3. Verificar logs
```powershell
Get-Content logs/ngrok_security.log -Tail 10
```

---

## 🔄 Usar com Tim de Teste

### Compartilhar URL (com cuidado!)
Você pode compartilhar:
- ✅ URL do Ngrok: `https://xxxx-xxxx.ngrok.io`
- ✅ API Key (é regenerada, não é credencial permanente)

### Instrução para o Time
```
1. Acessar: https://xxxx-xxxx.ngrok.io/auth/login
2. Fazer login com: tcharlyson / 123456Ab
3. Para API: usar header Authorization: Bearer <api_key>
```

---

## 🛠️ Configuração Avançada

### Customizar Rate Limit
Editar em `.ngrok/config.json`:
```json
"security": {
  "rate_limit": {
    "requests_per_minute": 100,
    "burst_size": 20
  }
}
```
Depois reiniciar `start_with_ngrok.py`

### Usar Region Diferente
Em `.env.ngrok`:
```
# sa = South America (recomendado para Brasil)
# us = USA
# eu = Europe
NGROK_REGION=us
```

### Log com Mais Detalhes
Em `ngrok_security.py`, mudar:
```python
ngrok_logger.setLevel(logging.DEBUG)  # ao invés de logging.INFO
```

---

## ✅ Checklist Final

- [ ] setup_ngrok.py executado
- [ ] Conta Ngrok criada
- [ ] Authtoken copiado para .env.ngrok
- [ ] start_with_ngrok.py executando
- [ ] URL Ngrok acessível no navegador
- [ ] API Key obtida
- [ ] Requisição curl com Auth header funcionando
- [ ] Logs sendo registrados em logs/

Pronto! 🎉 Seu BattleZone está online com segurança máxima!
