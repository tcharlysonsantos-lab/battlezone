#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from backend.models import User, Operador, Partida, PartidaParticipante
from backend.utils import PLANOS_WARFIELD, PLANOS_REDLINE, get_valores_plano, get_modos_permitidos

# Output para arquivo
output_file = 'criar_partidas_output.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    with app.app_context():
        try:
            f.write("="*60 + "\n")
            f.write("CRIANDO PARTIDAS DE TESTE LOCALMENTE\n")
            f.write("="*60 + "\n\n")
            
            # 1. Criar operadores
            f.write("[1/4] Verificando/criando operadores Keno e Tete...\n")
            
            keno = Operador.query.filter_by(nome='Keno').first()
            if not keno:
                f.write("  > Criando Operador 'Keno'...\n")
                keno = Operador(
                    nome='Keno',
                    warname='Keno',
                    email='keno@battlezone.com',
                    telefone='11999999999'
                )
                db.session.add(keno)
                db.session.flush()
                f.write(f"  OK Keno criado (ID: {keno.id})\n")
            else:
                f.write(f"  OK Keno ja existe (ID: {keno.id})\n")
            
            tete = Operador.query.filter_by(nome='Tete').first()
            if not tete:
                f.write("  > Criando Operador 'Tete'...\n")
                tete = Operador(
                    nome='Tete',
                    warname='Tete',
                    email='tete@battlezone.com',
                    telefone='11888888888'
                )
                db.session.add(tete)
                db.session.flush()
                f.write(f"  OK Tete criado (ID: {tete.id})\n")
            else:
                f.write(f"  OK Tete ja existe (ID: {tete.id})\n")
            
            db.session.commit()
            f.write("  OK Operadores salvos\n")
            
            # 2. Obter criador
            f.write("\n[2/4] Verificando usuario criador...\n")
            keno_user = User.query.filter_by(username='Keno').first()
            creator_id = keno_user.id if keno_user else None
            f.write(f"  > Creator ID: {creator_id}\n")
            
            # 3. Montar lista de combinacoes
            f.write("\n[3/4] Montando lista de combinacoes...\n")
            
            partidas_criar = []
            
            f.write("\n  > WARFIELD:\n")
            for plano in ['Avulso', 'Equipe', 'Sua Arma']:
                tempos = PLANOS_WARFIELD[plano]['tempos']
                f.write(f"    - {plano}: {len(tempos)} tempos\n")
                for tempo in tempos:
                    partidas_criar.append({'campo': 'Warfield', 'plano': plano, 'tempo': tempo})
            
            f.write("\n  > REDLINE:\n")
            for plano in ['Rifle', 'Pistola']:
                tempos = PLANOS_REDLINE[plano]['tempos']
                f.write(f"    - {plano}: {len(tempos)} tempos\n")
                for tempo in tempos:
                    partidas_criar.append({'campo': 'Redline', 'plano': plano, 'tempo': tempo})
            
            f.write(f"\n  OK Total de combinacoes: {len(partidas_criar)}\n")
            
            # 4. Criar partidas
            f.write(f"\n[4/4] Criando {len(partidas_criar)} partidas...\n")
            
            counter = 100
            resultado = []
            data_base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
            
            for idx, config in enumerate(partidas_criar, 1):
                campo = config['campo']
                plano = config['plano']
                tempo = config['tempo']
                
                modos = get_modos_permitidos(tempo, plano)
                modo = modos[0] if modos else 'PVP INFINITY'
                valor, bbs = get_valores_plano(campo, plano, tempo)
                
                data_partida = data_base + timedelta(days=idx-1)
                
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
                
                if idx % 10 == 0:
                    f.write(f"  > Criadas {idx}/{len(partidas_criar)} partidas...\n")
                    f.flush()
                
                counter += 1
            
            db.session.commit()
            
            f.write(f"\nOK SUCESSO! {len(resultado)} partidas criadas com sucesso!\n")
            f.write("="*60 + "\n\n")
            
            # Amostra
            f.write("AMOSTRA DAS PARTIDAS CRIADAS:\n\n")
            f.write(f"{'#':<5} {'Campo':<12} {'Plano':<12} {'Tempo':<20} {'Modo':<15} {'Valor':<8} {'BB':<6}\n")
            f.write("-" * 85 + "\n")
            for i, p in enumerate(resultado):
                if i < 5 or i >= len(resultado) - 5:
                    f.write(f"{p['numero']:<5} {p['campo']:<12} {p['plano']:<12} {p['tempo']:<20} {p['modo']:<15} R${p['valor']:<7} {p['bbs']:<6}\n")
                elif i == 5:
                    f.write("...\n")
            
            f.write("\n" + "="*60 + "\n")
            
        except Exception as e:
            f.write(f"\nERRO: {str(e)}\n")
            import traceback
            traceback.print_exc(file=f)
            db.session.rollback()

print("Script finalizado! Verifique criar_partidas_output.txt")
