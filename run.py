# run.py
import os
import sys
from app import app, db, cloud_manager

def main():
    """Função principal para iniciar o sistema"""
    print("=" * 50)
    print("BATTLEZONE - Sistema de Gerenciamento de Airsoft")
    print("Versão 3.0.0 - Flask")
    print("=" * 50)
    
    # Criar pastas necessárias
    os.makedirs('instance', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Verificar se banco existe
    if not os.path.exists('instance/database.db'):
        print("\n📦 Banco de dados não encontrado.")
        print("Criando banco de dados...")
        
        with app.app_context():
            db.create_all()
            
            # Criar admin padrão
            from werkzeug.security import generate_password_hash
            import secrets
            
            salt = secrets.token_hex(16)
            from models import User
            admin = User(
                username='admin',
                nome='Administrador',
                email='admin@battlezone.com',
                nivel='admin',
                status='aprovado',
                salt=salt,
                password_hash=generate_password_hash('admin123' + salt)
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Banco de dados criado!")
            print("   Usuário: admin")
            print("   Senha: admin123")
    
    # Verificar sincronização com Drive
    print(f"\n☁️ Pasta de nuvem: {cloud_manager.CAMINHO_NUVEM}")
    
    if cloud_manager.CAMINHO_NUVEM == cloud_manager.CAMINHO_LOCAL + '/backups_drive':
        print("⚠️  Pasta do Google Drive não encontrada!")
        print("   Os backups serão salvos localmente em: backups_drive/")
    
    print("\n🚀 Iniciando servidor...")
    print("   Acesse: http://localhost:5000")
    print("=" * 50)
    
    # Iniciar app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()