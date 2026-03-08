#!/usr/bin/env python
"""Script para criar usuário de teste no banco local"""

import sys
sys.path.insert(0, '.')

from app import app, db
from backend.models import User

def criar_usuario_teste():
    """Cria usuário admin para testes"""
    with app.app_context():
        # Verificar se usuário já existe
        user = User.query.filter_by(username='admin').first()
        if user:
            print("❌ Usuário 'admin' já existe!")
            return
        
        # Criar usuário admin
        novo_user = User(
            username='admin',
            email='admin@test.com',
            nome='Administrador',
            nivel='admin',
            status='aprovado',
            termo_aceito=True
        )
        novo_user.set_password('admin123')
        
        db.session.add(novo_user)
        db.session.commit()
        
        print("✅ Usuário criado com sucesso!")
        print("📧 Username: admin")
        print("🔑 Senha: admin123")
        print("\nAcesse o localhost e faça login!")

if __name__ == '__main__':
    criar_usuario_teste()
