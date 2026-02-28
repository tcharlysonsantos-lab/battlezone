from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from datetime import datetime
import re

# ==================== FUNÇÕES DE VALIDAÇÃO ====================

def validar_cpf(cpf):
    """Valida CPF brasileiro"""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais (CPF inválido)
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    digito1 = 11 - (soma % 11)
    if digito1 > 9:
        digito1 = 0
    
    # Calcula segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    digito2 = 11 - (soma % 11)
    if digito2 > 9:
        digito2 = 0
    
    # Verifica se os dígitos calculados conferem
    return int(cpf[9]) == digito1 and int(cpf[10]) == digito2

def validar_email_real(email):
    """Valida se o email tem formato válido"""
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

def validar_telefone(telefone):
    """Valida telefone brasileiro (10 ou 11 dígitos)"""
    telefone_limpo = re.sub(r'[^0-9]', '', telefone)
    return len(telefone_limpo) in [10, 11]


# ==================== FORMULÁRIO DE LOGIN ====================

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired()])


# ==================== FORMULÁRIO DE SOLICITAÇÃO DE ACESSO ====================

class SolicitacaoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=120)])
    
    def validate_nome(form, field):
        from models import Operador, User, Solicitacao
        # Verificar se nome já existe em operadores, usuários ou solicitações
        if Operador.query.filter_by(nome=field.data).first():
            raise ValidationError('Este nome já está cadastrado como operador')
        if User.query.filter_by(nome=field.data).first():
            raise ValidationError('Este nome já está cadastrado como usuário')
        if Solicitacao.query.filter_by(nome=field.data, status='pendente').first():
            raise ValidationError('Já existe uma solicitação pendente com este nome')
    
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    def validate_email(form, field):
        from models import User, Solicitacao
        if not validar_email_real(field.data):
            raise ValidationError('Email inválido')
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email já cadastrado')
        if Solicitacao.query.filter_by(email=field.data, status='pendente').first():
            raise ValidationError('Já existe uma solicitação pendente com este email')
    
    usuario = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    
    def validate_usuario(form, field):
        from models import User, Solicitacao
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Nome de usuário já existe')
        if Solicitacao.query.filter_by(usuario=field.data, status='pendente').first():
            raise ValidationError('Já existe uma solicitação pendente com este usuário')
    
    cpf = StringField('CPF', validators=[DataRequired()])
    
    def validate_cpf(form, field):
        from models import Operador, User, Solicitacao
        cpf_limpo = re.sub(r'[^0-9]', '', field.data)
        if not validar_cpf(cpf_limpo):
            raise ValidationError('CPF inválido')
        if Operador.query.filter_by(cpf=field.data).first():
            raise ValidationError('CPF já cadastrado como operador')
        if User.query.filter_by(cpf=field.data).first():
            raise ValidationError('CPF já cadastrado como usuário')
        if Solicitacao.query.filter_by(cpf=field.data, status='pendente').first():
            raise ValidationError('Já existe uma solicitação pendente com este CPF')
    
    telefone = StringField('Telefone', validators=[DataRequired()], 
                          render_kw={"placeholder": "(83) 99999-9999"})
    
    def validate_telefone(form, field):
        from models import Operador, User, Solicitacao
        if not validar_telefone(field.data):
            raise ValidationError('Telefone inválido')
        if Operador.query.filter_by(telefone=field.data).first():
            raise ValidationError('Telefone já cadastrado como operador')
        if User.query.filter_by(telefone=field.data).first():
            raise ValidationError('Telefone já cadastrado como usuário')
        if Solicitacao.query.filter_by(telefone=field.data, status='pendente').first():
            raise ValidationError('Já existe uma solicitação pendente com este telefone')
    
    data_nascimento = StringField('Data de Nascimento', validators=[DataRequired()], 
                                  render_kw={"placeholder": "DD/MM/AAAA"})
    
    def validate_data_nascimento(form, field):
        try:
            data = datetime.strptime(field.data, '%d/%m/%Y')
            if data > datetime.now():
                raise ValidationError('Data de nascimento não pode ser no futuro')
            
            # Calcula idade
            idade = datetime.now().year - data.year
            if (datetime.now().month, datetime.now().day) < (data.month, data.day):
                idade -= 1
            
            if idade < 16:
                raise ValidationError('Idade mínima é 16 anos')
            
            # Armazena idade calculada para uso posterior
            form.idade_calculada = idade
            
        except ValueError:
            raise ValidationError('Data inválida. Use o formato DD/MM/AAAA')
    
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('senha')])


# ==================== FORMULÁRIO DE OPERADOR ====================

class OperadorForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=120)])
    
    def validate_nome(form, field):
        from models import Operador
        # Esta validação é para edição, precisa ignorar o próprio operador
        if hasattr(form, 'id') and form.id:
            operador = Operador.query.get(form.id)
            if operador and operador.nome == field.data:
                return
        if Operador.query.filter_by(nome=field.data).first():
            raise ValidationError('Nome já cadastrado')
    
    warname = StringField('Warname', validators=[DataRequired(), Length(max=80)])
    
    def validate_warname(form, field):
        from models import Operador
        if hasattr(form, 'id') and form.id:
            operador = Operador.query.get(form.id)
            if operador and operador.warname == field.data:
                return
        if Operador.query.filter_by(warname=field.data).first():
            raise ValidationError('Warname já existe')
    
    cpf = StringField('CPF', validators=[Optional(), Length(max=20)])
    
    def validate_cpf(form, field):
        if field.data:
            from models import Operador, User
            cpf_limpo = re.sub(r'[^0-9]', '', field.data)
            if not validar_cpf(cpf_limpo):
                raise ValidationError('CPF inválido')
            if hasattr(form, 'id') and form.id:
                operador = Operador.query.get(form.id)
                if operador and operador.cpf == field.data:
                    return
            if Operador.query.filter_by(cpf=field.data).first():
                raise ValidationError('CPF já cadastrado')
            if User.query.filter_by(cpf=field.data).first():
                raise ValidationError('CPF já cadastrado como usuário')
    
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    
    def validate_email(form, field):
        if field.data:
            from models import Operador, User
            if hasattr(form, 'id') and form.id:
                operador = Operador.query.get(form.id)
                if operador and operador.email == field.data:
                    return
            if Operador.query.filter_by(email=field.data).first():
                raise ValidationError('Email já cadastrado')
            if User.query.filter_by(email=field.data).first():
                raise ValidationError('Email já cadastrado como usuário')
    
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    
    def validate_telefone(form, field):
        if field.data:
            from models import Operador, User
            if not validar_telefone(field.data):
                raise ValidationError('Telefone inválido')
            if hasattr(form, 'id') and form.id:
                operador = Operador.query.get(form.id)
                if operador and operador.telefone == field.data:
                    return
            if Operador.query.filter_by(telefone=field.data).first():
                raise ValidationError('Telefone já cadastrado')
            if User.query.filter_by(telefone=field.data).first():
                raise ValidationError('Telefone já cadastrado como usuário')
    
    data_nascimento = StringField('Data Nascimento', validators=[Optional(), Length(max=20)])
    idade = StringField('Idade', validators=[Optional(), Length(max=10)])
    battlepass = SelectField('Battlepass', choices=[('SIM', 'Sim'), ('NAO', 'Não')], default='NAO')


# ==================== FORMULÁRIO DE EQUIPE ====================

class EquipeForm(FlaskForm):
    nome = StringField('Nome da Equipe', validators=[DataRequired(), Length(max=100)])
    
    def validate_nome(form, field):
        from models import Equipe
        if hasattr(form, 'id') and form.id:
            equipe = Equipe.query.get(form.id)
            if equipe and equipe.nome == field.data:
                return
        if Equipe.query.filter_by(nome=field.data).first():
            raise ValidationError('Nome de equipe já existe')
    
    foto = StringField('URL da Foto', validators=[Optional(), Length(max=200)])
    battlepass = SelectField('Battlepass', choices=[('SIM', 'Sim'), ('NAO', 'Não')], default='NAO')
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
    
    def validate_nome(form, field):
        from models import Estoque
        if hasattr(form, 'id') and form.id:
            item = Estoque.query.get(form.id)
            if item and item.nome == field.data:
                return
        if Estoque.query.filter_by(nome=field.data).first():
            raise ValidationError('Item com este nome já existe')
    
    quantidade = IntegerField('Quantidade', validators=[DataRequired()])
    unidade = SelectField('Unidade', choices=[('un', 'Unidade'), ('kg', 'Kg'), ('ml', 'ml'), ('l', 'Litro')], default='un')
    quantidade_minima = IntegerField('Quantidade Mínima', default=0)
    custo = IntegerField('Preço de Custo', default=0)
    preco_venda = IntegerField('Preço de Venda', default=0)
    descricao = StringField('Descrição')
    data = StringField('Data', default=datetime.now().strftime("%d/%m/%Y"))