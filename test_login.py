#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar login e diagnosticar problemas com CSRF
"""
import requests
from bs4 import BeautifulSoup
import sys

BASE_URL = "http://192.168.0.100:5000"
LOGIN_URL = f"{BASE_URL}/auth/login"

def test_login(username, password):
    """Test login flow with CSRF token handling"""
    session = requests.Session()
    
    print(f"1️⃣ Fazendo GET para {LOGIN_URL}...")
    # Get login page
    response = session.get(LOGIN_URL, timeout=5)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ Erro ao acessar página de login: {response.status_code}")
        return
    
    # Parse CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_input:
        print("   ❌ CSRF token não encontrado na página!")
        return
    
    csrf_token = csrf_input.get('value')
    print(f"   ✅ CSRF token extraído: {csrf_token[:20]}...")
    print(f"   Cookies na sessão: {session.cookies}")
    
    print(f"\n2️⃣ Fazendo POST para {LOGIN_URL}...")
    # Try login
    login_data = {
        'username': username,
        'password': password,
        'csrf_token': csrf_token
    }
    
    response = session.post(LOGIN_URL, data=login_data, timeout=5, allow_redirects=True)
    print(f"   Status: {response.status_code}")
    print(f"   URL final: {response.url}")
    
    if response.status_code == 200:
        if 'Login' in response.text or 'login' in response.url.lower():
            print("   ❌ Ainda na página de login - login falhou")
            print(f"   Resposta contém 'Login': {'Login' in response.text}")
        else:
            print("   ✅ Login bem-sucedido!")
            return True
    elif response.status_code == 400:
        print("   ❌ Erro 400 - Bad Request")
        print(f"   Resposta: {response.text[:200]}")
    else:
        print(f"   ❌ Erro HTTP {response.status_code}")
    
    return False

if __name__ == '__main__':
    try:
        print("🔐 Testando login na BattleZone")
        print("=" * 50)
        test_login('tcharlyson', '123456Ab')
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)
