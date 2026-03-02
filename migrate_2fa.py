#!/usr/bin/env python3
"""
Script para migrar a base de dados - Adicionar colunas 2FA
Executar ANTES de iniciar o servidor!
"""

import os
import sqlite3
from pathlib import Path

def migrate_database():
    """Migra o banco de dados adicionando colunas 2FA ao User se necessário"""
    
    # Determinar caminho do banco
    db_path = Path(__file__).parent / 'instance' / 'database.db'
    
    if not db_path.exists():
        print("❌ Banco de dados não existe. Execute run.py primeiro para criar.")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(user)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Colunas 2FA a adicionar
        required_columns = {
            'two_factor_enabled',
            'two_factor_secret',
            'backup_codes',
            'two_factor_verified_at'
        }
        
        missing_columns = required_columns - columns
        
        if not missing_columns:
            print("✅ Banco de dados já tem todas as colunas 2FA")
            conn.close()
            return True
        
        print(f"➕ Adicionando colunas faltantes: {missing_columns}")
        
        # Adicionar cada coluna
        if 'two_factor_enabled' in missing_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0")
            print("   ✅ Adicionada: two_factor_enabled")
        
        if 'two_factor_secret' in missing_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN two_factor_secret VARCHAR(32)")
            print("   ✅ Adicionada: two_factor_secret")
        
        if 'backup_codes' in missing_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN backup_codes TEXT")
            print("   ✅ Adicionada: backup_codes")
        
        if 'two_factor_verified_at' in missing_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN two_factor_verified_at DATETIME")
            print("   ✅ Adicionada: two_factor_verified_at")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        return False

def recreate_database():
    """Opção de recriar o banco do zero (limpa dados!)"""
    db_path = Path(__file__).parent / 'instance' / 'database.db'
    
    if db_path.exists():
        print(f"⚠️  Deletando banco antigo: {db_path}")
        db_path.unlink()
        print("✅ Banco deletado!")
    
    print("✅ O banco será recriado ao iniciar a aplicação")

if __name__ == '__main__':
    print("=" * 60)
    print("BattleZone Database Migration - 2FA Support")
    print("=" * 60 + "\n")
    
    print("Tentando adicionar colunas 2FA ao banco existente...\n")
    success = migrate_database()
    
    if not success:
        print("\n⚠️  Falha na migração. Opções:")
        print("  1. Se é desenvolvimento: deletar e recriar o banco")
        print("  2. Se é produção: contactar administrador")
        
        response = input("\nDeseja recriar o banco? (S/N): ").strip().lower()
        if response == 's':
            recreate_database()
    
    print("\n" + "=" * 60)
