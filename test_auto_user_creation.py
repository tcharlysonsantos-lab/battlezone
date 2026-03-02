#!/usr/bin/env python
"""
Teste da funcionalidade de criar usuário automaticamente quando operador existe
"""
from app import app, db
from models import Operador, User
import requests
from bs4 import BeautifulSoup

with app.app_context():
    # 1. Criar um operador de teste (simulando o que o admin faz)
    print('1️⃣ CRIANDO OPERADOR DE TESTE')
    print('=' * 50)
    
    # Limpar dados anteriores
    User.query.filter_by(username='testeoper').delete()
    Operador.query.filter_by(warname='testeoper').delete()
    db.session.commit()
    
    operador_teste = Operador(
        nome='João Silva Teste',
        warname='testeoper',
        email='joao.teste@airsoft.com',
        cpf='12345678901',
        telefone='11987654321',
        data_nascimento='1995-05-15',
        idade=28,
        funcao='Atirador'
    )
    db.session.add(operador_teste)
    db.session.commit()
    
    print(f'✅ Operador criado:')
    print(f'   Nome: {operador_teste.nome}')
    print(f'   Warname: {operador_teste.warname}')
    print(f'   Email: {operador_teste.email}')
    print(f'   CPF: {operador_teste.cpf}')
    print()
    
    # 2. Simular registro com os mesmos 4 dados
    print('2️⃣ SIMULANDO REGISTRO COM DADOS IDÊNTICOS')
    print('=' * 50)
    
    session = requests.Session()
    
    # Acessar formulário
    r = session.get('http://192.168.0.100:5000/auth/solicitar', timeout=5)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf = soup.find('input', {'name': 'csrf_token'}).get('value')
    
    # Enviar formulário com os mesmos dados
    dados_registro = {
        'csrf_token': csrf,
        'nome': 'João Silva Teste',
        'usuario': 'testeoper',
        'email': 'joao.teste@airsoft.com',
        'cpf': '12345678901',
        'telefone': '11987654321',
        'data_nascimento': '15/05/1995',
        'senha': 'Teste@1234',
        'confirmar_senha': 'Teste@1234'
    }
    
    r2 = session.post(
        'http://192.168.0.100:5000/auth/solicitar',
        data=dados_registro,
        allow_redirects=True,
        timeout=5
    )
    
    print(f'Status: {r2.status_code}')
    print(f'URL final: {r2.url}')
    print()
    
    # 3. Verificar se usuário foi criado automaticamente
    print('3️⃣ VERIFICANDO SE USUÁRIO FOI CRIADO')
    print('=' * 50)
    
    user = User.query.filter_by(username='testeoper').first()
    if user:
        print(f'✅ USUÁRIO CRIADO AUTOMATICAMENTE!')
        print(f'   Username: {user.username}')
        print(f'   Nome: {user.nome}')
        print(f'   Email: {user.email}')
        print(f'   Status: {user.status}')
        print(f'   Operador_ID: {user.operador_id}')
        print()
        print(f'4️⃣ TESTANDO LOGIN')
        print('=' * 50)
        
        session2 = requests.Session()
        r3 = session2.get('http://192.168.0.100:5000/auth/login', timeout=5)
        soup2 = BeautifulSoup(r3.text, 'html.parser')
        csrf2 = soup2.find('input', {'name': 'csrf_token'}).get('value')
        
        login_data = {
            'csrf_token': csrf2,
            'username': 'testeoper',
            'password': 'Teste@1234'
        }
        
        r4 = session2.post(
            'http://192.168.0.100:5000/auth/login',
            data=login_data,
            allow_redirects=True,
            timeout=5
        )
        
        if 'dashboard' in r4.url:
            print(f'✅ LOGIN BEM-SUCEDIDO!')
            print(f'   Redirecionado para: {r4.url}')
        else:
            print(f'❌ Login falhou')
            print(f'   URL: {r4.url}')
    else:
        print(f'❌ Usuário NÃO foi criado.')
        print(f'   Verifique a resposta do servidor')
        if 'já existe' in r2.text.lower():
            print(f'   Mensagem: Usuário já existe')
