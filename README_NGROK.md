# 🚀 NGROK SECURE SETUP - RESUMO COMPLETO

## O que foi criado?

Você agora tem uma **infraestrutura completa e segura** para expor seu BattleZone Flask na internet via Ngrok.

### 📦 Arquivos Criados (6 novos arquivos)

```
1. setup_ngrok.py              - Configurar Ngrok com segurança
2. start_with_ngrok.py         - Iniciar Flask + Ngrok
3. ngrok_security.py           - Middleware de autenticação por API Key
4. test_ngrok_security.py      - Testar toda configuração
5. NGROK_QUICK_START.py        - Guia e status rápido
6. NGROK_SETUP.md              - Documentação completa (67 linhas)
7. NGROK_INTEGRATION.md        - Integração com código (200+ linhas)
8. NGROK_CHECKLIST.md          - Passo a passo em 10 fases
```

---

## 🚀 INÍCIO RÁPIDO (Em 5 minutos)

### Passo 1: Executar Setup
```powershell
python setup_ngrok.py
```

Gera:
- `.env.ngrok` com variáveis de configuração
- `.ngrok/config.json` com settings de segurança
- `logs/` para armazenar acessos

### Passo 2: Obter Authtoken do Ngrok
1. Acesse: https://dashboard.ngrok.com/auth
2. Copie seu token (começa com `ngrok_`)
3. Cole em `.env.ngrok`:
   ```
   NGROK_AUTH_TOKEN=ngrok_seu_token_aqui_1234567890
   ```

### Passo 3: Validar Configuração
```powershell
python test_ngrok_security.py
```

Verifica 10 pontos de segurança. Se tudo estiver ✅, pode prosseguir.

### Passo 4: Iniciar Servidor
```powershell
python start_with_ngrok.py
```

Saída:
```
✅ VALIDANDO CONFIGURAÇÃO DE SEGURANÇA
✅ INICIANDO NGROK
✅ NGROK URL: https://1a2b3c4d-5e6f.ngrok.io
✅ INICIANDO FLASK COM SEGURANÇA
```

### Passo 5: Acessar
- **Login**: https://sua-url.ngrok.io/auth/login
- **API**: Com header `Authorization: Bearer <sua_api_key>`

---

## 🔐 Camadas de Segurança

### 1. **API Key Authentication**
```
Gerada: Automaticamente (32 caracteres)
Acesso: Apenas com header "Authorization: Bearer <key>"
Armazenamento: .env.ngrok (protegido em .gitignore)
```

### 2. **Rate Limiting**
```
Limite: 60 requisições/minuto por IP
Burst: 10 requisições aceitas
Proteção: Contra DDoS e abuso
```

### 3. **Request Logging**
```
Arquivo: logs/ngrok_access.json
Conteúdo: IP, método, endpoint, timestamp
Segurança: Auditoria de acessos
```

### 4. **HTTPS + certificado SSL**
```
Ngrok fornece: Automático
Domínio: Ngrok.io sub-domain
Válido: Para desenvolvimento e teste
```

### 5. **CSRF Protection** (existente)
```
Flask-WTF: Ativado
Tokens: Gerados por sessão
Cookies: Secure + HttpOnly
```

### 6. **2FA/TOTP** (já implementado)
```
QR Code: Gerado automaticamente
Backup Codes: 10 códigos de recuperação
Verificação: Necessária a cada login
```

---

## 📊 Arquitetura de Fluxo

```
Internet (Ngrok URL)
        ↓
    HTTPS (SSL automático)
        ↓
Rate Limiter (60 req/min)
        ↓
API Key Validator
(Authorization: Bearer <key>)
        ↓
Flask App (localhost:5000)
        ↓
Request Logger (JSON + text)
        ↓
Response com Status Code
        ↓
Logs salvos em logs/
```

---

## 🗂️ Estrutura de Pastas

```
battlezone_flask/
├── setup_ngrok.py              # Setup inicial
├── start_with_ngrok.py         # Inicializador
├── ngrok_security.py           # Middleware de segurança
├── test_ngrok_security.py      # Testes
├── NGROK_QUICK_START.py        # Verificação rápida
│
├── .env.ngrok                  # 🔐 Configurações (gitignored)
├── .ngrok/
│   ├── config.json            # Config de segurança
│   └── url.txt                # URL atual do Ngrok
│
├── logs/                        # Acessos registrados
│   ├── ngrok_security.log     # Log legível
│   └── ngrok_access.json      # JSON para análise
│
├── NGROK_SETUP.md              # Guia completo
├── NGROK_INTEGRATION.md        # Como integrar ao código
├── NGROK_CHECKLIST.md          # 10 fases de validação
│
├── (resto do projeto Flask)
```

---

## 💻 Exemplos de Uso

### Via Navegador (Login com Sessão)
```
GET https://sua-url.ngrok.io/auth/login
→ Página de login carrega
→ Cookie de sessão gerenciado automaticamente
→ 2FA se habilitado
→ Dashboard após sucesso
```

### Via API com curl
```bash
# Com API Key
curl -H "Authorization: Bearer sua_chave_api" \
     https://sua-url.ngrok.io/api/usuarios

# Sem API Key (erro 401)
curl https://sua-url.ngrok.io/api/usuarios
→ {"erro": "Autenticação necessária"}
```

### Via Python
```python
import requests

api_key = "sua_chave_32_caracteres"
headers = {'Authorization': f'Bearer {api_key}'}

response = requests.get(
    'https://sua-url.ngrok.io/api/dados',
    headers=headers
)
print(response.json())
```

### Via JavaScript
```javascript
const apiKey = 'sua_chave_api';
const response = await fetch('https://sua-url.ngrok.io/api/dados', {
  headers: {'Authorization': `Bearer ${apiKey}`}
});
const data = await response.json();
```

---

## 📈 Monitoramento

### Dashboard Ngrok (tempo real)
```
http://127.0.0.1:4040
```
Mostra todas as requisições, headers, payloads, responses em tempo real.

### Analisar Acessos
```powershell
# Ver últimos 20 acessos
Get-Content logs/ngrok_security.log -Tail 20

# Converter JSON para tabela
$json = Get-Content logs/ngrok_access.json | ConvertFrom-Json
$json | Format-Table timestamp, ip, metodo, endpoint -AutoSize
```

---

## ⚙️ Configuração Personalizada

### Mudar Port
Edit `.env.ngrok`:
```env
NGROK_PORT=5001  # (default: 5000)
```

### Mudar Region
Edit `.env.ngrok`:
```env
NGROK_REGION=us   # sa, us, eu, in, au, jp
```

### Aumentar Rate Limit
Edit `.ngrok/config.json`:
```json
"security": {
  "rate_limit": {
    "requests_per_minute": 120,
    "burst_size": 20
  }
}
```

### Gerar Nova API Key
```powershell
# Deleta chave antiga, gera nova
python setup_ngrok.py
```

---

## 🛡️ Proteção de Segredos

### Nunca compartilhe:
- ❌ `.env.ngrok` (contém authtoken)
- ❌ `NGROK_AUTH_TOKEN` por email/chat
- ❌ `.ngrok/config.json` em código público

### Seguro para compartilhar:
- ✅ URL do Ngrok: `https://xxxx-xxxx.ngrok.io`
- ✅ API Key: regenerável, não é credencial permanente
- ✅ Documentação NGROK_SETUP.md

### Sempre protegido:
- ✅ Ambos em `.gitignore`
- ✅ Regenerável com `setup_ngrok.py`
- ✅ Cada execução gera nova API Key

---

## 🔄 Workflow Completo

```
DIA 1: Setup
  python setup_ngrok.py
  → Obter authtoken
  → Preencher .env.ngrok
  → python test_ngrok_security.py (validar)

DIA 2: Iniciar
  python start_with_ngrok.py
  → URL do Ngrok exibida
  → API Key exibida
  → Servidor rodando

DIA 3+: Compartilhar com Time
  → Enviar URL + API Key
  → Time acessa login/API
  → Monitorar em logs/
  → Escalar para VPS quando pronto
```

---

## 🚨 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| "Ngrok not found" | `choco install ngrok` |
| "NGROK_AUTH_TOKEN inválido" | Copiar exato de https://dashboard.ngrok.com/auth |
| "API Key rejected" | Header deve ser: `Authorization: Bearer <key>` |
| "401 Unauthorized" | Verificar se Authorization header está presente |
| "Port 5000 em uso" | Mudar NGROK_PORT em .env.ngrok ou: `netstat -ano \| findstr :5000` |
| "Rate limit 429" | Aguardar 1 minuto ou espaçar requisições |
| Ngrok desconecta | Reconectar: `python start_with_ngrok.py` |

---

## 📚 Documentação

- **NGROK_QUICK_START.py** → Verificar status rápido
- **NGROK_SETUP.md** → Guia detalhado (5 seções, 67 linhas)
- **NGROK_INTEGRATION.md** → Como integrar ao código (200+ linhas)
- **NGROK_CHECKLIST.md** → 10 fases de validação + troubleshooting

---

## ✅ Checklist Final

Tudo pronto quando:

- ✅ `python setup_ngrok.py` executado
- ✅ `.env.ngrok` preenchido com authtoken
- ✅ `python test_ngrok_security.py` passa 100%
- ✅ `python start_with_ngrok.py` iniciando sem erros
- ✅ URL do Ngrok acessível no navegador
- ✅ Login funcionando (com 2FA)
- ✅ API respondendo com API Key
- ✅ Logs sendo registrados em `logs/`

---

## 🎯 Próximas Etapas

### Para Desenvolvimento Imediato
1. Testar com time (compartilhar URL + API Key)
2. Acompanhar logs em `logs/ngrok_security.log`
3. Ajustar rate limiting conforme necessário

### Para Produção Futura
1. Comprar domínio
2. Usar VPS (DigitalOcean, AWS, etc)
3. Let's Encrypt para SSL
4. Gunicorn + Nginx
5. Backup automático
6. Monitoramento profissional

---

## 📞 Suporte

Se algo não funcionar:

1. Executar: `python NGROK_QUICK_START.py`
2. Ler erros com atenção
3. Revisar a seção "Troubleshooting" acima
4. Editar manualmente `.env.ngrok` se necessário

---

## 🎉 Conclusão

Você tem agora:
- ✅ Exposição segura via Ngrok
- ✅ Autenticação por API Key
- ✅ Rate limiting
- ✅ Logging auditável
- ✅ HTTPS automático
- ✅ 2FA habilitado
- ✅ Caso-insensitive login
- ✅ Password reset
- ✅ Pronto para team testing

**BattleZone está online com segurança máxima! 🚀**
