# auth_security.py - FUNÇÕES DE SEGURANÇA DE AUTENTICAÇÃO

import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

# ==================== 2FA - TOTP ====================

def gerar_secret_2fa():
    """
    Gera um novo segredo TOTP para 2FA
    
    Returns:
        str: Segredo em base32 (ex: "JBSWY3DPEBLW64TMMQ======")
    """
    return pyotp.random_base32()

def gerar_qr_code(username, secret, issuer="BattleZone"):
    """
    Gera um QR code para o usuário ler com autenticador
    
    Args:
        username (str): Username do usuário
        secret (str): Segredo TOTP
        issuer (str): Nome da aplicação
    
    Returns:
        str: QR code em base64
    """
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name=issuer)
    
    # Gerar QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Converter para base64
    buffer = io.BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

def validar_codigo_2fa(secret, codigo):
    """
    Valida um código TOTP de 6 dígitos
    
    Args:
        secret (str): Segredo do usuário
        codigo (str): Código digitado (ex: "123456")
    
    Returns:
        bool: True se válido, False caso contrário
    """
    try:
        totp = pyotp.TOTP(secret)
        # Aceitar código atual e 1 janela anterior (para timeouts)
        return totp.verify(codigo, valid_window=1)
    except:
        return False

def gerar_backup_codes(quantidade=10):
    """
    Gera códigos de backup para recuperação de 2FA
    
    Args:
        quantidade (int): Número de códigos a gerar
    
    Returns:
        list: Lista de códigos (ex: ["XXXX-XXXX-XXXX", ...])
    """
    import secrets
    codes = []
    for _ in range(quantidade):
        # Gerar código: XXXX-XXXX-XXXX (12 caracteres + 2 hífens)
        code = '-'.join([
            secrets.token_hex(2).upper(),
            secrets.token_hex(2).upper(),
            secrets.token_hex(2).upper()
        ])
        codes.append(code)
    return codes

# ==================== RATE LIMITING ====================

from collections import defaultdict
import time

class RateLimiter:
    """
    Rate limiter em memória para proteção contra força bruta
    """
    def __init__(self):
        self.attempts = defaultdict(list)  # IP -> [timestamps]
    
    def is_rate_limited(self, ip, max_attempts=5, window_seconds=900):  # 15 min
        """
        Verifica se IP excedeu limite de tentativas
        
        Args:
            ip (str): IP do cliente
            max_attempts (int): Máximo de tentativas
            window_seconds (int): Janela de tempo em segundos
        
        Returns:
            tuple: (is_limited, remaining, reset_time)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Limpar tentativas antigas
        self.attempts[ip] = [t for t in self.attempts[ip] if t > window_start]
        
        # Verificar limite
        remaining = max_attempts - len(self.attempts[ip])
        is_limited = len(self.attempts[ip]) >= max_attempts
        
        # Tempo até reset (quando a tentativa mais antiga sair da janela)
        reset_time = None
        if self.attempts[ip]:
            oldest = self.attempts[ip][0]
            reset_time = int((oldest + window_seconds - now) / 60)  # minutos
        
        return is_limited, max(0, remaining), reset_time
    
    def registrar_tentativa(self, ip):
        """Registra uma nova tentativa de login"""
        self.attempts[ip].append(time.time())
    
    def limpar_ip(self, ip):
        """Remove IP do rate limiter (após login bem-sucedido)"""
        if ip in self.attempts:
            del self.attempts[ip]

# Instância global
rate_limiter = RateLimiter()

# ==================== LOGGING DE SEGURANÇA ====================

def log_security_event(event_type, username=None, ip_address=None, details=None):
    """
    Log estruturado de eventos de segurança
    
    Args:
        event_type (str): Tipo (LOGIN_SUCESSO, LOGIN_FALHA, 2FA_ATIVADO, etc)
        username (str): Username afetado
        ip_address (str): IP do cliente
        details (dict): Detalhes adicionais
    """
    from models import Log, db
    
    try:
        log = Log(
            usuario=username or 'guest',
            acao=event_type,
            detalhes=str(details) if details else '',
            ip_address=ip_address or ''
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Erro ao registrar log de segurança: {e}")

def log_login_attempt(username, success, ip_address, motivo=None):
    """Log simplificado para tentativas de login"""
    event = "LOGIN_SUCESSO" if success else "LOGIN_FALHA"
    details = motivo or ("Autenticado com sucesso" if success else "Falha de autenticação")
    log_security_event(event, username, ip_address, {"motivo": details})

def log_2fa_event(username, event, ip_address, success=True):
    """Log de eventos de 2FA"""
    status = "SUCESSO" if success else "FALHA"
    event_type = f"2FA_{event.upper()}_{status}"
    log_security_event(event_type, username, ip_address)

# ==================== DECORADORES ====================

def requer_2fa(f):
    """
    Decorator para rotas que requerem 2FA verificado
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import redirect, url_for, flash
        
        if not current_user.is_authenticated:
            flash('Faça login primeiro.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Verificar se 2FA está ativado e verificado na sessão
        if current_user.two_factor_enabled:
            if not request.session.get('2fa_verified'):
                flash('2FA pendente. Complete a autenticação.', 'warning')
                return redirect(url_for('auth.verify_2fa'))
        
        return f(*args, **kwargs)
    
    return decorated_function

# ==================== VALIDAÇÃO ====================

def validar_codigo_2fa_format(codigo):
    """Valida se o código tem formato correto (6 dígitos)"""
    if not codigo:
        return False, "Código não pode estar vazio"
    
    codigo_clean = codigo.replace(' ', '')
    
    if not codigo_clean.isdigit():
        return False, "Código deve conter apenas números"
    
    if len(codigo_clean) != 6:
        return False, f"Código deve ter 6 dígitos (você tem {len(codigo_clean)})"
    
    return True, "OK"

def validar_backup_code_format(code):
    """Valida formato de backup code (XXXX-XXXX-XXXX)"""
    if not code or len(code) != 14:
        return False
    
    parts = code.split('-')
    if len(parts) != 3:
        return False
    
    return all(len(p) == 4 and p.isupper() for p in parts)
