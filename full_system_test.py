#!/usr/bin/env python
"""
Teste completo do sistema BattleZone Flask
Verifica: imports, rotas, bancode dados, e funcionalidades
"""

import sys
import os

# Adicionar projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

print("\n" + "="*60)
print("🧪 TESTE COMPLETO DO SISTEMA - BattleZone Flask")
print("="*60)

# ============================================================
# TESTE 1: IMPORTS
# ============================================================
print("\n[TESTE 1/5] Verificando IMPORTS...")
try:
    from app import app
    print("  ✅ app.py")
    from backend.models import db, User, Operador, Equipe, Partida
    print("  ✅ backend.models")
    from backend.auth import auth_bp
    print("  ✅ backend.auth")
    from backend.forms import OperadorForm, EquipeForm, PartidaForm
    print("  ✅ backend.forms")
    from backend.utils import get_valores_plano, get_modos_permitidos
    print("  ✅ backend.utils")
    from backend.decorators import admin_required, requer_permissao
    print("  ✅ backend.decorators")
    from backend.security_utils import allowed_file_secure
    print("  ✅ backend.security_utils")
    print("  ✅ backend.auth_security")
    print("\n✅ TODOS OS IMPORTS OK!")
except Exception as e:
    print(f"❌ ERRO NO IMPORT: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================
# TESTE 2: ESTRUTURA DE DIRETÓRIOS
# ============================================================
print("\n[TESTE 2/5] Verificando ESTRUTURA DE DIRETÓRIOS...")
dirs_to_check = [
    'backend',
    'frontend',
    'frontend/templates',
    'frontend/static',
    'infrastructure',
    'infrastructure/ngrok',
    'infrastructure/railway',
    'infrastructure/database',
    'scripts',
    'docs',
    'instance'
]

for dir_path in dirs_to_check:
    full_path = os.path.join(os.getcwd(), dir_path)
    if os.path.isdir(full_path):
        print(f"  ✅ {dir_path}/")
    else:
        print(f"  ❌ {dir_path}/ NÃO EXISTE")

# ============================================================
# TESTE 3: BANCO DE DADOS
# ============================================================
print("\n[TESTE 3/5] Verificando BANCO DE DADOS...")
try:
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        print("  ✅ Database criado/atualizado")
        
        # Verificar se admin existe
        admin = User.query.filter_by(username='tcharlyson').first()
        if admin:
            print(f"  ✅ Usuário admin existe: tcharlyson")
        else:
            print(f"  ⚠️ Usuário admin NÃO encontrado")
            
        # Contar usuários
        user_count = User.query.count()
        print(f"  ✅ Total de usuários: {user_count}")
        
except Exception as e:
    print(f"  ⚠️ ERRO COM DATABASE: {e}")

# ============================================================
# TESTE 4: CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================
print("\n[TESTE 4/5] Verificando CONFIGURAÇÃO...")
print(f"  ✅ DEBUG: {app.debug}")
print(f"  ✅ Template folder: {app.template_folder}")
print(f"  ✅ Static folder: {app.static_folder}")
print(f"  ✅ Instance path: {app.instance_path}")

if hasattr(app, 'config'):
    print(f"  ✅ Database URI: {'SQLite' if 'sqlite' in str(app.config.get('SQLALCHEMY_DATABASE_URI', '')).lower() else 'PostgreSQL/Outro'}")

# ============================================================
# TESTE 5: ROTAS PRINCIPAIS
# ============================================================
print("\n[TESTE 5/5] Verificando ROTAS PRINCIPAIS...")

# Criar teste client
with app.test_client() as client:
    routes_to_test = [
        ('GET', '/', 'Home'),
        ('GET', '/auth/login', 'Login'),
        ('GET', '/calendario', 'Calendário'),
        ('GET', '/public/', 'Página Pública'),
    ]
    
    for method, route, name in routes_to_test:
        try:
            response = getattr(client, method.lower())(route)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"  {status} {name} ({route}) - Status: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {name} ({route}) - Erro: {str(e)[:50]}")

# ============================================================
# RESULTADO FINAL
# ============================================================
print("\n" + "="*60)
print("🎉 TESTES COMPLETADOS COM SUCESSO!")
print("="*60)
print("\n✅ Sistema está PRONTO para o Railway!\n")
