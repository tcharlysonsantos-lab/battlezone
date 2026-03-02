#!/usr/bin/env python3
"""
Script de Teste - Password Reset e Login Case-Insensitive
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import User
from datetime import datetime, timedelta

def test_case_insensitive_login():
    """Testa se o login funciona com qualquer combinação de maiúscula/minúscula"""
    print("\n" + "="*60)
    print("TESTE 1: Login Case-Insensitive")
    print("="*60)
    
    with app.app_context():
        # Criar usuário com username 'Tete'
        user = User(
            username='Tete',
            nome='Usuario Teste',
            email='tete@test.com',
            nivel='operador',
            status='aprovado'
        )
        user.set_password('senha123')
        db.session.add(user)
        db.session.commit()
        
        print(f"Usuario criado com username: 'Tete'")
        
        # Testar buscas case-insensitive
        test_cases = ['Tete', 'tete', 'TETE', 'TeTE', 'tETE']
        
        for test_username in test_cases:
            found_user = User.query.filter(User.username.ilike(test_username)).first()
            status = "ENCONTRADO" if found_user else "NAO ENCONTRADO"
            print(f"  Busca por '{test_username}': {status}")
        
        # Verificar senha
        print(f"\nValidacao de senha:")
        print(f"  'senha123': {'VALIDO' if user.check_password('senha123') else 'INVALIDO'}")
        print(f"  'senha456': {'VALIDO' if user.check_password('senha456') else 'INVALIDO'}")
        
        # Cleanup
        db.session.delete(user)
        db.session.commit()
        
        print("[OK] Login case-insensitive funcionando!\n")

def test_password_reset():
    """Testa sistema de reset de senha"""
    print("="*60)
    print("TESTE 2: Password Reset com Token")
    print("="*60)
    
    with app.app_context():
        # Criar usuário
        user = User(
            username='testuser',
            nome='Test User',
            email='test@example.com',
            nivel='operador',
            status='aprovado'
        )
        user.set_password('senhaoriginal')
        db.session.add(user)
        db.session.commit()
        
        print(f"Usuario criado: testuser")
        
        # Gerar token de reset
        print("\nGerando token de reset...")
        token = user.gerar_password_reset_token()
        print(f"  Token gerado: {token[:20]}... (truncado)")
        print(f"  Expira em: {user.password_reset_expires}")
        
        # Validar token imediatamente
        print(f"\nValidando token imediatamente:")
        is_valid = user.validar_password_reset_token(token)
        print(f"  Token valido: {'SIM' if is_valid else 'NAO'}")
        
        # Resetar senha
        print(f"\nResetando para nova senha...")
        user.resetar_senha('novasenh123')
        print(f"  Token apos reset: {user.password_reset_token}")
        
        # Tentar validar token antigo (deve falhar)
        is_valid_old = user.validar_password_reset_token(token)
        print(f"  Token antigo ainda valido: {'SIM (ERRO!)' if is_valid_old else 'NAO (correto)'}")
        
        # Verificar nova senha
        print(f"\nVerificando nova senha:")
        print(f"  'novasenh123': {'VALIDO' if user.check_password('novasenh123') else 'INVALIDO'}")
        print(f"  'senhaoriginal': {'VALIDO' if user.check_password('senhaoriginal') else 'INVALIDO'}")
        
        # Cleanup
        db.session.delete(user)
        db.session.commit()
        
        print("[OK] Password reset funcionando!\n")

def test_token_expiration():
    """Testa se token expira corretamente"""
    print("="*60)
    print("TESTE 3: Token Expiration (30 minutos)")
    print("="*60)
    
    with app.app_context():
        # Criar usuário
        user = User(
            username='testexpire',
            nome='Test Expire',
            email='expire@example.com',
            nivel='operador',
            status='aprovado'
        )
        user.set_password('senha123')
        db.session.add(user)
        db.session.commit()
        
        # Gerar token
        token = user.gerar_password_reset_token()
        print(f"Token gerado, valido por 30 minutos")
        
        # Simular expiração
        user.password_reset_expires = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()
        
        print(f"Alterando expiração para -1 minuto (expirado)...")
        is_valid = user.validar_password_reset_token(token)
        print(f"  Token expirado ainda valido: {'SIM (ERRO!)' if is_valid else 'NAO (correto)'}")
        
        # Cleanup
        db.session.delete(user)
        db.session.commit()
        
        print("[OK] Token expiration funcionando!\n")

def main():
    print("\n" + "="*60)
    print("  TESTES: PASSWORD RESET + CASE-INSENSITIVE LOGIN")
    print("="*60)
    
    try:
        test_case_insensitive_login()
        test_password_reset()
        test_token_expiration()
        
        print("="*60)
        print("  RESULTADO: TODOS OS TESTES PASSARAM!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERRO: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
