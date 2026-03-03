# security_middleware.py - MIDDLEWARES E PROTEÇÕES DE SEGURANÇA
from flask import request, abort, current_app
import logging
import hashlib
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÕES DE SEGURANÇA ====================

# Headers de segurança obrigatórios
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',  # Previne MIME-sniffing
    'X-Frame-Options': 'SAMEORIGIN',  # Previne clickjacking
    'X-XSS-Protection': '1; mode=block',  # XSS Protection
    'Referrer-Policy': 'strict-origin-when-cross-origin',  # Privacy
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',  # Feature policy
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data: https:;",
}

# ==================== APLICAR SECURITY HEADERS ====================
def aplicar_security_headers(f):
    """Decorator para adicionar headers de segurança"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        # Adicionar headers ao response (será feito no after_request)
        return response
    return decorated_function

def add_security_headers(response):
    """Middleware para adicionar headers de segurança a TODAS as respostas"""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    
    # HSTS - Forçar HTTPS por 1 ano
    if not current_app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    return response

# ==================== VALIDAÇÃO DE ENTRADA ====================

MALICIOUS_PATTERNS = [
    '<script',
    'javascript:',
    'on\\w+\\s*=',  # onerror=, onclick=, etc
    'drop\\s+table',  # SQL
    'union\\s+select',  # SQL
    'exec\\s*\\(',  # Code injection
    '../',  # Path traversal
    '..\\',
]

def sanitizar_entrada(valor):
    """Sanitiza entrada para prevenir XSS e SQL injection"""
    if not isinstance(valor, str):
        return valor
    
    import re
    
    # Remover caracteres de controle
    valor = ''.join(char for char in valor if ord(char) >= 32 or char in '\n\r\t')
    
    # Verificar padrões maliciosos
    for pattern in MALICIOUS_PATTERNS:
        if re.search(pattern, valor, re.IGNORECASE):
            logger.warning(f"🚨 Entrada suspeita detectada: {pattern}")
            return None
    
    return valor.strip()

def validar_entrada(f):
    """Decorator para validar todas as entradas POST/PUT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Validar JSON
            if request.is_json:
                data = request.get_json(silent=True)
                if data and isinstance(data, dict):
                    for chave, valor in data.items():
                        if isinstance(valor, str):
                            sanitizado = sanitizar_entrada(valor)
                            if sanitizado is None and valor:
                                logger.warning(f"🚨 Entrada maliciosa bloqueada em {chave}")
                                abort(400)
            
            # Validar form data
            elif request.form:
                for chave, valor in request.form.items():
                    if isinstance(valor, str):
                        sanitizado = sanitizar_entrada(valor)
                        if sanitizado is None and valor:
                            logger.warning(f"🚨 Entrada maliciosa bloqueada em {chave}")
                            abort(400)
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== LOGGING DE SEGURANÇA ====================

def log_security_event(tipo_evento, usuario, detalhes="", nivel="INFO"):
    """Log centralizado de eventos de segurança"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip = request.remote_addr if request else "UNKNOWN"
    user_agent = request.user_agent if request else "UNKNOWN"
    
    mensagem = f"[{timestamp}] {tipo_evento} | Usuario: {usuario} | IP: {ip} | {detalhes}"
    
    if nivel == "WARNING":
        logger.warning(f"⚠️  {mensagem}")
    elif nivel == "ERROR":
        logger.error(f"❌ {mensagem}")
    else:
        logger.info(f"✅ {mensagem}")
    
    # Opcionalmente salvar em arquivo separado de segurança
    try:
        with open('logs/security.log', 'a', encoding='utf-8') as f:
            f.write(f"{mensagem}\n")
    except Exception as e:
        logger.error(f"Erro ao registrar log de segurança: {e}")

# ==================== PROTEÇÃO CONTRA ENUMERAÇÃO DE USUÁRIOS ====================

def respostas_genéricas(f):
    """Decorator para dar respostas genéricas em casos de erro (não revelar se user existe)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Log da exceção real
            logger.error(f"Erro: {str(e)}")
            # Resposta genérica para o usuário
            abort(401)  # Unauthorized em vez de 404
    return decorated_function

# ==================== PROTEÇÃO CONTRA BRUTE FORCE (REDIS OPTIONAL) ====================

# Usar dicionário em memória se Redis não disponível
tentativas_login = {}

def verificar_rate_limit_login(email, max_tentativas=5, janela_minutos=15):
    """Verifica rate limit para tentativas de login"""
    from datetime import datetime, timedelta
    
    chave = f"login:{email}"
    agora = datetime.now()
    
    if chave not in tentativas_login:
        tentativas_login[chave] = []
    
    # Remover tentativas fora da janela
    tentativas_login[chave] = [
        t for t in tentativas_login[chave] 
        if (agora - t).total_seconds() < (janela_minutos * 60)
    ]
    
    if len(tentativas_login[chave]) >= max_tentativas:
        return False
    
    return True

def registrar_tentativa_login(email):
    """Registra tentativa de login"""
    from datetime import datetime
    
    chave = f"login:{email}"
    if chave not in tentativas_login:
        tentativas_login[chave] = []
    
    tentativas_login[chave].append(datetime.now())

# ==================== PROTEÇÃO CONTRA CSRF ====================

def csrf_protegido(f):
    """Decorator para garantir CSRF token em rotas críticas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
            if not token:
                log_security_event("CSRF_ATTEMPT", 
                                 request.remote_addr, 
                                 f"Rota: {request.path}", 
                                 "WARNING")
                abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== HASH DE HASH SEGURO ====================

def hash_seguro(valor, salt=None):
    """Cria hash seguro com SHA256"""
    if salt is None:
        salt = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]
    
    return hashlib.sha256((valor + salt).encode()).hexdigest(), salt
