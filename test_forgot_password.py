#!/usr/bin/env python3
"""
Script para testar a recuperação de senha via HTTP
"""

import requests
import time
import sys
import re

# Aguardar um pouco para o servidor iniciar
print("⏳ Aguardando servidor iniciar...")
time.sleep(2)

BASE_URL = "http://localhost:5000"
EMAIL = "tcharlysonf.f@gmail.com"

print(f"\n🔐 TESTANDO RECUPERAÇÃO DE SENHA")
print(f"{'='*60}")
print(f"Email de teste: {EMAIL}")
print(f"URL base: {BASE_URL}")

# Teste 1: Acessar a página de forgot-password
print(f"\n📋 TESTE 1: Acessar página /auth/forgot-password (GET)")
session = requests.Session()
try:
    response = session.get(f"{BASE_URL}/auth/forgot-password", timeout=5)
    print(f"✅ Status: {response.status_code}")
    if "forgot" in response.text.lower() or "email" in response.text.lower():
        print("✅ Página carregou corretamente")
    else:
        print("⚠️  Página carregou mas conteúdo pode estar diferente")
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)

# Teste 2: Extrair CSRF token do HTML
print(f"\n🔐 TESTE 2: Extrair CSRF token")
csrf_token = None
try:
    # Procurar por {{ csrf_token() }} ou por um input hidden
    match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', response.text)
    if match:
        csrf_token = match.group(1)
        print(f"✅ CSRF token encontrado: {csrf_token[:20]}...")
    else:
        print("⚠️  CSRF token não encontrado no HTML")
        print("   Procurando por padrões diferentes...")
        if 'csrf_token' in response.text:
            print("   ⚠️  Mas 'csrf_token' aparece no HTML")
except Exception as e:
    print(f"❌ Erro ao extrair CSRF: {e}")

# Teste 3: Fazer POST com o email
print(f"\n📧 TESTE 3: Enviar formulário com email")
payload = {'email': EMAIL}
if csrf_token:
    payload['csrf_token'] = csrf_token
    print(f"📤 POST com CSRF token: {csrf_token[:20]}...")
else:
    print(f"📤 POST SEM CSRF token (isso provavelmente falhará)")

print(f"📤 Dados enviados: email={EMAIL}")

try:
    response = session.post(
        f"{BASE_URL}/auth/forgot-password",
        data=payload,
        allow_redirects=True,
        timeout=10
    )
    
    print(f"\n✅ Status da resposta: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Requisição processada (200 OK)")
        if "reset" in response.text.lower():
            print("✅ Resposta contém menção a reset")
        if "link" in response.text.lower():
            print("✅ Resposta contém menção a link")
    elif response.status_code == 302:
        print("✅ Redirecionamento (302) - Comportamento esperado!")
        print(f"📍 Redirecionou para: {response.headers.get('Location', 'N/A')}")
    elif response.status_code == 400:
        print("❌ Erro 400 Bad Request")
        print(f"Resposta: {response.text[:500]}")
    else:
        print(f"⚠️  Status inesperado: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na requisição: {e}")
    sys.exit(1)

print(f"\n{'='*60}")
print("✅ TESTES CONCLUÍDOS!")
print("\n💡 PRÓXIMAS ETAPAS:")
print("1. ✅ Se recebeu 200 ou 302 = sucesso na requisição")
print("2. ✅ Verifique seu email (tcharlysonf.f@gmail.com) por um link de reset")
print("3. ✅ Se não recebeu email, os logs do servidor mostrarão por quê")
print("\n📧 Verifique:")
print("   - Sua caixa de entrada")
print("   - Pasta SPAM/Lixo")
print("   - Logs do servidor para mensagens de erro de email")
