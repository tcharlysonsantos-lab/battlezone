#!/usr/bin/env python3
"""
Script para popular battlepasses no banco de dados
Execute: python scripts/seed_battlepasses.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from backend.models import db, Battlepass


def seed_battlepasses():
    """Seed battlepasses de operador e equipe para o banco de dados"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("🌱 SEEDING BATTLEPASSES")
        print("="*60)
        
        # Contar battlepasses existentes
        total_existentes = Battlepass.query.count()
        print(f"\n📊 Battlepasses já existentes: {total_existentes}")
        
        # Battlepasses e Operadores
        battlepasses_operador = [
            {
                "tipo": "operador_basico",
                "nome": "Operador Básico",
                "descricao": "Sorteio semanal para operadores - Categoria Básica",
                "categoria": "operador"
            },
            {
                "tipo": "operador_elite",
                "nome": "Operador Elite",
                "descricao": "Sorteio semanal para operadores - Categoria Elite",
                "categoria": "operador"
            },
        ]
        
        # Battlepasses de Equipes
        battlepasses_equipe = [
            {
                "tipo": "equipe_basica",
                "nome": "Equipe Básica",
                "descricao": "Sorteio mensal para equipes - Categoria Básica",
                "categoria": "equipe"
            },
        ]
        
        todos_battlepasses = battlepasses_operador + battlepasses_equipe
        criados = 0
        pulados = 0
        
        print(f"\n📋 Total a processar: {len(todos_battlepasses)} battlepasses\n")
        
        # Criar battlepasses
        for bp_data in todos_battlepasses:
            # Verificar se já existe
            existente = Battlepass.query.filter_by(
                tipo=bp_data['tipo'],
                categoria=bp_data['categoria']
            ).first()
            
            if existente:
                print(f"  ✓ PULADO: {bp_data['nome']} ({bp_data['categoria']}) - Já existe")
                pulados += 1
            else:
                try:
                    novo_bp = Battlepass(
                        tipo=bp_data['tipo'],
                        nome=bp_data['nome'],
                        descricao=bp_data['descricao'],
                        categoria=bp_data['categoria'],
                        ativo=True
                    )
                    db.session.add(novo_bp)
                    db.session.commit()
                    print(f"  ✅ CRIADO: {bp_data['nome']} ({bp_data['categoria']})")
                    criados += 1
                except Exception as e:
                    db.session.rollback()
                    print(f"  ❌ ERRO ao criar {bp_data['nome']}: {e}")
        
        print("\n" + "="*60)
        print(f"📊 RESUMO")
        print("="*60)
        print(f"  ✅ Criados: {criados}")
        print(f"  ⏭️  Pulados (já existem): {pulados}")
        print(f"  📦 Total no banco agora: {Battlepass.query.count()}")
        print("="*60 + "\n")
        
        # Listar todos os battlepasses
        print("📋 BATTLEPASSES NO BANCO DE DADOS:\n")
        
        operador_bps = Battlepass.query.filter_by(categoria='operador').all()
        print("👥 OPERADORES (Semanais):")
        for bp in operador_bps:
            status = "🟢 ATIVO" if bp.ativo else "🔴 INATIVO"
            print(f"  [{bp.id}] {bp.nome} - {status}")
        
        equipe_bps = Battlepass.query.filter_by(categoria='equipe').all()
        print("\n🛡️  EQUIPES (Mensais):")
        for bp in equipe_bps:
            status = "🟢 ATIVO" if bp.ativo else "🔴 INATIVO"
            print(f"  [{bp.id}] {bp.nome} - {status}")
        
        print()


if __name__ == '__main__':
    try:
        seed_battlepasses()
        print("✅ Script executado com sucesso!\n")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}\n")
        sys.exit(1)
