# security_config.py - CONFIGURAÇÕES DE SEGURANÇA CENTRALIZADAS
import os
from datetime import timedelta

# ==================== PROTEÇÃO CONTRA FORÇA BRUTA ====================

# Rate Limiting
RATELIMIT = {
    'LOGIN': {
        'max_attempts': 5,
        'window_minutes': 15,
        'lockout_minutes': 30
    },
    'API': {
        'default': '200 per day, 50 per hour',
        'login': '10 per hour',
        'register': '5 per day'
    }
}

# ==================== SESSÃO E COOKIES ====================

SESSION_CONFIG = {
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=24),
    'SESSION_COOKIE_SECURE': not os.getenv('FLASK_ENV') == 'development',  # HTTPS only em produção
    'SESSION_COOKIE_HTTPONLY': True,  # Não acessível via JavaScript
    'SESSION_COOKIE_SAMESITE': 'Lax',  # Proteção CSRF
    'SESSION_COOKIE_NAME': '__Session',  # Nome customizado (não expõe tecnologia)
}

# ==================== PASSWORD POLICY ====================

PASSWORD_POLICY = {
    'min_length': 8,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_numbers': True,
    'require_special': False,  # Opcional baseado em UX
    'max_age_days': 90,  # Expirar senha após 90 dias
    'history': 5,  # Não permitir últimas 5 senhas
}

# ==================== 2FA / MFA ====================

TWO_FACTOR_AUTH = {
    'required_for': ['admin', 'gerente'],  # Obrigatório para estes níveis
    'optional_for': ['operador', 'usuario'],
    'device_memory_days': 30,  # Lembrar dispositivo por 30 dias
    'backup_codes': 10,  # Número de códigos de backup
}

# ==================== AUDIT LOG ====================

AUDIT_LOG = {
    'enabled': True,
    'log_file': 'logs/audit.log',
    'eventos_criticos': [
        'user_created',
        'user_deleted',
        'user_role_changed',
        'admin_login',
        'data_export',
        'database_modified',
        'backup_created',
        'settings_changed',
    ]
}

# ==================== PROTEÇÃO DE DADOS ====================

DATA_PROTECTION = {
    'encrypt_pii': True,  # Criptografar dados pessoais (email, phone)
    'encrypt_algorithm': 'AES-256',
    'purge_logs_days': 90,  # Manter logs por 90 dias
    'gdpr_compliant': True,
}

# ==================== HEADERS DE SEGURANÇA ====================

SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
}

# ==================== PROTEÇÃO CONTRA ATAQUES ====================

ATTACK_PROTECTION = {
    'max_request_size': '16MB',  # Limitar tamanho de request
    'max_upload_size': '100MB',  # Limitar tamanho de upload
    'upload_extensions': ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'zip'],
    'scan_uploads': True,  # Escanear uploads em busca de malware
}

# ==================== VALIDAÇÃO ====================

VALIDATION = {
    'block_common_passwords': True,
    'check_compromised_password': False,  # Integrar com Have I Been Pwned?
    'validate_email': True,
    'email_verification': True,
}
