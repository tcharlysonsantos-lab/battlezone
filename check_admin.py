#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar usuário admin e testar senha"""

from app import app, db
from models import User
from werkzeug.security import check_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print('✅ Usuário admin encontrado')
        print(f'   Username: {admin.username}')
        print(f'   Email: {admin.email}')
        print(f'   Password hash: {admin.password_hash[:50]}...')
        print(f'   ID: {admin.id}')
        
        # Testar a senha fornecida
        test_password = 'F6yTVRPZC0KPhh3r'
        is_correct = check_password_hash(admin.password_hash, test_password)
        
        print(f'\n🔐 Testando senha: {test_password}')
        if is_correct:
            print(f'   ✅ Senha CORRETA - Login deveria funcionar')
        else:
            print(f'   ❌ Senha INCORRETA')
            print(f'   A senha fornecida não corresponde ao hash armazenado')
            print(f'\n💡 Possível solução:')
            print(f'   Sua senha inicial pode ter sido diferente')
            print(f'   Vou gerar uma nova senha para o admin:')
            
            from werkzeug.security import generate_password_hash
            new_password = 'F6yTVRPZC0KPhh3r'
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print(f'   ✅ Senha atualizada com sucesso')
            print(f'   Nova senha: {new_password}')
    else:
        print('❌ Usuário admin NÃO encontrado')
        print('\n📝 Listando todos os usuários no banco:')
        users = User.query.all()
        if users:
            for u in users:
                print(f'   - {u.username} ({u.email})')
        else:
            print('   (Nenhum usuário encontrado)')
