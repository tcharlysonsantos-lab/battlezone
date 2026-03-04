#!/usr/bin/env python
"""Script para testar a aplicação Flask localmente"""
import os
import sys

# Adicionar ao PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[1] Importando app...", flush=True)
try:
    from app import app, db, db_health_check
    print("[OK] App importada", flush=True)
except Exception as e:
    print(f"[ERROR] Erro ao importar app: {e}", flush=True)
    sys.exit(1)

print("[2] Criando contexto app...", flush=True)
try:
    with app.app_context():
        print("[OK] Contexto criado", flush=True)
        
        # Criar tabelas
        print("[3] Criando tabelas...", flush=True)
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            if not os.path.exists('instance/database.db'):
                print("[3.1] Executando create_all...", flush=True)
                db.create_all()
                print("[OK] Tabelas criadas", flush=True)
            else:
                print("[OK] Database já existe", flush=True)
        else:
            print("[OK] PostgreSQL detectado - pulando create_all", flush=True)
        
        # Testar health check
        print("[4] Testando health check...", flush=True)
        try:
            if not db_health_check._app:
                print("[4.1] Inicializando health check...", flush=True)
                db_health_check.init_app(app, db)
            print("[OK] Health check OK", flush=True)
        except Exception as e:
            print(f"[WARN] Health check: {e}", flush=True)
            
except Exception as e:
    print(f"[ERROR] Erro durante contextstack: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[5] Iniciando Flask...", flush=True)
print("=" * 70, flush=True)
print(f"Servidor rodando em: http://localhost:5000", flush=True)
print("Pressione CTRL+C para parar", flush=True)
print("=" * 70, flush=True)

try:
    app.run(debug=False, host='0.0.0.0', port=5000)
except KeyboardInterrupt:
    print("\n[OK] Servidor parado pelo usuário", flush=True)
except Exception as e:
    print(f"[ERROR] Erro ao rodar servidor: {e}", flush=True)
    import traceback
    traceback.print_exc()
