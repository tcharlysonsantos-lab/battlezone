# 🔒 SEGURANÇA DO BATTLEZONE

## ✅ Proteções Implementadas

### 1. **HTTPS + HSTS**
- ✅ Forçar HTTPS em produção via Railway
- ✅ HSTS ativado por 1 ano (`max-age=31536000`)
- ✅ Incluir subdomínios e preload

**Arquivo:** `app.py` - Talisman config

### 2. **Headers de Segurança**
- ✅ `X-Content-Type-Options: nosniff` - Previne MIME-sniffing
- ✅ `X-Frame-Options: SAMEORIGIN` - Protege contra clickjacking
- ✅ `X-XSS-Protection: 1; mode=block` - XSS Protection
- ✅ `Referrer-Policy: strict-origin-when-cross-origin` - Privacy
- ✅ `Permissions-Policy` - Bloqueia geolocation, microphone, camera
- ✅ `Content-Security-Policy` - Controla origem de scripts/styles

**Arquivo:** `backend/security_middleware.py`

### 3. **CSRF Protection**
- ✅ CSRF tokens em todos os formulários
- ✅ Verificação automática via Flask-WTF
- ✅ SameSite cookies (`Lax`)

**Validação:** Verificar presença de `{{ csrf_token() }}` em todos os `<form>` POST/PUT/DELETE

### 4. **Autenticação Forte**
- ✅ 2FA (TOTP + Backup Codes) para ADMIN e GERENTE
- ✅ Password hashing com werkzeug (PBKDF2 + salt)
- ✅ Sessões seguras com tokens únicos
- ✅ Auto-logout por inatividade (5 minutos para operadores)

**Arquivo:** `backend/auth.py`, `backend/auth_security.py`

### 5. **Rate Limiting**
- ✅ 5 tentativas de login em 15 minutos
- ✅ Lockout de 30 minutos após exceder limite
- ✅ Rate limiting global: 200 req/dia, 50 req/hora
- ✅ Proteção específica para endpoints críticos

**Arquivo:** `backend/auth_security.py`

### 6. **Validação de Entrada**
- ✅ Sanitização contra XSS
- ✅ Detecção de padrões maliciosos (SQL injection, code injection, path traversal)
- ✅ Limpeza de caracteres de controle
- ✅ Validação de tipos de arquivo em uploads

**Arquivo:** `backend/security_middleware.py`

**Middleware:** Aplicado automaticamente em rotas POST/PUT/PATCH

### 7. **Logging de Segurança**
- ✅ Todas as tentativas de login (sucesso/falha)
- ✅ Bloqueios por rate limit
- ✅ Acessos administrativos
- ✅ Alterações de dados críticos
- ✅ Eventos de 2FA

**Arquivos:** 
- `logs/app.log` - Log geral
- `logs/security.log` - Eventos de segurança

### 8. **Proteção de Sessão**
- ✅ `SESSION_COOKIE_SECURE` - HTTPS only em produção
- ✅ `SESSION_COOKIE_HTTPONLY` - Não acessível via JavaScript
- ✅ `SESSION_COOKIE_SAMESITE=Lax` - Proteção CSRF
- ✅ Nome customizado `__Session` (não expõe tecnologia)
- ✅ TTL de 24 horas

**Config:** `backend/security_config.py`

### 9. **Proteção de Dados**
- ✅ Senhas hasheadas (nunca em plaintext)
- ✅ Warnames e emails protegidos
- ✅ Backups locais (recomenda-se encriptação)
- ✅ SQL Injection prevenido via SQLAlchemy ORM

### 10. **Proteção contra Força Bruta**
- ✅ Limite de tentativas de login
- ✅ Exponential backoff (aumentar espera após falhas)
- ✅ Bloqueio de IP por período

### 11. **Enumeração de Usuários Prevenida**
- ✅ Mensagens genéricas em erros de autenticação
- ✅ Não revelar se email/username existe

### 12. **Proteção contra Uploads**
- ✅ Validação de extensão de arquivo
- ✅ Renomeação segura de arquivos
- ✅ Limite de tamanho (100 MB)
- ✅ Sanitização de nomes de arquivo

**Função:** `safe_filename_with_timestamp()`

---

## 🔐 Configuração de Segurança

### Variáveis de Ambiente (Railway)
```env
# Obrigatórios
FLASK_ENV=production
SECRET_KEY=<gerado aleatoriamente>
DATABASE_URL=postgresql://...
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=senha-app-especifica

# Opcionais
RATELIMIT_ENABLED=true
RATELIMIT_LOGIN_ATTEMPTS=5
RATELIMIT_LOGIN_WINDOW=900  # 15 minutos
```

### Arquivo `seguranca.env` (LOCAL APENAS)
- ⚠️ **NUNCA** fazer commit deste arquivo
- ✅ Incluído em `.gitignore`
- Usar para desenvolvimento local

---

## 🚨 Incidentes de Segurança

### Se Ocorrer...

#### **Suspeita de Brute Force**
1. Verificar `logs/security.log`
2. Bloquear IP manualmente em Railway
3. Resetar senhas de contas afetadas

#### **Suspeita de Compromisso de Conta**
1. Forçar 2FA para todos os admins
2. Auditar logs da conta
3. Reset de password obrigatório

#### **Injeção de Código/XSS**
1. Verificar alerts em `logs/security.log`
2. Identificar endpoint afetado
3. Adicionar padrão de detecção em `MALICIOUS_PATTERNS`
4. Deploy imediato

---

## ✅ Checklist de Deploy em Produção

- [ ] `FLASK_ENV=production` no Railway
- [ ] `SECRET_KEY` gerada aleatoriamente (64+ chars)
- [ ] HTTPS habilitado (SSL automático no Railway)
- [ ] Email de notificação configurado
- [ ] RATE_LIMIT ativado
- [ ] Logs centralizados
- [ ] Backups encriptados
- [ ] 2FA ativado para admins
- [ ] Monitoramento de segurança ativo

---

## 📚 Referências

- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **Flask Security:** https://flask.palletsprojects.com/security/
- **Python Security:** https://python-security.readthedocs.io/

---

## 🔄 Manutenção Contínua

### Semana
- Revisar `logs/security.log`
- Monitorar tentativas de acesso suspeito

### Mês
- Atualizar dependências Python (pip audit)
- Revisar acessos administrativos

### Trimestre
- Pentesting básico
- Auditoria de logs
- Review de políticas de senha

### Anual
- Pentesting profissional
- Atualização de biblioteca de segurança
- Review completo de infraestrutura

---

**Última atualização:** 2026-03-03  
**Versão:** 3.1.0
