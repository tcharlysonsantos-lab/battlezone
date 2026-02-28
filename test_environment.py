#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Verificação do Ambiente Flask
Testa se tudo está configurado corretamente
"""

import sys
import subprocess

def check_python_version():
    """Verifica versão do Python"""
    print("✓ Verificando versão do Python...")
    version = sys.version_info
    print(f"  → Python {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print("  ✅ Versão OK\n")
        return True
    else:
        print("  ❌ Python 3.8+ necessário\n")
        return False

def check_imports():
    """Verifica importações de pacotes essenciais"""
    print("✓ Verificando importações dos pacotes...")
    
    pacotes = {
        'flask': 'Flask',
        'flask_sqlalchemy': 'Flask-SQLAlchemy',
        'flask_login': 'Flask-Login',
        'flask_wtf': 'Flask-WTF',
        'wtforms': 'WTForms',
        'dotenv': 'python-dotenv'
    }
    
    todos_ok = True
    for modulo, nome in pacotes.items():
        try:
            __import__(modulo)
            print(f"  ✅ {nome}")
        except ImportError:
            print(f"  ❌ {nome} (não instalado)")
            todos_ok = False
    
    print()
    return todos_ok

def check_flask_version():
    """Verifica versão do Flask"""
    print("✓ Versões dos pacotes:")
    try:
        import flask
        print(f"  → Flask: {flask.__version__}")
        import flask_sqlalchemy
        print(f"  → Flask-SQLAlchemy: {flask_sqlalchemy.__version__}")
        import flask_login
        print(f"  → Flask-Login: {flask_login.__version__}")
        print("  ✅ Todos os pacotes OK\n")
        return True
    except Exception as e:
        print(f"  ❌ Erro ao verificar versões: {e}\n")
        return False

def main():
    print("\n" + "="*50)
    print("  TESTE DE CONFIGURAÇÃO DO AMBIENTE FLASK")
    print("="*50 + "\n")
    
    checks = [
        check_python_version(),
        check_imports(),
        check_flask_version()
    ]
    
    print("="*50)
    if all(checks):
        print("✅ AMBIENTE CONFIGURADO COM SUCESSO!")
        print("="*50)
        print("\n🚀 Próximos passos:")
        print("  1. cd battlezone_flask")
        print("  2. python apy.py")
        print("  3. Acesse http://localhost:5000\n")
        return 0
    else:
        print("❌ ALGUNS ERROS FORAM ENCONTRADOS")
        print("="*50)
        print("\n⚠️  Execute novamente:")
        print("  pip install -r requirements.txt\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
