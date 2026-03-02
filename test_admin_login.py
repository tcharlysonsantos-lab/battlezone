#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup

session = requests.Session()
r = session.get('http://192.168.0.100:5000/auth/login', timeout=5)
soup = BeautifulSoup(r.text, 'html.parser')
csrf = soup.find('input', {'name': 'csrf_token'}).get('value')

data = {'csrf_token': csrf, 'username': 'admin', 'password': 'F6yTVRPZC0KPhh3r'}
r2 = session.post('http://192.168.0.100:5000/auth/login', data=data, allow_redirects=True, timeout=5)

if 'dashboard' in r2.url:
    print('✅ LOGIN ADMIN BEM-SUCEDIDO!')
    print(f'   Redirecionado para: {r2.url}')
else:
    print('❌ Login falhou')
    print(f'   URL: {r2.url}')
    print(f'   Status: {r2.status_code}')
