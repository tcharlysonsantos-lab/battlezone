"""
Email Service - Envia notificações via email
"""

from flask import url_for, current_app
import logging
import os
import threading
import smtplib
from functools import wraps

logger = logging.getLogger(__name__)

# Tentar importar Flask-Mail, mas fazer fallback se não disponível
try:
    from flask_mail import Mail, Message
    HAS_FLASK_MAIL = True
except ImportError:
    HAS_FLASK_MAIL = False
    logger.warning("[WARNING] Flask-Mail nao instalado. Emails nao serao enviados. Instale com: pip install Flask-Mail")
    Mail = None
    Message = None

mail = None
MAIL_INITIALIZED = False

def _validar_configuracao_email(app):
    """
    Valida se as configurações de email estão corretas
    
    Returns:
        (is_valid: bool, message: str)
    """
    mail_server = app.config.get('MAIL_SERVER', '').strip()
    mail_username = app.config.get('MAIL_USERNAME', '').strip()
    mail_password = app.config.get('MAIL_PASSWORD', '').strip()
    
    # Verificar se variáveis de ambiente estão vazias ou como placeholder
    if not mail_server or mail_server == 'localhost':
        return False, "MAIL_SERVER não configurado"
    
    if not mail_username or mail_username == 'seu-email@gmail.com' or mail_username == 'noreply@battlezone.local':
        return False, f"MAIL_USERNAME inválido ou não configurado: '{mail_username}'"
    
    # VALIDACAO CRITICA: Verificar se MAIL_USERNAME tem @ (eh um email valido)
    if '@' not in mail_username:
        return False, f"MAIL_USERNAME invalido - nao eh um email: '{mail_username}' (falta @ no email!)"
    
    # Validar formato basico de email
    if not mail_username.endswith('@gmail.com') and not mail_username.endswith('@outlook.com') and '@' in mail_username:
        logger.warning(f"[WARNING] MAIL_USERNAME nao eh Gmail/Outlook, pode nao funcionar: '{mail_username}'")
    
    if not mail_password or mail_password == 'sua-app-password':
        return False, "MAIL_PASSWORD não configurado"
    
    return True, "✅ Configuração de email válida"


def init_mail(app):
    """
    Inicializa o servico de email com a aplicacao Flask
    
    [INFO] IMPORTANTE: Variaveis de ambiente devem estar configuradas:
       - MAIL_SERVER (ex: smtp.gmail.com)
       - MAIL_PORT (ex: 587)
       - MAIL_USE_TLS (ex: true)
       - MAIL_USERNAME (ex: seu-email@gmail.com)
       - MAIL_PASSWORD (ex: senha-de-app-16-caracteres)
    """
    global mail, MAIL_INITIALIZED
    
    if not HAS_FLASK_MAIL:
        logger.error("[ERROR] Flask-Mail nao instalado!")
        logger.error("   Instale com: pip install Flask-Mail")
        return
    
    # Validar configuracao
    is_valid, message = _validar_configuracao_email(app)
    
    if not is_valid:
        logger.error(f"[ERROR] Configuracao de email invalida: {message}")
        logger.error("   [WARNING] Desabilitar emails ate que as variaveis de ambiente sejam configuradas.")
        logger.error("   [INFO] Copie RAILWAY_DEPLOYMENT.env para Railway Settings > Environment")
        return
    
    try:
        mail = Mail(app)
        MAIL_INITIALIZED = True
        
        # Log de sucesso com informacoes (sem expor senha)
        logger.info("[OK] Email service initialized successfully")
        logger.info(f"   MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        logger.info(f"   MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        logger.info(f"   MAIL_PORT: {app.config.get('MAIL_PORT')}")
        logger.info(f"   MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        
    except Exception as e:
        logger.error(f"[ERROR] Falha ao inicializar Flask-Mail: {str(e)}")
        logger.error(f"   Tipo de erro: {type(e).__name__}")
        logger.error("   Possiveis causas:")
        logger.error("   - Variaveis de ambiente mal formatadas")
        logger.error("   - Servidor SMTP inacessivel")
        logger.error("   - Firewall/Network bloqueando SMTP")


def verificar_saude_email(app=None):
    """
    Verifica se o serviço de email está operacional
    
    Returns:
        (is_healthy: bool, status_message: str)
    """
    if not app:
        try:
            app = current_app
        except RuntimeError:
            return False, "Sem app context"
    
    if not HAS_FLASK_MAIL:
        return False, "Flask-Mail não instalado"
    
    if not mail or not MAIL_INITIALIZED:
        return False, "Email service não inicializado"
    
    is_valid, message = _validar_configuracao_email(app)
    if not is_valid:
        return False, message
    
    return True, "Email service operacional"


def _enviar_email_thread(app, destinatarios: list, assunto: str, html: str, remetente: str = None):
    """
    Função interna para enviar email em thread separada (NÃO BLOQUEIA)
    
    Esta função é chamada em uma thread separada para não bloquear a requisição HTTP
    Com retry automático (até 3 tentativas)
    """
    import sys
    import time
    import socket
    
    max_tentativas = 3
    tentativa = 0
    
    while tentativa < max_tentativas:
        tentativa += 1
        sys.stderr.write(f"[STDERR] Tentativa {tentativa}/{max_tentativas} de enviar email\n")
        sys.stderr.flush()
        logger.info(f"[INFO] Tentativa {tentativa} de enviar email para {destinatarios}")
        
        try:
            if not mail:
                logger.error("[ERROR] Email service nao inicializado")
                sys.stderr.write(f"[STDERR] Mail service não inicializado\n")
                sys.stderr.flush()
                return
            
            # Usar app context fornecido
            with app.app_context():
                logger.info(f"[INFO] App context ativado")
                
                # Preparar mensagem
                msg = Message(
                    subject=assunto,
                    recipients=destinatarios,
                    html=html,
                    sender=remetente
                )
                logger.info(f"[INFO] Mensagem preparada")
                sys.stderr.write(f"[STDERR] Tentando enviar via SMTP...\n")
                sys.stderr.flush()
                
                # ENVIAR COM TIMEOUT
                try:
                    # Configurar timeout de socket
                    socket.setdefaulttimeout(app.config.get('MAIL_TIMEOUT', 10))
                    
                    mail.send(msg)
                    
                    logger.info(f"[OK] Email enviado com sucesso na tentativa {tentativa}")
                    sys.stderr.write(f"[STDERR] Email enviado com sucesso!\n")
                    sys.stderr.flush()
                    return  # Sucesso!
                    
                except socket.timeout:
                    sys.stderr.write(f"[STDERR] TIMEOUT na tentativa {tentativa} - tentando novamente...\n")
                    sys.stderr.flush()
                    logger.warning(f"[WARNING] Timeout na tentativa {tentativa}, tentando novamente...")
                    time.sleep(2)  # Aguardar antes de retry
                    
                except Exception as e:
                    sys.stderr.write(f"[STDERR] Erro na tentativa {tentativa}: {type(e).__name__}: {str(e)}\n")
                    sys.stderr.flush()
                    logger.error(f"[ERROR] Tentativa {tentativa} falhou: {type(e).__name__}: {str(e)}")
                    time.sleep(2)  # Aguardar antes de retry
                    
        except Exception as e:
            sys.stderr.write(f"[STDERR] Erro geral: {type(e).__name__}: {str(e)}\n")
            sys.stderr.flush()
            logger.error(f"[ERROR] Erro geral: {str(e)}")
            time.sleep(2)
    
    # Se chegou aqui, todas as tentativas falharam
    sys.stderr.write(f"[STDERR] FALHA FINAL: Email não foi enviado após {max_tentativas} tentativas\n")
    sys.stderr.flush()
    logger.error(f"[ERROR] Email não foi enviado após {max_tentativas} tentativas para {destinatarios}")


def enviar_email(destinatarios: list, assunto: str, html: str, remetente: str = None) -> bool:
    """
    Envia um email ASSINCRONAMENTE (não bloqueia a requisição)
    
    Args:
        destinatarios: Lista de emails ou string com email único
        assunto: Assunto do email
        html: Corpo HTML do email
        remetente: Email do remetente (opcional)
    
    Returns:
        True se agendado para envio, False caso erro na preparação
    """
    
    # ===== VALIDACAO PRE-ENVIO =====
    
    if not HAS_FLASK_MAIL:
        logger.error("[ERROR] Flask-Mail nao disponivel - email nao pode ser enviado")
        return False
    
    if not mail:
        logger.error("[ERROR] Email service nao inicializado - email nao pode ser enviado")
        logger.error("   [INFO] Verifique as variaveis de ambiente MAIL_* em RAILWAY_DEPLOYMENT.env")
        return False
    
    # Validar destinatarios
    if not destinatarios:
        logger.warning("[WARNING] Nenhum destinatario especificado")
        return False
    
    # Converter para lista se necessário
    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]
    
    # Validar formato de emails
    destinatarios = [d.strip().lower() for d in destinatarios if d and isinstance(d, str)]
    if not destinatarios:
        logger.warning("[⚠️] Lista de destinatários vazia ou inválida")
        return False
    
    # Validar assunto
    if not assunto or not assunto.strip():
        logger.warning("[⚠️] Assunto do email vazio")
        return False
    
    # Validar HTML
    if not html or not html.strip():
        logger.warning("[⚠️] Corpo do email vazio")
        return False
    
    # ===== PREPARAR EMAIL =====
    
    try:
        # Usar remetente configurado ou fallback
        if not remetente or remetente == 'noreply@battlezone.local':
            try:
                remetente = current_app.config.get('MAIL_USERNAME', 'noreply@battlezone.local')
            except RuntimeError:
                remetente = 'noreply@battlezone.local'
        
        # Log detalhado (sem expor email real dos usuários)
        destinatarios_masked = [d[:3] + '***' + d[d.find('@'):] if '@' in d else d for d in destinatarios]
        logger.debug(f"[INFO] Preparando email:")
        logger.debug(f"     Para: {destinatarios_masked}")
        logger.debug(f"     Assunto: {assunto[:50]}...")
        logger.debug(f"     Remetente: {remetente}")
        
        # ===== ENVIAR EMAIL ASSINCRONAMENTE (NÃO BLOQUEIA) =====
        # Inicia thread para enviar, função retorna imediatamente
        
        # Capturar app context para passar à thread
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            logger.error("[ERROR] Nao conseguiu capturar app context para thread")
            return False
        
        thread = threading.Thread(
            target=_enviar_email_thread,
            args=(app, destinatarios, assunto, html, remetente),
            daemon=True
        )
        thread.start()
        
        logger.info(f"[OK] Email agendado para envio (async)")
        logger.info(f"     Para: {len(destinatarios)} destinatário(s)")
        logger.info(f"     Assunto: {assunto[:50]}...")
        
        return True
        
    except Exception as e:
        # ===== TRATAMENTO DE ERRO DETALHADO =====
        
        logger.error(f"[ERROR] ERRO ao enviar email: {str(e)}")
        logger.error(f"     Tipo de erro: {type(e).__name__}")
        logger.error(f"     Destinatarios: {destinatarios}")
        logger.error(f"     Assunto: {assunto}")
        
        # Tentar identificar tipo de erro
        error_str = str(e).lower()
        
        if 'connection' in error_str or 'timeout' in error_str:
            logger.error("   💡 Problema de conexão SMTP - verifique:")
            logger.error("     - MAIL_SERVER está correto?")
            logger.error("     - MAIL_PORT está correto?")
            logger.error("     - Firewall está bloqueando SMTP?")
        
        elif 'auth' in error_str or 'credential' in error_str or 'unauthorized' in error_str:
            logger.error("   💡 Erro de autenticação - verifique:")
            logger.error("     - MAIL_USERNAME está correto?")
            logger.error("     - MAIL_PASSWORD está correto?")
            logger.error("     - Está usando 'Senha de Aplicativo' do Gmail (não a senha da conta)?")
        
        elif 'smtpauthenticationerror' in error_str:
            logger.error("   💡 Autenticação SMTP falhou")
            logger.error("     - Para Gmail: Use 'Senha de Aplicativo' em https://myaccount.google.com/apppasswords")
            logger.error("     - Verifique se 2FA está ativado na conta")
        
        elif 'tls' in error_str.lower():
            logger.error("   💡 Erro TLS/SSL - verifique:")
            logger.error("     - MAIL_USE_TLS está configurado como true?")
            logger.error("     - Certificados SSL estão válidos?")
        
        return False


def enviar_notificacao_solicitacao(solicitacao, app):
    """
    Envia notificação de nova solicitação para todos os admins/gerentes
    
    Args:
        solicitacao: Objeto Solicitacao
        app: Aplicação Flask (para contexto de app_context)
    """
    from backend.models import User
    
    if not mail:
        logger.warning("⚠️ Email service not initialized, cannot send notification")
        return False
    
    try:
        # Buscar todos os admins e gerentes
        admins_gerentes = User.query.filter(
            User.nivel.in_(['admin', 'gerente']),
            User.status == 'aprovado'
        ).all()
        
        if not admins_gerentes:
            logger.warning("⚠️ Nenhum admin/gerente configurado com email")
            return False
        
        # Emails dos admins/gerentes
        emails_destinatarios = [user.email for user in admins_gerentes if user.email]
        
        if not emails_destinatarios:
            logger.warning("⚠️ Nenhum email cadastrado para admins/gerentes")
            return False
        
        # Usar contexto da aplicação para gerar URLs
        with app.app_context():
            # Gerar link para visualizar solicitação no painel admin
            link_visualizar = url_for('admin_solicitacoes', _external=True)
            link_aprovar = url_for('admin_solicitacoes', _external=True)  # Mesmo link, pode filtrar por ID depois
            
            # Template HTML do email
            html_email = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #FF6B00; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                    .info-box {{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
                    .action-box {{ text-align: center; margin: 20px 0; }}
                    .btn {{ display: inline-block; padding: 12px 30px; background-color: #FF6B00; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                    .btn:hover {{ background-color: #e55a00; }}
                    .footer {{ color: #666; font-size: 12px; margin-top: 20px; text-align: center; }}
                    .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                    .detail-row strong {{ color: #333; }}
                    .status-badge {{ display: inline-block; padding: 5px 10px; background-color: #ffc107; color: #333; border-radius: 3px; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎮 Battlezone - Nova Solicitação de Acesso</h1>
                    </div>
                    
                    <div class="content">
                        <p>Olá,</p>
                        <p>Uma <strong>nova solicitação de acesso</strong> foi enviada ao sistema Battlezone. Verifique os detalhes abaixo:</p>
                        
                        <div class="info-box">
                            <h3 style="margin-top: 0;">📋 Informações do Solicitante</h3>
                        </div>
                        
                        <div class="details">
                            <div class="detail-row">
                                <strong>Nome Completo:</strong>
                                <span>{solicitacao.nome}</span>
                            </div>
                            <div class="detail-row">
                                <strong>Warname:</strong>
                                <span>{solicitacao.usuario}</span>
                            </div>
                            <div class="detail-row">
                                <strong>Email:</strong>
                                <span><a href="mailto:{solicitacao.email}">{solicitacao.email}</a></span>
                            </div>
                            <div class="detail-row">
                                <strong>CPF:</strong>
                                <span>{solicitacao.cpf}</span>
                            </div>
                            <div class="detail-row">
                                <strong>Telefone:</strong>
                                <span>{solicitacao.telefone}</span>
                            </div>
                            <div class="detail-row">
                                <strong>Data de Nascimento:</strong>
                                <span>{solicitacao.data_nascimento}</span>
                            </div>
                            <div class="detail-row">
                                <strong>Nível:</strong>
                                <span><span class="status-badge">OPERADOR</span></span>
                            </div>
                            <div class="detail-row" style="border-bottom: none;">
                                <strong>Enviado em:</strong>
                                <span>{solicitacao.created_at.strftime('%d/%m/%Y às %H:%M') if solicitacao.created_at else 'Agora'}</span>
                            </div>
                        </div>
                        
                        <div class="info-box">
                            <strong>⏳ Ação Necessária:</strong> Acesse o painel administrativo para aprovar ou rejeitar esta solicitação.
                        </div>
                        
                        <div class="action-box">
                            <a href="{link_visualizar}" class="btn">
                                Acessar Painel Admin
                            </a>
                        </div>
                        
                        <div class="footer">
                            <p>Este é um email automático. Não responda este email.</p>
                            <p>Battlezone © 2026</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Enviar email
            from flask import current_app
            mail_username = current_app.config.get('MAIL_USERNAME', 'noreply@battlezone.local')
            
            sucesso = enviar_email(
                emails_destinatarios,
                f"🔔 Nova Solicitação de Acesso - {solicitacao.usuario}",
                html_email,
                remetente=mail_username
            )
            
            return sucesso
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar notificação de solicitação: {str(e)}")
        return False


def enviar_confirmacao_solicitacao(usuario_email: str, nome_usuario: str, app):
    """
    Envia email de confirmação para o usuário que enviou a solicitação
    
    Args:
        usuario_email: Email do solicitante
        nome_usuario: Nome do solicitante
        app: Aplicação Flask
    """
    if not mail:
        logger.warning("⚠️ Email service not initialized")
        return False
    
    try:
        with app.app_context():
            link_login = url_for('auth.login', _external=True)
            
            html_email = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #FF6B00; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                    .success-box {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; color: #155724; }}
                    .info-box {{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
                    .footer {{ color: #666; font-size: 12px; margin-top: 20px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎮 Battlezone - Solicitação Recebida</h1>
                    </div>
                    
                    <div class="content">
                        <p>Olá <strong>{nome_usuario}</strong>,</p>
                        
                        <div class="success-box">
                            <h3 style="margin-top: 0;">✅ Solicitação Enviada com Sucesso!</h3>
                            <p>Sua solicitação de acesso foi recebida com sucesso. Agora aguarde a aprovação do administrador do sistema.</p>
                        </div>
                        
                        <div class="info-box">
                            <strong>📌 Próximos Passos:</strong>
                            <ul>
                                <li>O administrador analisará sua solicitação</li>
                                <li>Você receberá um email quando sua conta for aprovada</li>
                                <li>Para agilizar, entre em contato conosco por WhatsApp ou telefone</li>
                            </ul>
                        </div>
                        
                        <p>Se você tiver dúvidas ou precisar de mais informações, entre em contato com o suporte.</p>
                        
                        <div class="footer">
                            <p>Este é um email automático. Não responda este email.</p>
                            <p>Battlezone © 2026</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            from flask import current_app
            mail_username = current_app.config.get('MAIL_USERNAME', 'noreply@battlezone.local')
            
            sucesso = enviar_email(
                usuario_email,
                "✅ Solicitação Recebida - Battlezone",
                html_email,
                remetente=mail_username
            )
            
            return sucesso
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar confirmação de solicitação: {str(e)}")
        return False


def enviar_email_reset_senha(usuario_email: str, nome_usuario: str, reset_link: str) -> bool:
    """
    Envia email com link para reset de senha
    
    Args:
        usuario_email: Email do usuário
        nome_usuario: Nome do usuário
        reset_link: Link completo para reset de senha
    
    Returns:
        True se enviado com sucesso, False caso contrário
    """
    # ===== VALIDACAO PRE-ENVIO =====
    
    if not mail:
        logger.error("[ERROR] Email service nao inicializado - nao pode enviar reset de senha")
        return False
    
    if not usuario_email or not usuario_email.strip():
        logger.warning("[WARNING] Email do usuario vazio")
        return False
    
    if not reset_link or not reset_link.strip():
        logger.warning("[WARNING] Link de reset vazio")
        return False
    
    usuario_email = usuario_email.strip().lower()
    nome_usuario = (nome_usuario or 'Usuário').strip()
    
    try:
        # ===== PREPARAR HTML DO EMAIL =====
        
        html_email = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%); color: white; padding: 30px; text-align: center; border-radius: 5px 5px 0 0; }}
                .header h1 {{ margin: 0; font-size: 28px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
                .content {{ background-color: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                .warning-box {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 3px; color: #856404; }}
                .button-container {{ text-align: center; margin: 30px 0; }}
                .reset-button {{ 
                    display: inline-block;
                    padding: 15px 40px;
                    background-color: #FF6B00;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 16px;
                    transition: background-color 0.3s;
                }}
                .reset-button:hover {{ background-color: #FF8C00; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
                .security-tips {{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 3px; }}
                .security-tips strong {{ color: #1a5276; }}
                .security-tips ul {{ margin: 10px 0; padding-left: 20px; }}
                .security-tips li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮 BATTLEZONE</h1>
                    <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Redefinir Senha</p>
                </div>
                
                <div class="content">
                    <p>Olá <strong>{nome_usuario}</strong>,</p>
                    
                    <p>Você solicitou a redefinição de sua senha no BattleZone. Clique no botão abaixo para criar uma nova senha:</p>
                    
                    <div class="button-container">
                        <a href="{reset_link}" class="reset-button">Redefinir Minha Senha</a>
                    </div>
                    
                    <p style="text-align: center; color: #666; font-size: 13px; margin-top: 15px;">
                        Ou copie e cole este link no seu navegador:<br>
                        <code style="background-color: #f5f5f5; padding: 5px 10px; border-radius: 3px; word-break: break-all;">
                            {reset_link}
                        </code>
                    </p>
                    
                    <div class="warning-box">
                        <strong>⏰ ATENÇÃO:</strong> Este link é válido por apenas 30 minutos. Se não redefinir sua senha dentro deste prazo, você precisará solicitar um novo link.
                    </div>
                    
                    <div class="security-tips">
                        <strong>🔒 Dicas de Segurança:</strong>
                        <ul>
                            <li>Sua nova senha deve ter no mínimo 8 caracteres</li>
                            <li>Inclua letras maiúsculas, minúsculas e números</li>
                            <li>Use uma senha que você não utiliza em outros sites</li>
                            <li>Nunca compartilhe sua senha com outras pessoas</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 25px; color: #666;">
                        Não solicitou esta redefinição de senha? Pode ignorar este email com segurança. 
                        Apenas alguém com acesso ao seu email pode redefinir sua senha.
                    </p>
                    
                    <div class="footer">
                        <p style="margin: 0 0 10px 0;">Este é um email automático. Não responda este email.</p>
                        <p style="margin: 0;">
                            <strong>Precisa de ajuda?</strong><br>
                            Entre em contato conosco por WhatsApp ou através do site
                        </p>
                        <p style="margin-top: 15px; font-style: italic;">BattleZone © 2026 - Todos os direitos reservados</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # ===== OBTER REMETENTE COM APP CONTEXT =====
        
        try:
            mail_username = current_app.config.get('MAIL_USERNAME', 'noreply@battlezone.local')
        except RuntimeError:
            # Sem app context - usar fallback
            mail_username = 'noreply@battlezone.local'
            logger.warning("[⚠️] Sem app context ativo - usando remetente padrão")
        
        # ===== ENVIAR EMAIL =====
        
        sucesso = enviar_email(
            [usuario_email],
            "🔑 Redefinir Senha - BattleZone",
            html_email,
            remetente=mail_username
        )
        
        if sucesso:
            logger.info(f"[OK] Email de reset de senha enviado para: {usuario_email[:3]}***@...") 
        else:
            logger.error(f"[ERROR] Falha ao enviar email de reset de senha para: {usuario_email}")
        
        return sucesso
    
    except Exception as e:
        logger.error(f"[ERROR] EXCE CAO ao enviar email de reset de senha: {str(e)}")
        logger.error(f"     Tipo: {type(e).__name__}")
        logger.error(f"     Para: {usuario_email}")
        return False
