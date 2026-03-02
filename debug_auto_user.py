#!/usr/bin/env python
"""Debug da auto-criação de usuário"""

import requests
from bs4 import BeautifulSoup

session = requests.Session()

# Obter página de solicitação
r1 = session.get('http://192.168.0.100:5000/auth/solicitar', timeout=5)
soup = BeautifulSoup(r1.text, 'html.parser')
csrf = soup.find('input', {'name': 'csrf_token'}).get('value')

# Enviar formulário
dados = {
    'csrf_token': csrf,
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
                 data=dados, allow_redirects=False, timeout=5)

print(f"Status Code: {r2.status_code}")
print(f"Location Header: {r2.headers.get('Location', 'Nenhum')}")
print(f"URL: {r2.url}")
print()
print("Resposta (primeiras 1000 chars):")
print(r2.text[:1000])

# Com follow redirect
r3 = session.post('http://192.168.0.100:5000/auth/solicitar', 
                 data=dados, allow_redirects=True, timeout=5)

print(f"\nCom redirect:")
print(f"URL final: {r3.url}")

# Procurar por mensagens
soup2 = BeautifulSoup(r3.text, 'html.parser')
alerts = soup2.find_all('div', class_='alert')
if alerts:
    print("\nMensagens encontradas:")
    for alert in alerts:
        print(f"  • {alert.get_text().strip()}")
else:
    print("\nNenhuma mensagem de alerta encontrada")
