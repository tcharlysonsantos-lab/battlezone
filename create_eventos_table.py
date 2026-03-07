#!/usr/bin/env python
"""
Script para criar as tabelas de Evento e EventoBrinde no banco PostgreSQL
Executa: python create_eventos_table.py
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from backend.models import Evento, EventoBrinde

def criar_tabelas():
    """Cria as tabelas no banco de dados"""
    with app.app_context():
        try:
            print("[INFO] Verificando e criando tabelas de Evento e EventoBrinde...")
            
            # Criar as tabelas
            db.create_all()
            
            print("[INFO] ✅ Tabelas criadas com sucesso!")
            print("  - Tabela 'eventos' criada")
            print("  - Tabela 'evento_brindes' criada")
            
            # Verificar se as tabelas existem
            inspector = db.inspect(db.engine)
            tabelas_existentes = inspector.get_table_names()
            
            if 'eventos' in tabelas_existentes:
                print("\n✅ Tabela 'eventos' está ATIVA no banco de dados")
                colunas = inspector.get_columns('eventos')
                print(f"   Colunas: {len(colunas)}")
                for col in colunas[:3]:
                    print(f"   - {col['name']}: {col['type']}")
            else:
                print("\n❌ Tabela 'eventos' NÃO foi criada")
                
            if 'evento_brindes' in tabelas_existentes:
                print("✅ Tabela 'evento_brindes' está ATIVA no banco de dados")
            else:
                print("❌ Tabela 'evento_brindes' NÃO foi criada")
                
            return True
            
        except Exception as e:
            print(f"❌ ERRO ao criar tabelas: {str(e)}")
            print(f"   Tipo: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("CRIAR TABELAS DE EVENTOS")
    print("=" * 60)
    
    sucesso = criar_tabelas()
    
    if sucesso:
        print("\n" + "=" * 60)
        print("✅ Operação concluída com sucesso!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Operação falhou!")
        print("=" * 60)
        sys.exit(1)
