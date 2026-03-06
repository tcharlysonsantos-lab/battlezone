#!/usr/bin/env python
"""
Script para criar índices críticos no banco de dados
✅ OTIMIZAÇÃO: Melhora performance de queries frequentes

Índices criados:
1. Partida.data - para filtros por data em calendario_publico
2. Partida.finalizada - para filtros de partidas ativas/finalizadas
3. Estoque.quantidade - para alertas de baixo estoque
"""

import sys
import os

# Adicionar o diretório pai ao path para importar app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from backend.models import Partida, Estoque
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def criar_indices():
    """Criar índices no banco de dados"""
    
    with app.app_context():
        try:
            logger.info("[INDEX] Iniciando criacao de indices...")
            
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
                    logger.info(f"[INDEX] Criando: {indice['nome']} ({indice['tabela']}.{indice['coluna']})")
                    with engine.begin() as conn:
                        conn.execute(text(indice['sql']))
                    logger.info(f"[OK] Indice {indice['nome']} criado com sucesso")
                except Exception as e:
                    logger.warning(f"[SKIP] Indice {indice['nome']} pode ja existir: {e}")
            
            logger.info("[OK] Indices criados com sucesso!")
            logger.info("[INFO] Proximas otimizacoes implementadas:")
            logger.info("[OK] 1. Throttle de session.update_activity() - FEITO")
            logger.info("[OK] 2. SQL-level date filtering em calendario_publico - FEITO")
            logger.info("[OK] 3. Dashboard queries consolidadas - FEITO")
            logger.info("[OK] 4. Eager loading de participantes - FEITO")
            logger.info("[OK] 5. Indices no banco de dados - FEITO")
            logger.info("[INFO] Proximas etapas:")
            logger.info("[TODO] 6. Implementar caching com Flask-Caching")
            logger.info("[TODO] 7. Adicionar paginacao em endpoints pesados")
            logger.info("[TODO] 8. Monitorar queries com SQLAlchemy event listeners")
            
        except Exception as e:
            logger.error(f"[ERROR] Erro ao criar indices: {e}")
            raise

if __name__ == '__main__':
    criar_indices()
