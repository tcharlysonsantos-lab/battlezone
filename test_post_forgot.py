from app import app
import re

with app.test_client() as client:
    # 1. GET para buscar o HTML e o CSRF token
    response = client.get('/auth/forgot-password')
    print(f"1. GET /auth/forgot-password: {response.status_code}")
    
    html = response.data.decode('utf-8')
    
    # Extrair token
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if not match:
        match = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
    
    if match:
        csrf_token = match.group(1)
        print(f"2. CSRF Token extraído: {csrf_token[:30]}...")
        
        # 2. POST com o token
        response = client.post('/auth/forgot-password', 
                              data={'email': 'test@example.com', 'csrf_token': csrf_token},
                              follow_redirects=False)
        
        print(f"3. POST /auth/forgot-password: {response.status_code}")
        
        if response.status_code == 302:
            print("✓ POST foi bem-sucedido! Redirecionou para login")
        else:
            print(f"✗ POST retornou {response.status_code}")
            print(f"Response: {response.data[:500]}")
    else:
        print("✗ Token CSRF não encontrado no HTML")
