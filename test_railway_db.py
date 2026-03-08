#!/usr/bin/env python
# test_railway_db.py - Script para testar a inicialização do banco Railway
"""
Testing script to verify if Railway PostgreSQL has all required tables.
Run locally to simulate what will happen on Railway during startup.
"""

import os
import sys
from datetime import datetime

print("=" * 80)
print("[TEST] Railway Database Initialization Verification")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Test 1: Import Flask app
print("\n[1] Testing Flask app import...")
try:
    from app import app, db
    print("    ✓ Flask app imported successfully")
except Exception as e:
    print(f"    ✗ Failed to import Flask app: {e}")
    sys.exit(1)

# Test 2: Import init_database function
print("\n[2] Testing init_database import...")
try:
    from backend.init_db import init_database
    print("    ✓ init_database function imported")
except Exception as e:
    print(f"    ✗ Failed to import init_database: {e}")
    sys.exit(1)

# Test 3: Import all models to register them
print("\n[3] Registering all SQLAlchemy models...")
try:
    from backend.models import (
        db, User, Operador, Equipe, Partida, PartidaParticipante,
        Venda, Estoque, Log, Solicitacao, PagamentoOperador,
        Evento, Sorteio, Battlepass
    )
    print("    ✓ All 13 models registered successfully")
except Exception as e:
    print(f"    ✗ Failed to import models: {e}")
    sys.exit(1)

# Test 4: Run database initialization
print("\n[4] Running database initialization...")
try:
    init_database(app)
    print("    ✓ Database initialization completed")
except Exception as e:
    print(f"    ✗ Database initialization failed: {e}")
    sys.exit(1)

# Test 5: Verify tables exist
print("\n[5] Verifying required tables...")
try:
    with app.app_context():
        inspector = db.inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        
        required_tables = {
            'user', 'operador', 'equipe', 'partida',
            'partida_participante', 'venda', 'estoque', 'log',
            'solicitacao', 'pagamento_operador', 'evento', 'sorteio', 'battlepass'
        }
        
        missing = required_tables - existing_tables
        
        print(f"    Total tables in database: {len(existing_tables)}")
        print(f"    Required tables: {len(required_tables)}")
        
        if missing:
            print(f"    ✗ Missing tables: {missing}")
            sys.exit(1)
        else:
            print(f"    ✓ All required tables present!")
            
except Exception as e:
    print(f"    ✗ Failed to verify tables: {e}")
    sys.exit(1)

# Test 6: Check admin user
print("\n[6] Checking for admin user...")
try:
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"    ✓ Admin user exists (ID: {admin.id})")
        else:
            print(f"    ℹ Admin user not found (will be created on first run)")
except Exception as e:
    print(f"    ⚠ Could not check admin user: {e}")

# Test 7: Database type detection
print("\n[7] Database type detection...")
try:
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
    if 'postgresql' in db_url or 'postgres' in db_url:
        db_type = "PostgreSQL (Railway)"
    elif 'sqlite' in db_url:
        db_type = "SQLite (Local)"
    else:
        db_type = "Unknown"
    
    print(f"    Database: {db_type}")
    print(f"    URL: {db_url[:50]}..." if len(db_url) > 50 else f"    URL: {db_url}")
except Exception as e:
    print(f"    ⚠ Could not detect database type: {e}")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - Database is ready for Railway deployment!")
print("=" * 80)
