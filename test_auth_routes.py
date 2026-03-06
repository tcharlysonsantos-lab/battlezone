#!/usr/bin/env python
"""
Teste simples para verificar se rotas auth estão funcionando
"""
from app import app

print("[TEST] Testing auth routes without redirect loop...")

with app.test_client() as client:
    # Test 1: Access login page
    print('\n[TEST 1] GET /auth/login')
    try:
        response = client.get('/auth/login', follow_redirects=False)
        print(f'  Status Code: {response.status_code}')
        if response.status_code in [301, 302, 303, 307]:
            print(f'  Redirect to: {response.location}')
        else:
            print(f'  Content length: {len(response.get_data())} bytes')
    except Exception as e:
        print(f'  ERROR: {e}')
    
    # Test 2: Access index
    print('\n[TEST 2] GET /')
    try:
        response = client.get('/', follow_redirects=False)
        print(f'  Status Code: {response.status_code}')
        if response.status_code in [301, 302, 303, 307]:
            print(f'  Redirect to: {response.location}')
        else:
            print(f'  Content length: {len(response.get_data())} bytes')
    except Exception as e:
        print(f'  ERROR: {e}')
    
    # Test 3: Access signup
    print('\n[TEST 3] GET /auth/criar-conta')
    try:
        response = client.get('/auth/criar-conta', follow_redirects=False)
        print(f'  Status Code: {response.status_code}')
        if response.status_code in [301, 302, 303, 307]:
            print(f'  Redirect to: {response.location}')
        else:
            print(f'  Content length: {len(response.get_data())} bytes')
    except Exception as e:
        print(f'  ERROR: {e}')
    
    # Test 4: Access forgot password
    print('\n[TEST 4] GET /auth/forgot-password')
    try:
        response = client.get('/auth/forgot-password', follow_redirects=False)
        print(f'  Status Code: {response.status_code}')
        if response.status_code in [301, 302, 303, 307]:
            print(f'  Redirect to: {response.location}')
        else:
            print(f'  Content length: {len(response.get_data())} bytes')
    except Exception as e:
        print(f'  ERROR: {e}')

print("\n[TEST] Complete!")
