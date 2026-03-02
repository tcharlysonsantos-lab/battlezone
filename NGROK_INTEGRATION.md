"""
INTEGRATION GUIDE - Como integrar Ngrok Security ao Flask App

Este arquivo mostra como adicionar o middleware de Ngrok ao seu app.py
"""

# ============================================================================
# OPÇÃO 1: Adicionar ao app.py (RECOMENDADO)
# ============================================================================

"""
No seu app.py, adicione estas linhas após criar a app Flask:

from ngrok_security import NgrokSecurityInit

app = Flask(__name__)
# ... outras configurações ...

# Inicializar segurança de Ngrok
ngrok_security = NgrokSecurityInit()
ngrok_security.init_app(app)

# ... resto do app ...
"""

# ============================================================================
# OPÇÃO 2: Proteger rotas específicas com @validar_api_key
# ============================================================================

"""
Use o decorator @validar_api_key nas rotas que precisam de proteção:

from ngrok_security import validar_api_key
from flask import jsonify

@app.route('/api/usuarios', methods=['GET'])
@validar_api_key  # Requer API Key para acessar
def get_usuarios():
    # ... seu código ...
    return jsonify({'usuarios': []})

@app.route('/auth/login', methods=['GET', 'POST'])
# Sem decorator - aceita tanto localhost quanto Ngrok (com session cookies)
def login():
    # ... seu código ...
    pass

Notas:
- Rotas de autenticação (login, 2FA) não precisam de @validar_api_key
  porque são acessadas pelo navegador que gerencia cookies de sessão
- Use @validar_api_key para API endpoints que são chamados programaticamente
"""

# ============================================================================
# OPÇÃO 3: Middleware customizado (para reqs específicas)
# ============================================================================

"""
from ngrok_security import get_api_key, log_ngrok_acesso
from flask import request, jsonify

@app.before_request
def validar_acesso_ngrok():
    '''Valida API Key para requisições via Ngrok'''
    
    # Identificar se é acesso remoto
    is_remote = request.remote_addr not in ['127.0.0.1', 'localhost', '::1']
    
    if is_remote:
        # Log do acesso
        log_ngrok_acesso()
        
        # Se é endpoint de API, validar chave
        if request.path.startswith('/api/'):
            api_key_esperada = get_api_key()
            auth_header = request.headers.get('Authorization', '')
            
            try:
                _, api_key_fornecida = auth_header.split(' ')
                if api_key_fornecida != api_key_esperada:
                    return jsonify({'erro': 'Não autorizado'}), 401
            except:
                return jsonify({'erro': 'Authorization header inválido'}), 401
"""

# ============================================================================
# EXEMPLO DE USO COMPLETO
# ============================================================================

"""
# app.py (EXEMPLO COMPLETO)

from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

from ngrok_security import NgrokSecurityInit, validar_api_key
from ngrok_security import log_ngrok_acesso

app = Flask(__name__)

# ========== CONFIGURAÇÕES ==========
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'sua-chave-secreta'

# ========== INICIALIZAR EXTENSÕES ==========
db = SQLAlchemy(app)
limiter = Limiter(app=app, key_func=get_remote_address)
talisman = Talisman(app)

# ========== INICIALIZAR NGROK SECURITY ==========
ngrok_security = NgrokSecurityInit()
ngrok_security.init_app(app)

# ========== ROTAS DE AUTENTICAÇÃO (sem @validar_api_key) ==========
@app.route('/auth/login', methods=['GET', 'POST'])
@limiter.limit('5 per 15 minute')
def login():
    # Aceita tanto localhost quanto Ngrok (com cookies de sessão)
    # ... seu código de login ...
    return render_template('auth/login.html')

@app.route('/auth/logout')
def logout():
    # ... seu código de logout ...
    return redirect('/auth/login')

# ========== ROTAS DE API (com @validar_api_key) ==========
@app.route('/api/usuarios', methods=['GET'])
@validar_api_key  # Requer API Key
@limiter.limit('30 per minute')
def get_usuarios():
    usuarios = {'usuarios': ['user1', 'user2']}
    return jsonify(usuarios)

@app.route('/api/criar-usuario', methods=['POST'])
@validar_api_key  # Requer API Key
@limiter.limit('10 per minute')
def criar_usuario():
    # ... seu código ...
    return jsonify({'status': 'criado'})

@app.route('/api/stats')
@validar_api_key  # Requer API Key
def get_stats():
    # ... seu código ...
    return jsonify({'stats': {}})

# ========== ROTAS PÚBLICAS (sem autenticação) ==========
@app.route('/public/info')
def get_info():
    return jsonify({'app': 'BattleZone', 'version': '1.0'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
"""

# ============================================================================
# TESTE DE REQUISIÇÃO
# ============================================================================

"""
# Terminal 1: Iniciar servidor
python start_with_ngrok.py

# Terminal 2: Testar requisições

# 1. Login via navegador (sem API Key)
curl https://xxxxx.ngrok.io/auth/login

# 2. Requisição à API COM API Key
$apiKey = "coloque_sua_chave_aqui"
curl -H "Authorization: Bearer $apiKey" \\
     https://xxxxx.ngrok.io/api/usuarios

# 3. Requisição sem API Key (vai dar erro 401)
curl https://xxxxx.ngrok.io/api/usuarios

# 4. Ver logs
Get-Content logs/ngrok_security.log -Tail 20
Get-Content logs/ngrok_access.json | ConvertFrom-Json | Select timestamp, ip, metodo, endpoint
"""

# ============================================================================
# ESTRUTURA DE PASTAS RECOMENDADA
# ============================================================================

"""
battlezone_flask/
├── app.py                      # Seu app Flask
├── auth.py                     # Rotas de autenticação
├── models.py                   # Modelos SQLAlchemy
├── auth_security.py            # 2FA, TOTP
├── ngrok_security.py           # 🆕 Middleware de Ngrok
├── decorators.py               # Decorators customizados
├── 
├── start_with_ngrok.py         # 🆕 Iniciar e Ngrok
├── setup_ngrok.py              # 🆕 Configurar Ngrok
├── test_ngrok_security.py      # 🆕 Testar configuração
├── NGROK_SETUP.md              # 🆕 Guia de uso
├── NGROK_INTEGRATION.md        # Este arquivo
├── 
├── .env.ngrok                  # 🆕 Configurações (gitignore)
├── .ngrok/                     # 🆕 Pasta de config (gitignore)
│   ├── config.json
│   └── url.txt
├── logs/                       # 🆕 Logs de acesso
│   ├── ngrok_security.log
│   ├── ngrok_access.json
│   └── ngrok_request_*.log
├── 
├── instance/
│   └── database.db
├── templates/
├── static/
└── ...
"""

# ============================================================================
# VARIÁVEIS DE AMBIENTE
# ============================================================================

"""
Seu .env.ngrok deve conter:

NGROK_AUTH_TOKEN=ngrok_coloque_seu_token_aqui_1234567890
NGROK_API_KEY=YmQuUqtJ8HwpK-Tzl9AzM7cXyZ3FvWjX  # Gerado automaticamente
NGROK_REGION=sa
NGROK_PORT=5000
NGROK_Protocol=http
"""

# ============================================================================
# MONITORAMENTO
# ============================================================================

"""
Acessar em tempo real:

1. Dashboard Ngrok:
   http://127.0.0.1:4040
   
   Mostra:
   - Todas as requisições e respostas
   - Headers enviados e recebidos
   - Status codes
   - Tempo de resposta

2. Logs de segurança:
   logs/ngrok_security.log
   
   Mostra:
   - Validação de API Keys
   - Erros de autenticação
   - IPs que acessaram
   - Timestamps

3. Acesso JSON (para análise):
   logs/ngrok_access.json
   
   Cada linha é um JSON:
   {
     "timestamp": "2024-...",
     "ip": "...",
     "metodo": "GET",
     "endpoint": "/api/usuarios",
     "tem_api_key": true
   }
"""

# ============================================================================
# EXEMPLOS DE CÓDIGO
# ============================================================================

"""
# 1. Proteger todas as rotas de API
from ngrok_security import validar_api_key

@app.route('/api/dados')
@validar_api_key
def get_dados():
    return jsonify({'dados': 'valor'})

# 2. Combinada com rate limiting
@app.route('/api/criar')
@validar_api_key
@limiter.limit('10 per minute')
def criar():
    return jsonify({'status': 'criado'})

# 3. Log customizado
from ngrok_security import log_ngrok_acesso

@app.before_request
def antes():
    log_ngrok_acesso()

# 4. Obter API Key programaticamente
from ngrok_security import get_api_key

api_key = get_api_key()
print(f"API Key atual: {api_key}")
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
PROBLEMA: "Authorization header invalid"
SOLUÇÃO: Verificar formato é "Bearer <api_key>" (com espaço)

PROBLEMA: "API Key inválida"
SOLUÇÃO: 
  1. Copiar API Key de .env.ngrok exatamente
  2. Não incluir espaços extras
  3. Regenerar com python setup_ngrok.py se necessário

PROBLEMA: "Porta 5000 em uso"
SOLUÇÃO:
  1. Mudar em .env.ngrok: NGROK_PORT=5001
  2. Ou: netstat -ano | findstr :5000 && taskkill /PID <PID> /F

PROBLEMA: "Ngrok desconectando"
SOLUÇÃO:
  1. Verificar NGROK_AUTH_TOKEN está correto
  2. Rate limiting pode estar bloqueando
  3. Reiniciar: python start_with_ngrok.py
"""

print(__doc__)
