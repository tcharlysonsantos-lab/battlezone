#!/usr/bin/env python
"""
Script para corrigir o tamanho da coluna 'battlepass' no banco PostgreSQL
Executa: python fix_battlepass_column.py (local) ou railway run python fix_battlepass_column.py (Railway)
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def corrigir_colunas():
    """Corrige o tamanho das colunas battlepass no banco de dados"""
    with app.app_context():
        try:
            print("\n[INFO] 🔨 Corrigindo tamanho da coluna 'battlepass'...")
            print("=" * 60)
            
            # Verificar tipo de banco de dados
            db_type = str(db.engine.url).split(':')[0]
            print(f"Banco de dados: {db_type}")
            
            # SQL para PostgreSQL
            if 'postgresql' in db_type:
                print("\n[INFO] Executando alterações para PostgreSQL...")
                
                # Alterar coluna de operadores
                print("  - Alterando operadores.battlepass (10 → 50)...")
                db.session.execute(db.text("""
                    ALTER TABLE operadores 
                    ALTER COLUMN battlepass 
                    TYPE character varying(50)
                """))
                
                # Alterar coluna de equipes
                print("  - Alterando equipes.battlepass (10 → 50)...")
                db.session.execute(db.text("""
                    ALTER TABLE equipes 
                    ALTER COLUMN battlepass 
                    TYPE character varying(50)
                """))
                
                db.session.commit()
                print("\n✅ Colunas corrigidas com sucesso!")
                print("=" * 60)
                print("\nAgora você pode:")
                print("  ✓ Atualizar operadores com battlepass 'ELITE_CAVEIRA'")
                print("  ✓ Atualizar equipes com battlepass 'EQUIPE_BASICA'")
                print("\nTamanho anterior: 10 caracteres")
                print("Tamanho novo: 50 caracteres")
                
            elif 'sqlite' in db_type:
                print("[WARNING] SQLite não suporta ALTER COLUMN TYPE")
                print("SQLite requer recreação da tabela para alterar tipos")
                print("Recomenda-se usar PostgreSQL para produção")
                return False
                
            else:
                print(f"[ERROR] Banco de dados não suportado: {db_type}")
                return False
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro ao corrigir colunas:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    sucesso = corrigir_colunas()
    sys.exit(0 if sucesso else 1)
