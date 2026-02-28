# utils.py
from datetime import datetime

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
    "20 min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA", "CAÇA AO VIP", "CAÇADA NOTURNA"],
    "30 min": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "CAÇADA NOTURNA", "PLANTAÇÃO DE BOMBA"],
    "60 min": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "CAÇADA NOTURNA", "PLANTAÇÃO DE BOMBA"],
    "30 min*": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "CAÇADA NOTURNA", "PLANTAÇÃO DE BOMBA"],
    "60 min*": ["PVP INFINITY", "ONE LIFE", "PEGA REFÉM", "CAÇA AO VIP", "CAPTURA DE BANDEIRA", "CAÇADA NOTURNA", "PLANTAÇÃO DE BOMBA"],
    "60¹ min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA", "CAÇADA NOTURNA"],
    "60² min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA", "CAÇADA NOTURNA"],
    "60³ min": ["PVP INFINITY", "ONE LIFE", "CAPTURA DE BANDEIRA", "CAÇADA NOTURNA"],
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

def get_modos_permitidos(tempo):
    """Retorna modos permitidos para um tempo"""
    tempo_base = tempo.replace("*", "").strip()
    return MODOS_POR_TEMPO.get(tempo_base, MODOS_PARTIDA)

def format_brl(valor):
    """Formata valor em reais"""
    return f"R$ {valor:.2f}".replace('.', ',')
# Adicionar em utils.py

def sincronizar_user_operador(user):
    """Garante que usuário e operador estejam sincronizados"""
    if not user.operador:
        # Criar operador se não existir
        operador = Operador.query.filter_by(warname=user.username).first()
        if not operador:
            operador = Operador(
                nome=user.nome,
                warname=user.username,
                cpf=user.cpf,
                email=user.email,
                telefone=user.telefone,
                data_nascimento=user.data_nascimento,
                idade=str(user.idade) if user.idade else '',
                battlepass='NAO'
            )
            db.session.add(operador)
            db.session.flush()
        
        user.operador_id = operador.id
    
    return user.operador

def parse_brl(valor_str):
    """Converte string BRL para float"""
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    return float(valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip())