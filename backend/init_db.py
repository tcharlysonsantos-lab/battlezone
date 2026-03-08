# backend/init_db.py - Create database tables on app startup
import logging
from backend.models import db, User, Operador, Equipe, Partida, PartidaParticipante, Venda, Estoque, Log, Solicitacao, PagamentoOperador, Evento, Sorteio, Battlepass

logger = logging.getLogger(__name__)

def init_database(app):
    """Initialize database tables if they don't exist - Improved version"""
    try:
        with app.app_context():
            # ===== VERIFICAR CONEXÃO COM BANCO =====
            try:
                inspector = db.inspect(db.engine)
                existing_tables = set(inspector.get_table_names())
                logger.info(f"[DB] ✓ Conexão estabelecida. Tabelas existentes: {len(existing_tables)}")
            except Exception as conn_error:
                logger.error(f"[DB] ✗ Erro na conexão: {conn_error}")
                raise
            
            # ===== TABELAS NECESSÁRIAS =====
            required_tables = {
                'user',
                'operador',
                'equipe',
                'partida',
                'partida_participante',
                'venda',
                'estoque',
                'log',
                'solicitacao',
                'pagamento_operador',
                'evento',
                'sorteio',
                'battlepass'
            }
            
            # ===== VERIFICAR TABELAS FALTANTES =====
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                logger.warning(f"[DB] ⚠️  Tabelas faltando: {missing_tables}")
                logger.info("[DB] 🔄 Criando todas as tabelas do sistema...")
                
                try:
                    db.create_all()
                    logger.info("[DB] ✅ Todas as tabelas foram criadas com sucesso!")
                    
                    # Verificar novamente
                    inspector = db.inspect(db.engine)
                    new_tables = set(inspector.get_table_names())
                    logger.info(f"[DB] ✓ Verificação: {len(new_tables)} tabelas agora presentes")
                    
                except Exception as create_error:
                    logger.error(f"[DB] ✗ Erro ao criar tabelas: {create_error}")
                    raise
            else:
                logger.info(f"[DB] ✅ Todas as {len(existing_tables)} tabelas necessárias existem!")
                
    except Exception as e:
        logger.error(f"[DB] ✗ Erro crítico na inicialização: {e}")
        # Não lançar exceção para não derrubar a app, apenas avisar
        logger.error("[DB] ⚠️  A aplicação continuará, mas funcionalidades podem estar limitadas")
