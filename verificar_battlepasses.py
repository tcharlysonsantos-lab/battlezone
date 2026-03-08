#!/usr/bin/env python
"""Script para verificar battlepasses no banco local"""

import sys
sys.path.insert(0, '.')

from app import app, db
from backend.models import Battlepass

def verificar():
    """Verifica battlepasses existentes"""
    with app.app_context():
        total = Battlepass.query.count()
        operadores = Battlepass.query.filter_by(categoria='operador', ativo=True).all()
        equipes = Battlepass.query.filter_by(categoria='equipe', ativo=True).all()
        
        print(f"Total de battlepasses: {total}")
        print(f"\nOperadores ({len(operadores)}):")
        for bp in operadores:
            print(f"  - {bp.nome} (tipo: {bp.tipo})")
        
        print(f"\nEquipes ({len(equipes)}):")
        for bp in equipes:
            print(f"  - {bp.nome} (tipo: {bp.tipo})")
        
        if total == 0:
            print("\n⚠️ Nenhuma battlepass encontrada! Você precisa criar algumas.")

if __name__ == '__main__':
    verificar()
