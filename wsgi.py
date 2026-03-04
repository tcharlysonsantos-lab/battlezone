# wsgi.py - Entry point para Gunicorn e Railway
import sys
import os
import logging

# Configurar logging ANTES de importar app
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*70, flush=True)
print("[WSGI] STARTING APPLICATION INITIALIZATION", flush=True)
print("="*70, flush=True)

logger.info(f"[WSGI] Python: {sys.version}")
logger.info(f"[WSGI] Platform: {sys.platform}")
logger.info(f"[WSGI] CWD: {os.getcwd()}")

# Auto-detect production from environment
logger.info(f"[WSGI] FLASK_ENV in environ: {'FLASK_ENV' in os.environ}")
logger.info(f"[WSGI] DATABASE_URL in environ: {'DATABASE_URL' in os.environ}")
logger.info(f"[WSGI] SECRET_KEY in environ: {'SECRET_KEY' in os.environ}")

if 'DATABASE_URL' in os.environ and 'FLASK_ENV' not in os.environ:
    logger.warning("[WSGI] DATABASE_URL detected but FLASK_ENV not set - auto-setting to production")
    os.environ['FLASK_ENV'] = 'production'
elif 'FLASK_ENV' not in os.environ:
    logger.warning("[WSGI] FLASK_ENV not set - defaulting to development")
    os.environ['FLASK_ENV'] = 'development'

logger.info(f"[WSGI] FLASK_ENV is now: {os.environ.get('FLASK_ENV')}")

try:
    logger.info("[WSGI] ===== IMPORTING FLASK APP =====")
    
    logger.info("[WSGI] Importing config...")
    from config import config
    logger.info(f"[WSGI] Config loaded. DB_TYPE: {getattr(config, 'DB_TYPE', 'Unknown')}")
    logger.info(f"[WSGI] Database URI: {config.SQLALCHEMY_DATABASE_URI[:50]}...")
    
    logger.info("[WSGI] Importing app module...")
    from app import app
    logger.info(f"[WSGI] App imported: {app}")
    logger.info(f"[WSGI] App debug: {app.debug}")
    logger.info(f"[WSGI] App name: {app.name}")
    
    # Verificar extensões
    logger.info("[WSGI] Checking app extensions...")
    logger.info(f"[WSGI] - Has db: {hasattr(app, 'extensions') and 'sqlalchemy' in app.extensions}")
    logger.info(f"[WSGI] - Has login_manager: {hasattr(app, 'login_manager')}")
    
    logger.info("[WSGI] ===== APP INITIALIZATION SUCCESSFUL =====")
    
    # Exportar app para Gunicorn/WSGI
    application = app
    logger.info("[WSGI] Application object exported successfully")
    logger.info(f"[WSGI] Ready to serve requests!")
    print("="*70 + "\n", flush=True)
    
except ImportError as e:
    logger.error(f"[WSGI] IMPORT ERROR: {e}", exc_info=True)
    print("="*70, flush=True)
    sys.exit(1)
except Exception as e:
    logger.error(f"[WSGI] FATAL ERROR: {e}", exc_info=True)
    print("="*70, flush=True)
    sys.exit(1)


