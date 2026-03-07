#!/usr/bin/env python
"""
🚀 Auto-Migration - Executa correções de schema na inicialização
Será chamado automaticamente quando a app inicia em produção
"""

import os
import sys
from sqlalchemy import inspect

def auto_migrate_battlepass(app, db):
    """
    Migração automática: corrige VARCHAR(10) → VARCHAR(50) em produção
    Chamada automaticamente na inicialização da app
    """
    
    # Só executar em produção e com PostgreSQL
    if os.environ.get('FLASK_ENV') != 'production':
        return False
    
    if 'postgresql' not in str(db.engine.url):
        return False
    
    try:
        print("\n[AUTO-MIGRATE] 🔄 Verificando schema...")
        
        inspector = inspect(db.engine)
        
        # Verificar operadores.battlepass
        operadores_cols = inspector.get_columns('operadores')
        operadores_battlepass = next((col for col in operadores_cols if col['name'] == 'battlepass'), None)
        
        if operadores_battlepass:
            current_type = str(operadores_battlepass['type'])
            print(f"  operadores.battlepass: {current_type}")
            
            # Se ainda for VARCHAR(10), corrigir
            if 'VARCHAR(10)' in current_type.upper():
                print("  ⚠️  Detectado VARCHAR(10) - corrigindo...")
                
                db.session.execute(db.text("""
                    ALTER TABLE operadores 
                    ALTER COLUMN battlepass 
                    TYPE character varying(50)
                """))
                
                db.session.commit()
                print("  ✅ operadores.battlepass corrigido para VARCHAR(50)")
        
        # Verificar equipes.battlepass
        equipes_cols = inspector.get_columns('equipes')
        equipes_battlepass = next((col for col in equipes_cols if col['name'] == 'battlepass'), None)
        
        if equipes_battlepass:
            current_type = str(equipes_battlepass['type'])
            print(f"  equipes.battlepass: {current_type}")
            
            # Se ainda for VARCHAR(10), corrigir
            if 'VARCHAR(10)' in current_type.upper():
                print("  ⚠️  Detectado VARCHAR(10) - corrigindo...")
                
                db.session.execute(db.text("""
                    ALTER TABLE equipes 
                    ALTER COLUMN battlepass 
                    TYPE character varying(50)
                """))
                
                db.session.commit()
                print("  ✅ equipes.battlepass corrigido para VARCHAR(50)")
        
        print("[AUTO-MIGRATE] ✅ Schema verificado e corrigido!\n")
        return True
        
    except Exception as e:
        print(f"[AUTO-MIGRATE] ⚠️  Erro: {str(e)}")
        return False
