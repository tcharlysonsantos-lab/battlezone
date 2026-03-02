from app import app, db
from models import Partida, PartidaParticipante, Equipe

with app.app_context():
    print("===== VERIFICAÇÃO DE PARTIDAS COM EQUIPES =====\n")
    
    # Buscar todas as partidas em modo equipe
    partidas_equipe = Partida.query.filter_by(tipo_participacao='equipe').all()
    
    print(f"Total de partidas em modo equipe: {len(partidas_equipe)}\n")
    
    for partida in partidas_equipe:
        print(f"Partida ID {partida.id}: {partida.nome}")
        print(f"  Data: {partida.data} - Horário: {partida.horario}")
        print(f"  Finalizada: {'Sim' if partida.finalizada else 'Não'}")
        print(f"  Vencedora: {partida.equipe_vencedora}")
        print(f"  Participantes:")
        
        equipes_envolvidas = {}
        for participante in partida.participantes:
            equipe = participante.equipe or 'Sem equipe'
            if equipe not in equipes_envolvidas:
                equipes_envolvidas[equipe] = []
            equipes_envolvidas[equipe].append(participante.warname)
        
        for equipe, membros in equipes_envolvidas.items():
            print(f"    - {equipe}: {', '.join(membros)}")
        
        print()
