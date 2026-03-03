from app import app
from flask import render_template

# Verificar se CSRF está ativado
print(f"WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED')}")
print(f"WTF_CSRF_CHECK_DEFAULT: {app.config.get('WTF_CSRF_CHECK_DEFAULT')}")

# Testar renderização do template
with app.test_request_context():
    from flask_wtf.csrf import generate_csrf
    token = generate_csrf()
    print(f"CSRF Token gerado: {token[:20]}...")
    
    # Verificar template
    html = render_template('auth/forgot_password.html')
    if 'csrf_token' in html:
        print("✓ Template contém field csrf_token")
    else:
        print("✗ Template NÃO contém csrf_token")
    
    if 'value="{{ csrf_token()' in html:
        print("✓ CSRF token está sendo renderizado com template syntax")
    else:
        print("? Verifica se o token está no HTML final")
        # Grep for the actual rendered token
        if f'value="{token}"' in html or 'name="csrf_token"' in html:
            print("✓ CSRF token field está presente no HTML")
