#!/usr/bin/env python
"""Debug completo da requisição"""

from app import app, db
from models import User, Operador, Solicitacao
from forms import SolicitacaoForm
from werkzeug.datastructures import ImmutableMultiDict

app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    # Limpara
    User.query.filter_by(username='debugtest').delete()
    Operador.query.filter_by(warname='debugtest').delete()
    Solicitacao.query.filter_by(usuario='debugtest').delete()
    db.session.commit()
    
    # Usar CPF válido (já validado matematicamente)
    cpf_valido = "11144477735"  # CPF válido de teste
    
    # Criar operador com CPF válido
    operador = Operador(
        nome='Debug Test',
        warname='debugtest',
        email='debug@test.com',
        cpf=cpf_valido,
        idade='25'
    )
    db.session.add(operador)
    db.session.commit()
    
    print("1️⃣ Operador criado")
    print(f"   Nome: {operador.nome}")
    print(f"   Warname: {operador.warname}")
    print(f"   CPF: {operador.cpf}\n")
    
    # Usar o mesmo CPF no formulário
    cpf_para_form = cpf_valido
    
    # Simular formulário
    print("2️⃣ Testando formulário...")
    
    dados_form = ImmutableMultiDict([
        ('csrf_token', 'dummy'),
        ('nome', 'Debug Test'),
        ('usuario', 'debugtest'),
        ('email', 'debug@test.com'),
        ('cpf', cpf_para_form),
        ('telefone', '11999999999'),
        ('data_nascimento', '15/05/1999'),
        ('senha', 'Test@12345'),
        ('confirmar_senha', 'Test@12345')
    ])
    
    with app.test_request_context(method='POST', data=dados_form):
        form = SolicitacaoForm()
        
        print(f"   Form validate(): {form.validate()}")
        
        if form.errors:
            print(f"   ❌ Erros de validação:")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"      • {field}: {error}")
        else:
            print(f"   ✅ Sem erros de validação")
        
        # Verificar operador encontrado
        operador_encontrado = getattr(form, 'operador_encontrado', None)
        print(f"\n   Operador encontrado: {operador_encontrado}")
        
        if operador_encontrado:
            print(f"   ✅ DEVERIA CRIAR USUÁRIO AUTOMATICAMENTE!")
        else:
            print(f"   ❌ Nenhum operador encontrado - vai criar solicitação")

print("\n" + "=" * 70)
