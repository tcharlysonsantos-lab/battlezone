# forms.py - ATUALIZADO

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from datetime import datetime
import re

# ==================== FUNÇÕES DE VALIDAÇÃO ====================
def validar_cpf(cpf):
    """Valida CPF brasileiro"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Validar dígitos verificadores
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * (i+1 - num) for num in range(0, i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if int(cpf[i]) != digito:
            return False
    return True

def validar_telefone(telefone):
    """Valida telefone brasileiro"""
    telefone_limpo = re.sub(r'[^0-9]', '', telefone)
    return len(telefone_limpo) in [10, 11]

# ==================== FORMULÁRIO DE LOGIN ====================
class LoginForm(FlaskForm):
    username = StringField('Warname', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired()])

# ==================== FORMULÁRIO DE SOLICITAÇÃO ====================
class SolicitacaoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    usuario = StringField('Warname', validators=[DataRequired(), Length(min=3, max=80)])
    cpf = StringField('CPF', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    data_nascimento = StringField('Data de Nascimento', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('senha')])
    
    def validate_cpf(self, field):
        from .models import Operador, User, Solicitacao
        
        if not validar_cpf(field.data):
            raise ValidationError('CPF inválido')
        
        # Verificar se CPF já existe em operador
        operador = Operador.query.filter_by(cpf=field.data).first()
        if operador:
            # Se existe operador, verifica se os dados são IGUAIS
            if (operador.nome == self.nome.data and 
                operador.warname == self.usuario.data and 
                operador.email == self.email.data):
                # Tudo igual - pode criar usuário (vai vincular depois)
                return
            else:
                # CPF existe mas dados diferentes
                raise ValidationError('❌ Este CPF já pertence a outro operador. Entre em contato com a BATTLEZONE!')
        
        # Verificar se CPF já existe em usuário
        if User.query.filter_by(cpf=field.data).first():
            raise ValidationError('❌ CPF já cadastrado como usuário')
        
        # Verificar se CPF já existe em solicitação pendente
        if Solicitacao.query.filter_by(cpf=field.data, status='pendente').first():
            raise ValidationError('❌ Já existe uma solicitação pendente com este CPF')
    
    def validate_nome(self, field):
        from .models import Operador, User, Solicitacao
        
        # Verificar se nome já existe em operador
        operador = Operador.query.filter_by(nome=field.data).first()
        if operador:
            # Se existe operador com este nome, verifica se os dados são IGUAIS
            if (operador.cpf == self.cpf.data and 
                operador.warname == self.usuario.data and 
                operador.email == self.email.data):
                return  # Tudo igual - permite
            else:
                raise ValidationError('❌ Nome já cadastrado para outro operador')
        
        # Verificar se nome já existe em usuário
        if User.query.filter_by(nome=field.data).first():
            raise ValidationError('❌ Nome já cadastrado como usuário')
        
        # Verificar se nome já existe em solicitação pendente
        if Solicitacao.query.filter_by(nome=field.data, status='pendente').first():
            raise ValidationError('❌ Já existe uma solicitação pendente com este nome')
    
    def validate_usuario(self, field):
        from .models import Operador, User, Solicitacao
        
        # Verificar se warname já existe em operador
        operador = Operador.query.filter_by(warname=field.data).first()
        if operador:
            # Se existe operador com este warname, verifica se os dados são IGUAIS
            if (operador.cpf == self.cpf.data and 
                operador.nome == self.nome.data and 
                operador.email == self.email.data):
                return  # Tudo igual - permite
            else:
                raise ValidationError('❌ Warname já cadastrado para outro operador')
        
        # Verificar se warname já existe em usuário
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('❌ Warname já cadastrado como usuário')
        
        # Verificar se warname já existe em solicitação pendente
        if Solicitacao.query.filter_by(usuario=field.data, status='pendente').first():
            raise ValidationError('❌ Já existe uma solicitação pendente com este warname')
    
    def validate_email(self, field):
        from .models import Operador, User, Solicitacao
        
        # Verificar se email já existe em operador
        operador = Operador.query.filter_by(email=field.data).first()
        if operador:
            # Se existe operador com este email, verifica se os dados são IGUAIS
            if (operador.cpf == self.cpf.data and 
                operador.nome == self.nome.data and 
                operador.warname == self.usuario.data):
                return  # Tudo igual - permite
            else:
                raise ValidationError('❌ Email já cadastrado para outro operador')
        
        # Verificar se email já existe em usuário
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('❌ Email já cadastrado como usuário')
        
        # Verificar se email já existe em solicitação pendente
        if Solicitacao.query.filter_by(email=field.data, status='pendente').first():
            raise ValidationError('❌ Já existe uma solicitação pendente com este email')
    
    def validate_telefone(self, field):
        # SÓ VALIDA FORMATO, NÃO VERIFICA DUPLICIDADE
        if not validar_telefone(field.data):
            raise ValidationError('Telefone inválido')
    
    def validate_data_nascimento(self, field):
        try:
            data = datetime.strptime(field.data, '%d/%m/%Y')
            if data > datetime.now():
                raise ValidationError('Data não pode ser no futuro')
            idade = datetime.now().year - data.year
            if (datetime.now().month, datetime.now().day) < (data.month, data.day):
                idade -= 1
            if idade < 16:
                raise ValidationError('Idade mínima é 16 anos')
            self.idade_calculada = idade
        except ValueError:
            raise ValidationError('Data inválida. Use DD/MM/AAAA')
    
    def validate(self, extra_validators=None):
        """Validação global do formulário - roda APÓS validações individuais"""
        # Chamar validação padrão primeiro
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # VALIDAÇÃO GLOBAL: Verificar operador com dados exatos
        # Isso permite auto-criar usuário quando operador existe com mesmos 4 dados
        from .models import Operador
        
        operador_exato = Operador.query.filter_by(
            nome=self.nome.data,
            warname=self.usuario.data,
            email=self.email.data,
            cpf=self.cpf.data
        ).first()
        
        # Se operador exato existe, marcar para auto-criação (não erra aqui)
        if operador_exato:
            self.operador_encontrado = operador_exato
        else:
            self.operador_encontrado = None
        
        return True

# ==================== FORMULÁRIO DE OPERADOR ====================
class OperadorForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=120)])
    warname = StringField('Warname (Apelido no jogo)', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(max=20)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])  # ← OPCIONAL
    data_nascimento = StringField('Data de Nascimento', validators=[DataRequired(), Length(max=20)])
    idade = StringField('Idade', validators=[Optional(), Length(max=10)])
    battlepass = SelectField('Battlepass', choices=[('NAO', 'Não'), ('SIM', 'Sim')], default='NAO')
    
    def __init__(self, *args, **kwargs):
        super(OperadorForm, self).__init__(*args, **kwargs)
        if kwargs.get('obj'):
            self.id = kwargs['obj'].id
    
    def validate_nome(self, field):
        from .models import Operador
        # Se for edição (tem id) e o nome não mudou, permite
        if hasattr(self, 'id') and self.id:
            operador = Operador.query.get(self.id)
            if operador and operador.nome == field.data:
                return
        # Se for criação ou nome mudou, verifica se já existe
        if Operador.query.filter_by(nome=field.data).first():
            raise ValidationError('❌ Nome já cadastrado')
    
    def validate_warname(self, field):
        from .models import Operador
        # Se for edição (tem id) e o warname não mudou, permite
        if hasattr(self, 'id') and self.id:
            operador = Operador.query.get(self.id)
            if operador and operador.warname == field.data:
                return
        # Se for criação ou warname mudou, verifica se já existe
        if Operador.query.filter_by(warname=field.data).first():
            raise ValidationError('❌ Warname já existe')
    
    def validate_email(self, field):
        from .models import Operador
        # Se for edição (tem id) e o email não mudou, permite
        if hasattr(self, 'id') and self.id:
            operador = Operador.query.get(self.id)
            if operador and operador.email == field.data:
                return
        # Se for criação ou email mudou, verifica se já existe
        if field.data and Operador.query.filter_by(email=field.data).first():
            raise ValidationError('❌ Email já cadastrado')
    
    def validate_telefone(self, field):
        # APENAS VALIDA FORMATO SE FOI PREENCHIDO
        if field.data:
            if not validar_telefone(field.data):
                raise ValidationError('❌ Telefone inválido')
    
    def validate_cpf(self, field):
        from .models import Operador
        
        if not field.data:
            raise ValidationError('❌ CPF é obrigatório')
        
        cpf_limpo = re.sub(r'[^0-9]', '', field.data)
        if not validar_cpf(cpf_limpo):
            raise ValidationError('❌ CPF inválido')
        
        # Se for edição (tem id) e o CPF não mudou, permite
        if hasattr(self, 'id') and self.id:
            operador_atual = Operador.query.get(self.id)
            if operador_atual and operador_atual.cpf == field.data:
                return
        
        # Verificar se CPF já existe em OUTRO operador
        query = Operador.query.filter_by(cpf=field.data)
        if hasattr(self, 'id') and self.id:
            query = query.filter(Operador.id != self.id)
        
        if query.first():
            raise ValidationError('❌ CPF já cadastrado para outro operador')
    
    def validate_data_nascimento(self, field):
        try:
            data = datetime.strptime(field.data, '%d/%m/%Y')
            if data > datetime.now():
                raise ValidationError('❌ Data não pode ser no futuro')
            
            idade = datetime.now().year - data.year
            if (datetime.now().month, datetime.now().day) < (data.month, data.day):
                idade -= 1
            
            if idade < 16:
                raise ValidationError('❌ Idade mínima é 16 anos')
            
            self.idade.data = str(idade)
            
        except ValueError:
            raise ValidationError('❌ Data inválida. Use o formato DD/MM/AAAA')

# ==================== FORMULÁRIO DE EQUIPE ====================
class EquipeForm(FlaskForm):
    nome = StringField('Nome da Equipe', validators=[DataRequired(), Length(max=100)])
    foto = StringField('URL da Foto', validators=[Optional(), Length(max=200)])
    battlepass = SelectField('Battlepass', choices=[('NAO', 'Não'), ('SIM', 'Sim')], default='NAO')
    capitao_id = SelectField('Capitão (Opcional)', coerce=int, validators=[Optional()], default=0)

# ==================== FORMULÁRIO DE PARTIDA ====================
class PartidaForm(FlaskForm):
    nome = StringField('Nome da Partida', validators=[DataRequired(), Length(max=100)])
    data = StringField('Data', validators=[DataRequired()], default=datetime.now().strftime("%d/%m/%Y"))
    horario = StringField('Horário', validators=[DataRequired()], default=datetime.now().strftime("%H:%M"))
    campo = SelectField('Campo', choices=[('Warfield', 'Warfield'), ('Redline', 'Redline')], validators=[DataRequired()])
    plano = SelectField('Plano', choices=[], validators=[DataRequired()])
    tempo = SelectField('Tempo', choices=[], validators=[DataRequired()])
    modo = SelectField('Modo', choices=[], validators=[DataRequired()])
    num_participantes = IntegerField('Número de Participantes', validators=[DataRequired()])

# ==================== FORMULÁRIO DE VENDA ====================
class VendaForm(FlaskForm):
    produto = StringField('Produto', validators=[DataRequired(), Length(max=100)])
    quantidade = IntegerField('Quantidade', default=0)
    unidade = SelectField('Unidade', choices=[('un', 'Unidade'), ('kg', 'Kg'), ('ml', 'ml'), ('l', 'Litro')], default='un')
    valor = IntegerField('Valor', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[
        ('Loja', 'Loja'),
        ('Açaí', 'Açaí'),
        ('Warfield', 'Warfield'),
        ('Redline', 'Redline'),
        ('Estoque', 'Estoque')
    ], validators=[DataRequired()])
    pagamento = SelectField('Pagamento', choices=[
        ('A definir', 'A definir'),
        ('Dinheiro', 'Dinheiro'),
        ('PIX', 'PIX'),
        ('Crédito', 'Crédito'),
        ('Débito', 'Débito')
    ], default='A definir')
    data = StringField('Data', default=datetime.now().strftime("%d/%m/%Y"))
    cliente = StringField('Cliente', validators=[DataRequired(), Length(max=120)])
    descricao = StringField('Descrição')

# ==================== FORMULÁRIO DE ESTOQUE ====================
class EstoqueForm(FlaskForm):
    nome = StringField('Nome do Item', validators=[DataRequired(), Length(max=100)])
    quantidade = IntegerField('Quantidade', validators=[DataRequired()])
    unidade = SelectField('Unidade', choices=[('un', 'Unidade'), ('kg', 'Kg'), ('ml', 'ml'), ('l', 'Litro')], default='un')
    quantidade_minima = IntegerField('Quantidade Mínima', default=0)
    custo = IntegerField('Preço de Custo', default=0)
    preco_venda = IntegerField('Preço de Venda', default=0)
    descricao = StringField('Descrição')
    data = StringField('Data', default=datetime.now().strftime("%d/%m/%Y"))
