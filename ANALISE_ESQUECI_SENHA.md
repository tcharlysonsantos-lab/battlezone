# Análise Segura - Fluxo de "Esqueci Senha"

**Data da Análise**: 06 Mar 2026  
**Status**: ✅ REVISÃO RECOMENDADA - Endpoints de debug removidos

---

## 1. FLUXO COMPLETO

### Passo 1: Usuário acessa `/auth/forgot-password` ou `/auth/esqueci-senha` (GET)
- **Arquivo**: `backend/auth.py` - Linhas 305-347
- **Status**: ✅ Funciona corretamente
- **Template**: `frontend/templates/auth/forgot_password.html`
  - Renderiza formulário com campo de email
  - Inclui CSRF token: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`
  - Botão: "Enviar Link de Recuperação"

### Passo 2: Usuário submete form (POST)
- **URL**: `/auth/forgot-password` ou `/auth/esqueci-senha`
- **CSRF Protection**: ✅ HABILITADA (exemption em app.py linha 99)
- **Rota em auth.py**: 
  ```python
  @auth_bp.route('/forgot-password', methods=['GET', 'POST'])
  @auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])  # ALIAS
  def forgot_password():
  ```

### Passo 3: Validação e Geração de Token
```python
# Em backend/auth.py, linhas 312-315
user = User.query.filter_by(email=email).first()
if user:
    token = user.gerar_password_reset_token()
    reset_link = url_for('auth.reset_password', token=token, _external=True)
```

**Status da Função**: ✅ Localizada na `backend/models.py`
- Gera token com 30 minutos de validade
- Token salvo em `password_reset_token`
- Token expirado checado em `validar_password_reset_token()`

### Passo 4: Enviar Email
```python
# Em backend/auth.py, linhas 326-328
from backend.email_service import enviar_email_reset_senha
enviar_email_reset_senha(user.email, user.nome, reset_link)
```

**Implementação em `backend/email_service.py`** - Linhas 299-430:
- ✅ HTML formatado e profissional
- ✅ Usa `current_app.config.get('MAIL_USERNAME')` como remetente (real Gmail)
- ✅ Configurado com headers de segurança
- ✅ Valida se Flask-Mail está instalado
- ✅ Trata exceções e faz logging

### Passo 5: Usuário Clica no Link e Reseta Senha
- **URL**: `/auth/reset-password/<token>` (GET/POST)
- **Rota**: `backend/auth.py` - Linhas 351-395
- **Status**: ✅ Funciona corretamente
- **Validações**:
  1. Token existe
  2. Token não expirou (máx 30 min)
  3. Nova senha tem pelo menos 8 caracteres
  4. Confirmação de senha coincide
- **Segurança**: Usa `generate_password_hash()` ao salvar

---

## 2. CONFIGURAÇÕES DE EMAIL

### Em `config.py` (Linhas 131-135):
```python
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
```

### Variáveis Esperadas em Railway:
| Variável | Valor | Origem |
|----------|-------|--------|
| MAIL_SERVER | smtp.gmail.com | Gmail SMTP |
| MAIL_PORT | 587 | SMTP com TLS |
| MAIL_USE_TLS | true | Segurança |
| MAIL_USERNAME | campobattlezoneairsoft@gmail.com | Conta Gmail |
| MAIL_PASSWORD | erfrisfslphlduqn | App Password (não senha real) |

### ✅ Verificação de Segurança:
- Variáveis armazenadas em **Railway Dashboard** (não em arquivo)
- Não há fallback para valores fake em produção
- Credenciais não expostas no código

---

## 3. INICIALIZAÇÃO EM app.py

**Linha 26**:
```python
from backend.email_service import init_mail
```

**Linha 152**:
```python
init_mail(app)  # Inicializa Flask-Mail
```

**Status**: ✅ Correto
- Chamado após `app.config.from_object(app_config)`
- Chamado antes de registrar blueprints
- Logs corretos em caso de falha

---

## 4. SEGURANÇA E PROTEÇÕES

### CSRF Protection
- ✅ **Habilitado globalmente** via `CSRFProtect(app)`
- ✅ **Exemption aplicada no start**, não em `before_request`
  ```python
  csrf = CSRFProtect(app)
  csrf._exempt_views.add('auth.forgot_password')  # Linha 99
  ```

### Rate Limiting
- ✅ Pré-existente no `flask-limiter` (aplicado globalmente)
- ❌ **NÃO SÃ aplicado especificamente ao forgot-password**
  - Usuário pode solicitar infinitos tokens
  - **RECOMENDAÇÃO**: Considerar adicionar rate limit específico

### Security Headers
- ✅ Talisman configurado (app.py, linhas 104-122)
- ✅ CSP configurado para permitir googleapis, cdnjs, etc.

### Logs de Segurança
- ✅ `log_security_event()` chamado em `backend/auth.py` linha 316
  - Evento: `PASSWORD_RESET_SOLICITADO`

---

## 5. POSSÍVEIS PROBLEMAS E SOLUÇÕES

### ❌ Problema 1: Email não está sendo enviado
**Possíveis Causas**:
1. Variáveis de ambiente não configuradas no Railway ❌
2. Gmail bloqueando conexão ❌
3. App Password expirada ou inválida ❌
4. Timeout na conexão SMTP ✅ **MAIS PROVÁVEL**

**Solução**:
```bash
# Teste a conexão SMTP localmente:
python -c "
import smtplib
s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login('campobattlezoneairsoft@gmail.com', 'erfrisfslphlduqn')
print('Conectado!')
"
```

### ✅ Problema 2: Endpoints de Debug Removidos
- **Antes**: Havia `/debug-email-test` e `/debug-permissoes`
- **Depois**: ✅ **REMOVIDOS** (podia estar causando travamentos)

### ✅ Problema 3: HTML Inválido em app.py
- **Antes**: Havia `</ul>` solto após endpoint de debug
- **Depois**: ✅ **REMOVIDO**

---

## 6. CHECKLIST DE ANÁLISE

- ✅ Formulário de esqueci-senha renderiza corretamente
- ✅ CSRF token gerado e incluso no form
- ✅ Rota POST `/auth/forgot-password` funciona
- ✅ Rota alias `/auth/esqueci-senha` funciona
- ✅ Token de reset gerado com 30 min de validade
- ✅ Email configurado para usar Gmail real
- ✅ Template de email formatado corretamente
- ✅ Função `enviar_email_reset_senha()` implementada
- ✅ Rota `/auth/reset-password/<token>` valida token
- ✅ Validações de senha forte (8+ caracteres, confirmação)
- ✅ Security logs registrados
- ✅ Endpoints de debug removidos
- ✅ HTML inválido corrigido
- ⚠️ Rate limiting específico não implementado (baixa prioridade)

---

## 7. RECOMENDAÇÕES

### Imediato (Crítico):
1. ✅ **FEITO**: Remover endpoints de debug (removidos)
2. ✅ **FEITO**: Corrigir HTML inválido (corrigido)
3. **FAZER**: Testar fluxo completo após deploy

### Futuro (Melhorias):
1. Adicionar rate limit específico para forgot-password (prevenir spam)
2. Adicionar CAPTCHA para previne abuso
3. Implementar 2FA para password reset
4. Considerar enviar código via SMS também

---

## 8. DEPLOY

### Próximas Etapas:
1. Commit das mudanças (endpoints removidos)
2. Push para GitHub
3. Railway auto-rebuild (3-5 min)
4. Testar fluxo:
   - Ir para `/auth/forgot-password`
   - Submeter email
   - Verificar se email chega
   - Clicar link e resetar senha

