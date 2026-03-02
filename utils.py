# utils.py
from datetime import datetime
from models import Operador, db  # ← IMPORT CORRIGIDO
import logging

# Cores do tema (para CSS)
COR_LARANJA = "#FF6B00"
COR_LARANJA_ESCURO = "#CC5500"
COR_PRETA = "#1A1A1A"
COR_CINZA_ESCURO = "#2D2D2D"
COR_CINZA_CLARO = "#3D3D3D"
COR_VERDE = "#00C851"
COR_VERMELHO = "#FF4444"

# Dicionários com os planos (MANTIDO IGUAL DO SEU CÓDIGO)
PLANOS_WARFIELD = {
    "Avulso": {
        "tempos": ["10 min", "20 min", "30 min", "60 min", "30 min*", "60 min*"],
        "bbs": [100, 200, 200, 400, 200, 400],
        "valores": [10, 20, 25, 40, 160, 280]
    },
    "Equipe": {
        "tempos": ["60¹ min", "60² min", "60³ min"],
        "bbs": [0, 200, 400],
        "valores": [160, 200, 240]
    },
    "Sua Arma": {
        "tempos": ["10 min", "60¹ min", "120¹ min", "150 min", "180¹ min", "60² min", "120² min", "180² min"],
        "bbs": [0, 0, 0, 0, 0, 0, 0, 0],
        "valores": [5, 15, 25, 35, 40, 80, 140, 250]
    }
}

PLANOS_REDLINE = {
    "Rifle": {
        "tempos": ["5 min", "5 min*", "10 min", "15 min"],
        "bbs": [50, 100, 200, 300],
        "valores": [5, 10, 15, 25]
    },
    "Pistola": {
        "tempos": ["5 min", "10 min"],
        "bbs": [50, 100],
        "valores": [5, 10]
    }
}

MODOS_PARTIDA = [
    "ONE LIFE", "PVP INFINITY", "CAPTURA DE BANDEIRA", 
    "PEGA REFÉM", "PLANTAÇÃO DE BOMBA", "INFECTADO", 
    "CAÇA AO VIP", "CAÇADA NOTURNA"
]

# Dicionário de modos permitidos por tempo
MODOS_POR_TEMPO = {
    "10 min": ["PVP INFINITY", "CAÇADA NOTURNA"],
    "20 min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA", "CAÇA AO VIP"],
    "30 min": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "PLANTAÇÃO DE BOMBA"],
    "60 min": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "PLANTAÇÃO DE BOMBA"],
    "30 min*": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "PLANTAÇÃO DE BOMBA"],
    "60 min*": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "PLANTAÇÃO DE BOMBA"],
    "60¹ min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA"],
    "60² min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA"],
    "60³ min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA"],
    "120¹ min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA"],
    "150 min": ["PVP INFINITY", "ONE LIFE"],
    "180¹ min": ["PVP INFINITY", "ONE LIFE"],
    "5 min": ["PVP INFINITY"],
    "5 min*": ["PVP INFINITY"],
    "15 min": ["PVP INFINITY", "ONE LIFE"],
}

def get_valores_plano(campo, plano, tempo):
    """Retorna valor e BBs para um plano/tempo específico"""
    if campo == "Warfield" and plano in PLANOS_WARFIELD:
        planos = PLANOS_WARFIELD[plano]
        if tempo in planos["tempos"]:
            idx = planos["tempos"].index(tempo)
            return planos["valores"][idx], planos["bbs"][idx]
    elif campo == "Redline" and plano in PLANOS_REDLINE:
        planos = PLANOS_REDLINE[plano]
        if tempo in planos["tempos"]:
            idx = planos["tempos"].index(tempo)
            return planos["valores"][idx], planos["bbs"][idx]
    return 0, 0

def get_modos_permitidos(tempo, plano=None):
    """Retorna modos permitidos para um tempo e plano
    CAÇADA NOTURNA é exclusiva para Avulso/10 min
    """
    tempo_base = tempo.replace("*", "").strip()
    modos = MODOS_POR_TEMPO.get(tempo_base, MODOS_PARTIDA)
    
    # CAÇADA NOTURNA só aparece para Avulso com 10 min
    if "CAÇADA NOTURNA" in modos:
        # Se o plano é diferente de "Avulso" ou o tempo não é "10 min", remove CAÇADA NOTURNA
        if plano != "Avulso" or tempo_base != "10 min":
            modos = [m for m in modos if m != "CAÇADA NOTURNA"]
    
    return modos

def format_brl(valor):
    """Formata valor em reais"""
    return f"R$ {valor:.2f}".replace('.', ',')

def parse_brl(valor_str):
    """Converte string BRL para float"""
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    return float(valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip())

# ==================== FUNÇÃO CORRIGIDA (SEM IMPORT DO APP) ====================
def sincronizar_user_operador(user):
    """Garante que usuário e operador estejam sincronizados"""
    try:
        # Buscar operador pelo warname
        operador = Operador.query.filter_by(warname=user.username).first()
        
        if not operador:
            # Criar novo operador se não existir
            print(f"🔧 Criando operador para usuário {user.username}")
            
            operador = Operador(
                nome=user.nome,
                warname=user.username,
                cpf=user.cpf or '',
                email=user.email,
                telefone=user.telefone or '',
                data_nascimento=user.data_nascimento or '',
                idade=str(user.idade) if user.idade else '',
                battlepass='NAO'
            )
            db.session.add(operador)
            db.session.flush()
            
            # Vincular ao usuário
            user.operador_id = operador.id
            
            # Registrar log (import aqui para evitar circular)
            from models import Log
            log = Log(
                usuario=user.username,
                acao='OPERADOR_CRIADO_AUTO',
                detalhes=f"Operador criado automaticamente para usuário {user.username}"
            )
            db.session.add(log)
            
        else:
            # Vincular se não estiver vinculado
            if not user.operador_id:
                user.operador_id = operador.id
            
            # Atualizar dados do operador se necessário
            precisa_atualizar = False
            
            if operador.nome != user.nome:
                operador.nome = user.nome
                precisa_atualizar = True
                
            if user.email and operador.email != user.email:
                operador.email = user.email
                precisa_atualizar = True
                
            if user.cpf and operador.cpf != user.cpf:
                operador.cpf = user.cpf
                precisa_atualizar = True
                
            if user.telefone and operador.telefone != user.telefone:
                operador.telefone = user.telefone
                precisa_atualizar = True
            
            if precisa_atualizar:
                print(f"🔄 Atualizando dados do operador {operador.warname}")
        
        db.session.commit()
        return operador
        
    except Exception as e:
        db.session.rollback()
        print(f'❌ Erro ao sincronizar user/operador: {str(e)}')
        return None

# ==================== FUNÇÃO AUXILIAR PARA VERIFICAR CONSISTÊNCIA ====================
def verificar_consistencia_user_operador():
    """
    Verifica se todos os usuários têm operadores correspondentes
    """
    from models import User  # Import aqui para evitar circular
    
    inconsistencias = []
    
    users = User.query.filter_by(status='aprovado').all()
    
    for user in users:
        operador = Operador.query.filter_by(warname=user.username).first()
        
        if not operador:
            inconsistencias.append({
                'user_id': user.id,
                'username': user.username,
                'problema': 'Sem operador associado'
            })
        else:
            # Verificar dados inconsistentes
            if operador.nome != user.nome:
                inconsistencias.append({
                    'user_id': user.id,
                    'username': user.username,
                    'problema': f'Nome diferente: User="{user.nome}", Operador="{operador.nome}"'
                })
            
            # Verificar se o vínculo está correto
            if user.operador_id != operador.id:
                inconsistencias.append({
                    'user_id': user.id,
                    'username': user.username,
                    'problema': f'Vínculo incorreto: operador_id={user.operador_id}, deveria ser {operador.id}'
                })
    
    return inconsistencias

# ==================== SINCRONIZAÇÃO DE ESTATÍSTICAS ====================
def sincronizar_estatisticas_operadores():
    """
    Sincroniza as estatísticas dos operadores removendo registros órfãos
    e recalculando as estatísticas baseado no que existe de verdade.
    
    Chamada quando partidas são deletadas diretamente do banco.
    """
    from models import PartidaParticipante, Partida, Operador
    
    try:
        logging.info("🔄 Iniciando sincronização de estatísticas dos operadores...")
        
        # 1. ENCONTRAR E REMOVER PARTICIPANTES ÓRFÃOS
        participantes_orfaos = PartidaParticipante.query.filter(
            ~PartidaParticipante.partida_id.in_(
                db.session.query(Partida.id)
            )
        ).all()
        
        orfaos_removidos = len(participantes_orfaos)
        for pp in participantes_orfaos:
            logging.info(f"🗑️ Removendo participante órfão (id={pp.id}, operador_id={pp.operador_id})")
            db.session.delete(pp)
        
        if orfaos_removidos > 0:
            db.session.commit()
            logging.info(f"✅ {orfaos_removidos} participante(s) órfão(s) removido(s)")
        
        # 2. RECALCULAR ESTATÍSTICAS DE TODOS OS OPERADORES
        operadores = Operador.query.all()
        operadores_atualizados = 0
        
        for operador in operadores:
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
            
            # Somar estatísticas de cada participação
            for pp in participantes:
                # Verificar se a partida ainda existe (precaução extra)
                partida = Partida.query.get(pp.partida_id)
                if not partida:
                    logging.warning(f"⚠️ Partida {pp.partida_id} do participante {pp.id} não existe, removendo...")
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
            
            if operadores_atualizados % 10 == 0:
                logging.info(f"  ✓ {operadores_atualizados} operador(es) recalculado(s)...")
            
            operadores_atualizados += 1
        
        db.session.commit()
        logging.info(f"✅ Sincronização completa! {operadores_atualizados} operador(es) recalculado(s)")
        
        return {
            'sucesso': True,
            'orfaos_removidos': orfaos_removidos,
            'operadores_recalculados': operadores_atualizados,
            'mensagem': f'✅ Sincronização concluída: {orfaos_removidos} registros órfãos removidos, {operadores_atualizados} operadores recalculados'
        }
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'❌ Erro na sincronização: {str(e)}')
        return {
            'sucesso': False,
            'mensagem': f'❌ Erro na sincronização: {str(e)}'
        }

def remover_estadisticas_partida(partida):
    """
    Remove as estatísticas de uma partida das estatísticas dos operadores.
    Deve ser chamado ANTES de deletar a partida.
    
    Args:
        partida: Objeto Partida a ter suas stats removidas
    """
    try:
        for participante in partida.participantes:
            operador = participante.operador
            if operador:
                # Remover kills/deaths
                operador.total_kills = max(0, (operador.total_kills or 0) - (participante.kills or 0))
                operador.total_deaths = max(0, (operador.total_deaths or 0) - (participante.deaths or 0))
                
                # Remover outras estatísticas
                operador.total_capturas = max(0, (operador.total_capturas or 0) - (participante.capturas or 0))
                operador.total_plantas_bomba = max(0, (operador.total_plantas_bomba or 0) - (participante.plantou_bomba or 0))
                operador.total_desarmes_bomba = max(0, (operador.total_desarmes_bomba or 0) - (participante.desarmou_bomba or 0))
                operador.total_refens = max(0, (operador.total_refens or 0) - (participante.refens or 0))
                operador.total_cacos = max(0, (operador.total_cacos or 0) - (participante.cacou or 0))
                operador.total_partidas = max(0, (operador.total_partidas or 0) - 1)
                
                # Remover vitória/derrota
                if participante.resultado == 'vitoria':
                    operador.total_vitorias = max(0, (operador.total_vitorias or 0) - 1)
                elif participante.resultado == 'derrota':
                    operador.total_derrotas = max(0, (operador.total_derrotas or 0) - 1)
                
                # Remover MVP
                if participante.mvp:
                    operador.total_mvps = max(0, (operador.total_mvps or 0) - 1)
                
                logging.info(f"📊 Estatísticas de {operador.warname} atualizadas (partida removida)")
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'❌ Erro ao remover estatísticas da partida: {str(e)}')
        return False