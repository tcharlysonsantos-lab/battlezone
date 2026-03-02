#!/usr/bin/env python
# Quick test to verify all imports work

try:
    from app import app
    print("✅ App imported successfully")
    print(f"✅ Template folder: {app.template_folder}")
    print(f"✅ Static folder: {app.static_folder}")
    
    # Test backend imports
    from backend.models import db, User, Operador
    print("✅ Backend.models imported successfully")
    
    from backend.auth import auth_bp
    print("✅ Backend.auth imported successfully")
    
    from backend.forms import OperadorForm
    print("✅ Backend.forms imported successfully")
    
    from backend.utils import get_valores_plano
    print("✅ Backend.utils imported successfully")
    
    print("\n🎉 ALL IMPORTS WORKING CORRECTLY!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
