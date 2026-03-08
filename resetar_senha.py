#!/usr/bin/env python
"""Script para resetar senha do usuário admin"""

import sys
sys.path.insert(0, '.')

from app import app, db
from backend.models import User

def resetar_senha_admin():
    """Reseta senha do admin para admin123"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("❌ Usuário 'admin' não encontrado!")
            return
        
        user.set_password('admin123')
        db.session.commit()
        
        print("✅ Senha resetada com sucesso!")
        print("📧 Username: admin")
        print("🔑 Senha: admin123")

if __name__ == '__main__':
    resetar_senha_admin()
