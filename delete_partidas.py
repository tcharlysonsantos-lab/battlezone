#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para deletar todas as partidas, vendas e estoque"""

import sys
from app import app, db
from models import Partida, PartidaParticipante, Venda, Estoque

def delete_all_data():
    with app.app_context():
        try:
            # Contar antes
            total_partidas = Partida.query.count()
            total_participantes = PartidaParticipante.query.count()
            total_vendas = Venda.query.count()
            total_estoque = Estoque.query.count()
            total_valor_vendas = db.session.query(db.func.sum(Venda.valor)).scalar() or 0
            
            print(f"\n📊 ANTES DE DELETAR:")
            print(f"  ├─ Partidas: {total_partidas}")
            print(f"  ├─ Participantes: {total_participantes}")
            print(f"  ├─ Vendas: {total_vendas} (Total: R$ {total_valor_vendas:.2f})")
            print(f"  └─ Itens Estoque: {total_estoque}")
            
            # Deletar
            print(f"\n🗑️  DELETANDO...")
            
            # Deletar vendas (isso remove do caixa também)
            Venda.query.delete()
            print(f"  ✓ Vendas deletadas (Caixa atualizado)")
            
            # Deletar participantes (por cascata)
            PartidaParticipante.query.delete()
            print(f"  ✓ Participantes deletados")
            
            # Deletar partidas
            Partida.query.delete()
            print(f"  ✓ Partidas deletadas")
            
            # Deletar estoque
            Estoque.query.delete()
            print(f"  ✓ Estoque deletado")
            
            # Commit
            db.session.commit()
            
            # Contar depois
            total_partidas = Partida.query.count()
            total_participantes = PartidaParticipante.query.count()
            total_vendas = Venda.query.count()
            total_estoque = Estoque.query.count()
            total_valor_vendas = db.session.query(db.func.sum(Venda.valor)).scalar() or 0
            
            print(f"\n✅ DEPOIS DE DELETAR:")
            print(f"  ├─ Partidas: {total_partidas}")
            print(f"  ├─ Participantes: {total_participantes}")
            print(f"  ├─ Vendas: {total_vendas} (Total: R$ {total_valor_vendas:.2f})")
            print(f"  └─ Itens Estoque: {total_estoque}")
            print(f"\n✨ Banco de dados completamente limpo!\n")
            
        except Exception as e:
            print(f"\n❌ ERRO ao deletar dados: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    delete_all_data()
