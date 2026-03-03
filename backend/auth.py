# auth.py - ATUALIZADO COM SEGURANÇA
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, Solicitacao, Log, Operador
from .forms import LoginForm, SolicitacaoForm
from datetime import datetime
import secrets
import json
from werkzeug.security import generate_password_hash
from .email_service import enviar_notificacao_solicitacao, enviar_confirmacao_solicitacao

# Importar funções de segurança
from .auth_security import (
    rate_limiter, 
    log_login_attempt,
    log_security_event,
    validar_codigo_2fa,
    log_2fa_event,
    validar_codigo_2fa_format
)

# CRIAÇÃO DO BLUEPRINT (LINHA OBRIGATÓRIA)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login com Rate Limiting e 2FA"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # ==================== VERIFICAR RATE LIMIT ====================
    ip = request.remote_addr
    is_limited, remaining, reset_time = rate_limiter.is_rate_limited(ip)
    
    if is_limited:
        msg = f"Muitas tentativas de login. Tente novamente em {reset_time} minutos."
        flash(msg, 'danger')
        log_security_event('LOGIN_BLOQUEADO_RATE_LIMIT', ip_address=ip, details={"tentativas_excedidas": True})
        return render_template('auth/login.html', form=LoginForm())
    
    form = LoginForm()
    if form.validate_on_submit():
        # Buscar usuário case-insensitive (independente de maiúscula/minúscula)
        user = User.query.filter(User.username.ilike(form.username.data)).first()
        
        # ==================== VALIDAÇÃO DE CREDENCIAIS ====================
        if not user or not user.check_password(form.password.data):
            rate_limiter.registrar_tentativa(ip)
            log_login_attempt(form.username.data, False, ip, "Usuário ou senha incorretos")
            flash('Usuário ou senha incorretos', 'danger')
            return render_template('auth/login.html', form=form)
        
        if user.status != 'aprovado':
            flash('Sua conta ainda não foi aprovada. Aguarde o administrador.', 'warning')
            return render_template('auth/login.html', form=form)
        
        # ==================== VERIFICAR 2FA ====================
        if user.two_factor_enabled:
            # Armazenar username temporariamente para 2FA
            session['pending_2fa_user'] = user.id
            session['pending_2fa_username'] = user.username
            log_security_event('2FA_REQUERIDO', user.username, ip)
            return redirect(url_for('auth.verify_2fa'))
        
        # ==================== LOGIN BEM-SUCEDIDO ====================
        rate_limiter.limpar_ip(ip)  # Limpar tentativas após sucesso
        
        user.generate_session_token()
        user.last_login = datetime.utcnow()
        user.tentativas = 0
        db.session.commit()
        
        login_user(user)
        log_login_attempt(user.username, True, ip, "Login bem-sucedido")
        
        flash(f'Bem-vindo, {user.nome}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/login.html', form=form)


# ==================== ROTA: CRIAR CONTA ====================
@auth_bp.route('/criar-conta', methods=['GET', 'POST'])
def criar_conta():
    """Criar nova conta de usuário"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = SolicitacaoForm()
    
    if form.validate_on_submit():
        try:
            # Verificar se usuário já existe
            if User.query.filter_by(username=form.usuario.data).first():
                flash('❌ Este usuário já existe! Escolha outro.', 'danger')
                return render_template('auth/criar_conta.html', form=form)
            
            if User.query.filter_by(email=form.email.data).first():
                flash('❌ Este email já está cadastrado!', 'danger')
                return render_template('auth/criar_conta.html', form=form)
            
            # Criar novo usuário
            salt = secrets.token_hex(16)
            user = User(
                username=form.usuario.data,
                nome=form.nome.data,
                email=form.email.data,
                cpf=form.cpf.data,
                telefone=form.telefone.data,
                data_nascimento=form.data_nascimento.data,
                idade=form.idade_calculada,
                nivel='operador',
                status='aprovado',
                salt=salt,
                password_hash=generate_password_hash(form.senha.data + salt),
                terms_accepted=True,
                terms_accepted_date=datetime.utcnow()
            )
            
            db.session.add(user)
            
            # Criar operador também
            operador = Operador(
                nome=form.nome.data,
                warname=form.usuario.data,
                cpf=form.cpf.data,
                email=form.email.data,
                telefone=form.telefone.data,
                data_nascimento=form.data_nascimento.data,
                idade=form.idade_calculada or '0',
                battlepass='NAO'
            )
            db.session.add(operador)
            
            log = Log(
                usuario=form.usuario.data,
                acao='USUARIO_CRIADO',
                detalhes=f"Nova conta criada: {form.nome.data} | Email: {form.email.data} | Termos aceitos"
            )
            db.session.add(log)
            db.session.commit()
            
            flash('✅ Conta criada com sucesso! Você pode fazer login agora.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao criar conta: {str(e)}', 'danger')
    
    return render_template('auth/criar_conta.html', form=form)


# ==================== ROTAS DE 2FA ====================

@auth_bp.route('/2fa/verify', methods=['GET', 'POST'])
def verify_2fa():
    """Verifica código 2FA após login"""
    # Verificar se usuário está aguardando 2FA
    pending_user_id = session.get('pending_2fa_user')
    if not pending_user_id:
        flash('Nenhuma verificação 2FA pendente. Faça login novamente.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(pending_user_id)
    if not user or not user.two_factor_enabled:
        flash('Erro na verificação 2FA.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        usar_backup = request.form.get('usar_backup') == 'on'
        
        ip = request.remote_addr
        
        # ==================== VALIDAÇÃO DO CÓDIGO ====================
        if usar_backup:
            # Usar backup code
            is_valid = user.usar_backup_code(codigo)
            evento = "BACKUP_CODE_USADO"
        else:
            # Usar código TOTP (6 dígitos)
            is_valid_format, msg = validar_codigo_2fa_format(codigo)
            if not is_valid_format:
                flash(f"Código inválido: {msg}", 'danger')
                return render_template('auth/verify_2fa.html')
            
            is_valid = validar_codigo_2fa(user.two_factor_secret, codigo)
            evento = "2FA_VERIFICADO"
        
        if is_valid:
            # Login bem-sucedido com 2FA
            user.generate_session_token()
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user)
            
            # Limpar sessão de 2FA pendente
            session.pop('pending_2fa_user', None)
            session.pop('pending_2fa_username', None)
            session['2fa_verified'] = True
            
            log_2fa_event(user.username, "SUCESSO", ip, success=True)
            flash(f'2FA validado com sucesso! Bem-vindo, {user.nome}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            log_2fa_event(user.username, "FALHA", ip, success=False)
            flash('Código 2FA inválido ou expirado. Tente novamente.', 'danger')
            return render_template('auth/verify_2fa.html')
    
    return render_template('auth/verify_2fa.html')


@auth_bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup inicial de 2FA"""
    from .auth_security import gerar_qr_code
    
    user = current_user
    
    if request.method == 'POST':
        # Confirmar código após verificar
        codigo = request.form.get('codigo', '').strip()
        
        is_valid_format, msg = validar_codigo_2fa_format(codigo)
        if not is_valid_format:
            flash(f"Código inválido: {msg}", 'danger')
            # Regenerar QR code
            qr_code = gerar_qr_code(user.username, user.two_factor_secret)
            backup_codes = json.loads(user.backup_codes) if user.backup_codes else []
            return render_template('auth/setup_2fa.html', qr_code=qr_code, backup_codes=backup_codes)
        
        # Validar código
        if validar_codigo_2fa(user.two_factor_secret, codigo):
            user.confirm_2fa()
            log_2fa_event(user.username, "ATIVADO", request.remote_addr)
            flash('2FA ativado com sucesso! Salve seus backup codes em local seguro.', 'success')
            return redirect(url_for('auth.visualizar_backup_codes_2fa'))
        else:
            flash('Código 2FA inválido ou expirado. Tente novamente.', 'danger')
            qr_code = gerar_qr_code(user.username, user.two_factor_secret)
            backup_codes = json.loads(user.backup_codes) if user.backup_codes else []
            return render_template('auth/setup_2fa.html', qr_code=qr_code, backup_codes=backup_codes)
    
    # GET: Gerar QR code
    if not user.two_factor_secret:
        secret, backup_codes = user.setup_2fa()
    else:
        backup_codes = json.loads(user.backup_codes) if user.backup_codes else []
    
    qr_code = gerar_qr_code(user.username, user.two_factor_secret)
    
    return render_template('auth/setup_2fa.html', qr_code=qr_code, backup_codes=backup_codes)


@auth_bp.route('/2fa/backup-codes')
@login_required
def visualizar_backup_codes_2fa():
    """Visualiza backup codes do usuário"""
    user = current_user
    if not user.two_factor_enabled:
        flash('2FA não está ativado.', 'danger')
        return redirect(url_for('dashboard'))
    
    backup_codes = json.loads(user.backup_codes) if user.backup_codes else []
    return render_template('auth/backup_codes_2fa.html', backup_codes=backup_codes)


@auth_bp.route('/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    """Desativa 2FA do usuário"""
    user = current_user
    user.disable_2fa()
    log_2fa_event(user.username, "DESATIVADO", request.remote_addr)
    flash('2FA foi desativado.', 'info')
    return redirect(url_for('meu_perfil'))


@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    session.clear()
    
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))


# ==================== TERMS OF SERVICE ROUTE ====================

@auth_bp.route('/terms')
def terms():
    """Exibe os Termos de Serviço"""
    return render_template('auth/terms.html')


# ==================== PASSWORD RESET ROUTES ====================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Requisitar reset de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Gerar token de reset
            token = user.gerar_password_reset_token()
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            
            # Log do evento
            log_security_event('PASSWORD_RESET_SOLICITADO', user.username, request.remote_addr)
            
            # Mensagem para o usuário
            flash(
                'Se esta conta existe, um link para reset de senha foi enviado.\n'
                'Link: ' + reset_link,
                'info'
            )
        else:
            # Segurança: não revelar se email existe ou não
            flash(
                'Se esta conta existe, um link para reset de senha foi enviado.',
                'info'
            )
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resetar senha com token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Buscar usuário por token
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user:
        flash('Link inválido ou expirado.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Validar token
    if not user.validar_password_reset_token(token):
        flash('Link expirou. Por favor, solicite um novo.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('password', '').strip()
        confirma_senha = request.form.get('password_confirm', '').strip()
        
        # Validações
        if not nova_senha or not confirma_senha:
            flash('Preenchimento de senha obrigatório.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if nova_senha != confirma_senha:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if len(nova_senha) < 8:
            flash('Senha deve ter pelo menos 8 caracteres.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Resetar senha
        user.resetar_senha(nova_senha)
        log_security_event('PASSWORD_RESETADO', user.username, request.remote_addr)
        
        flash('Sua senha foi alterada com sucesso! Agora faça login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)
