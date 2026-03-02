from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Limpar usuários de teste anteriores
    User.query.filter_by(username='testeuser').delete()
    
    # Criar novo usuário de teste
    novo_user = User(
        username='testeuser',
        email='teste@test.com',
        nome='Usuário Teste',
        password_hash=generate_password_hash('senha123'),
        verified=True
    )
    
    db.session.add(novo_user)
    db.session.commit()
    
    print('✅ Usuário de teste criado:')
    print('   Username: testeuser')
    print('   Password: senha123')
    print()
    print('Tente fazer login com essas credenciais na página de login')
