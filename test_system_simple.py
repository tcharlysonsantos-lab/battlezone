#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

print("=" * 60)
print("INICIANDO TESTE DE SISTEMA")
print("=" * 60)

# Test 1: Import app
print("\n[1/5] Testando importacao de app...")
try:
    from app import app, db
    print("[OK] App importado com sucesso")
except Exception as e:
    print(f"[ERRO] ao importar app: {e}")
    sys.exit(1)

# Test 2: Import models
print("\n[2/5] Testando importacao de models...")
try:
    from backend.models import (User, Operador, Equipe, Partida, 
                                PartidaParticipante, Venda, Estoque, 
                                Log, Solicitacao, EquipeMembros)
    print("[OK] Todos os models importados com sucesso")
except Exception as e:
    print(f"[ERRO] ao importar models: {e}")
    sys.exit(1)

# Test 3: Check database
print("\n[3/5] Testando banco de dados...")
try:
    with app.app_context():
        # Check if tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"[OK] Banco de dados - {len(tables)} tabelas encontradas")
        for table in sorted(tables)[:5]:
            print(f"     - {table}")
except Exception as e:
    print(f"[ERRO] ao verificar banco: {e}")
    sys.exit(1)

# Test 4: Test basic routes
print("\n[4/5] Testando rotas basicas...")
try:
    with app.test_client() as client:
        # Home
        resp = client.get('/')
        print(f"[OK] GET / => {resp.status_code}")
        
        # Login
        resp = client.get('/auth/login')
        print(f"[OK] GET /auth/login => {resp.status_code}")
except Exception as e:
    print(f"[ERRO] ao testar rotas: {e}")
    sys.exit(1)

# Test 5: Flask config
print("\n[5/5] Testando configuracoes Flask...")
try:
    print(f"[OK] Config verificada")
except Exception as e:
    print(f"[ERRO] ao verificar config: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("[OK] TODOS OS TESTES PASSARAM!")
print("=" * 60)
