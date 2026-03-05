# config.py - CONFIGURAÇÃO CENTRALIZADA E SEGURA
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# ==================== CARREGAR VARIÁVEIS DE AMBIENTE ====================
# Carrega o arquivo seguranca.env APENAS em desenvolvimento
# Em produção (Railway), as variáveis vêm do dashboard
if os.environ.get('FLASK_ENV') != 'production':
    load_dotenv('seguranca.env')

# ==================== CRIAR PASTA INSTANCE ====================
# Criar pasta instance se não existir (necessário para banco de dados)
BASE_DIR = Path(__file__).parent
INSTANCE_PATH = BASE_DIR / 'instance'
INSTANCE_PATH.mkdir(exist_ok=True)

# ==================== VALIDAÇÃO OBRIGATÓRIA ====================
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError(
        "❌ ERRO CRÍTICO: SECRET_KEY não configurada ou muito curta!\n"
        "Instruções:\n"
        "1. Copie seguranca.env.example para seguranca.env\n"
        "2. Gere uma chave segura: python -c \"import secrets; print(secrets.token_hex(32))\"\n"
        "3. Coloque o valor em SECRET_KEY no seguranca.env"
    )

# ==================== CONFIGURAÇÃO GERAL ====================
class Config:
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Banco de dados (compatível com SQLite local e PostgreSQL em produção)
    # Railway passa DATABASE_URL automaticamente quando você adiciona PostgreSQL
    
    # Se estiver em produção e há DATABASE_URL (Railway), usa PostgreSQL
    # Caso contrário, usa SQLite local
    _database_url = os.environ.get('DATABASE_URL')
    
    # DEBUG: print da DATABASE_URL
    print(f"[CONFIG] DATABASE_URL raw: {_database_url}")
    print(f"[CONFIG] DATABASE_URL type: {type(_database_url)}")
    print(f"[CONFIG] DATABASE_URL is empty: {not _database_url}")
    if _database_url:
        print(f"[CONFIG] DATABASE_URL starts with: {_database_url[:20]}")
        print(f"[CONFIG] DATABASE_URL full (first 100 chars): {_database_url[:100]}")
    
    # Aceitar postgresql:// OU postgres://
    if _database_url and (_database_url.startswith('postgres') or _database_url.startswith('postgresql')):
        # Railway PostgreSQL - Railway pode usar postgresql:// ou postgres://
        print(f"[CONFIG] Using PostgreSQL from DATABASE_URL")
        SQLALCHEMY_DATABASE_URI = _database_url
        DB_TYPE = 'PostgreSQL'
    else:
        # SQLite local (desenvolvimento e free tier Railway)
        print(f"[CONFIG] Using SQLite - DATABASE_URL not valid for PostgreSQL")
        # Usa caminho ABSOLUTO para SQLite funcionar corretamente
        db_file = os.path.abspath(os.path.join(str(INSTANCE_PATH), 'database.db'))
        # Converte backslashes em slashes para URL (IMPORTANTE para Windows!)
        db_file = db_file.replace('\\', '/')
        # URL de SQLite: sqlite:///caminho/absoluto
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_file}'
        DB_TYPE = 'SQLite'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração de pool para manter conexão SEMPRE ATIVA (conexão persistente)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # Mantém 10 conexões abertas sempre
        'pool_recycle': 1800,  # Recicla a cada 30 minutos
        'pool_pre_ping': True,  # Verifica saúde antes de usar
        'pool_use_lifo': True,  # Usa conexão mais recente (menos chance de timeout)
        'max_overflow': 5,  # Permite 5 conexões extras se necessário
        'echo_pool': False,  # Log de pool (desabilitar em produção)
        'isolation_level': 'AUTOCOMMIT',  # Autocommit para evitar locks longos
    }
    
    # Sessões (melhorado para produção com HTTPS)
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    # Em produção com HTTPS, usar Secure + SameSite=Lax para máxima compatibilidade
    # Railway: setting SESSION_COOKIE_SECURE=False allows HTTPS proxy to work properly
    # The ProxyFix middleware will handle X-Forwarded-Proto correctly
    SESSION_COOKIE_SECURE = False  # Let proxy handle HTTPS, don't force Secure flag
    SESSION_COOKIE_HTTPONLY = True  # Protege contra XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protege contra CSRF, funciona bem com HTTPS
    SESSION_COOKIE_DOMAIN = None  # Deixar None para funcionar em subdomínios
    REMEMBER_COOKIE_SECURE = False  # Railway proxy handles HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # Em produção, fazer força permanência de sessão para não perder durante navegação
    PERMANENT_SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutos
    
    # Upload
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))  # 16MB padrão
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configuração de Health Check (verifica conexão a cada 30 segundos)
    DB_HEALTH_CHECK_INTERVAL = 30  # segundos
    DB_HEALTH_CHECK_ENABLED = True
    
    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'true').lower() == 'true'
    RATELIMIT_LOGIN_ATTEMPTS = int(os.environ.get('RATELIMIT_LOGIN_ATTEMPTS', 5))
    RATELIMIT_LOGIN_WINDOW = int(os.environ.get('RATELIMIT_LOGIN_WINDOW', 900))  # 15 minutos
    
    # 2FA
    TWO_FACTOR_ENABLED = os.environ.get('TWO_FACTOR_ENABLED', 'false').lower() == 'true'
    OTP_ISSUER_NAME = os.environ.get('OTP_ISSUER_NAME', 'BattleZone')
    
    # Logging
    LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Sentry (monitoramento de erros)
    SENTRY_DSN = os.environ.get('SENTRY_DSN')

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # HTTP permitido em dev

class ProductionConfig(Config):
    """Configuração para produção - MAIS RESTRITIVA"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS obrigatório
    
    # Se não tiver SECRET_KEY em produção, falha
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY é obrigatória em produção!")

class TestingConfig(Config):
    """Configuração para testes"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Selecionar configuração baseado em FLASK_ENV
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

if FLASK_ENV == 'production':
    config = ProductionConfig()
elif FLASK_ENV == 'testing':
    config = TestingConfig()
else:
    config = DevelopmentConfig()
