# reset_admin_password.py - RESETAR SENHA DO ADMIN

import os
import sys
import secrets
import json
from datetime import datetime

# Validar se seguranca.env existe
if not os.path.exists('seguranca.env'):
    print("❌ Arquivo seguranca.env não encontrado!")
    sys.exit(1)

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reseta a senha do admin e salva em ADMIN_CREDENTIALS.json"""
    
    with app.app_context():
        # Buscar admin
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("❌ Admin não encontrado no banco de dados!")
            sys.exit(1)
        
        # Gerar nova senha
        nova_senha = secrets.token_urlsafe(12)
        
        # Atualizar hash
        admin.set_password(nova_senha)
        db.session.commit()
        
        # Salvar credenciais
        credenciais = {
            'usuario': 'admin',
            'senha_inicial': nova_senha,
            'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'alerta': '⚠️ IMPORTANTE: Trocar essa senha IMEDIATAMENTE após primeiro login!'
        }
        
        file_credenciais = 'ADMIN_CREDENTIALS.json'
        with open(file_credenciais, 'w', encoding='utf-8') as f:
            json.dump(credenciais, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*60)
        print("🔐 SENHA DO ADMIN RESETADA COM SUCESSO!")
        print("="*60)
        print(f"Usuário: {credenciais['usuario']}")
        print(f"Senha:   {credenciais['senha_inicial']}")
        print(f"\nArquivo '{file_credenciais}' criado")
        print("\n⚠️  IMPORTANTE:")
        print("   1. Salve essa senha em local seguro")
        print("   2. Mude para uma senha forte após login")
        print("   3. Delete ADMIN_CREDENTIALS.json depois de logar")
        print("="*60)

if __name__ == '__main__':
    reset_admin_password()
