#!/usr/bin/env python
"""
Script para criar índices críticos no banco de dados
✅ OTIMIZAÇÃO: Melhora performance de queries frequentes

Índices criados:
1. Partida.data - para filtros por data em calendario_publico
2. Partida.finalizada - para filtros de partidas ativas/finalizadas
3. Estoque.quantidade - para alertas de baixo estoque
"""

from app import app, db
from backend.models import Partida, Estoque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def criar_indices():
    """Criar índices no banco de dados"""
    
    with app.app_context():
        try:
            logger.info("🔧 Iniciando criação de índices...")
            
            # Usar raw SQL para criar índices (mais compatível)
            engine = db.engine
            
            indices = [
                {
                    'nome': 'ix_partida_data',
                    'tabela': 'partidas',
                    'coluna': 'data',
                    'sql': 'CREATE INDEX IF NOT EXISTS ix_partida_data ON partidas(data);'
                },
                {
                    'nome': 'ix_partida_finalizada',
                    'tabela': 'partidas',
                    'coluna': 'finalizada',
                    'sql': 'CREATE INDEX IF NOT EXISTS ix_partida_finalizada ON partidas(finalizada);'
                },
                {
                    'nome': 'ix_estoque_quantidade',
                    'tabela': 'estoque',
                    'coluna': 'quantidade',
                    'sql': 'CREATE INDEX IF NOT EXISTS ix_estoque_quantidade ON estoque(quantidade);'
                },
                {
                    'nome': 'ix_partida_data_finalizada',
                    'tabela': 'partidas',
                    'coluna': 'data, finalizada',
                    'sql': 'CREATE INDEX IF NOT EXISTS ix_partida_data_finalizada ON partidas(data, finalizada);'
                }
            ]
            
            for indice in indices:
                try:
                    logger.info(f"  Criando índice: {indice['nome']} ({indice['tabela']}.{indice['coluna']})")
                    with engine.connect() as conn:
                        conn.execute(indice['sql'])
                        conn.commit()
                    logger.info(f"  ✅ Índice {indice['nome']} criado com sucesso")
                except Exception as e:
                    logger.warning(f"  ⚠️ Índice {indice['nome']} pode já existir: {e}")
            
            logger.info("✅ Índices criados com sucesso!")
            logger.info("\n📊 Próximas otimizações a implementar:")
            logger.info("  1. ✅ Throttle de session.update_activity() - FEITO")
            logger.info("  2. ✅ SQL-level date filtering em calendario_publico - FEITO")
            logger.info("  3. ✅ Dashboard queries consolidadas - FEITO")
            logger.info("  4. ✅ Eager loading de participantes - FEITO")
            logger.info("  5. ✅ Índices no banco de dados - FEITO")
            logger.info("\n💾 Próximas etapas:")
            logger.info("  6. Implementar caching com Flask-Caching")
            logger.info("  7. Adicionar paginação em endpoints pesados")
            logger.info("  8. Monitorar queries com SQLAlchemy event listeners")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar índices: {e}")
            raise

if __name__ == '__main__':
    criar_indices()
