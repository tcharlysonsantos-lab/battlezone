#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste detalhado da endpoint AJAX de validacao de email
"""
import json

from app import app
from backend.models import db, User

def test_ajax_endpoint():
    """Testar endpoint AJAX de validacao"""
    try:
        with app.app_context():
            print("=" * 70)
            print("TESTE DE AJAX ENDPOINT - VALIDAO DE EMAIL")
            print("=" * 70)
            
            # 1. Ver todos os usuarios
            all_users = User.query.all()
            print(f"\n[1] Total de usuarios no banco: {len(all_users)}")
            
            if not all_users:
                print("    [ERRO] Nenhum usuario!")
                return
            
            for user in all_users:
                print(f"    - {user.email} (status: {user.status})")
            
            # 2. Testar com test client
            print(f"\n[2] Testando AJAX endpoint com test client:")
            
            with app.test_client() as client:
                # Teste 1: Email valido que existe
                test_email = all_users[0].email
                print(f"\n    Teste A: Email que existe no banco: {test_email}")
                
                response = client.post(
                    '/auth/api/validate-email',
                    data=json.dumps({"email": test_email}),
                    content_type='application/json'
                )
                
                print(f"    Status: {response.status_code}")
                data = response.get_json()
                print(f"    Response: {json.dumps(data, indent=6)}")
                
                if response.status_code == 200:
                    if data.get('exists'):
                        print(f"    [OK] Email encontrado!")
                    else:
                        print(f"    [ERRO] Email nao encontrado!")
                        print(f"    Debug total_users: {data.get('debug_total_users')}")
                else:
                    print(f"    [ERRO] Status code: {response.status_code}")
                
                # Teste 2: Email com lowercase
                print(f"\n    Teste B: Email em LOWERCASE:")
                test_email_lower = test_email.lower()
                print(f"    Email original: {test_email}")
                print(f"    Email lowercase: {test_email_lower}")
                
                response = client.post(
                    '/auth/api/validate-email',
                    data=json.dumps({"email": test_email_lower}),
                    content_type='application/json'
                )
                
                print(f"    Status: {response.status_code}")
                data = response.get_json()
                print(f"    Response: {json.dumps(data, indent=6)}")
                
                # Teste 3: Email que nao existe
                print(f"\n    Teste C: Email que NAO existe:")
                fake_email = "naoexiste@example.com"
                
                response = client.post(
                    '/auth/api/validate-email',
                    data=json.dumps({"email": fake_email}),
                    content_type='application/json'
                )
                
                print(f"    Email: {fake_email}")
                print(f"    Status: {response.status_code}")
                data = response.get_json()
                print(f"    Response: {json.dumps(data, indent=6)}")
                
                # Teste 4: Debug endpoint
                print(f"\n    Teste D: Debug endpoint /api/debug/usuarios:")
                response = client.get('/auth/api/debug/usuarios')
                print(f"    Status: {response.status_code}")
                data = response.get_json()
                print(f"    Response: {json.dumps(data, indent=6)}")
            
            print("\n" + "=" * 70)
            print("[OK] Testes completos!")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n[ERRO] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ajax_endpoint()
