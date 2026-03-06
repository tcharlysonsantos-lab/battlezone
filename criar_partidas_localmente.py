#!/usr/bin/env python3
# criar_partidas_localmente.py - SCRIPT PARA CRIAR PARTIDAS DE TESTE LOCALMENTE

import os
import sys
from datetime import datetime, timedelta

# Adiciona o diretório do app ao path
sys.path.insert(0, os.path.dirname(__file__))

# Importa a aplicação Flask
from app import app, db
from backend.models import User, Operador, Partida, PartidaParticipante
from backend.utils import PLANOS_WARFIELD, PLANOS_REDLINE, get_valores_plano, get_modos_permitidos

def criar_partidas_teste():
    """Cria partidas de teste para todas as combinações de campo, plano e tempo"""
    
    with app.app_context():
        try:
            print("\n" + "="*60)
            print("CRIANDO PARTIDAS DE TESTE LOCALMENTE")
            print("="*60)
            
            # 1. Criar/obter Keno e Tete como Operadores
            print("\n[1/4] Verificando/criando operadores Keno e Tete...")
            
            keno = Operador.query.filter_by(nome='Keno').first()
            if not keno:
print("  > Criando Operador 'Keno'...")
            keno = Operador(
                nome='Keno',
                warname='Keno',
                email='keno@battlezone.com',
                telefone='11999999999'
            )
            db.session.add(keno)
            db.session.flush()
            print(f"  OK Keno criado (ID: {keno.id})")
        else:
            print(f"  OK Keno ja existe (ID: {keno.id})")
        
        tete = Operador.query.filter_by(nome='Tete').first()
        if not tete:
            print("  > Criando Operador 'Tete'...")
            tete = Operador(
                nome='Tete',
                warname='Tete',
                email='tete@battlezone.com',
                telefone='11888888888'
            db.session.commit()
            
            # 2. Obter usuario criador (Keno User, se existir)
            print("\n[2/4] Verificando usuario criador...")
            keno_user = User.query.filter_by(username='Keno').first()
            creator_id = keno_user.id if keno_user else None
            print(f"  > Creator ID: {creator_id if creator_id else 'None (criadas sem usuario)'}")
            
            # 3. Montar lista de combinacoes (campo, plano, tempo)
            print("\n[3/4] Montando lista de combinacoes de plano/tempo...")
            
            partidas_criar = []
            
            # Warfield
            print(f"\n  > WARFIELD:")
            for plano in ['Avulso', 'Equipe', 'Sua Arma']:
                tempos = PLANOS_WARFIELD[plano]['tempos']
                print(f"    - {plano}: {len(tempos)} tempos")
                for tempo in tempos:
                    partidas_criar.append({'campo': 'Warfield', 'plano': plano, 'tempo': tempo})
            
            # Redline
            print(f"\n  > REDLINE:")
            for plano in ['Rifle', 'Pistola']:
                tempos = PLANOS_REDLINE[plano]['tempos']
                print(f"    - {plano}: {len(tempos)} tempos")
                for tempo in tempos:
                    partidas_criar.append({'campo': 'Redline', 'plano': plano, 'tempo': tempo})
            
            print(f"\n  OK Total de combinacoes: {len(partidas_criar)}")
            
            # 4. Criar as partidas
            print(f"\n[4/4] Criando {len(partidas_criar)} partidas...")
            
            counter = 100
            resultado = []
            data_base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
            
            for idx, config in enumerate(partidas_criar, 1):
                campo = config['campo']
                plano = config['plano']
                tempo = config['tempo']
                
                # Obter modo e valores
                modos = get_modos_permitidos(tempo, plano)
                modo = modos[0] if modos else 'PVP INFINITY'
                valor, bbs = get_valores_plano(campo, plano, tempo)
                
                # Calcular data (offset por dia para cada partida)
                data_partida = data_base + timedelta(days=idx-1)
                
                # Criar Partida
                partida = Partida(
                    nome=str(counter),
                    data=data_partida.date(),
                    horario='18:00',
                    campo=campo,
                    plano=plano,
                    tempo=tempo,
                    modo=modo,
                    tipo_participacao='individual',
                    valor_total=valor,
                    valor_por_participante=valor // 2 if valor > 0 else 0,
                    bbs_por_pessoa=bbs,
                    total_bbs=bbs * 2,
                    status='Agendada',
                    created_by=creator_id
                )
                db.session.add(partida)
                db.session.flush()
                
                # Adicionar Keno e Tete como participantes
                db.session.add(PartidaParticipante(partida_id=partida.id, operador_id=keno.id))
                db.session.add(PartidaParticipante(partida_id=partida.id, operador_id=tete.id))
                
                resultado.append({
                    'numero': counter,
                    'campo': campo,
                    'plano': plano,
                    'tempo': tempo,
                    'modo': modo,
                    'valor': valor,
                    'bbs': bbs,
                    'data': data_partida.strftime('%d/%m/%Y')
                })
                
                # Print a cada 5 partidas para acompanhamento
                if idx % 5 == 0:
                    print(f"  > Criadas {idx}/{len(partidas_criar)} partidas...")
                
                counter += 1
            
            # Commit final
            db.session.commit()
            
            # Resultado
            print(f"\n{'='*60}")
            print(f"OK SUCESSO! {len(resultado)} partidas criadas com sucesso!")
            print(f"{'='*60}\n")
            
            # Listar algumas partidas criadas
            print("AMOSTRA DAS PARTIDAS CRIADAS:\n")
            print(f"{'#':<5} {'Campo':<12} {'Plano':<12} {'Tempo':<20} {'Modo':<15} {'Valor':<8} {'BB':<6}")
            print("-" * 85)
            for i, p in enumerate(resultado):
                if i < 5 or i >= len(resultado) - 5:  # Mostra primeiras 5 e ultimas 5
                    print(f"{p['numero']:<5} {p['campo']:<12} {p['plano']:<12} {p['tempo']:<20} {p['modo']:<15} R${p['valor']:<7} {p['bbs']:<6}")
                elif i == 5:
                    print("...")
            
            print(f"\n{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\nERRO ao criar partidas: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    sucesso = criar_partidas_teste()
    sys.exit(0 if sucesso else 1)
