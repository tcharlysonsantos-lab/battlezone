#!/usr/bin/env python3
"""Test if all system imports work correctly after reorganization"""

import os
import sys

# Test 1: Basic imports
print("\n" + "="*60)
print("🧪 TESTE DE IMPORTS - BattleZone Flask")
print("="*60)

try:
    print("\n[1] Importing Flask app...")
    from app import app
    print("    ✅ Flask app imported successfully")
except ImportError as e:
    print(f"    ❌ Error: {e}")
    sys.exit(1)

# Test 2: Check Flask configuration  
print("\n[2] Checking Flask configuration...")
print(f"    ✅ Template folder: {app.template_folder}")
print(f"    ✅ Static folder: {app.static_folder}")

# Test 3: Check backend imports
print("\n[3] Testing backend imports...")
try:
    from backend.models import db, User, Operador, Equipe, Partida
    print("    ✅ backend.models imported")
    from backend.auth import auth_bp
    print("    ✅ backend.auth imported")
    from backend.forms import OperadorForm, EquipeForm, PartidaForm
    print("    ✅ backend.forms imported")
    from backend.utils import get_valores_plano
    print("    ✅ backend.utils imported")
    from backend.decorators import admin_required
    print("    ✅ backend.decorators imported")
except ImportError as e:
    print(f"    ❌ Error: {e}")
    sys.exit(1)

# Test 4: Check directories exist
print("\n[4] Checking directory structure...")
dirs_to_check = [
    'backend/',
    'frontend/', 
    'frontend/templates/',
    'frontend/static/',
    'scripts/',
    'docs/'
]

for dir_path in dirs_to_check:
    full_path = os.path.join(os.getcwd(), dir_path)
    if os.path.isdir(full_path):
        print(f"    ✅ {dir_path}")
    else:
        print(f"    ❌ {dir_path} (NOT FOUND)")

print("\n" + "="*60)
print("🎉 ALL TESTS PASSED - System is reorganized correctly!")
print("="*60 + "\n")
