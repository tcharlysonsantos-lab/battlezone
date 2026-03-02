from app import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    print('=== CORRIGINDO SENHA ADMIN ===\n')
    
    # Usar o método set_password correto que inclui salt
    senha_nova = 'F6yTVRPZC0KPhh3r'
    admin.set_password(senha_nova)
    db.session.commit()
    
    print(f'✅ Senha atualizada com sucesso!')
    print(f'   Username: admin')
    print(f'   Nueva senha: {senha_nova}')
    print()
    print(f'Validando...')
    print(f'check_password("F6yTVRPZC0KPhh3r"): {admin.check_password(senha_nova)}')
