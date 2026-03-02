"""
ngrok_security.py - Middleware de Segurança para Ngrok
Valida API Key e registra acessos externos
"""

import os
import json
import logging
from functools import wraps
from datetime import datetime
from pathlib import Path
from flask import request, jsonify, current_app

# Configurar logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

ngrok_logger = logging.getLogger('ngrok_security')
handler = logging.FileHandler('logs/ngrok_security.log')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
ngrok_logger.addHandler(handler)
ngrok_logger.setLevel(logging.INFO)

def get_api_key():
    """Carrega a API Key do arquivo de configuração"""
    try:
        with open('.ngrok/config.json') as f:
            config = json.load(f)
            return config.get('api_key')
    except Exception as e:
        ngrok_logger.error(f"Erro ao carregar chave de API: {e}")
        return None

def validar_api_key(f):
    """
    Decorator para validar API Key em requisições Ngrok
    
    Uso:
        @app.route('/api/dados')
        @validar_api_key
        def get_dados():
            return jsonify({'dados': 'valor'})
    
    Cliente envia:
        curl -H "Authorization: Bearer <api_key>" https://url.ngrok.io/api/dados
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se é localhost
        remote_addr = request.remote_addr
        is_localhost = remote_addr in ['127.0.0.1', 'localhost', '::1']
        
        # Se for localhost, não exigir API Key
        if is_localhost:
            ngrok_logger.debug(f"Acesso local de {remote_addr} - API Key não exigida")
            return f(*args, **kwargs)
        
        # Para acessos remotos, validar API Key
        api_key_esperada = get_api_key()
        if not api_key_esperada:
            ngrok_logger.error("API Key não configurada!")
            return jsonify({'erro': 'Segurança não configurada'}), 500
        
        # Tentar obter API Key do header Authorization
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header:
            ngrok_logger.warning(f"Acesso negado de {remote_addr}: sem Authorization header")
            return jsonify({'erro': 'Autenticação necessária'}), 401
        
        try:
            # Format esperado: "Bearer <api_key>"
            parts = auth_header.split(' ')
            if len(parts) != 2 or parts[0] != 'Bearer':
                ngrok_logger.warning(f"Acesso negado de {remote_addr}: formato inválido")
                return jsonify({'erro': 'Formato Authorization inválido'}), 401
            
            api_key_fornecida = parts[1]
            
            if api_key_fornecida != api_key_esperada:
                ngrok_logger.warning(f"Acesso negado de {remote_addr}: API Key inválida")
                return jsonify({'erro': 'Autenticação falhou'}), 403
            
            ngrok_logger.info(f"Acesso autorizado de {remote_addr}")
            return f(*args, **kwargs)
            
        except Exception as e:
            ngrok_logger.error(f"Erro ao validar API Key: {e}")
            return jsonify({'erro': 'Erro de autenticação'}), 500
    
    return decorated_function

def log_ngrok_acesso():
    """Middleware para logar todos os acessos do Ngrok"""
    if request.remote_addr not in ['127.0.0.1', 'localhost', '::1']:
        # Dados da requisição
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'metodo': request.method,
            'endpoint': request.path,
            'user_agent': request.headers.get('User-Agent', 'desconhecido'),
            'tem_api_key': 'Authorization' in request.headers,
        }
        
        # Log em arquivo JSON para análise
        with open('logs/ngrok_access.json', 'a') as f:
            f.write(json.dumps(log_data) + '\n')
        
        # Log também em formato legível
        ngrok_logger.info(
            f"{request.method} {request.path} de {request.remote_addr}"
        )

class NgrokSecurityInit:
    """
    Inicializa a segurança do Ngrok no Flask
    
    Uso em app.py:
        from ngrok_security import NgrokSecurityInit
        
        app = Flask(__name__)
        ngrok_security = NgrokSecurityInit()
        ngrok_security.init_app(app)
    """
    
    def init_app(self, app):
        """Registra os middleware de segurança"""
        
        # Registrar before_request para logar
        @app.before_request
        def securityBefore():
            log_ngrok_acesso()
        
        # Registrar manipulador de erro para requisições sem auth
        @app.errorhandler(401)
        def unauthorized(error):
            return jsonify({'erro': 'Não autorizado'}), 401
        
        @app.errorhandler(403)
        def forbidden(error):
            return jsonify({'erro': 'Acesso negado'}), 403
        
        ngrok_logger.info("Segurança de Ngrok inicializada")

def gerar_curl_exemplo():
    """Gera exemplo de comando curl com a chave"""
    try:
        with open('.ngrok/config.json') as f:
            config = json.load(f)
            api_key = config.get('api_key')
            
        exemplo = f"""
# Exemplo de requisição com curl:
curl -H "Authorization: Bearer {api_key}" \\
     https://sua-url.ngrok.io/auth/login
"""
        return exemplo
    except:
        return "# Erro ao gerar exemplo"

def listar_acessos_recentes(linhas=20):
    """Exibe os últimos acessos logados"""
    try:
        with open('logs/ngrok_access.json', 'r') as f:
            linhas_arquivo = f.readlines()[-linhas:]
        
        print("\n" + "="*70)
        print("  ÚLTIMOS ACESSOS DO NGROK")
        print("="*70)
        
        for linha in linhas_arquivo:
            try:
                dados = json.loads(linha)
                print(f"  {dados['timestamp']}: {dados['metodo']:6} {dados['endpoint']:30} ({dados['ip']})")
            except:
                pass
        
        print("="*70 + "\n")
    except FileNotFoundError:
        print("Nenhum acesso registrado ainda")

if __name__ == '__main__':
    print(gerar_curl_exemplo())
    listar_acessos_recentes()
