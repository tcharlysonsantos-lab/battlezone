# wsgi.py - Entry point para Gunicorn e Railway
import sys
import os
import logging

# Configurar logging para capturar erros durante inicialização
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('wsgi.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("[WSGI] Starting application initialization...")
logger.info(f"[WSGI] Environment: FLASK_ENV={os.environ.get('FLASK_ENV', 'NOT SET')}")
logger.info(f"[WSGI] Has DATABASE_URL: {'DATABASE_URL' in os.environ}")

# Auto-detect production from environment
# Railway sets DATABASE_URL when PostgreSQL is added
if 'DATABASE_URL' in os.environ and 'FLASK_ENV' not in os.environ:
    logger.info("[WSGI] Auto-detecting production (DATABASE_URL found, setting FLASK_ENV=production)")
    os.environ['FLASK_ENV'] = 'production'
elif 'FLASK_ENV' not in os.environ:
    logger.warning("[WSGI] FLASK_ENV not set, using development mode")
    os.environ['FLASK_ENV'] = 'development'

try:
    logger.info("[WSGI] Importing Flask app from app.py...")
    from app import app
    logger.info("[WSGI] App imported successfully!")
    logger.info(f"[WSGI] App config: DEBUG={app.debug}, ENV={os.environ.get('FLASK_ENV')}")
    
    # Exportar app para Gunicorn/WSGI
    application = app
    logger.info("[WSGI] Application ready for Gunicorn")
    
except Exception as e:
    logger.error(f"[WSGI] FATAL ERROR during app initialization: {e}", exc_info=True)
    sys.exit(1)


