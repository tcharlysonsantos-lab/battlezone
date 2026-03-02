from app import app, db
from models import User, EquipeMembros, Solicitacao, Operador, Equipe, Partida, PartidaParticipante, Venda, Estoque, Log
from werkzeug.security import generate_password_hash
import secrets

print("🚀 Inicializando banco de dados...")

with app.app_context():
    # Criar todas as tabelas
    db.create_all()
    print("✅ Tabelas criadas com sucesso!")
    
    # Criar admin
    salt = secrets.token_hex(16)
    admin = User(
        username='tcharlyson',
        nome='Tcharlyson',
        email='tcharlysonf.f@gmail.com',
        nivel='admin',
        status='aprovado',
        salt=salt,
        password_hash=generate_password_hash('123456Ab' + salt)
    )
    
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin criado: tcharlyson / 123456Ab")
    
    # Listar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Tabelas no banco: {', '.join(tables)}")

print("🎉 Banco de dados pronto!")