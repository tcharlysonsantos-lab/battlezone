#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script para verificar se email está sendo enviado corretamente
"""
import os
import sys
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from backend.models import User
from backend.email_service import enviar_link_recuperacao

def test_email_send():
    """Testa envio de email de recuperação de senha"""
    
    app = create_app()
    
    with app.app_context():
        print("[INFO] Criando app Flask com contexto...")
        
        # Verificar configuração de email
        print(f"\n[INFO] Configuração de Email:")
        print(f"  MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"  MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"  MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"  MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        print(f"  MAIL_PASSWORD: {'*' * len(app.config.get('MAIL_PASSWORD', '')) if app.config.get('MAIL_PASSWORD') else 'NÃO CONFIGURADO'}")
        
        # Buscar usuário
        print(f"\n[INFO] Buscando usuário tcharlysonf.f@gmail.com...")
        user = User.query.filter(User.email.ilike('tcharlysonf.f@gmail.com')).first()
        
        if not user:
            print("[ERROR] Usuário não encontrado!")
            return False
        
        print(f"[OK] Usuário encontrado: {user.email}")
        
        # Tentar enviar email
        print(f"\n[INFO] Tentando enviar email de recuperação...")
        try:
            resultado = enviar_link_recuperacao(user)
            print(f"[OK] Email enviado! Resultado: {resultado}")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao enviar email:")
            print(f"  Tipo: {type(e).__name__}")
            print(f"  Mensagem: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_email_send()
    sys.exit(0 if success else 1)
