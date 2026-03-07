#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de case-insensitive email search
"""
import json
from app import app
from backend.models import db, User

def test_case_insensitive():
    """Testar busca case-insensitive de email"""
    try:
        with app.app_context():
            print("=" * 70)
            print("TESTE DE CASE-INSENSITIVE EMAIL SEARCH")
            print("=" * 70)
            
            # Pegar um usuario existente
            users = User.query.limit(3).all()
            if not users:
                print("Nenhum usuario no banco!")
                return
            
            with app.test_client() as client:
                for test_user in users:
                    original_email = test_user.email
                    
                    # Teste com original
                    print(f"\n[Teste] Email original: {original_email}")
                    response = client.post(
                        '/auth/api/validate-email',
                        data=json.dumps({"email": original_email}),
                        content_type='application/json'
                    )
                    result = response.get_json()
                    print(f"  Resultado: {'ENCONTRADO' if result.get('exists') else 'NAO ENCONTRADO'}")
                    
                    # Teste com MAIUSCULA
                    upper_email = original_email.upper()
                    print(f"\n[Teste] Email em MAIUSCULA: {upper_email}")
                    response = client.post(
                        '/auth/api/validate-email',
                        data=json.dumps({"email": upper_email}),
                        content_type='application/json'
                    )
                    result = response.get_json()
                    print(f"  Resultado: {'ENCONTRADO' if result.get('exists') else 'NAO ENCONTRADO'}")
                    
                    # Teste com MISTO
                    mixed_email = original_email[0].upper() + original_email[1:].lower()
                    print(f"\n[Teste] Email MiStO: {mixed_email}")
                    response = client.post(
                        '/auth/api/validate-email',
                        data=json.dumps({"email": mixed_email}),
                        content_type='application/json'
                    )
                    result = response.get_json()
                    print(f"  Resultado: {'ENCONTRADO' if result.get('exists') else 'NAO ENCONTRADO'}")
                    
                    print("\n" + "-" * 70)
            
            print("\n" + "=" * 70)
            print("[OK] Testes completos!")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n[ERRO] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_case_insensitive()
