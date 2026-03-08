#!/usr/bin/env python
# deployment.py - Script para garantir que tudo está pronto para deploy
import os
import sys
from datetime import datetime

print("=" * 70)
print("[DEPLOY] Script de Pré-Deploy - Verificação Completo do Sistema")
print(f"[DEPLOY] Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 70)

# ===== 1. VERIFICAR VARIÁVEIS DE AMBIENTE =====
print("\n[1] Verificando variáveis de ambiente...")
env_vars = [
    'SECRET_KEY',
    'FLASK_ENV',
    'DATABASE_URL'
]

missing_vars = []
for var in env_vars:
    value = os.getenv(var)
    status = "✓" if value else "✗"
    print(f"    {status} {var}: {'Configurado' if value else 'NÃO CONFIGURADO'}")
    if not value:
        missing_vars.append(var)

if missing_vars:
    print(f"\n    ⚠️  FALTAM: {', '.join(missing_vars)}")

# ===== 2. VERIFICAR ARQUIVOS CRÍTICOS =====
print("\n[2] Verificando arquivos críticos...")
critical_files = [
    'app.py',
    'run.py',
    'requirements.txt',
    'backend/models.py',
    'backend/init_db.py',
    'config.py'
]

for file in critical_files:
    exists = os.path.isfile(file)
    status = "✓" if exists else "✗"
    print(f"    {status} {file}")

# ===== 3. INICIALIZAR BANCO DE DADOS =====
print("\n[3] Inicializando banco de dados...")
try:
    from app import app
    from backend.init_db import init_database
    
    init_database(app)
    print("    ✓ Banco de dados inicializado com sucesso")
except Exception as e:
    print(f"    ✗ Erro ao inicializar banco: {e}")
    sys.exit(1)

# ===== 4. VERIFICAR IMPORTS =====
print("\n[4] Verificando importações críticas...")
try:
    from backend.models import db, User, Operador, Equipe, Evento, Sorteio, Battlepass
    print("    ✓ Models importados com sucesso")
except Exception as e:
    print(f"    ✗ Erro ao importar models: {e}")
    sys.exit(1)

# ===== 5. CRIAR ESTRUTURA DE PASTAS =====
print("\n[5] Criando estrutura de pastas...")
folders = ['logs', 'instance', 'backups', 'backups_local']
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"    ✓ Criada pasta: {folder}")
    else:
        print(f"    ✓ Pasta existe: {folder}")

print("\n" + "=" * 70)
print("[DEPLOY] ✅ Sistema pronto para deploy!")
print("=" * 70)
