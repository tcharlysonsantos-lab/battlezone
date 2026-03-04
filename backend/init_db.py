# backend/init_db.py - Create database tables on app startup
import logging
from backend.models import db, User, Operador, Equipe, Partida, PartidaParticipante, Venda, Estoque, Log, Solicitacao, PagamentoOperador

logger = logging.getLogger(__name__)

def init_database(app):
    """Initialize database tables if they don't exist"""
    try:
        with app.app_context():
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                logger.info("[DB] Creating all database tables...")
                db.create_all()
                logger.info("[DB] All tables created successfully")
            else:
                logger.info(f"[DB] Database already initialized ({len(existing_tables)} tables found)")
                
    except Exception as e:
        logger.error(f"[DB] Error initializing database: {e}")
        raise
