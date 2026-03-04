# wsgi.py - Entry point para Gunicorn e Railway
import os
import logging
from app import app, db, db_health_check

logger = logging.getLogger(__name__)

# Inicializar app context e serviços quando WSGI é carregado
def init_app():
    """Inicializa app na primeira requisição para produção"""
    try:
        with app.app_context():
            # Criar tabelas se necessário
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                if not os.path.exists('instance/database.db'):
                    logger.info("[WSGI] Criando tabelas SQLite...")
                    db.create_all()
            
            # Iniciar health check em background (sem bloquear)
            try:
                if not hasattr(db_health_check, '_app'):
                    db_health_check.init_app(app, db)
                if not db_health_check.running:
                    db_health_check.start()
                    logger.info("[WSGI] Database Health Check iniciado")
            except Exception as e:
                logger.warning(f"[WSGI] Health check não disponível: {e}")
    except Exception as e:
        logger.error(f"[WSGI] Erro ao inicializar: {e}")

# Inicializar uma vez
init_app()

# Exportar app para Gunicorn/WSGI
if __name__ != '__main__':
    # Railway/Gunicorn usa isto
    application = app
else:
    # Local development
    application = app
