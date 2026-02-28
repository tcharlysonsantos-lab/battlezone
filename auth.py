# auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Solicitacao, Log, Operador
from forms import LoginForm, SolicitacaoForm
from datetime import datetime
import secrets
from werkzeug.security import generate_password_hash

# CRIAÇÃO DO BLUEPRINT (LINHA OBRIGATÓRIA)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if not user or not user.check_password(form.password.data):
            log = Log(
                usuario=form.username.data,
                acao='LOGIN_FALHA',
                detalhes='Usuário ou senha incorretos',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Usuário ou senha incorretos', 'danger')
            return render_template('auth/login.html', form=form)
        
        if user.status != 'aprovado':
            flash('Sua conta ainda não foi aprovada. Aguarde o administrador.', 'warning')
            return render_template('auth/login.html', form=form)
        
        user.generate_session_token()
        user.last_login = datetime.utcnow()
        user.tentativas = 0
        db.session.commit()
        
        login_user(user)
        
        log = Log(
            usuario=user.username,
            acao='LOGIN_SUCESSO',
            detalhes=f"Nível: {user.nivel}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Bem-vindo, {user.nome}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/solicitar', methods=['GET', 'POST'])
def solicitar_acesso():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = SolicitacaoForm()
    
    # ===== DEBUG =====
    print("\n" + "="*50)
    print("🔍 DEBUG - SOLICITAR ACESSO")
    print(f"Método: {request.method}")
    print(f"POST: {request.method == 'POST'}")
    
    if request.method == 'POST':
        print(f"\n📝 Dados recebidos:")
        print(f"nome: {request.form.get('nome')}")
        print(f"email: {request.form.get('email')}")
        print(f"usuario: {request.form.get('usuario')}")
        print(f"cpf: {request.form.get('cpf')}")
        print(f"telefone: {request.form.get('telefone')}")
        print(f"data_nascimento: {request.form.get('data_nascimento')}")
        
        print(f"\n✅ Form validate: {form.validate_on_submit()}")
        if form.errors:
            print(f"❌ Erros de validação:")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"   - {field}: {error}")
                    flash(f"{field}: {error}", 'danger')
    print("="*50 + "\n")
    # ================
    
    if form.validate_on_submit():
        # VERIFICAR SE JÁ EXISTE OPERADOR COM ESTE CPF
        operador_existente = Operador.query.filter_by(cpf=form.cpf.data).first()
        
        if operador_existente:
            usuario_existente = User.query.filter_by(cpf=form.cpf.data).first()
            
            if usuario_existente:
                flash('Já existe um usuário cadastrado com este CPF!', 'danger')
                return render_template('auth/solicitar.html', form=form)
            
            # Criar usuário VINCULADO ao operador existente
            salt = secrets.token_hex(16)
            
            user = User(
                username=form.usuario.data,
                nome=operador_existente.nome,
                email=form.email.data,
                cpf=form.cpf.data,
                data_nascimento=operador_existente.data_nascimento,
                idade=int(operador_existente.idade) if operador_existente.idade else 0,
                telefone=form.telefone.data,
                nivel='operador',
                status='aprovado',
                salt=salt,
                password_hash=generate_password_hash(form.senha.data + salt)
            )
            
            db.session.add(user)
            
            log = Log(
                usuario=form.usuario.data,
                acao='USUARIO_CRIADO_VINCULADO',
                detalhes=f"Usuário vinculado ao operador {operador_existente.warname}"
            )
            db.session.add(log)
            db.session.commit()
            
            flash('✅ Usuário criado e vinculado ao operador existente! Faça login.', 'success')
            return redirect(url_for('auth.login'))
        
        # SE NÃO EXISTE OPERADOR, VERIFICAR SE USUÁRIO JÁ EXISTE
        if User.query.filter_by(username=form.usuario.data).first():
            flash('Nome de usuário já existe', 'danger')
            return render_template('auth/solicitar.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado', 'danger')
            return render_template('auth/solicitar.html', form=form)
        
        if User.query.filter_by(cpf=form.cpf.data).first():
            flash('CPF já cadastrado', 'danger')
            return render_template('auth/solicitar.html', form=form)
        
        if User.query.filter_by(telefone=form.telefone.data).first():
            flash('Telefone já cadastrado', 'danger')
            return render_template('auth/solicitar.html', form=form)
        
        # Verificar solicitação pendente
        solicitacao_existente = Solicitacao.query.filter_by(
            usuario=form.usuario.data, 
            status='pendente'
        ).first()
        
        if solicitacao_existente:
            flash('Já existe uma solicitação pendente para este usuário', 'warning')
            return render_template('auth/solicitar.html', form=form)
        
        # Criar solicitação com novos campos
        salt = secrets.token_hex(16)
        
        solicitacao = Solicitacao(
            usuario=form.usuario.data,
            nome=form.nome.data,
            email=form.email.data,
            cpf=form.cpf.data,
            telefone=form.telefone.data,
            data_nascimento=form.data_nascimento.data,
            idade=form.idade_calculada,
            nivel='operador',
            password_hash=generate_password_hash(form.senha.data + salt),
            salt=salt,
            status='pendente'
        )
        
        db.session.add(solicitacao)
        
        log = Log(
            usuario=form.usuario.data,
            acao='SOLICITACAO_CRIADA',
            detalhes=f"Nome: {form.nome.data} | Email: {form.email.data}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash('✅ Solicitação enviada! Aguarde a aprovação da conta. Para que seja mais rápido, entre em contato conosco!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/solicitar.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    session.clear()
    
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))