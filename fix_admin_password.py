from app import app, db
from models import User
from werkzeug.security import check_password_hash, generate_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    print('=== VERIFICAÇÃO DE SENHA ADMIN ===\n')
    
    print('Hash atual no banco:')
    print(admin.password_hash)
    print()
    
    senha_teste = 'F6yTVRPZC0KPhh3r'
    resultado = check_password_hash(admin.password_hash, senha_teste)
    print(f'Testando senha "{senha_teste}": {resultado}')
    print()
    
    if not resultado:
        print('A senha não corresponde. Atualizando...')
        novo_hash = generate_password_hash(senha_teste)
        admin.password_hash = novo_hash
        db.session.commit()
        print(f'✅ Atualizado com novo hash:')
        print(novo_hash)
        print()
        print('Validando novo hash:')
        print(check_password_hash(novo_hash, senha_teste))
