from app import app

with app.test_client() as client:
    # GET para buscar o HTML
    response = client.get('/auth/forgot-password')
    
    print(f"GET Status: {response.status_code}")
    
    html = response.data.decode('utf-8')
    
    # Procurar por csrf_token no HTML
    if 'name="csrf_token"' in html:
        print("✓ Campo csrf_token encontrado no HTML")
        
        # Extrair o valor do token
        import re
        match = re.search(r'value="([^"]+)".*?name="csrf_token"', html)
        if match:
            token = match.group(1)
            print(f"✓ Token encontrado: {token[:30]}...")
        else:
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', html)
            if match:
                token = match.group(1)
                print(f"✓ Token encontrado: {token[:30]}...")
            else:
                print("? Token não encontrado via regex")
                # Imprimir linhas com csrf_token
                for i, line in enumerate(html.split('\n')):
                    if 'csrf_token' in line:
                        print(f"Linha {i}: {line.strip()}")
    else:
        print("✗ Campo csrf_token NÃO encontrado no HTML")
        
    # Também procurar por {{ csrf_token() }}
    if '{{ csrf_token()' in html:
        print("? Template Jinja2 não foi renderizado ({{ csrf_token() }} ainda está no HTML)")
