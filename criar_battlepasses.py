#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar battlepasses padrão no banco de dados
"""
from app import app, db
from backend.models import Battlepass

def criar_battlepasses():
    """Cria os battlepasses padrão"""
    print("\n" + "="*60)
    print("🎖️ CRIANDO BATTLEPASSES")
    print("="*60)
    
    with app.app_context():
        # Verificar se já existem
        existentes = Battlepass.query.all()
        if existentes:
            print(f"\n⚠️  Já existem {len(existentes)} battlepass(es) no banco:")
            for bp in existentes:
                print(f"  • {bp.nome} (tipo: {bp.tipo})")
            return
        
        # Criar battlepasses
        battlepasses = [
            {
                'tipo': 'operador_basico',
                'nome': 'Battlepass Operador',
                'descricao': 'Battlepass padrão para operadores',
                'categoria': 'operador',
                'ativo': True
            },
            {
                'tipo': 'operador_elite',
                'nome': 'Battlepass Elite-Caveira',
                'descricao': 'Battlepass elite para operadores especiais',
                'categoria': 'operador',
                'ativo': True
            },
            {
                'tipo': 'equipe_basica',
                'nome': 'Battlepass Equipe Básica',
                'descricao': 'Battlepass padrão para equipes',
                'categoria': 'equipe',
                'ativo': True
            }
        ]
        
        for bp_data in battlepasses:
            bp = Battlepass(**bp_data)
            db.session.add(bp)
            print(f"  ✅ {bp_data['nome']}")
        
        db.session.commit()
        
        print("\n✅ Battlepasses criados com sucesso!\n")

if __name__ == '__main__':
    criar_battlepasses()
