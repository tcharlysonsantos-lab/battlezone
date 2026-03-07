#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test SMTP connection com a App Password
"""
import os
import sys
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from backend.email_service import mail, enviar_email
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_smtp_connection():
    """Testa conexão SMTP com a App Password"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("TEST: Conexão SMTP com App Password")
        print("="*80)
        
        # Verificar configuração
        config = {
            'MAIL_SERVER': app.config.get('MAIL_SERVER'),
            'MAIL_PORT': app.config.get('MAIL_PORT'),
            'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
            'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
            'MAIL_PASSWORD': '***HIDDEN***' if app.config.get('MAIL_PASSWORD') else 'NÃO CONFIGURADO'
        }
        
        print("\n[INFO] Configuração de Email:")
        for key, val in config.items():
            print(f"  {key}: {val}")
        
        # Verificar se mail está inicializado
        if not mail:
            print("\n[ERROR] Flask-Mail não inicializado!")
            return False
        
        print(f"\n[INFO] Flask-Mail inicializado: {mail}")
        
        # Tentar enviar email de teste
        print("\n[INFO] Enviando email de teste...")
        
        try:
            resultado = enviar_email(
                ['tcharlysonf.f@gmail.com'],
                'Teste SMTP - BattleZone',
                '<h1>Teste</h1><p>Se você recebeu este email, o SMTP está funcionando!</p>',
                remetente=app.config.get('MAIL_USERNAME')
            )
            
            print(f"[OK] Email agendado para envio (async): {resultado}")
            
            # Aguardar thread enviar
            import time
            print("\n[INFO] Aguardando 5 segundos para thread enviar (aumentado)...")
            time.sleep(5)
            
            print("[OK] Email deveria ter sido enviado")
            
            print("\n" + "="*80)
            print("RESULTADO: Teste completado")
            print("Verifique sua caixa de entrada (ou spam) por um email de teste")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Erro ao enviar email: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_smtp_connection()
    sys.exit(0 if success else 1)
