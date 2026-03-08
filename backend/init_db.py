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


def seed_battlepasses(app):
    """Insert default battlepasses if none exist - for Railway initialization"""
    try:
        with app.app_context():
            # Verificar se já existem battlepasses
            existing_battlepasses = Battlepass.query.count()
            
            if existing_battlepasses > 0:
                logger.info(f"[SEED] ✓ Battlepasses já existem ({existing_battlepasses}). Pulando seed.")
                return
            
            logger.info("[SEED] 🌱 Inserindo battlepasses de exemplo...")
            
            # Battlepasses de Operador (semanais)
            battlepasses_operador = [
                Battlepass(
                    tipo="operador_basico",
                    nome="Operador Básico",
                    descricao="Sorteio semanal para operadores - Categoria Básica",
                    categoria="operador",
                    ativo=True
                ),
                Battlepass(
                    tipo="operador_elite",
                    nome="Operador Elite",
                    descricao="Sorteio semanal para operadores - Categoria Elite",
                    categoria="operador",
                    ativo=True
                ),
            ]
            
            # Battlepasses de Equipe (mensais)
            battlepasses_equipe = [
                Battlepass(
                    tipo="equipe_basica",
                    nome="Equipe Básica",
                    descricao="Sorteio mensal para equipes - Categoria Básica",
                    categoria="equipe",
                    ativo=True
                ),
            ]
            
            # Adicionar todas as battlepasses
            for bp in battlepasses_operador + battlepasses_equipe:
                db.session.add(bp)
            
            db.session.commit()
            
            total_criadas = len(battlepasses_operador) + len(battlepasses_equipe)
            logger.info(f"[SEED] ✅ {total_criadas} battlepasses foram criadas com sucesso!")
            
    except Exception as e:
        logger.error(f"[SEED] ✗ Erro ao seed battlepasses: {e}")
        try:
            db.session.rollback()
        except:
            pass
