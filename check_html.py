#!/usr/bin/env python3
"""
Script para verificar HTML do formulário
"""

import requests

BASE_URL = "http://localhost:5000"
response = requests.get(f"{BASE_URL}/auth/forgot-password")

html = response.text
# Procurar líneas com form  e csrf
lines = html.split('\n')
for i, line in enumerate(lines):
    if 'form' in line.lower() or 'csrf' in line.lower():
        print(f"Line {i}: {line}")
