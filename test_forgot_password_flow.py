#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script para validar o fluxo completo de esqueci senha
"""
import os
import sys
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from backend.models import User
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
logger = logging.getLogger(__name__)

def test_forgot_password_flow():
    """Testa o fluxo completo de forgot password"""
    
    with app.app_context():
        with app.test_request_context():
            print("\n" + "="*80)
            print("TEST: Fluxo Completo de Esqueci Senha")
            print("="*80)
            
            # 1. Buscar usuário
            print("\n[1] Buscando usuário...")
            email = 'tcharlysonf.f@gmail.com'
            user = User.query.filter(User.email.ilike(email)).first()
            
            if not user:
                print(f"[ERROR] Usuário não encontrado: {email}")
                return False
            
            print(f"[OK] Usuário encontrado: {user.email}")
            
            # 2. Gerar token de reset
            print("\n[2] Gerando token de reset...")
            try:
                token = user.gerar_password_reset_token()
                print(f"[OK] Token gerado: {token[:20]}...")
                print(f"    user.password_reset_token: {user.password_reset_token[:20]}...")
                print(f"    user.password_reset_expires: {user.password_reset_expires}")
            except Exception as e:
                print(f"[ERROR] Erro ao gerar token: {e}")
                return False
            
            # 3. Criar reset link
            print("\n[3] Criando reset link...")
            try:
                from flask import url_for
                reset_link = url_for('auth.reset_password', token=token, _external=True)
                print(f"[OK] Reset link: {reset_link}")
            except Exception as e:
                print(f"[ERROR] Erro ao criar link: {e}")
                return False
            
            # 4. Enviar email (assincronamente)
            print("\n[4] Enviando email (ASSINCRONAMENTE)...")
            print("   Isso deve retornar RAPIDAMENTE (em menos de 1s)")
            
            import time
            start = time.time()
            
            try:
                from backend.email_service import enviar_email_reset_senha
                resultado = enviar_email_reset_senha(user.email, user.nome, reset_link)
                elapsed = time.time() - start
                
                print(f"[OK] Email function retornou em {elapsed:.2f}s")
                print(f"    Resultado: {resultado}")
                
                if elapsed > 5:
                    print(f"[WARNING] DEMOROU {elapsed:.1f}s - PODE ESTAR SÍNCRONO!")
                    return False
                else:
                    print(f"[OK] Tempo aceitável")
                    
            except Exception as e:
                elapsed = time.time() - start
                print(f"[ERROR] Erro ao enviar email (após {elapsed:.2f}s): {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # 5. Aguardar thread de email
            print("\n[5] Aguardando 2 segundos para thread enviar email...")
            import time
            time.sleep(2)
            print("[OK] Thread deveria ter enviado o email em background")
            
            print("\n" + "="*80)
            print("RESULTADO: TESTE PASSOU")
            print("="*80)
            return True

if __name__ == '__main__':
    success = test_forgot_password_flow()
    sys.exit(0 if success else 1)
