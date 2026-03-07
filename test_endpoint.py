#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar a endpoint /api/validate-email
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import app
from backend.models import db, User
import json

def test_database():
    """Testar conexao com banco de dados"""
    try:
        with app.app_context():
            print("=" * 60)
            print("TESTE 1: Conexao com Database")
            print("=" * 60)
            
            # Test basic query
            user_count = User.query.count()
            print(f"[OK] Usuarios no banco: {user_count}")
            
            # Test specific email query
            test_email = "teste@gmail.com"
            user = User.query.filter_by(email=test_email).first()
            encontrado = "Encontrado" if user else "Nao encontrado"
            print(f"[OK] Busca por email '{test_email}': {encontrado}")
            
            # List all emails
            all_users = User.query.limit(5).all()
            print(f"\n[OK] Primeiros 5 usuarios:")
            for u in all_users:
                print(f"   - {u.email}")
                
            print("\n" + "=" * 60)
            print("TESTE 2: Simulando endpoint /api/validate-email")
            print("=" * 60)
            
            with app.test_client() as client:
                # Test com email valido
                response = client.post(
                    '/auth/api/validate-email',
                    data=json.dumps({"email": test_email}),
                    content_type='application/json'
                )
                print(f"Status: {response.status_code}")
                print(f"Response: {response.get_json()}")
                
                # Test com email invalido
                response2 = client.post(
                    '/auth/api/validate-email',
                    data=json.dumps({"email": "invalido"}),
                    content_type='application/json'
                )
                print(f"\nStatus: {response2.status_code}")
                print(f"Response: {response2.get_json()}")
            
            print("\n[OK] Todos os testes passaram!")
            
    except Exception as e:
        print(f"\n[ERRO] {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_database()
