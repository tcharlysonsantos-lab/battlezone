from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import json

db = SQLAlchemy()

# ==================== TABELA DE ASSOCIAÇÃO ====================
class EquipeMembros(db.Model):
    __tablename__ = 'equipe_membros'
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), primary_key=True)
    operador_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== MODELO DE USUÁRIO ====================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.String(10), nullable=True)
    idade = db.Column(db.Integer, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    nivel = db.Column(db.String(20), nullable=False, default='operador')
    status = db.Column(db.String(20), default='pendente')
    tentativas = db.Column(db.Integer, default=0)
                
    session_token = db.Column(db.String(100), unique=True, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(80), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    partidas_criadas = db.relationship('Partida', back_populates='criador', lazy=True, foreign_keys='Partida.created_by')

    # Relacionamento com Operador
    operador_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=True)
    operador = db.relationship('Operador', backref='usuario', uselist=False)
    
    # ==================== 2FA FIELDS ====================
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)  # Segredo TOTP em base32
    backup_codes = db.Column(db.Text, nullable=True)  # JSON com códigos de backup
    two_factor_verified_at = db.Column(db.DateTime, nullable=True)
    
    # ==================== PASSWORD RESET FIELDS ====================
    password_reset_token = db.Column(db.String(100), unique=True, nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    # ==================== TERMS OF SERVICE FIELDS ====================
    terms_accepted = db.Column(db.Boolean, default=False)
    terms_accepted_date = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'salt' not in kwargs:
            self.salt = secrets.token_hex(16)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password + self.salt)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password + self.salt)
    
    def generate_session_token(self):
        self.session_token = secrets.token_urlsafe(32)
        self.last_activity = datetime.utcnow()
        return self.session_token
    
    def is_session_valid(self):
        if self.nivel == 'operador':
            if not self.last_activity:
                return False
            time_diff = datetime.utcnow() - self.last_activity
            return time_diff.total_seconds() < 1800  # 30 minutos
        return True
    
    def update_activity(self):
        """Atualiza atividade - OTIMIZADO: só atualiza a cada 30s"""
        self.last_activity = datetime.utcnow()
        # Mark for batch update - commit deve ser feito manualmente ou ao final da request
        db.session.add(self)
        # Não fazer commit automático aqui - deixar para depois_request
    
    def tem_permissao(self, recurso):
        """
        Verifica se o usuário tem permissão para acessar um recurso
        
        Args:
            recurso (str): Nome do recurso (ex: 'operadores', 'partidas', 'dashboard')
        
        Returns:
            bool: True se tem permissão, False caso contrário
        """
        # Admin tem acesso a TUDO
        if self.nivel == 'admin':
            return True
        
        # Gerente tem acesso a quase tudo (exceto áreas administrativas)
        if self.nivel == 'gerente':
            recursos_gerente = [
                'dashboard', 'operadores', 'equipes', 'partidas', 
                'calendario', 'estatisticas', 'vendas', 'caixa', 'estoque'
            ]
            return recurso in recursos_gerente
        
        # Financeiro - acesso apenas a finanças
        if self.nivel == 'financeiro':
            recursos_financeiro = ['dashboard', 'vendas', 'caixa', 'estoque']
            return recurso in recursos_financeiro
        
        # Operador - acesso básico
        if self.nivel == 'operador':
            recursos_operador = ['dashboard', 'partidas', 'calendario', 'estatisticas']
            return recurso in recursos_operador
        
        # Qualquer outro nível (ex: 'pendente') não tem acesso
        return False
    
    # ==================== 2FA METHODS ====================
    def setup_2fa(self):
        """Inicia setup de 2FA (gera secret)"""
        from .auth_security import gerar_secret_2fa, gerar_backup_codes
        
        self.two_factor_secret = gerar_secret_2fa()
        backup_codes = gerar_backup_codes()
        self.backup_codes = json.dumps(backup_codes)
        self.two_factor_enabled = False  # Só ativa após confirmar código
        
        db.session.commit()
        return self.two_factor_secret, backup_codes
    
    def confirm_2fa(self):
        """Confirma e ativa 2FA após validação de código"""
        self.two_factor_enabled = True
        self.two_factor_verified_at = datetime.utcnow()
        db.session.commit()
    
    def disable_2fa(self):
        """Desativa 2FA"""
        self.two_factor_enabled = False
        self.two_factor_secret = None
        self.backup_codes = None
        db.session.commit()
    
    def usar_backup_code(self, code):
        """
        Usa um backup code para login sem autenticador
        Remove o código após usar (one-time use)
        """
        if not self.backup_codes:
            return False
        
        try:
            codes = json.loads(self.backup_codes)
            if code in codes:
                codes.remove(code)
                self.backup_codes = json.dumps(codes)
                db.session.commit()
                return True
        except:
            pass
        
        return False
    
    def gerar_password_reset_token(self):
        """Gera token para reset de senha com validade de 30 minutos"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
        return self.password_reset_token
    
    def validar_password_reset_token(self, token):
        """Valida token de reset (não expirou? é o token correto?)"""
        if not self.password_reset_token or self.password_reset_token != token:
            return False
        
        if not self.password_reset_expires or datetime.utcnow() > self.password_reset_expires:
            return False
        
        return True
    
    def resetar_senha(self, nova_senha):
        """Reseta a senha e limpa o token"""
        self.set_password(nova_senha)
        self.password_reset_token = None
        self.password_reset_expires = None
        db.session.commit()


# ==================== FUNÇÃO DE VERIFICAÇÃO ====================
def verificar_consistencia_user_operador():
    """
    Verifica se todos os usuários têm operadores correspondentes
    """
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
            if operador.nome != user.nome:
                inconsistencias.append({
                    'user_id': user.id,
                    'username': user.username,
                    'problema': f'Nome diferente: User="{user.nome}", Operador="{operador.nome}"'
                })
    
    return inconsistencias


# ==================== MODELO DE SOLICITAÇÕES ====================
class Solicitacao(db.Model):
    __tablename__ = 'solicitacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), nullable=False, unique=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    cpf = db.Column(db.String(14), nullable=False, unique=True)
    telefone = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.String(10), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    nivel = db.Column(db.String(20), default='operador')
    password_hash = db.Column(db.String(200), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(20), default='pendente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(80), nullable=True)
    
    # ==================== TERMS OF SERVICE FIELDS ====================
    terms_accepted = db.Column(db.Boolean, default=False)
    terms_accepted_date = db.Column(db.DateTime, nullable=True)


# ==================== MODELO DE OPERADOR ====================
class Operador(db.Model):
    __tablename__ = 'operadores'
    
    id = db.Column(db.Integer, primary_key=True)
    old_id = db.Column(db.String(50), unique=True, nullable=True)
    
    nome = db.Column(db.String(120), nullable=False, unique=True)
    warname = db.Column(db.String(80), unique=True, nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.String(20), nullable=True)
    idade = db.Column(db.String(10), nullable=True)
    battlepass = db.Column(db.String(50), nullable=True)  # NULL, 'OPERADOR', 'ELITE_CAVEIRA'
    
    def get_battlepass_info(self):
        """Retorna nome e emoji do battlepass"""
        battlepass_config = {
            'OPERADOR': {'nome': 'Battlepass Operador', 'emoji': '🎖️'},
            'ELITE_CAVEIRA': {'nome': 'Battlepass Elite-Caveira', 'emoji': '☠️'},
        }
        if self.battlepass in battlepass_config:
            config = battlepass_config[self.battlepass]
            return f"{config['emoji']} {config['nome']}"
        return None
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Estatísticas
    total_kills = db.Column(db.Integer, default=0)
    total_deaths = db.Column(db.Integer, default=0)
    total_vitorias = db.Column(db.Integer, default=0)
    total_derrotas = db.Column(db.Integer, default=0)
    total_mvps = db.Column(db.Integer, default=0)
    total_capturas = db.Column(db.Integer, default=0)
    total_plantas_bomba = db.Column(db.Integer, default=0)
    total_desarmes_bomba = db.Column(db.Integer, default=0)
    total_refens = db.Column(db.Integer, default=0)
    total_cacos = db.Column(db.Integer, default=0)
    total_partidas = db.Column(db.Integer, default=0)
    
    # Relacionamentos
    membro_equipes = db.relationship('Equipe', secondary='equipe_membros', back_populates='membros')
    partidas = db.relationship('PartidaParticipante', back_populates='operador', foreign_keys='PartidaParticipante.operador_id')
    

# ==================== MODELO DE EQUIPE ====================
class Equipe(db.Model):
    __tablename__ = 'equipes'
    
    id = db.Column(db.Integer, primary_key=True)
    old_id = db.Column(db.String(50), unique=True, nullable=True)
    
    nome = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(200), nullable=True)
    battlepass = db.Column(db.String(50), nullable=True)  # NULL, 'EQUIPE_BASICA'
    capitao_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=True)
    
    def get_battlepass_info(self):
        """Retorna nome e emoji do battlepass"""
        battlepass_config = {
            'EQUIPE_BASICA': {'nome': 'Battlepass Equipe Básica', 'emoji': '🛡️'},
        }
        if self.battlepass in battlepass_config:
            config = battlepass_config[self.battlepass]
            return f"{config['emoji']} {config['nome']}"
        return None
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    capitao = db.relationship('Operador', foreign_keys=[capitao_id])
    membros = db.relationship('Operador', secondary='equipe_membros', back_populates='membro_equipes', lazy='dynamic')


# ==================== MODELO DE PARTIDA ====================
class Partida(db.Model):
    __tablename__ = 'partidas'
    
    id = db.Column(db.Integer, primary_key=True)
    old_id = db.Column(db.String(50), unique=True, nullable=True)
    
    # Dados da partida
    nome = db.Column(db.String(100), nullable=False)
    data = db.Column(db.String(20), nullable=False, index=True)  # ✅ ÍNDICE: busca frequente por data
    horario = db.Column(db.String(10), nullable=False)
    campo = db.Column(db.String(20), nullable=False)
    plano = db.Column(db.String(50), nullable=False)
    tempo = db.Column(db.String(20), nullable=False)
    modo = db.Column(db.String(50), nullable=False)
    tipo_participacao = db.Column(db.String(20), default='individual')
    
    # Valores
    valor_total = db.Column(db.Float, default=0)
    valor_por_participante = db.Column(db.Float, default=0)
    bbs_por_pessoa = db.Column(db.Integer, default=0)
    total_bbs = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='Agendada')
    finalizada = db.Column(db.Boolean, default=False, index=True)  # ✅ ÍNDICE: filtro frequente
    
    # Resultado (para modo equipe)
    equipe_vencedora = db.Column(db.String(20), nullable=True)
    placar_equipe1 = db.Column(db.Integer, default=0)
    placar_equipe2 = db.Column(db.Integer, default=0)
    mvp_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=True)
    
    # Campo de pagamento
    pagamento = db.Column(db.String(20), default='Pendente')
    
    # Controle de concorrência
    version = db.Column(db.Integer, default=1)
    locked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    locked_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relacionamentos
    mvp = db.relationship('Operador', foreign_keys=[mvp_id])
    criador = db.relationship('User', foreign_keys=[created_by], back_populates='partidas_criadas')
    participantes = db.relationship('PartidaParticipante', back_populates='partida', cascade='all, delete-orphan')
    
    def lock(self, user_id):
        """Trava a partida para edição"""
        if self.locked_by and self.locked_by != user_id:
            if self.locked_at:
                lock_time = datetime.utcnow() - self.locked_at
                if lock_time.total_seconds() < 300:
                    return False
        self.locked_by = user_id
        self.locked_at = datetime.utcnow()
        db.session.commit()
        return True
    
    def unlock(self):
        """Destrava a partida"""
        self.locked_by = None
        self.locked_at = None
        db.session.commit()
        

# ==================== MODELO DE PARTICIPANTE ====================
class PartidaParticipante(db.Model):
    __tablename__ = 'partida_participantes'
    
    id = db.Column(db.Integer, primary_key=True)
    partida_id = db.Column(db.Integer, db.ForeignKey('partidas.id'), nullable=False)
    operador_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=False)
    
    warname = db.Column(db.String(80))
    nome_operador = db.Column(db.String(120))
    equipe = db.Column(db.String(50), nullable=True)
    
    # Estatísticas detalhadas
    kills = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    capturas = db.Column(db.Integer, default=0)
    plantou_bomba = db.Column(db.Integer, default=0)
    desarmou_bomba = db.Column(db.Integer, default=0)
    refens = db.Column(db.Integer, default=0)
    cacou = db.Column(db.Integer, default=0)
    resultado = db.Column(db.String(20), nullable=True)
    mvp = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    partida = db.relationship('Partida', back_populates='participantes')
    operador = db.relationship('Operador', back_populates='partidas', foreign_keys=[operador_id])


# ==================== MODELO DE VENDA ====================
class Venda(db.Model):
    __tablename__ = 'vendas'
    
    id = db.Column(db.Integer, primary_key=True)
    old_id = db.Column(db.String(50), unique=True, nullable=True)
    
    partida_id = db.Column(db.Integer, db.ForeignKey('partidas.id'), nullable=True)
    warname = db.Column(db.String(80), nullable=True)
    nome_operador = db.Column(db.String(120), nullable=True)
    
    nome_partida = db.Column(db.String(100), nullable=True)
    produto = db.Column(db.String(100), nullable=False)
    cliente = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    valor = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='Pendente')
    tipo = db.Column(db.String(50), default='Venda')
    data = db.Column(db.String(20), nullable=False)
    pagamento = db.Column(db.String(50), default='A definir')
    bbs = db.Column(db.Integer, default=0)
    
    quantidade = db.Column(db.Float, default=0)
    unidade = db.Column(db.String(10), default='un')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== MODELO DE ESTOQUE ====================
class Estoque(db.Model):
    __tablename__ = 'estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    old_id = db.Column(db.String(50), unique=True, nullable=True)
    
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Float, default=0, index=True)  # ✅ ÍNDICE: busca produtos com baixo estoque
    unidade = db.Column(db.String(10), default='un')
    quantidade_minima = db.Column(db.Float, default=0)
    custo = db.Column(db.Float, default=0)
    preco_venda = db.Column(db.Float, default=0)
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data = db.Column(db.String(20), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== MODELO DE LOG ====================
class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(80), nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    detalhes = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)


# ==================== MODELO DE PAGAMENTO DE OPERADOR ====================
class PagamentoOperador(db.Model):
    __tablename__ = 'pagamento_operador'
    
    id = db.Column(db.Integer, primary_key=True)
    operador_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=False)
    partida_id = db.Column(db.Integer, db.ForeignKey('partidas.id'), nullable=True)  # NULL = pagamento geral
    
    valor = db.Column(db.Float, nullable=False)  # Valor esperado
    valor_pago = db.Column(db.Float, default=0)  # Valor realmente pago
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Parcial, Pago, Cancelado
    
    # Rastreamento
    data_vencimento = db.Column(db.DateTime, nullable=True)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    metodo_pagamento = db.Column(db.String(50), nullable=True)  # PIX, Dinheiro, Débito, Crédito
    registrado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Quem registrou
    observacoes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    operador = db.relationship('Operador', backref='pagamentos')
    partida = db.relationship('Partida', backref='pagamentos_operadores')
    registrador = db.relationship('User', backref='pagamentos_registrados')
    
    def marcar_pago(self, valor=None, metodo=None, usuario=None):
        """Marca o pagamento como realizado"""
        if valor is None:
            valor = self.valor
        
        self.status = 'Pago' if valor >= self.valor else 'Parcial'
        self.valor_pago = valor
        self.data_pagamento = datetime.utcnow()
        self.metodo_pagamento = metodo
        self.registrado_por = usuario
        db.session.commit()
    
    def pendente(self):
        """Retorna quanto ainda está pendente"""
        return max(0, self.valor - self.valor_pago)
    
    def __repr__(self):
        return f"<PagamentoOperador {self.operador.warname} - {self.status}>"


# ==================== MODELO DE BATTLEPASS ====================
class Battlepass(db.Model):
    __tablename__ = 'battlepasses'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tipo de battlepass
    tipo = db.Column(db.String(50), nullable=False)  # 'operador_basico', 'operador_elite', 'equipe_basica'
    nome = db.Column(db.String(120), nullable=False)  # "Battlepass Operador", "Battlepass Elite-Caveira", "Battlepass Equipe Basica"
    descricao = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.String(20), nullable=False)  # 'operador' ou 'equipe'
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    sorteios = db.relationship('Sorteio', back_populates='battlepass', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Battlepass {self.nome}>"


# ==================== MODELO DE SORTEIO ====================
class Sorteio(db.Model):
    __tablename__ = 'sorteios'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamento com battlepass
    battlepass_id = db.Column(db.Integer, db.ForeignKey('battlepasses.id'), nullable=False)
    
    # Semana/Mês
    mes = db.Column(db.Integer, nullable=False)  # 1-12
    ano = db.Column(db.Integer, nullable=False)
    semana = db.Column(db.Integer, nullable=True)  # 1-4, NULL significa resultado do mês
    
    # Resultado do sorteio
    operador_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=True)  # Se for operador
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=True)  # Se for equipe
    
    # Quem realizou o sorteio
    sorteado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sorteado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status
    deletado = db.Column(db.Boolean, default=False)
    deletado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    deletado_em = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    battlepass = db.relationship('Battlepass', back_populates='sorteios')
    operador = db.relationship('Operador', backref='sorteios')
    equipe = db.relationship('Equipe', backref='sorteios')
    usuario_sorteio = db.relationship('User', foreign_keys=[sorteado_por], backref='sorteios_realizados')
    usuario_delecao = db.relationship('User', foreign_keys=[deletado_por], backref='sorteios_deletados')
    
    def __repr__(self):
        return f"<Sorteio {self.battlepass.nome} - Mês {self.mes}/{self.ano}>"


# ==================== MODELO DE EVENTO ====================
class Evento(db.Model):
    __tablename__ = 'eventos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações básicas
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_evento = db.Column(db.DateTime, nullable=False)  # Data e hora do evento
    
    # Campo do evento (Warfield, Redline, ou geral)
    campo = db.Column(db.String(50), default='GERAL')  # 'Warfield', 'Redline', 'GERAL'
    
    # Preço
    valor_pessoa = db.Column(db.Float, nullable=True)  # Valor por pessoa
    valor_individual = db.Column(db.Float, nullable=True)  # Valor individual si é diferente
    tipo_cobranca = db.Column(db.String(20), default='POR_PESSOA')  # 'POR_PESSOA' ou 'INDIVIDUAL'
    
    # Fotos (JSON com lista de paths)
    fotos = db.Column(db.Text, nullable=True)  # JSON: ["foto1.jpg", "foto2.jpg", ...]
    
    # Criado por
    criado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    deletado = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    brindes = db.relationship('EventoBrinde', back_populates='evento', cascade='all, delete-orphan')
    criador = db.relationship('User', backref='eventos_criados', foreign_keys=[criado_por])
    
    def get_fotos_lista(self):
        """Retorna lista de fotos ou lista vazia"""
        if not self.fotos:
            return []
        try:
            return json.loads(self.fotos)
        except:
            return []
    
    @property
    def fotos_list(self):
        """Property que retorna fotos como lista (para uso no template)"""
        return self.get_fotos_lista()
    
    def __repr__(self):
        return f"<Evento {self.nome} - {self.data_evento}>"


# ==================== MODELO DE BRINDE DE EVENTO ====================
class EventoBrinde(db.Model):
    __tablename__ = 'evento_brindes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamento com evento
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    
    # Informação do brinde
    descricao = db.Column(db.String(255), nullable=False)
    ordem = db.Column(db.Integer, default=0)  # Para ordenar brindes
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    evento = db.relationship('Evento', back_populates='brindes')
    
    def __repr__(self):
        return f"<EventoBrinde {self.descricao}>"
