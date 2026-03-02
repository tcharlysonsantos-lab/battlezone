#!/usr/bin/env python
"""Teste com CPF válido para auto-criação de usuário"""

from app import app, db
from models import User, Operador, Solicitacao
import requests
from bs4 import BeautifulSoup
import re

# Função para gerar CPF válido
def gerar_cpf_valido():
    """Gera um CPF válido para testes"""
    # CPF: 12345678901 é um exemplo comum de teste
    cpf = "12345678901"
    
    # Validar usando o mesmo algoritmo do forms.py
    cpf_numeros = re.sub(r'[^0-9]', '', cpf)
    if len(cpf_numeros) != 11 or cpf_numeros == cpf_numeros[0] * 11:
        return None
    
    for i in range(9, 11):
        soma = sum(int(cpf_numeros[num]) * (i+1 - num) for num in range(0, i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if int(cpf_numeros[i]) != digito:
            return None
    
    return cpf_numeros

print("🔍 TESTE DE AUTO-CRIAÇÃO COM CPF VÁLIDO")
print("=" * 70)

with app.app_context():
    # Limpar dados de testes anteriores
    User.query.filter_by(username='testvalido').delete()
    Operador.query.filter_by(warname='testvalido').delete()
    Solicitacao.query.filter_by(usuario='testvalido').delete()
    db.session.commit()
    
    # CPF válido
    cpf_valido = "53018268799"  # CPF válido de exemplo
    
    # Criar operador
    operador = Operador(
        nome='Usuario Valido',
        warname='testvalido',
        email='valido@test.com',
        cpf=cpf_valido,
        idade='25'
    )
    db.session.add(operador)
    db.session.commit()
    
    print(f"1️⃣ Operador criado:")
    print(f"   Nome: {operador.nome}")
    print(f"   Warname: {operador.warname}")
    print(f"   Email: {operador.email}")
    print(f"   CPF: {operador.cpf}\n")
    
    # Tentar auto-registro
    print(f"2️⃣ Tentando registro com dados idênticos...")
    
    session = requests.Session()
    r = session.get('http://192.168.0.100:5000/auth/solicitar', timeout=5)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf = soup.find('input', {'name': 'csrf_token'}).get('value')
    
    dados = {
        'csrf_token': csrf,
        'nome': 'Usuario Valido',
        'usuario': 'testvalido',
        'email': 'valido@test.com',
        'cpf': cpf_valido,
        'telefone': '11999999999',
        'data_nascimento': '15/05/1999',
        'senha': 'Test@12345',
        'confirmar_senha': 'Test@12345'
    }
    
    r2 = session.post('http://192.168.0.100:5000/auth/solicitar',
                     data=dados, allow_redirects=True, timeout=5)
    
    # Verificar resultado
    user = User.query.filter_by(username='testvalido').first()
    
    if user:
        print(f"   ✅ USUÁRIO CRIADO COM SUCESSO!")
        print(f"   Status: {user.status}")
        print(f"   Operador_ID: {user.operador_id}")
        print(f"   2FA: {user.two_factor_enabled}")
        
        # Tentar login
        print(f"\n3️⃣ Testando login...")
        session2 = requests.Session()
        r3 = session2.get('http://192.168.0.100:5000/auth/login', timeout=5)
        soup2 = BeautifulSoup(r3.text, 'html.parser')
        csrf2 = soup2.find('input', {'name': 'csrf_token'}).get('value')
        
        login_data = {
            'csrf_token': csrf2,
            'username': 'testvalido',
            'password': 'Test@12345'
        }
        
        r4 = session2.post('http://192.168.0.100:5000/auth/login',
                          data=login_data, allow_redirects=True, timeout=5)
        
        if 'dashboard' in r4.url:
            print(f"   ✅ LOGIN BEM-SUCEDIDO!")
            print(f"   URL: {r4.url}")
        else:
            print(f"   ❌ Login falhou")
            print(f"   URL: {r4.url}")
    else:
        print(f"   ❌ Usuário NÃO foi criado")
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        alerts = soup2.find_all('div', class_='alert')
        if alerts:
            print(f"\n   Mensagens do servidor:")
            for alert in alerts:
                msg = alert.get_text().strip()
                print(f"   • {msg}")
        else:
            print(f"   (Sem mensagens de erro)")

print("\n" + "=" * 70)
