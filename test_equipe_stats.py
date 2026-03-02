from app import app, db
from models import Equipe, Partida, PartidaParticipante

with app.app_context():
    print("===== TESTE DE ESTATÍSTICAS POR EQUIPE =====\n")
    
    # Buscar equipe spartas
    equipe_spartas = Equipe.query.filter(Equipe.nome.ilike('spartas')).first()
    
    if equipe_spartas:
        print(f"Equipe: {equipe_spartas.nome} (ID: {equipe_spartas.id})\n")
        
        # Buscar partidas em modo equipe finalizadas
        partidas_equipe = Partida.query.filter_by(
            tipo_participacao='equipe',
            finalizada=True
        ).all()
        
        print(f"Total de partidas equipe finalizadas: {len(partidas_equipe)}\n")
        
        partidas_encontradas = []
        total_vitorias = 0
        total_derrotas = 0
        total_empates = 0
        
        for partida in partidas_equipe:
            # Verificar se a equipe participou (case-insensitive)
            participantes_equipe = [p for p in partida.participantes if p.equipe and p.equipe.lower() == equipe_spartas.nome.lower()]
            
            if participantes_equipe:
                print(f"Partida encontrada: {partida.nome} (ID: {partida.id})")
                print(f"  Vencedora: {partida.equipe_vencedora}")
                print(f"  Participantes de {equipe_spartas.nome}:")
                for p in participantes_equipe:
                    print(f"    - {p.warname} ({p.nome_operador}) - Equipe: {p.equipe}")
                
                # Determinar resultado
                equipe_vencedora_lower = partida.equipe_vencedora.lower() if partida.equipe_vencedora else None
                equipe_nome_lower = equipe_spartas.nome.lower()
                
                if equipe_vencedora_lower == equipe_nome_lower:
                    resultado = 'VITÓRIA'
                    total_vitorias += 1
                elif partida.equipe_vencedora and equipe_vencedora_lower != equipe_nome_lower:
                    resultado = 'DERROTA'
                    total_derrotas += 1
                else:
                    resultado = 'EMPATE'
                    total_empates += 1
                
                print(f"  Resultado: {resultado}\n")
                partidas_encontradas.append(partida.id)
        
        print("===== RESUMO =====")
        print(f"Partidas encontradas: {len(partidas_encontradas)}")
        print(f"Vitórias: {total_vitorias}")
        print(f"Derrotas: {total_derrotas}")
        print(f"Empates: {total_empates}")
        print(f"Total: {total_vitorias + total_derrotas + total_empates}")
    else:
        print("Equipe 'spartas' não encontrada!")
