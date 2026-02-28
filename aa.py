from app import app, db
from models import Solicitacao
from werkzeug.security import generate_password_hash
import secrets

with app.app_context():
    print("="*50)
    print("🔍 TESTE DE CRIAÇÃO DIRETA NO BANCO")
    print("="*50)
    
    # Gerar salt
    salt = secrets.token_hex(16)
    
    # Criar solicitação
    solicitacao = Solicitacao(
        usuario="teste123",
        nome="Teste Silva",
        email="teste@email.com",
        cpf="123.456.789-09",
        telefone="(83) 99999-9999",
        data_nascimento="01/01/2000",
        idade=26,
        nivel="operador",
        password_hash=generate_password_hash("123456" + salt),
        salt=salt,
        status="pendente"
    )
    
    try:
        db.session.add(solicitacao)
        db.session.commit()
        print("✅ Solicitação criada com sucesso no banco!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar: {str(e)}")
    
    print("\n" + "="*50)