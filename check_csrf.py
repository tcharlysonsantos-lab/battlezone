#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificar CSRF exemptions aplicadas
"""
from app import app, csrf

def check_csrf_exemptions():
    """Verificar quais rotas estao exemptadas de CSRF"""
    print("=" * 70)
    print("VERIFICAR CSRF EXEMPTIONS")
    print("=" * 70)
    
    print(f"\nCSRF Exempt Views: {csrf._exempt_views}")
    
    # Listar todas as rotas
    print(f"\nTodas as rotas registradas:")
    for rule in app.url_map.iter_rules():
        rota = rule.rule
        endpoint = rule.endpoint
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        
        exempt = "[EXEMPT]" if endpoint in csrf._exempt_views else ""
        
        print(f"  {endpoint:40} {rota:50} {methods:20} {exempt}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    check_csrf_exemptions()
