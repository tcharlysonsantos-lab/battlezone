# 🔐 SISTEMAS DE SEGURANÇA - BattleZone Flask

## 📋 Resumo Executivo

Seu sistema implementa **11 camadas de segurança** profissionais:

| # | Sistema | Status | Função |
|---|---------|--------|--------|
| 1 | **CSRF Protection** | ✅ Ativa | Protege contra ataques Cross-Site Request Forgery |
| 2 | **Talisman (Security Headers)** | ✅ Ativa | Headers de segurança HTTP (CSP, HSTS, etc) |
| 3 | **Rate Limiting** | ✅ Ativa | Proteção contra brute force e DDoS |
| 4 | **Password Hashing** | ✅ Ativa | Senhas com salt + werkzeug |
| 5 | **2FA TOTP** | ✅ Implementado | Autenticação de dois fatores com QR code |
| 6 | **Session Management** | ✅ Ativa | Timeout de 30min para operadores + tokens |
| 7 | **Role-Based Access Control** | ✅ Ativa | Decorators @admin, @requer_permissao |
| 8 | **Input Validation** | ✅ Ativa | WTForms + validators personalizados |
| 9 | **File Upload Security** | ✅ Ativa | MIME type checking + double extension prevention |
| 10 | **Logging & Auditing** | ✅ Ativa | Log INFO para eventos importantes |
| 11 | **SQL Injection Prevention** | ✅ Ativa | SQLAlchemy ORM (parametrized queries) |

---

## 🔒 DETALHES DE CADA SISTEMA

### 1️⃣ CSRF Protection (Cross-Site Request Forgery)

**Como funciona:**
- Flask-WTF com `CSRFProtect(app)`
- **Localização**: [app.py](app.py#L4) e [forms.py](backend/forms.py)
- Gera token único por sessão
- Valida token em cada POST/PUT/DELETE

**Proteção contra:**
```
❌ Atacante enganar você fazer requisição maliciosa
❌ Formulário fake em site externo
```

**Configuração:**
```python
# app.py linha 39
csrf = CSRFProtect(app)  # ← Automático em todos formulários
```

---

### 2️⃣ Talisman - Security Headers

**Headers implementados:**
- `Content-Security-Policy (CSP)` - Controla origem de scripts/styles/imagens
- `Strict-Transport-Security (HSTS)` - Força HTTPS em produção (1 ano)
- `X-Content-Type-Options: nosniff` - Previne MIME type sniffing
- `X-Frame-Options: DENY` - Impede clickjacking
- `X-XSS-Protection` - XSS filtering no navegador

**Configuração:**
```python
# app.py linhas 52-62
Talisman(app, 
    force_https=True,           # Em produção HTTPS obrigatório
    strict_transport_security=True,
    content_security_policy={
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", 'data:', 'https:']
    }
)
```

**Proteção contra:**
```
❌ XSS (Cross-Site Scripting)
❌ Clickjacking
❌ MIME type attacks
❌ Man-in-the-middle (HTTPS)
```

---

### 3️⃣ Rate Limiting

**Sistema:**
- Flask-Limiter com `get_remote_address` (IP do usuário)
- **Localização**: [app.py](app.py#L74) + [backend/auth.py](backend/auth.py#L45-L65)

**Limites implementados:**
```python
# app.py
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]  # Global
)

# backend/auth.py - Rate limiter customizado para LOGIN
class RateLimiter:
    max_attempts = 5              # 5 tentativas
    timeout = 900                 # 15 minutos de bloqueio
    
    def registrar_tentativa(ip):  # Registra tentativa falha
    def limpar_ip(ip):            # Limpa após login bem-sucedido
    def is_rate_limited(ip):      # Verifica se IP está bloqueado
```

**Proteção contra:**
```
❌ Brute force (5 tentativas = bloqueio de 15min)
❌ DDoS attacks
❌ Credential stuffing
❌ Spam
```

---

### 4️⃣ Password Hashing com Salt

**Sistema:**
- Werkzeug `generate_password_hash()` + `check_password_hash()`
- Salt aleatório de 32 caracteres hex
- **Localização**: [backend/models.py](backend/models.py#L64-L68)

**Como funciona:**
```python
# User model
salt = secrets.token_hex(16)  # 32 chars aleatório
password_hash = generate_password_hash(password + salt)

# Verificação
check_password_hash(self.password_hash, password_input + self.salt)
```

**Hash gerado:**
```
Input: "123456Ab"
Salt: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
Hash: pbkdf2:sha256:600000$a1b2c3d4e5f6g7h8...$xyz123...
```

**Proteção contra:**
```
❌ Rainbow table attacks (salt único)
❌ Dictionary attacks (algoritmo strong - PBKDF2)
❌ Brute force (600.000 iterações - lento)
```

---

### 5️⃣ 2FA TOTP (Two-Factor Authentication)

**Tecnologia:**
- PyOTP para TOTP (Time-based One-Time Password)
- QRCode - escanear com Google Authenticator/Authy
- Backup codes (10 códigos para recuperação)
- **Localização**: [backend/auth_security.py](backend/auth_security.py)

**Fluxo de setup:**

1. Usuário clica "Ativar 2FA"
2. Sistema gera secret (base32): `JBSWY3DPEBLW64TMMQ======`
3. Gera QR code em base64
4. Usuário abre Authenticator > Scan QR
5. Authenticator mostra código (6 dígitos)
6. Usuário confirma código (validado com `totp.verify()`)
7. 2FA ativado + recebe 10 backup codes

**Proteção contra:**
```
❌ Credential theft (mesmo com senha roubada)
❌ Phishing (código muda a cada 30 segundos)
❌ Account takeover
```

**Backup codes:**
- 10 códigos de 8 caracteres cada
- Cada um pode ser usado uma única vez
- Armazenados como JSON no banco (hasheado em produção)

---

### 6️⃣ Session Management

**Sistema de Sessão:**
- `session_token` aleatório (secrets.token_urlsafe)
- `last_activity` timestamp
- Timeout de **30 minutos** para OPERADORES
- Admin não expira

**Localização**: [backend/models.py](backend/models.py#L75-L83)

```python
# User model
session_token = db.Column(db.String(100))
last_activity = db.Column(db.DateTime)

# Verificação
def is_session_valid(self):
    if self.nivel == 'operador':
        time_diff = datetime.utcnow() - self.last_activity
        return time_diff.total_seconds() < 1800  # 30 minutos

# Update na cada requisição
def update_activity(self):
    self.last_activity = datetime.utcnow()
    db.session.commit()
```

**Middleware automático:**
```python
# app.py antes_de_cada_requisição
@app.before_request
def before_request():
    if current_user.nivel == 'operador':
        if not current_user.is_session_valid():
            logout_user()
            # Redireciona para login
```

**Proteção contra:**
```
❌ Session hijacking
❌ Session fixation
❌ Unauthorized access após logout
```

---

### 7️⃣ Role-Based Access Control (RBAC)

**Decorators implementados:**

1. **`@admin_required`** - Apenas admin/gerente
   ```python
   @admin_required
   def admin_dashboard():
       pass  # Só admin acessa
   ```

2. **`@requer_permissao(recurso)`** - Verificar permissões por recurso
   ```python
   @requer_permissao('operadores')      # Precisa de acesso a 'operadores'
   def listar_operadores():
       pass
   ```

3. **`@operador_session_required`** - Validar timeout de sessão
   ```python
   @operador_session_required
   def criar_partida():
       pass  # Se timeout, logout automático
   ```

**Níveis de acesso:**

| Nível | Recursos | Notas |
|-------|----------|-------|
| **admin** | ✅ TUDO | Full access |
| **gerente** | dashboard, operadores, equipes, partidas, vendas, caixa, estoque | Todos exceto admin areas |
| **financeiro** | dashboard, vendas, caixa, estoque | Apenas financeiro |
| **operador** | dashboard, partidas, calendario, estatisticas | Acesso limitado |
| **pendente** | ❌ NADA | Aguardando aprovação |

**Localização**: [backend/decorators.py](backend/decorators.py) + [backend/models.py#L87-L112](backend/models.py#L87-L112)

---

### 8️⃣ Input Validation (WTForms)

**Validadores implementados:**

1. **CPF Validation**
   ```python
   def validar_cpf(cpf):
       # Verifica formato + dígitos verificadores
       # Rejeita padrões óbvios (111.111.111-11)
   ```

2. **Telefone Validation**
   ```python
   def validar_telefone(telefone):
       # Aceita 10 ou 11 dígitos
       # Remove formatação automática
   ```

3. **Email Validation**
   ```python
   email = StringField(validators=[Email()])  # WTForms built-in
   ```

4. **Tamanho mínimo/máximo**
   ```python
   username = StringField(validators=[Length(min=3, max=80)])
   password = PasswordField(validators=[Length(min=6)])
   ```

5. **Igualdade de campos**
   ```python
   confirmar_senha = PasswordField(validators=[EqualTo('senha')])
   ```

**Localização**: [backend/forms.py](backend/forms.py) + [backend/validators.py](backend/validators.py)

**Proteção contra:**
```
❌ Invalid data
❌ Injection attacks
❌ Buffer overflow
```

---

### 9️⃣ File Upload Security

**Sistema completo:**

```python
def allowed_file_secure(filename, max_size=None, file_obj=None):
    # 1. Validar nome
    if len(filename) > 255:
        return False  # Nome muito longo
    
    # 2. Validar extensão
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False  # Extensão proibida
    
    # 3. PROTEÇÃO contra double extension
    # ❌ fake.exe.png → BLOQUEADO
    # ✅ foto.jpg → PERMITIDO
    
    # 4. Validar MIME type REAL (não confia na extensão)
    mime_type = file_obj.content_type
    if mime_type not in EXPECTED_MIMES:
        return False  # MIME suspeito
    
    # 5. Validar tamanho
    if file_size > MAX_SIZE:
        return False  # Arquivo grande demais
```

**Extensões permitidas:**
```
✅ .png, .jpg, .jpeg, .gif, .bmp, .webp
❌ .exe, .bat, .sh, .py, .php, .asp, .jsp
```

**Localização**: [backend/security_utils.py](backend/security_utils.py#L1-L120)

**Proteção contra:**
```
❌ Malware upload
❌ Double extension attacks
❌ MIME type spoofing
❌ Directory traversal
```

---

### 🔟 Logging & Auditing

**Sistema de logs:**
```python
# app.py
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Exemplos de logs:**
- Login attempts (sucesso/falha)
- Failed rate limiting
- File uploads
- Database changes
- Admin actions

**Localização**: [app.py](app.py#L25-L27)

**Proteção contra:**
```
❌ Undetected attacks
❌ Forensics issues
❌ Compliance violations
```

---

### 1️⃣1️⃣ SQL Injection Prevention

**Tecnologia:**
- SQLAlchemy ORM (parametrized queries)
- **Nunca** concatenar strings em queries

**Seguro (ORM):**
```python
# ✅ SEGURO
user = User.query.filter_by(username=username).first()
users = User.query.filter(User.nivel == 'admin').all()
```

**Inseguro (NÃO fazer):**
```python
# ❌ PERIGOSO - NÃO USE!
user = db.session.execute(f"SELECT * FROM users WHERE username='{username}'")
```

**Localização**: Todo [backend/models.py](backend/models.py) + [app.py](app.py#L1-L3000)

**Proteção contra:**
```
❌ SQL Injection attacks
❌ Database compromise
❌ Data theft
```

---

## 📊 Matriz de Segurança vs Ataques

| Ataque | Proteção |
|--------|----------|
| Brute force | Rate limiting + password hash |
| Phishing | 2FA TOTP |
| CSRF | CSRF token validation |
| XSS | CSP headers + template escaping |
| SQL Injection | SQLAlchemy ORM |
| HTTPS stripping | Talisman HSTS |
| Session hijacking | Session timeout + tokens |
| Unauthorized access | RBAC decorators |
| Malware upload | File validation + MIME checking |
| Man-in-the-middle | HTTPS enforced |

---

## 🚀 Como Usar Cada Sistema

### Ativar 2FA para usuário:
```bash
GET /auth/setup-2fa
# Mostra QR code para Authenticator
# Usuário confirma código de 6 dígitos
```

### Fazer login com 2FA:
```bash
POST /auth/login
# Username + Senha
POST /auth/verify-2fa
# Código 6 dígitos do Authenticator
```

### Usar backup code:
```bash
POST /auth/verify-backup-code
# Se perder Authenticator
# Usar um dos 10 backup codes
```

### Verificar permissão:
```python
@app.route('/admin/users')
@admin_required  # Só admin
def admin_users():
    pass

@app.route('/operadores')
@requer_permissao('operadores')  # Verificar permissão
def listar_operadores():
    pass
```

---

## 📈 Recomendações Futuras

### Melhoras possíveis:
1. **Redis para rate limiting** - Escalar para múltiplos servidores
2. **Password reset link** - Com token temporário
3. **Email verification** - Verificar email ao cadastrar
4. **Account lockout** - Bloquear após X tentativas
5. **Security audit log** - Registrar todas as ações
6. **IP whitelisting** - Para admin panel
7. **Encryption** - Dados sensíveis no BD
8. **OAuth2/SSO** - Google/GitHub login
9. **API key security** - Para APIs externas
10. **Penetration testing** - Teste de segurança profissional

---

## ✅ Checklist de Segurança

- [x] HTTPS em produção
- [x] Senhas hasheadas com salt
- [x] CSRF protection
- [x] 2FA disponível
- [x] Rate limiting
- [x] Session timeout
- [x] Input validation
- [x] File upload security
- [x] Security headers (CSP, HSTS)
- [x] SQL injection prevention
- [x] Logging & auditing
- [x] RBAC (role-based access)
- [ ] Database encryption
- [ ] API authentication
- [ ] Security scanning

---

**Última atualização**: 2026-03-02
**Versão**: 1.0 - Sistema Completo
**Status**: ✅ Produção Ready
