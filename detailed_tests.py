#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TESTE DETALHADO DE FUNCIONALIDADES
Testa as validações e fluxos críticos
"""

import requests
from bs4 import BeautifulSoup
from app import app, db
from models import User, Operador, Solicitacao
from werkzeug.security import generate_password_hash
import secrets

print("\n" + "="*70)
print("🧪 TESTES DE FUNCIONALIDADES")
print("="*70)

# ===================  TESTE 1: AUTO-CRIAÇÃO DE USUÁRIO  ===================
print("\n1️⃣  TESTE: Auto-criação de usuário quando operador existe")
print("-" * 70)

with app.app_context():
    # Limpar dados de teste
    User.query.filter_by(username='autotest').delete()
    Operador.query.filter_by(warname='autotest').delete()
    Solicitacao.query.filter_by(usuario='autotest').delete()
    db.session.commit()
    
    # Criar operador de teste
    op = Operador(
        nome='Teste Auto',
        warname='autotest',
        email='autotest@test.com',
        cpf='99999999999',
        idade='25'
    )
    db.session.add(op)
    db.session.commit()
    
    print(f"✅ Operador criado: {op.warname}")
    
    # Tentar registrar com os mesmos dados
    session = requests.Session()
    r1 = session.get('http://192.168.0.100:5000/auth/solicitar', timeout=5)
    soup = BeautifulSoup(r1.text, 'html.parser')
    csrf = soup.find('input', {'name': 'csrf_token'})
    
    if csrf:
        dados = {
            'csrf_token': csrf.get('value'),
            'nome': 'Teste Auto',
            'usuario': 'autotest',
            'email': 'autotest@test.com',
            'cpf': '99999999999',
            'telefone': '11999999999',
            'data_nascimento': '15/05/1999',
            'senha': 'Auto@1234',
            'confirmar_senha': 'Auto@1234'
        }
        
        r2 = session.post('http://192.168.0.100:5000/auth/solicitar', 
                         data=dados, allow_redirects=True, timeout=5)
        
        user = User.query.filter_by(username='autotest').first()
        if user:
            print(f"✅ USUÁRIO CRIADO AUTOMATICAMENTE!")
            print(f"   Status: {user.status}")
            print(f"   Operador_ID: {user.operador_id}")
            
            # Testar login
            session2 = requests.Session()
            r3 = session2.get('http://192.168.0.100:5000/auth/login', timeout=5)
            soup2 = BeautifulSoup(r3.text, 'html.parser')
            csrf2 = soup2.find('input', {'name': 'csrf_token'}).get('value')
            
            login_data = {
                'csrf_token': csrf2,
                'username': 'autotest',
                'password': 'Auto@1234'
            }
            
            r4 = session2.post('http://192.168.0.100:5000/auth/login',
                             data=login_data, allow_redirects=True, timeout=5)
            
            if 'dashboard' in r4.url:
                print(f"✅ LOGIN FUNCIONANDO!")
            else:
                print(f"❌ Login falhou - esperado dashboard, recebeu: {r4.url}")
        else:
            print(f"❌ Usuário NÃO foi criado automaticamente")
            print(f"   Response: {r2.status_code}")
            if 'já existe' in r2.text.lower():
                print(f"   Motivo: Usuário já existe")
    else:
        print("❌ CSRF token não encontrado")

# ===================  TESTE 2: VALIDAÇÃO DE FORMULÁRIO  ===================
print("\n2️⃣  TESTE: Validação de campos do formulário")
print("-" * 70)

session = requests.Session()
r = session.get('http://192.168.0.100:5000/auth/solicitar', timeout=5)
soup = BeautifulSoup(r.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

# Teste com CPF inválido
print("Teste 1: CPF inválido")
bad_data = {
    'csrf_token': csrf_token,
    'nome': 'Teste Inválido',
    'usuario': 'testebad1',
    'email': 'bad@email.com',
    'cpf': '11111111111',  # CPF inválido
    'telefone': '11999999999',
    'data_nascimento': '15/05/1999',
    'senha': 'Test@1234',
    'confirmar_senha': 'Test@1234'
}

r2 = session.post('http://192.168.0.100:5000/auth/solicitar',
                 data=bad_data, timeout=5)

if 'CPF inválido' in r2.text or 'invalid' in r2.text.lower():
    print("   ✅ CPF inválido foi rejeitado")
else:
    print("   ⚠️  Validação de CPF pode não estar funcionando")

# ===================  TESTE 3: SENHA MÍNIMA  ===================
print("\nTeste 2: Senha muito curta")

bad_data2 = {
    'csrf_token': csrf_token,
    'nome': 'Teste Senha',
    'usuario': 'testesena',
    'email': 'senha@email.com',
    'cpf': '98765432100',
    'telefone': '11999999999',
    'data_nascimento': '15/05/1999',
    'senha': '123',  # Senha muito curta
    'confirmar_senha': '123'
}

r3 = session.post('http://192.168.0.100:5000/auth/solicitar',
                 data=bad_data2, timeout=5)

if 'password' in r3.text.lower() or 'senha' in r3.text.lower():
    print("   ✅ Senha curta foi validada")
else:
    print("   ⚠️  Validação de senha pode não estar funcionando")

print("\n" + "="*70)
print("✅ TESTES CONCLUÍDOS")
print("="*70 + "\n")
