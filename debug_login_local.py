import requests
from bs4 import BeautifulSoup

session = requests.Session()

print("1️⃣ GET /auth/login para obter CSRF token e session cookie")
try:
    r = session.get('http://localhost:5000/auth/login', timeout=5)
    print(f"   Status: {r.status_code}")
    print(f"   Cookies: {dict(session.cookies)}")

    soup = BeautifulSoup(r.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    csrf_token_value = csrf_input.get('value') if csrf_input else None

    print(f"   CSRF Token: {csrf_token_value[:40] if csrf_token_value else 'NOT FOUND'}...")

    # Mostrar Set-Cookie header
    print(f"\n   Set-Cookie header:")
    print(f"   {r.headers.get('Set-Cookie', 'NÃO ENCONTRADO')}")

    if csrf_token_value:
        print("\n2️⃣ POST /auth/login com CSRF token")
        
        post_data = {
            'csrf_token': csrf_token_value,
            'username': 'tcharlyson',
            'password': '123456Ab'
        }
        
        r2 = session.post(
            'http://localhost:5000/auth/login',
            data=post_data,
            allow_redirects=True,
            timeout=5
        )
        
        print(f"   Status: {r2.status_code}")
        print(f"   URL final: {r2.url}")
        
        if 'dashboard' in r2.url or 'verify_2fa' in r2.url:
            print("   ✅ Login bem-sucedido! Redirecionado para:", r2.url)
        elif '400' in r2.text or 'Bad Request' in r2.text:
            print("   ❌ Erro 400")
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            p = soup2.find('p')
            if p:
                print(f"   Mensagem: {p.text}")
        else:
            print(f"   Status: {r2.status_code}")
            if 'Login' in r2.text:
                print("   ℹ️ Ainda na página de login")

except Exception as e:
    print(f"   ❌ Erro: {e}")
