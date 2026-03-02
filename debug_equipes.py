from app import app, db
from models import Equipe, Partida, PartidaParticipante

with app.app_context():
    print("===== EQUIPES NO BANCO =====")
    equipes = Equipe.query.all()
    for eq in equipes:
        print(f"ID: {eq.id}, Nome: '{eq.nome}'")
    
    print("\n===== PARTIDAS EM MODO EQUIPE =====")
    partidas = Partida.query.filter_by(tipo_participacao='equipe').all()
    for p in partidas:
        print(f"\nPartida ID {p.id}: {p.nome} (Vencedora: {p.equipe_vencedora})")
        print("  Participantes:")
        for participant in p.participantes:
            print(f"    - {participant.warname} ({participant.nome_operador}): equipe='{participant.equipe}'")
