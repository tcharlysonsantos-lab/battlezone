"""
Email Service - Envia notificações via SendGrid API
Substituiu Flask-Mail por SendGrid para contornar limitações de SMTP em Railway
"""

from flask import url_for, current_app
import logging
import os
import threading
import sys
import time
from functools import wraps

logger = logging.getLogger(__name__)

# Importar SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, Content
    HAS_SENDGRID = True
except ImportError:
    HAS_SENDGRID = False
    logger.warning("[WARNING] SendGrid nao instalado. Emails nao serao enviados. Instale com: pip install sendgrid")
    SendGridAPIClient = None

sg_client = None
MAIL_INITIALIZED = False

def _validar_configuracao_email(app):
    """
    Valida se as configurações de email estão corretas para SendGrid
    
    Returns:
        (is_valid: bool, message: str)
    """
    # Verificar None antes de fazer .strip()
    sendgrid_api_key = app.config.get('SENDGRID_API_KEY')
    if sendgrid_api_key:
        sendgrid_api_key = sendgrid_api_key.strip()
    
    mail_username = app.config.get('MAIL_USERNAME')
    if mail_username:
        mail_username = mail_username.strip()
    
    if not sendgrid_api_key or sendgrid_api_key == 'sua-chave-sendgrid-aqui':
        return False, "SENDGRID_API_KEY não configurado"
    
    if not mail_username or mail_username == 'seu-email@gmail.com' or mail_username == 'noreply@battlezone.local':
        return False, f"MAIL_USERNAME inválido ou não configurado: '{mail_username}'"
    
    # VALIDACAO CRITICA: Verificar se MAIL_USERNAME tem @ (eh um email valido)
    if '@' not in mail_username:
        return False, f"MAIL_USERNAME invalido - nao eh um email: '{mail_username}' (falta @ no email!)"
    
    return True, "✅ Configuração de email válida"


def init_mail(app):
    """
    Inicializa o servico de email SendGrid com a aplicacao Flask
    
    [INFO] IMPORTANTE: Variaveis de ambiente devem estar configuradas:
       - SENDGRID_API_KEY (chave de API do SendGrid)
       - MAIL_USERNAME (email do remetente verificado no SendGrid)
    """
    global sg_client, MAIL_INITIALIZED
    
    if not HAS_SENDGRID:
        logger.error("[ERROR] SendGrid nao instalado!")
        logger.error("   Instale com: pip install sendgrid")
        return
    
    # Validar configuracao
    is_valid, message = _validar_configuracao_email(app)
    
    if not is_valid:
        logger.error(f"[ERROR] Configuracao de email invalida: {message}")
        logger.error("   [WARNING] Desabilitar emails ate que as variaveis de ambiente sejam configuradas.")
        logger.error("   [INFO] Configure SENDGRID_API_KEY e MAIL_USERNAME em Railway Settings > Environment")
        return
    
    try:
        sendgrid_api_key = app.config.get('SENDGRID_API_KEY')
        sg_client = SendGridAPIClient(sendgrid_api_key)
        MAIL_INITIALIZED = True
        
        # Log de sucesso com informacoes (sem expor chave)
        logger.info("[OK] Email service (SendGrid) initialized successfully")
        logger.info(f"   MAIL_USERNAME (From): {app.config.get('MAIL_USERNAME')}")
        logger.info(f"   SENDGRID_API_KEY: {'***' + sendgrid_api_key[-6:]}")
        
    except Exception as e:
        logger.error(f"[ERROR] Falha ao inicializar SendGrid: {str(e)}")
        logger.error(f"   Tipo de erro: {type(e).__name__}")
        logger.error("   Possiveis causas:")
        logger.error("   - SENDGRID_API_KEY inválida ou expirada")
        logger.error("   - MAIL_USERNAME não verificado no SendGrid")


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
    
    if not HAS_SENDGRID:
        return False, "SendGrid não instalado"
    
    if not sg_client or not MAIL_INITIALIZED:
        return False, "Email service não inicializado"
    
    is_valid, message = _validar_configuracao_email(app)
    if not is_valid:
        return False, message
    
    return True, "Email service (SendGrid) operacional"


def _enviar_email_thread(app, destinatarios: list, assunto: str, html: str, remetente: str = None):
    """
    Função interna para enviar email via SendGrid em thread separada (NÃO BLOQUEIA)
    
    Esta função é chamada em uma thread separada para não bloquear a requisição HTTP
    Com retry automático (até 3 tentativas)
    """
    max_tentativas = 3
    tentativa = 0
    
    while tentativa < max_tentativas:
        tentativa += 1
        sys.stderr.write(f"[STDERR] Tentativa {tentativa}/{max_tentativas} de enviar email via SendGrid\n")
        sys.stderr.flush()
        logger.info(f"[INFO] Tentativa {tentativa} de enviar email para {destinatarios}")
        
        try:
            if not sg_client:
                logger.error("[ERROR] SendGrid client nao inicializado")
                sys.stderr.write(f"[STDERR] SendGrid client não inicializado\n")
                sys.stderr.flush()
                return
            
            # Usar app context fornecido
            with app.app_context():
                logger.info(f"[INFO] App context ativado")
                
                # Preparar remetente
                if not remetente or remetente == 'noreply@battlezone.local':
                    remetente = app.config.get('MAIL_USERNAME', 'noreply@battlezone.local')
                
                logger.info(f"[INFO] Preparando email via SendGrid")
                sys.stderr.write(f"[STDERR] Preparando email para envio via SendGrid...\n")
                sys.stderr.flush()
                
                try:
                    # Criar mensagem para SendGrid
                    message = Mail(
                        from_email=Email(remetente),
                        to_emails=destinatarios,  # SendGrid aceita lista de emails
                        subject=assunto,
                        html_content=Content("text/html", html)
                    )
                    
                    logger.info(f"[INFO] Mensagem preparada para SendGrid")
                    sys.stderr.write(f"[STDERR] Enviando via API SendGrid...\n")
                    sys.stderr.flush()
                    
                    # Enviar email via API SendGrid (nenhum timeout de socket necessário)
                    response = sg_client.send(message)
                    
                    # Verificar response status (200-299 = sucesso)
                    if 200 <= response.status_code <= 299:
                        logger.info(f"[OK] Email enviado com sucesso na tentativa {tentativa}")
                        logger.info(f"   Status: {response.status_code}")
                        sys.stderr.write(f"[STDERR] Email enviado com sucesso! (Status: {response.status_code})\n")
                        sys.stderr.flush()
                        return  # Sucesso!
                    else:
                        # Erro da API
                        error_msg = f"SendGrid API retornou status {response.status_code}"
                        logger.warning(f"[WARNING] {error_msg} na tentativa {tentativa}")
                        sys.stderr.write(f"[STDERR] Erro na tentativa {tentativa}: {error_msg}\n")
                        sys.stderr.flush()
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
    Envia um email ASSINCRONAMENTE via SendGrid (não bloqueia a requisição)
    
    Args:
        destinatarios: Lista de emails ou string com email único
        assunto: Assunto do email
        html: Corpo HTML do email
        remetente: Email do remetente (opcional)
    
    Returns:
        True se agendado para envio, False caso erro na preparação
    """
    
    # ===== VALIDACAO PRE-ENVIO =====
    
    if not HAS_SENDGRID:
        logger.error("[ERROR] SendGrid nao disponivel - email nao pode ser enviado")
        return False
    
    if not sg_client:
        logger.error("[ERROR] Email service nao inicializado - email nao pode ser enviado")
        logger.error("   [INFO] Verifique as variaveis de ambiente SENDGRID_API_KEY e MAIL_USERNAME")
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
        
        logger.info(f"[OK] Email agendado para envio (async) via SendGrid")
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
        
        if 'api' in error_str or '401' in error_str or '403' in error_str:
            logger.error("   Erro de autenticação - verifique:")
            logger.error("     - SENDGRID_API_KEY está correto?")
            logger.error("     - Chave não expirou?")
        
        elif 'email' in error_str or 'sender' in error_str:
            logger.error("   Erro com email - verifique:")
            logger.error("     - MAIL_USERNAME (From email) não verificado no SendGrid?")
            logger.error("     - Email está bem formatado?")
        
        return False


def enviar_notificacao_solicitacao(solicitacao, app):
    """
    Envia notificação de nova solicitação para todos os admins/gerentes
    
    Args:
        solicitacao: Objeto Solicitacao
        app: Aplicação Flask (para contexto de app_context)
    """
    from backend.models import User
    
    if not sg_client:
        logger.warning("Email service not initialized, cannot send notification")
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
    if not sg_client:
        logger.warning("Email service not initialized")
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
    
    if not sg_client:
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
        
        html_email = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 28px; letter-spacing: 1px; }}
        .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
        .content {{ background-color: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .content p {{ line-height: 1.6; color: #333; margin: 15px 0; }}
        .button-box {{ text-align: center; margin: 35px 0 25px 0; }}
        .btn {{ 
            display: inline-block;
            padding: 14px 48px;
            background-color: #FF6B00;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            border: 2px solid #FF6B00;
            transition: all 0.3s ease;
            mso-padding-alt: 14px 48px;
            mso-border-alt: medium none #FF6B00;
        }}
        .btn:hover {{ background-color: #ff7d1a; border-color: #ff7d1a; text-decoration: none; }}
        .link-box {{ 
            background-color: #f9f9f9; 
            padding: 15px; 
            border-left: 4px solid #FF6B00; 
            margin: 20px 0; 
            border-radius: 4px; 
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        .link-box a {{ color: #FF6B00; text-decoration: none; word-break: break-all; }}
        .warning-box {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 4px; color: #856404; font-size: 14px; }}
        .security-tips {{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 4px; font-size: 13px; }}
        .security-tips strong {{ color: #1a5276; display: block; margin-bottom: 10px; }}
        .security-tips ul {{ margin: 8px 0; padding-left: 20px; }}
        .security-tips li {{ margin: 4px 0; }}
        .footer {{ color: #999; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid #eee; padding-top: 20px; line-height: 1.5; }}
        .footer a {{ color: #FF6B00; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BATTLEZONE</h1>
            <p>Redefinir Senha</p>
        </div>
        
        <div class="content">
            <p>Ola <strong>{nome_usuario}</strong>,</p>
            
            <p>Voce solicitou a redefinicao de sua senha no BattleZone. Clique no botao abaixo para criar uma nova senha:</p>
            
            <div class="button-box">
                <table border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                    <tr>
                        <td style="border-radius: 6px; background: #FF6B00;" align="center">
                            <a href="{reset_link}" style="display: inline-block; padding: 14px 48px; background: #FF6B00; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
                                Redefinir Minha Senha
                            </a>
                        </td>
                    </tr>
                </table>
            </div>
            
            <p style="text-align: center; color: #999; font-size: 12px; margin: 20px 0;">
                Ou copie e cole este link no seu navegador:
            </p>
            
            <div class="link-box">
                <a href="{reset_link}">{reset_link}</a>
            </div>
            
            <div class="warning-box">
                <strong>ATENCAO:</strong> Este link e valido por apenas 30 minutos. Se nao redefinir sua senha dentro deste prazo, voce precisara solicitar um novo link.
            </div>
            
            <div class="security-tips">
                <strong>Dicas de Seguranca:</strong>
                <ul>
                    <li>Sua nova senha deve ter no minimo 8 caracteres</li>
                    <li>Inclua letras maiusculas, minusculas, numeros e simbolos</li>
                    <li>Use uma senha unica que nao utiliza em outros sites</li>
                    <li>Nunca compartilhe sua senha com outras pessoas</li>
                </ul>
            </div>
            
            <p style="margin-top: 25px; color: #666; font-size: 13px;">
                Nao solicitou esta redefinicao de senha? Pode ignorar este email com seguranca. Apenas alguem com acesso ao seu email pode redefinir sua senha.
            </p>
            
            <div class="footer">
                <p style="margin: 0 0 10px 0;">Este e um email automatico. Nao responda este email.</p>
                <p style="margin: 10px 0;">
                    Precisa de ajuda? Entre em contato conosco por WhatsApp ou atraves do site.
                </p>
                <p style="margin-top: 15px; font-style: italic; font-size: 11px;">BattleZone 2026 - Todos os direitos reservados</p>
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
