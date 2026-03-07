# auth.py - ATUALIZADO COM SEGURANÇA
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask.views import MethodView
from functools import wraps
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
        # ✅ NÃO fazer commit aqui - deixar pro after_request
        
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
            # ✅ NÃO fazer commit aqui - deixar pro after_request
            
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
            # ✅ NÃO fazer commit aqui - deixar pro after_request
            
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
@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])  # ALIAS para URL antiga
def forgot_password():
    """Requisitar reset de senha"""
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # ===== VALIDAÇÃO PRÉ-ENVIO =====
        
        if not email or '@' not in email:
            flash('Email inválido. Por favor, digite um email válido.', 'danger')
            return render_template('auth/forgot_password.html')
        
        # ===== BUSCAR USUÁRIO =====
        
        user = User.query.filter(User.email.ilike(email)).first()
        
        if not user:
            # 🔐 SEGURANÇA: Mostrar que não existe, mas de forma clara
            flash(
                '❌ Não existe nenhuma conta cadastrada com este email.\n'
                'Verifique se digitou corretamente ou crie uma nova conta.',
                'danger'
            )
            return render_template('auth/forgot_password.html')
        
        # ===== EMAIL EXISTE - PROCESSAR RESET =====
        
        # Gerar token de reset
        token = user.gerar_password_reset_token()
        reset_link = url_for('auth.reset_password', token=token, _external=True)
        
        # Log do evento
        log_security_event('PASSWORD_RESET_SOLICITADO', user.username, request.remote_addr)
        
        # Enviar email com link de reset
        try:
            from backend.email_service import enviar_email_reset_senha, verificar_saude_email
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Verificar saude do servico de email antes de enviar
            is_healthy, health_msg = verificar_saude_email()
            logger.info(f"[INFO] Saude Email: {health_msg}")
            
            if not is_healthy:
                logger.warning(f"[WARNING] Email service nao esta saudavel: {health_msg}")
                flash(
                    'Servico de email temporariamente indisponivel.\n'
                    'Por favor, tente novamente em alguns minutos.\n'
                    f'(Detalhes tecnicos: {health_msg})',
                    'warning'
                )
                return render_template('auth/forgot_password.html')
            
            # Tentar enviar email
            email_enviado = enviar_email_reset_senha(user.email, user.nome, reset_link)
            
            if email_enviado:
                logger.info(f"[OK] Email de reset enviado para: {user.email}")
                flash(
                    'Email sera enviado em alguns segundos!\n'
                    'Verifique sua caixa de entrada (ou spam).\n'
                    'O link e valido por 30 minutos.',
                    'success'
                )
            else:
                logger.error(f"[ERROR] Falha ao enviar email de reset para: {user.email}")
                flash(
                    'Falha ao enviar email.\n'
                    'Erros tecnicos podem estar ocorrendo.\n'
                    'Tente novamente em alguns minutos.',
                    'danger'
                )
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[ERROR] Excecao ao tentar enviar email de reset: {str(e)}")
            logger.error(f"     Tipo: {type(e).__name__}")
            logger.error(f"     User: {user.email}")
            
            flash(
                'Erro ao processar o reset de senha.\n'
                'Por favor, tente novamente mais tarde.',
                'danger'
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


@auth_bp.route('/health/email', methods=['GET'])
def health_check_email():
    """
    Endpoint para verificar a saúde do serviço de email
    
    🔒 SEGURANÇA: Este endpoint retorna informações sensíveis.
    Em produção, considere restringir acesso apenas para admins.
    
    Resposta JSON:
    {
        "status": "healthy" | "unhealthy",
        "service": "email",
        "is_initialized": bool,
        "has_flask_mail": bool,
        "config_valid": bool,
        "messages": [...]
    }
    """
    from backend.email_service import HAS_FLASK_MAIL, MAIL_INITIALIZED, verificar_saude_email
    import logging
    
    logger = logging.getLogger(__name__)
    
    # ⚠️ OPTIONAL: Verificar se é admin antes de retornar info
    # if not current_user.is_authenticated or current_user.nivel != 'admin':
    #     return jsonify({"error": "Unauthorized"}), 403
    
    is_healthy, health_msg = verificar_saude_email()
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "email",
        "is_initialized": MAIL_INITIALIZED,
        "has_flask_mail": HAS_FLASK_MAIL,
        "config_valid": is_healthy,
        "message": health_msg,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Log do health check
    logger.info(f"[INFO] Email Health Check: {response['status']}")
    
    return jsonify(response), 200 if is_healthy else 503


@auth_bp.route('/api/validate-email', methods=['POST'])
def validate_email_for_reset():
    """
    API AJAX: Valida se um email existe no sistema para reset de senha
    
    Request:
        {
            "email": "user@gmail.com"
        }
    
    Response:
        {
            "exists": true/false,
            "message": "Email encontrado!" / "Email não encontrado"
        }
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # ===== RECEBER E VALIDAR JSON =====
        
        data = request.get_json()
        
        if not data:
            logger.warning("[WARNING] Request sem JSON valido")
            return jsonify({
                "exists": False,
                "message": "ERRO: Formato de requisicao invalido"
            }), 400
        
        email = data.get('email', '').strip().lower() if isinstance(data.get('email'), str) else ''
        
        # Validar email
        if not email:
            logger.warning("[WARNING] Email vazio na requisicao")
            return jsonify({
                "exists": False,
                "message": "ERRO: Email vazio"
            }), 400
        
        if '@' not in email:
            logger.warning(f"[WARNING] Email invalido (sem @): {email}")
            return jsonify({
                "exists": False,
                "message": "ERRO: Email invalido"
            }), 400
        
        # ===== BUSCAR USUARIO NO BANCO =====
        
        logger.info(f"[INFO] Email recebido (bruto): {repr(data.get('email'))}")
        logger.info(f"[INFO] Email processado: {email}")
        logger.info(f"[INFO] Iniciando busca por email: {email}")
        
        # Verificar se User model está disponível
        logger.info(f"[INFO] Modelo User carregado: {User}")
        
        # Executar query com debugging detalhado
        # Usar ilike para case-insensitive search
        logger.info(f"[INFO] Executando query: User.query.filter(User.email.ilike('{email}')).first()")
        user = User.query.filter(User.email.ilike(email)).first()
        
        logger.info(f"[INFO] Resultado da query: {user}")
        
        if user:
            logger.info(f"[OK] Email encontrado no sistema: {email} (user_id={user.id})")
            return jsonify({
                "exists": True,
                "message": "OK: Email encontrado! Sera enviado em segundos.",
                "user_found": True,
                "debug_user_id": user.id
            }), 200
        else:
            logger.info(f"[INFO] Email nao encontrado: {email}")
            
            # Debug: contar total de usuarios
            total_users = User.query.count()
            logger.info(f"[DEBUG] Total de usuarios no banco: {total_users}")
            
            # Debug: listar alguns emails (primeiros 5)
            if total_users > 0:
                sample_users = User.query.limit(5).all()
                sample_emails = [u.email for u in sample_users if hasattr(u, 'email')]
                logger.info(f"[DEBUG] Amostra de emails no banco: {sample_emails}")
            
            return jsonify({
                "exists": False,
                "message": "Nao existe nenhuma conta cadastrada com este email",
                "user_found": False,
                "debug_total_users": total_users
            }), 200
    
    except Exception as e:
        # ===== TRATAMENTO DE ERRO =====
        
        logger.error(f"[ERROR] ERRO ao validar email: {str(e)}")
        logger.error(f"     Tipo: {type(e).__name__}")
        logger.error(f"     Stack: {repr(e)}")
        
        import traceback
        logger.error(f"     Traceback: {traceback.format_exc()}")
        
        # Retornar erro JSON em vez de HTML
        return jsonify({
            "exists": False,
            "message": "Erro ao processar validacao. Tente novamente.",
            "error": type(e).__name__,
            "error_detail": str(e)
        }), 500


@auth_bp.route('/api/debug/usuarios', methods=['GET'])
def debug_usuarios():
    """
    DEBUG ONLY: Lista todos os usuarios para diagnostico
    Remove apos resolver o problema!
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("[DEBUG] Endpoint /api/debug/usuarios acessada")
        
        # Query: contar total
        total = User.query.count()
        logger.info(f"[DEBUG] Total de usuarios: {total}")
        
        # Query: listar todos
        usuarios = User.query.all()
        
        dados = {
            "total_usuarios": total,
            "usuarios": []
        }
        
        for user in usuarios:
            dados["usuarios"].append({
                "id": user.id,
                "username": user.username,
                "nome": user.nome,
                "email": user.email,
                "status": user.status
            })
        
        logger.info(f"[DEBUG] Retornando {len(usuarios)} usuarios")
        
        return jsonify(dados), 200
        
    except Exception as e:
        logger.error(f"[ERROR] Erro em /api/debug/usuarios: {str(e)}")
        return jsonify({
            "error": type(e).__name__,
            "message": str(e)
        }), 500
