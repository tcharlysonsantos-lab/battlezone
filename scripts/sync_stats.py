#!/usr/bin/env python
"""
Script para sincronizar estatísticas dos operadores.
Remove registros órfãos e recalcula as estatísticas baseado no que existe.

Uso:
    python sync_stats.py
"""

from app import app, db
from backend.models import Operador, PartidaParticipante, Partida
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def sincronizar():
    """Executa a sincronização de estatísticas"""
    with app.app_context():
        print("\n" + "="*70)
        print("🔄 SINCRONIZAÇÃO DE ESTATÍSTICAS DOS OPERADORES")
        print("="*70 + "\n")
        
        try:
            # 1. ENCONTRAR E REMOVER PARTICIPANTES ÓRFÃOS
            print("📍 Etapa 1: Procurando por registros órfãos...")
            
            participantes_orfaos = PartidaParticipante.query.filter(
                ~PartidaParticipante.partida_id.in_(
                    db.session.query(Partida.id)
                )
            ).all()
            
            orfaos_removidos = len(participantes_orfaos)
            
            if orfaos_removidos > 0:
                print(f"   ⚠️ Encontrados {orfaos_removidos} registro(s) órfão(s):")
                for pp in participantes_orfaos:
                    print(f"      - Participante ID {pp.id} (operador_id={pp.operador_id}, partida_id={pp.partida_id})")
                    db.session.delete(pp)
                
                db.session.commit()
                print(f"   ✅ {orfaos_removidos} registro(s) removido(s)\n")
            else:
                print("   ✅ Nenhum registro órfão encontrado\n")
            
            # 2. RECALCULAR ESTATÍSTICAS DE TODOS OS OPERADORES
            print("📍 Etapa 2: Recalculando estatísticas dos operadores...")
            
            operadores = Operador.query.all()
            total_operadores = len(operadores)
            operadores_atualizados = 0
            
            for idx, operador in enumerate(operadores, 1):
                # Resetar todas as estatísticas
                operador.total_kills = 0
                operador.total_deaths = 0
                operador.total_vitorias = 0
                operador.total_derrotas = 0
                operador.total_mvps = 0
                operador.total_capturas = 0
                operador.total_plantas_bomba = 0
                operador.total_desarmes_bomba = 0
                operador.total_refens = 0
                operador.total_cacos = 0
                operador.total_partidas = 0
                
                # Buscar TODOS os participantes válidos do operador
                participantes = PartidaParticipante.query.filter_by(
                    operador_id=operador.id
                ).all()
                
                partidas_processadas = 0
                
                # Somar estatísticas de cada participação
                for pp in participantes:
                    # Verificar se a partida ainda existe (precaução extra)
                    partida = Partida.query.get(pp.partida_id)
                    if not partida:
                        logging.warning(f"⚠️ Partida {pp.partida_id} do participante {pp.id} não existe")
                        db.session.delete(pp)
                        continue
                    
                    # Se for partida finalizada, contar nas estatísticas
                    if partida.finalizada:
                        operador.total_kills += pp.kills or 0
                        operador.total_deaths += pp.deaths or 0
                        operador.total_capturas += pp.capturas or 0
                        operador.total_plantas_bomba += pp.plantou_bomba or 0
                        operador.total_desarmes_bomba += pp.desarmou_bomba or 0
                        operador.total_refens += pp.refens or 0
                        operador.total_cacos += pp.cacou or 0
                        operador.total_partidas += 1
                        
                        # Contar vitórias/derrotas
                        if pp.resultado == 'vitoria':
                            operador.total_vitorias += 1
                        elif pp.resultado == 'derrota':
                            operador.total_derrotas += 1
                        
                        # Contar MVPs
                        if pp.mvp:
                            operador.total_mvps += 1
                        
                        partidas_processadas += 1
                
                if partidas_processadas > 0:
                    print(f"   [{idx:3d}/{total_operadores}] {operador.warname:15s} - {partidas_processadas:2d} partida(s) - "
                          f"K/D: {operador.total_kills}/{operador.total_deaths}")
                
                operadores_atualizados += 1
            
            db.session.commit()
            
            print(f"\n   ✅ {operadores_atualizados} operador(es) recalculado(s)\n")
            
            # 3. RESUMO FINAL
            print("="*70)
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*70)
            print(f"📊 Estatísticas finais:")
            print(f"   • Registros órfãos removidos: {orfaos_removidos}")
            print(f"   • Operadores recalculados: {operadores_atualizados}")
            print(f"   • Total de operadores no sistema: {total_operadores}")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {str(e)}\n")
            db.session.rollback()
            raise

if __name__ == '__main__':
    sincronizar()
