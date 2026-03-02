import requests
from bs4 import BeautifulSoup
import json

session = requests.Session()

print("1️⃣ GET /auth/login para obter CSRF token e session cookie")
r = session.get('http://192.168.0.100:5000/auth/login')
print(f"   Status: {r.status_code}")
print(f"   Cookies: {dict(session.cookies)}")

soup = BeautifulSoup(r.text, 'html.parser')
csrf_input = soup.find('input', {'name': 'csrf_token'})
csrf_token_value = csrf_input.get('value') if csrf_input else None

print(f"   CSRF Token: {csrf_token_value[:40] if csrf_token_value else 'NOT FOUND'}...")

if csrf_token_value:
    print("\n2️⃣ POST /auth/login com CSRF token")
    
    # Criar dados POST
    post_data = {
        'csrf_token': csrf_token_value,
        'username': 'tcharlyson',
        'password': '123456Ab'
    }
    
    # Enviar
    r2 = session.post(
        'http://192.168.0.100:5000/auth/login',
        data=post_data,
        allow_redirects=True
    )
    
    print(f"   Status: {r2.status_code}")
    print(f"   URL final: {r2.url}")
    print(f"   Response length: {len(r2.text)} chars")
    
    # Verificar se tem mensagem de erro
    if '400' in r2.text or 'Bad Request' in r2.text:
        print("   ❌ Erro 400 recebido")
        # Extrair mensagem de erro
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        p = soup2.find('p')
        if p:
            print(f"   Mensagem: {p.text}")
    else:
        print("   ✅ Login aparentemente bem-sucedido")

print("\n3️⃣ Verificando se há problemas de SESSION")
print(f"   Headers HTTP enviados:")
r3 = session.get('http://192.168.0.100:5000/auth/login')
print(f"   Cookies na sessão: {list(session.cookies)}")
