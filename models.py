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

    # ✅ NOVO - Relacionamento com Operador
    operador_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=True)
    operador = db.relationship('Operador', backref='usuario', uselist=False)
    
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
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def tem_permissao(self, recurso):
        if self.nivel in ['admin', 'gerente']:
            return True
        
        permissoes = {
            'financeiro': ['dashboard', 'vendas', 'caixa', 'estoque'],
            'operador': ['dashboard', 'partidas', 'estatisticas']
        }
        
        return recurso in permissoes.get(self.nivel, [])

# ============================================
# ✅ FUNÇÃO FORA DA CLASSE - NO models.py (após a classe User)
# ============================================

def verificar_consistencia_user_operador():
    """
    Verifica se todos os usuários têm operadores correspondentes
    Útil para executar no startup ou via comando
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
            # Verificar dados inconsistentes
            if operador.nome != user.nome:
                inconsistencias.append({
                    'user_id': user.id,
                    'username': user.username,
                    'problema': f'Nome diferente: User="{user.nome}", Operador="{operador.nome}"'
                })
    
    return inconsistencias

@app.cli.command("sincronizar-users")
def sincronizar_users():
    """Sincroniza todos os usuários com operadores"""
    with app.app_context():
        users = User.query.filter_by(status='aprovado').all()
        total = 0
        criados = 0
        
        print(f"📊 Verificando {len(users)} usuários...")
        
        for user in users:
            operador = Operador.query.filter_by(warname=user.username).first()
            
            if not operador:
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
                criados += 1
                print(f"  ✅ Criado operador para {user.username}")
            
            total += 1
        
        db.session.commit()
        print(f"\n✅ Sincronização concluída!")
        print(f"   Total: {total} usuários")
        print(f"   Criados: {criados} operadores")

# ==================== MODELO DE SOLICITAÇÕES ====================
class Solicitacao(db.Model):
    __tablename__ = 'solicitacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), nullable=False, unique=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    cpf = db.Column(db.String(14), nullable=False, unique=True)
    telefone = db.Column(db.String(20), nullable=False)  # NOVO CAMPO
    data_nascimento = db.Column(db.String(10), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    nivel = db.Column(db.String(20), default='operador')
    password_hash = db.Column(db.String(200), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(20), default='pendente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(80), nullable=True)

# ==================== MODELO DE OPERADOR ====================
class Operador(db.Model):
    __tablename__ = 'operadores'
    
    id = db.Column(db.Integer, primary_key=True)
    old_id = db.Column(db.String(50), unique=True, nullable=True)
    
    nome = db.Column(db.String(120), nullable=False, unique=True)  # AGORA É ÚNICO
    warname = db.Column(db.String(80), unique=True, nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)  # NOVO CAMPO
    data_nascimento = db.Column(db.String(20), nullable=True)
    idade = db.Column(db.String(10), nullable=True)
    battlepass = db.Column(db.String(10), default='NAO')
    
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
    battlepass = db.Column(db.String(10), default='NAO')
    capitao_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=True)
    
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
    data = db.Column(db.String(20), nullable=False)  # DD/MM/YYYY
    horario = db.Column(db.String(10), nullable=False)
    campo = db.Column(db.String(20), nullable=False)  # Warfield, Redline
    plano = db.Column(db.String(50), nullable=False)
    tempo = db.Column(db.String(20), nullable=False)
    modo = db.Column(db.String(50), nullable=False)
    tipo_participacao = db.Column(db.String(20), default='individual')  # 'individual' ou 'equipe'
    
    # Valores
    valor_total = db.Column(db.Float, default=0)
    valor_por_participante = db.Column(db.Float, default=0)
    bbs_por_pessoa = db.Column(db.Integer, default=0)
    total_bbs = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='Agendada')  # Agendada, Finalizada
    finalizada = db.Column(db.Boolean, default=False)
    
    # Resultado (para modo equipe)
    equipe_vencedora = db.Column(db.String(20), nullable=True)  # 'GTA', 'SPARTAS', 'EMPATE'
    placar_equipe1 = db.Column(db.Integer, default=0)  # Pontos GTA
    placar_equipe2 = db.Column(db.Integer, default=0)  # Pontos SPARTAS
    mvp_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=True)
    
    # ===== NOVO CAMPO DE PAGAMENTO =====
    pagamento = db.Column(db.String(20), default='Pendente')  # Dinheiro, PIX, Crédito, Débito, Pendente
    
    # Controle de concorrência
    version = db.Column(db.Integer, default=1)  # Para optimistic locking
    locked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    locked_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relacionamentos - CORRIGIDOS
    mvp = db.relationship('Operador', foreign_keys=[mvp_id])
    criador = db.relationship('User', foreign_keys=[created_by], 
                             back_populates='partidas_criadas',
                             overlaps="partidas_criadas")
    participantes = db.relationship('PartidaParticipante', back_populates='partida', cascade='all, delete-orphan')
    
    def lock(self, user_id):
        """Trava a partida para edição"""
        if self.locked_by and self.locked_by != user_id:
            if self.locked_at:
                lock_time = datetime.utcnow() - self.locked_at
                if lock_time.total_seconds() < 300:  # 5 minutos de lock
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
    equipe = db.Column(db.String(50), nullable=True)  # GTA ou SPARTAS
    
    # Estatísticas detalhadas
    kills = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    capturas = db.Column(db.Integer, default=0)
    plantou_bomba = db.Column(db.Integer, default=0)
    desarmou_bomba = db.Column(db.Integer, default=0)
    refens = db.Column(db.Integer, default=0)
    cacou = db.Column(db.Integer, default=0)
    resultado = db.Column(db.String(20), nullable=True)  # vitoria, derrota, empate
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
    quantidade = db.Column(db.Float, default=0)
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