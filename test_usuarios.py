#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para diagnosticar dados de usuarios no banco de dados
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import app
from backend.models import db, User

def test_users():
    """Testar dados de usuarios"""
    try:
        with app.app_context():
            print("=" * 70)
            print("DIAGNOSTICO DE USUARIOS NO BANCO DE DADOS")
            print("=" * 70)
            
            # Teste 1: Contagem
            total = User.query.count()
            print(f"\n[1] Total de usuarios: {total}")
            
            if total == 0:
                print("    [ERRO] Nenhum usuario no banco!")
                return
            
            # Teste 2: Listar todos com detalhes
            print(f"\n[2] Detalhes de cada usuario:")
            users = User.query.all()
            for i, user in enumerate(users, 1):
                print(f"\n    Usuario #{i}:")
                print(f"      ID: {user.id}")
                print(f"      Username: {user.username}")
                print(f"      Nome: {user.nome}")
                print(f"      Email: {user.email}")
                print(f"      Status: {user.status}")
            
            # Teste 3: Teste de query com email
            print(f"\n[3] Teste de query com filtro de email:")
            if users:
                test_email = users[0].email
                print(f"    Procurando usuario com email: {test_email}")
                result = User.query.filter_by(email=test_email).first()
                if result:
                    print(f"    [OK] Encontrado: {result.username}")
                else:
                    print(f"    [ERRO] Nao encontrado!")
            
            # Teste 4: Teste com email lowercase
            print(f"\n[4] Teste de query com email lowercase:")
            if users:
                test_email_lower = users[0].email.lower()
                print(f"    Procurando usuario com email: {test_email_lower}")
                result = User.query.filter_by(email=test_email_lower).first()
                if result:
                    print(f"    [OK] Encontrado: {result.username}")
                else:
                    print(f"    [ERRO] Nao encontrado com lowercase!")
                    
                    # Comparar valores
                    print(f"    [DEBUG] Comparacao de emails:")
                    print(f"      Email original: {repr(users[0].email)} (tipo: {type(users[0].email)})")
                    print(f"      Email lowercase: {repr(test_email_lower)} (tipo: {type(test_email_lower)})")
                    print(f"      Iguais? {users[0].email.lower() == test_email_lower}")
            
            # Teste 5: Teste com email inexistente
            print(f"\n[5] Teste com email inexistente:")
            fake_email = "naoexiste@example.com"
            result = User.query.filter_by(email=fake_email).first()
            print(f"    Procurando: {fake_email}")
            print(f"    Resultado: {result} (esperado: None)")
            
            print("\n" + "=" * 70)
            print("[OK] Diagnostico completo!")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n[ERRO] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_users()
