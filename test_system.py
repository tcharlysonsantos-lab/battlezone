#!/usr/bin/env python
"""Test script to find errors"""

import sys
import traceback

sys.path.insert(0, '.')

try:
    print("[1/3] Testando import de app...")
    from app import app
    print("✅ app importado")
    
    print("\n[2/3] Testando app context...")
    with app.app_context():
        print("✅ app context OK")
        
        print("\n[3/3] Testando database...")
        from backend.models import db, User
        db.create_all()
        print("✅ database OK")
        
    print("\n🎉 TUDO OK - Sistema pronto!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    print("\nStack trace:")
    traceback.print_exc()
    sys.exit(1)
