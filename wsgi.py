# wsgi.py - WSGI entry point for Gunicorn and Railway
import sys
import os
import logging

# Configure logging BEFORE importing app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("[WSGI] APPLICATION INITIALIZATION START")
print("="*70)

logger.info(f"[WSGI] Python: {sys.version.split()[0]}")
logger.info(f"[WSGI] CWD: {os.getcwd()}")

# Auto-detect production from environment
logger.info(f"[WSGI] FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT SET')}")
logger.info(f"[WSGI] DATABASE_URL: {'YES' if 'DATABASE_URL' in os.environ else 'NO'}")

if 'DATABASE_URL' in os.environ and 'FLASK_ENV' not in os.environ:
    logger.warning("[WSGI] DATABASE_URL found, auto-setting FLASK_ENV=production")
    os.environ['FLASK_ENV'] = 'production'
elif 'FLASK_ENV' not in os.environ:
    logger.info("[WSGI] FLASK_ENV not set, using development")
    os.environ['FLASK_ENV'] = 'development'

logger.info(f"[WSGI] Mode: {os.environ.get('FLASK_ENV')}")

try:
    logger.info("[WSGI] Importing Flask app...")
    from app import app
    logger.info(f"[WSGI] App imported OK")
    logger.info(f"[WSGI] Debug: {app.debug}")
    
    # Export for Gunicorn/WSGI
    application = app
    logger.info("[WSGI] Ready for Gunicorn")
    
except Exception as e:
    logger.error(f"[WSGI] FATAL: {e}", exc_info=True)
    print("="*70)
    sys.exit(1)

print("="*70 + "\n")


