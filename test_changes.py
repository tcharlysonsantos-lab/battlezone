#!/usr/bin/env python
import requests

try:
    r = requests.get('http://localhost:5000/historico-sorteios')
    print(f"Status Code: {r.status_code}")
    
    if 'Sorteado por' in r.text:
        print("✅ SUCCESS: 'Sorteado por' texto ENCONTRADO na página!")
        # Print context
        lines = r.text.split('\n')
        for i, line in enumerate(lines):
            if 'Sorteado por' in line:
                print(f"\nLinha {i}: {line.strip()[:100]}")
    else:
        print("❌ FAIL: 'Sorteado por' NÃO encontrado")
        
    # Also check for history.back()
    if 'history.back()' in r.text:
        print("✅ SUCCESS: 'history.back()' ENCONTRADO no botão Voltar!")
    else:
        print("❌ FAIL: 'history.back()' NÃO encontrado")
        
except Exception as e:
    print(f"Erro ao fazer request: {e}")
