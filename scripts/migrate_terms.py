"""
Script para migrar banco de dados - Adiciona novos campos
"""
import os
import sys
from pathlib import Path

# Adicionar raiz ao path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
os.chdir(project_root)

def migrate_to_add_terms_and_security():
    """Adiciona campos terms_accepted e terms_accepted_date ao banco"""
    from app import app, db
    from sqlalchemy import inspect, text
    
    with app.app_context():
        # Inspecionar a tabela users
        inspector = inspect(db.engine)
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        solicitacoes_columns = [col['name'] for col in inspector.get_columns('solicitacoes')]
        
        print("📋 Colunas atuais em 'users':", users_columns)
        print("📋 Colunas atuais em 'solicitacoes':", solicitacoes_columns)
        
        # Adicionar colunas faltantes em users
        try:
            if 'terms_accepted' not in users_columns:
                print("\n➕ Adicionando terms_accepted em users...")
                with db.engine.connect() as connect:
                    connect.execute(text('ALTER TABLE users ADD COLUMN terms_accepted BOOLEAN DEFAULT 0'))
                    connect.commit()
                print("✅ terms_accepted adicionado")
        except Exception as e:
            print(f"⚠️  terms_accepted: {e}")
        
        try:
            if 'terms_accepted_date' not in users_columns:
                print("\n➕ Adicionando terms_accepted_date em users...")
                with db.engine.connect() as connect:
                    connect.execute(text('ALTER TABLE users ADD COLUMN terms_accepted_date DATETIME'))
                    connect.commit()
                print("✅ terms_accepted_date adicionado")
        except Exception as e:
            print(f"⚠️  terms_accepted_date: {e}")
        
        # Adicionar colunas faltantes em solicitacoes
        try:
            if 'terms_accepted' not in solicitacoes_columns:
                print("\n➕ Adicionando terms_accepted em solicitacoes...")
                with db.engine.connect() as connect:
                    connect.execute(text('ALTER TABLE solicitacoes ADD COLUMN terms_accepted BOOLEAN DEFAULT 0'))
                    connect.commit()
                print("✅ terms_accepted adicionado em solicitacoes")
        except Exception as e:
            print(f"⚠️  terms_accepted em solicitacoes: {e}")
        
        try:
            if 'terms_accepted_date' not in solicitacoes_columns:
                print("\n➕ Adicionando terms_accepted_date em solicitacoes...")
                with db.engine.connect() as connect:
                    connect.execute(text('ALTER TABLE solicitacoes ADD COLUMN terms_accepted_date DATETIME'))
                    connect.commit()
                print("✅ terms_accepted_date adicionado em solicitacoes")
        except Exception as e:
            print(f"⚠️  terms_accepted_date em solicitacoes: {e}")
        
        print("\n✅ Migração concluída com sucesso!")

if __name__ == '__main__':
    try:
        migrate_to_add_terms_and_security()
    except Exception as e:
        print(f"❌ ERRO na migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
