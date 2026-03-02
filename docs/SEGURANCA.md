# 🔐 Segurança - BattleZone

## Implementações de Segurança

### Autenticação
- ✅ CSRF Protection (Flask-WTF)
- ✅ Password hashing com salt (werkzeug)
- ✅ Session security (HttpOnly, SameSite, Secure)
- ✅ Two-Factor Authentication (2FA) disponível
- ✅ Rate limiting (60 req/min no login)

### Headers de Segurança
- ✅ Flask-Talisman
- ✅ Content Security Policy (CSP)
- ✅ HSTS (em produção)
- ✅ X-Frame-Options

### Validação
- ✅ Email validation
- ✅ CPF validation (11 dígitos)
- ✅ Telefone validation
- ✅ Password strength

### Variáveis de Ambiente
- ✅ SECRET_KEY obrigatória (32+ caracteres)
- ✅ FLASK_ENV (development/production)
- ✅ Arquivo `.env` ignorado no Git

## Arquivos Relevantes

### Security Utils
- `security_utils.py` - Funções de validação e sanitização
- `auth_security.py` - Funções de 2FA

### Configuração
- `config.py` - Configuração centralizada
- `seguranca.env` - Variáveis secretas (LOCAL ONLY)

## Práticas de Segurança

1. **Senhas**: Sempre com hash + salt
2. **CSRF**: Token em todos os forms
3. **SQL Injection**: SQLAlchemy ORM + parameterized queries
4. **XSS**: Jinja2 templates auto-escape
5. **CORS**: Controlado via Talisman

## 2FA (Two-Factor Authentication)

### Disponível em:
- `auth_security.py` - Funções principais
- `models.py` - Campo `User.two_factor_enabled`

### Como ativar:
User pode ativar 2FA no perfil. Scanner com QR code gera TOTP.

## Acesso e Permissões

### Níveis de Acesso
- `admin` - Acesso total
- `operador` - Gerencia partidas e estatísticas
- `user` - Visualiza informações básicas

### Decoradores
- `@admin_required` - Restringe a admins
- `@requer_permissao` - Baseado em recurso
- `@operador_session_required` - Restringe a operadores

## Production Checklist

- [ ] `FLASK_ENV=production`
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` configurada (32+ chars)
- [ ] HTTPS habilitado (Railway faz automaticamente)
- [ ] Database backup configurado
- [ ] Logs persistidos
- [ ] Rate limiting ativo
- [ ] CSP configurado

