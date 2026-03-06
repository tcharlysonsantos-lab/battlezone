#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar partidas de teste com todas as combinações de campo, plano e tempo
Usa Keno e Tete como operadores
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import create_app, db
    print("[DEBUG] Imports successful")
except Exception as e:
    print(f"[ERROR] Failed to import: {e}")
    sys.exit(1)
from backend.models import Operador, Partida, PartidaParticipante, User
from backend.utils import PLANOS_WARFIELD, PLANOS_REDLINE, get_valores_plano, get_modos_permitidos

app = create_app()

with app.app_context():
    # 1. Criar ou obter operadores Keno e Tete
    print("📋 Verificando operadores...")
    
    keno = Operador.query.filter_by(nome='Keno').first()
    if not keno:
        keno = Operador(nome='Keno', warname='Keno', email='keno@battlezone.com')
        db.session.add(keno)
        db.session.flush()
        print(f"✅ Criado operador: Keno (ID: {keno.id})")
    else:
        print(f"✓ Operador Keno já existe (ID: {keno.id})")
    
    tete = Operador.query.filter_by(nome='Tete').first()
    if not tete:
        tete = Operador(nome='Tete', warname='Tete', email='tete@battlezone.com')
        db.session.add(tete)
        db.session.flush()
        print(f"✅ Criado operador: Tete (ID: {tete.id})")
    else:
        print(f"✓ Operador Tete já existe (ID: {tete.id})")
    
    db.session.commit()
    
    # 2. Buscar usuário criador (Keno)
    keno_user = User.query.filter_by(username='Keno').first()
    if not keno_user:
        print("⚠️  Usuário Keno não encontrado, usando None como criador")
        creator_id = None
    else:
        creator_id = keno_user.id
        print(f"✓ Usuário criador: Keno (ID: {creator_id})")
    
    # 3. Gerar lista de combinações
    partidas_criar = []
    
    # Warfield
    for plano in ['Avulso', 'Equipe', 'Sua Arma']:
        tempos = PLANOS_WARFIELD[plano]['tempos']
        for tempo in tempos:
            partidas_criar.append({
                'campo': 'Warfield',
                'plano': plano,
                'tempo': tempo
            })
    
    # Redline
    for plano in ['Rifle', 'Pistola']:
        tempos = PLANOS_REDLINE[plano]['tempos']
        for tempo in tempos:
            partidas_criar.append({
                'campo': 'Redline',
                'plano': plano,
                'tempo': tempo
            })
    
    print(f"\n🎮 Total de partidas a criar: {len(partidas_criar)}")
    print("=" * 80)
    
    # 4. Criar partidas
    counter = 100
    data_base = datetime.now()
    
    for config in partidas_criar:
        campo = config['campo']
        plano = config['plano']
        tempo = config['tempo']
        
        # Obter modo (primeiro disponível) e valores
        modos = get_modos_permitidos(tempo, plano)
        modo = modos[0] if modos else 'PVP INFINITY'
        
        valor, bbs = get_valores_plano(campo, plano, tempo)
        
        # Criar partida
        partida = Partida(
            nome=str(counter),
            data=(data_base + timedelta(days=counter-100)).strftime('%Y-%m-%d'),
            horario='18:00',
            campo=campo,
            plano=plano,
            tempo=tempo,
            modo=modo,
            tipo_participacao='individual',
            valor_total=valor,
            valor_por_participante=valor / 2,  # Dividido entre 2 operadores
            bbs_por_pessoa=bbs,
            total_bbs=bbs * 2,
            status='Agendada',
            created_by=creator_id
        )
        db.session.add(partida)
        db.session.flush()
        
        # Adicionar participantes
        part_keno = PartidaParticipante(partida_id=partida.id, operador_id=keno.id)
        part_tete = PartidaParticipante(partida_id=partida.id, operador_id=tete.id)
        
        db.session.add(part_keno)
        db.session.add(part_tete)
        
        print(f"✅ Partida {counter}: [{campo}] {plano} - {tempo} ({modo})")
        counter += 1
    
    db.session.commit()
    
    print("=" * 80)
    print(f"🎉 Todas as {len(partidas_criar)} partidas foram criadas com sucesso!")
    print(f"\n📊 Resumo:")
    print(f"   - Operador 1: Keno (ID: {keno.id})")
    print(f"   - Operador 2: Tete (ID: {tete.id})")
    print(f"   - Total de combinações: {len(partidas_criar)}")
    print(f"   - Nomes: de 100 a {counter-1}")
    print(f"\n✨ Script finalizado com sucesso!")
