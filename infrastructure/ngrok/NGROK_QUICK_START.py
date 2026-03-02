#!/usr/bin/env python3
"""
NGROK_QUICK_START.py - Iniciar rápido com guia
"""

import os
import sys
from pathlib import Path

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                   🚀 NGROK QUICK START GUIDE                     ║
║               BattleZone Flask - Exposição Segura                 ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

def check_step(description, condition):
    status = "✅ FEITO" if condition else "❌ PENDENTE"
    print(f"  {status:12} {description}")
    return condition

def main():
    print_banner()
    
    print("\n📋 VERIFICANDO PROGRESSO:\n")
    
    steps = [
        ("setup_ngrok.py executado", Path("setup_ngrok.py").exists()),
        (".env.ngrok criado", Path(".env.ngrok").exists()),
        (".ngrok/config.json criado", Path(".ngrok/config.json").exists()),
        ("logs/ diretório criado", Path("logs").exists()),
        ("start_with_ngrok.py criado", Path("start_with_ngrok.py").exists()),
        ("ngrok_security.py criado", Path("ngrok_security.py").exists()),
        ("test_ngrok_security.py criado", Path("test_ngrok_security.py").exists()),
        ("NGROK_SETUP.md criado", Path("NGROK_SETUP.md").exists()),
        ("NGROK_INTEGRATION.md criado", Path("NGROK_INTEGRATION.md").exists()),
        ("NGROK_CHECKLIST.md criado", Path("NGROK_CHECKLIST.md").exists()),
    ]
    
    completed = sum(check_step(desc, cond) for desc, cond in steps)
    total = len(steps)
    
    print(f"\n  Status: {completed}/{total} completo\n")
    
    # Verificar NGROK_AUTH_TOKEN
    if Path(".env.ngrok").exists():
        with open(".env.ngrok") as f:
            content = f.read()
            has_token = "NGROK_AUTH_TOKEN" in content
            token_set = "COLOQUE_SEU_TOKEN_AQUI" not in content
            has_api_key = "NGROK_API_KEY" in content
        
        print("📝 CONFIGURAÇÃO .env.ngrok:\n")
        check_step("NGROK_API_KEY preenchida", has_api_key)
        check_step("NGROK_AUTH_TOKEN existe", has_token)
        check_step("NGROK_AUTH_TOKEN preenchido", token_set if has_token else False)
    
    print("\n" + "="*70 + "\n")
    
    # Menu de próximas ações
    print("🎯 PRÓXIMAS AÇÕES:\n")
    
    print("OPÇÃO 1: Setup Inicial")
    print("  1. Execute: python setup_ngrok.py")
    print("  2. Copie seu authtoken de: https://dashboard.ngrok.com/auth")  
    print("  3. Cole em .env.ngrok: NGROK_AUTH_TOKEN=ngrok_...\n")
    
    print("OPÇÃO 2: Validar Configuração")
    print("  Execute: python test_ngrok_security.py\n")
    
    print("OPÇÃO 3: Iniciar Servidor")
    print("  Execute: python start_with_ngrok.py\n")
    
    print("OPÇÃO 4: Ler Documentação")
    print("  - NGROK_SETUP.md (guia completo)")
    print("  - NGROK_INTEGRATION.md (integração com código)")
    print("  - NGROK_CHECKLIST.md (verificação passo a passo)\n")
    
    print("="*70 + "\n")
    
    # Status final
    if completed == total and has_api_key:
        if has_token and token_set:
            print("✅ TUDO PRONTO! Execute: python start_with_ngrok.py\n")
            return 0
        else:
            print("⚠️  Aguardando: NGROK_AUTH_TOKEN em .env.ngrok")
            print("   Copie de: https://dashboard.ngrok.com/auth\n")
            return 1
    else:
        print("📌 Alguns componentes ausentes. Veja opções acima.\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
