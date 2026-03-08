# run.py - VERSÃO SEGURA
import os
import sys
import secrets
import json
from pathlib import Path
from datetime import datetime

# Importar com tratamento de erro se config.py não existir
try:
    from app import app, db, cloud_manager
    from backend.health_check import db_health_check
    from backend.init_db import init_database
except Exception as e:
    print(f"ERROR importing app: {e}")
    print("\nVerify:")
    print("1. File seguranca.env exists?")
    print("2. SECRET_KEY is defined in seguranca.env?")
    sys.exit(1)

def gerar_senha_segura():
    """Gera uma senha segura de 16 caracteres"""
    return secrets.token_urlsafe(12)

def criar_admin_inicial():
    """Cria usuário admin com senha segura (APENAS NA PRIMEIRA VEZ)"""
    from backend.models import User
    from werkzeug.security import generate_password_hash
    
    # Verificar se admin já existe
    admin_existente = User.query.filter_by(username='admin').first()
    if admin_existente:
        print("[OK] Admin já existe no banco de dados")
        return False
    
    # Gerar senha segura
    senha_inicial = gerar_senha_segura()
    
    # Criar admin
    salt = secrets.token_hex(16)
    admin = User(
        username='admin',
        nome='Administrador do Sistema',
        email='admin@battlezone.local',
        nivel='admin',
        status='aprovado',
        salt=salt,
        password_hash=generate_password_hash(senha_inicial + salt)
    )
    
    db.session.add(admin)
    db.session.commit()
    
    # Salvar credenciais em arquivo seguro
    credenciais = {
        'usuario': 'admin',
        'senha_inicial': senha_inicial,
        'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'alerta': '⚠️ IMPORTANTE: Trocar essa senha IMEDIATAMENTE após primeiro login!'
    }
    
    file_credenciais = 'ADMIN_CREDENTIALS.json'
    try:
        with open(file_credenciais, 'w', encoding='utf-8') as f:
            json.dump(credenciais, f, indent=2, ensure_ascii=False)
        
        # Remover permissão de leitura para outros (se Linux)
        try:
            os.chmod(file_credenciais, 0o600)
        except:
            pass
    except Exception as e:
        print(f"[ERROR] Erro ao salvar credenciais: {e}")
        # Mesmo se falhar o arquivo, mostrar a senha no console
        pass
    
    print("\n" + "="*60)
    print("[OK] ADMIN CRIADO COM SUCESSO!")
    print("="*60)
    print(f"Usuário: {credenciais['usuario']}")
    print(f"Senha:   {credenciais['senha_inicial']}")
    print("\n[WARN] IMPORTANTE:")
    print("   1. Salve essa senha em local seguro")
    print("   2. Mude para uma senha forte IMEDIATAMENTE após login")
    print(f"   3. Arquivo '{file_credenciais}' criado com essas credenciais")
    print("   4. Delete esse arquivo após confirmação de acesso")
    print("="*60 + "\n")
    
    return True

def main():
    """Função principal para iniciar o sistema"""
    print("=" * 70)
    print("[BATTLEZONE] Sistema de Gerenciamento de Airsoft")
    print("Versão 3.0.0 - Flask | Edição com Segurança Ativada")
    print("=" * 70)
    
    # Criar pastas necessárias
    os.makedirs('instance', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("\n[DB] Inicializando banco de dados...")
    
    # ===== NOVA INICIALIZAÇÃO ROBUSTA =====
    try:
        print("   ➜ Chamando init_database() para validar todas as tabelas...")
        from backend.init_db import seed_battlepasses
        init_database(app)
        seed_battlepasses(app)
        print("   [OK] Banco de dados validado com sucesso!")
    except Exception as e:
        print(f"   [WARN] Erro no init_database (continuando): {e}")
        # Tentar fallback: db.create_all() básico
        try:
            with app.app_context():
                print("   ➜ Tentando fallback com db.create_all()...")
                db.create_all()
                print("   [OK] Fallback executado!")
                criar_admin_inicial()
        except Exception as e2:
            print(f"   [WARN] Fallback também falhou: {e2}")
            print("   [INFO] Continuando mesmo assim (tabelas podem ser criadas na primeira conexão)...")
    
    # Iniciar Health Check para conexão persistente
    print("\n[DB] Iniciando Database Health Check...")
    try:
        with app.app_context():
            db_health_check.start()
            print("   [OK] Database Health Check iniciado")
    except Exception as e:
        print(f"   [WARNING] Erro ao iniciar health check: {e}")
    
    # Verificar variáveis críticas
    print("\n[SECURITY] Verificando configuração de segurança...")
    try:
        from config import config
        
        checks = {
            'SECRET_KEY': '[OK]' if config.SECRET_KEY else '[FAIL]',
            'FLASK_ENV': '[OK]' if os.environ.get('FLASK_ENV') else '[WARN]',
            'DEBUG': '[OK]' if not config.DEBUG else '[FAIL]',  # DEBUG=False é bom
        }
        
        for item, status in checks.items():
            print(f"   {status} {item}")
        
        # Avisar se está em debug
        if config.DEBUG:
            print("\n[WARN] DEBUG MODE ATIVADO! Isso é apenas para desenvolvimento.")
            print("   Para produção, defina FLASK_ENV=production em seguranca.env")
    except Exception as e:
        print(f"[ERROR] ERRO ao verificar configuração: {e}")
    
    # Verificar sincronização com Drive
    print(f"\n[CLOUD] Pasta de nuvem: {cloud_manager.CAMINHO_NUVEM}")
    
    if cloud_manager.CAMINHO_NUVEM == cloud_manager.CAMINHO_LOCAL + '/backups_drive':
        print("[WARN] Pasta do Google Drive não encontrada!")
        print("   Os backups serão salvos localmente em: backups_drive/")
    
    print("\n" + "=" * 70)
    print("[START] INICIANDO SERVIDOR...")
    print("   Acesse: http://localhost:5000")
    print("   Para parar: Ctrl + C")
    print("=" * 70 + "\n")
    
    try:
        # Iniciar app
        app.run(
            debug=config.DEBUG,
            host='0.0.0.0',  # Escuta em todas as interfaces (necessário para Ngrok)
            port=5000,
            use_reloader=config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n\n[OK] Servidor parado pelo usuário (Ctrl + C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] ERRO ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
