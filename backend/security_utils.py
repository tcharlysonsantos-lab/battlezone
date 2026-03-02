# security_utils.py - FUNÇÕES DE SEGURANÇA
import os
import mimetypes
from werkzeug.utils import secure_filename
from datetime import datetime

# ==================== VALIDAÇÃO DE UPLOAD SEGURA ====================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Mapeamento de extensões para MIME types esperados
MIME_TYPES = {
    '.jpg': {'image/jpeg'},
    '.jpeg': {'image/jpeg'},
    '.png': {'image/png'},
    '.gif': {'image/gif'},
    '.bmp': {'image/bmp', 'image/x-bmp'},
    '.webp': {'image/webp'},
}

def allowed_file_secure(filename, max_size=None, file_obj=None):
    """
    Valida arquivo de forma SEGURA
    
    Args:
        filename (str): Nome do arquivo
        max_size (int): Tamanho máximo em bytes
        file_obj: Objeto FileStorage do Flask (para verificar MIME type real)
    
    Returns:
        tuple: (bool válido, str mensagem de erro ou "OK")
    """
    
    # 1. VALIDAR NOME
    if not filename or filename == '':
        return False, "Nome de arquivo inválido"
    
    if len(filename) > 255:
        return False, "Nome de arquivo muito longo (máx 255 caracteres)"
    
    # 2. VALIDAR EXTENSÃO
    if '.' not in filename:
        return False, "Arquivo sem extensão"
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extensão não permitida: .{ext}. Permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # 3. PROTEGER CONTRA DOUBLE EXTENSION (fake.exe.png)
    parts = filename.rsplit('.', 1)[0].split('.')
    if len(parts) > 1:
        # Verificar se a penúltima "extensão" é suspeita
        suspicious = ['exe', 'bat', 'cmd', 'sh', 'py', 'php', 'asp', 'jsp', 'jar']
        if parts[-1].lower() in suspicious:
            return False, "Arquivo com extensão suspeita detectado (double extension attack)"
    
    # 4. VALIDAR MIME TYPE REAL (se arquivo foi enviado)
    if file_obj:
        # Detectar MIME type real do arquivo (não confia na extensão)
        mime_type = file_obj.content_type or 'application/octet-stream'
        
        expected_mimes = MIME_TYPES.get(f'.{ext}', set())
        
        if expected_mimes and mime_type not in expected_mimes:
            return False, f"Tipo MIME suspeito: {mime_type}. Esperado: {expected_mimes}"
    
    # 5. VALIDAR TAMANHO
    if max_size and file_obj:
        # Ler arquivo em chunks para não sobrecarregar memória
        file_obj.seek(0, 2)  # Ir ao final
        file_size = file_obj.tell()
        file_obj.seek(0)  # Voltar ao início
        
        if file_size > max_size:
            return False, f"Arquivo muito grande: {file_size/1024/1024:.2f}MB. Máximo: {max_size/1024/1024:.2f}MB"
    
    return True, "OK"

def safe_filename_with_timestamp(filename):
    """
    Gera um nome seguro de arquivo com timestamp
    
    Args:
        filename (str): Nome original do arquivo
    
    Returns:
        str: Nome seguro (ex: "equipe_20260302_143022.jpg")
    """
    # Extrair extensão
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
    else:
        ext = 'bin'
    
    # Gerar nome seguro com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = f"upload_{timestamp}.{ext}"
    
    return safe_name

def create_upload_directory(path):
    """
    Cria diretório de upload com permissões seguras
    
    Args:
        path (str): Caminho do diretório
    """
    os.makedirs(path, exist_ok=True)
    
    # Em Windows, não há permissões POSIX, skipa
    # Em Linux, você poderia fazer: os.chmod(path, 0o750)

# ==================== VALIDAÇÃO DE ENTRADA ====================

def sanitize_filename(filename):
    """Remove caracteres perigosos do nome"""
    return secure_filename(filename)

def is_safe_string(text, max_length=1000, allow_html=False):
    """
    Valida se texto é seguro
    
    Args:
        text (str): Texto a validar
        max_length (int): Tamanho máximo
        allow_html (bool): Permitir HTML
    
    Returns:
        tuple: (bool válido, str mensagem)
    """
    if not text or not isinstance(text, str):
        return False, "Texto inválido"
    
    if len(text) > max_length:
        return False, f"Texto muito longo (máx {max_length} caracteres)"
    
    if not allow_html:
        # Verificar se tem HTML/scripts
        dangerous_chars = ['<', '>', '{', '}', 'javascript:', 'onerror=', 'onclick=']
        text_lower = text.lower()
        for char in dangerous_chars:
            if char in text_lower:
                return False, "Texto contém caracteres não permitidos (possível XSS)"
    
    return True, "OK"

# ==================== LOGGING DE SEGURANÇA ====================

def log_security_event(user, event_type, details, ip_address=None):
    """
    Log de eventos de segurança
    
    Args:
        user (str): Usuário que fez a ação
        event_type (str): Tipo de evento (LOGIN_FAIL, UPLOAD_REJECT, etc)
        details (str): Detalhes do evento
        ip_address (str): IP do cliente
    
    Returns:
        dict: Log formatado
    """
    from .models import Log, db
    
    log = Log(
        usuario=user,
        acao=event_type,
        detalhes=details,
        ip_address=ip_address
    )
    
    try:
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"❌ Erro ao registrar log: {e}")
    
    return {
        'timestamp': datetime.now().isoformat(),
        'user': user,
        'event': event_type,
        'details': details,
        'ip': ip_address
    }
