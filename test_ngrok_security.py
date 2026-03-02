#!/usr/bin/env python3
"""
test_ngrok_security.py - Validar configuração de segurança do Ngrok
"""

import os
import json
import sys
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Cores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(titulo):
    print(f"\n{BLUE}{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}{RESET}\n")

def print_ok(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def validate_setup():
    """Valida arquivos de setup"""
    print_header("1. VALIDAÇÃO DE ARQUIVOS DE SETUP")
    
    checks = {
        '.env.ngrok': Path('.env.ngrok').exists(),
        '.ngrok/config.json': Path('.ngrok/config.json').exists(),
        'logs/': Path('logs').exists(),
        'setup_ngrok.py': Path('setup_ngrok.py').exists(),
        'start_with_ngrok.py': Path('start_with_ngrok.py').exists(),
        'ngrok_security.py': Path('ngrok_security.py').exists(),
    }
    
    for arquivo, existe in checks.items():
        if existe:
            print_ok(f"{arquivo}")
        else:
            print_error(f"{arquivo}")
    
    return all(checks.values())

def validate_env_config():
    """Valida variáveis de ambiente"""
    print_header("2. VALIDAÇÃO DE CONFIGURAÇÃO (.env.ngrok)")
    
    # Carregar .env.ngrok
    if not Path('.env.ngrok').exists():
        print_error("Arquivo .env.ngrok não encontrado")
        return False
    
    load_dotenv('.env.ngrok')
    
    checks = {
        'NGROK_API_KEY': os.getenv('NGROK_API_KEY'),
        'NGROK_AUTH_TOKEN': os.getenv('NGROK_AUTH_TOKEN'),
        'NGROK_REGION': os.getenv('NGROK_REGION', 'sa'),
        'NGROK_PORT': os.getenv('NGROK_PORT', '5000'),
    }
    
    all_valid = True
    
    # Validar NGROK_API_KEY
    api_key = checks['NGROK_API_KEY']
    if api_key and len(api_key) > 20:
        print_ok(f"NGROK_API_KEY: {api_key[:16]}...{api_key[-8:]}")
    else:
        print_error(f"NGROK_API_KEY inválida ou não configurada")
        all_valid = False
    
    # Validar NGROK_AUTH_TOKEN
    auth_token = checks['NGROK_AUTH_TOKEN']
    if auth_token and auth_token != 'COLOQUE_SEU_TOKEN_AQUI':
        print_ok(f"NGROK_AUTH_TOKEN: {auth_token[:16]}...{auth_token[-8:]}")
    else:
        print_error(f"NGROK_AUTH_TOKEN não configurado (necesário para Ngrok)")
        all_valid = False
    
    # Validar Region
    if checks['NGROK_REGION'] in ['sa', 'us', 'eu', 'in', 'au', 'jp']:
        print_ok(f"NGROK_REGION: {checks['NGROK_REGION']}")
    else:
        print_warning(f"NGROK_REGION inválida: {checks['NGROK_REGION']}")
    
    # Validar Port
    try:
        port = int(checks['NGROK_PORT'])
        if 1 <= port <= 65535:
            print_ok(f"NGROK_PORT: {port}")
        else:
            print_error(f"NGROK_PORT inválida: {port}")
            all_valid = False
    except:
        print_error(f"NGROK_PORT não é um número: {checks['NGROK_PORT']}")
        all_valid = False
    
    return all_valid

def validate_config_json():
    """Valida config.json"""
    print_header("3. VALIDAÇÃO DE config.json")
    
    try:
        with open('.ngrok/config.json') as f:
            config = json.load(f)
        
        # Validar estrutura
        if 'api_key' in config:
            print_ok(f"api_key: {config['api_key'][:16]}...{config['api_key'][-8:]}")
        else:
            print_error("api_key não encontrada em config.json")
            return False
        
        # Validar ngrok settings
        if 'ngrok' in config:
            ngrok = config['ngrok']
            print_ok(f"ngrok.region: {ngrok.get('region', 'não definido')}")
            print_ok(f"ngrok.port: {ngrok.get('port', 5000)}")
            print_ok(f"ngrok.bind_tls: {ngrok.get('bind_tls', 'não definido')}")
        else:
            print_error("Seção 'ngrok' não encontrada")
            return False
        
        # Validar security settings
        if 'security' in config:
            security = config['security']
            if 'rate_limit' in security:
                rl = security['rate_limit']
                print_ok(f"rate_limit.requests_per_minute: {rl.get('requests_per_minute', 60)}")
                print_ok(f"rate_limit.burst_size: {rl.get('burst_size', 10)}")
                print_ok(f"require_api_key: {security.get('require_api_key', False)}")
                print_ok(f"log_all_requests: {security.get('log_all_requests', False)}")
        else:
            print_warning("Seção 'security' não encontrada")
        
        return True
        
    except json.JSONDecodeError as e:
        print_error(f"Erro ao parsear config.json: {e}")
        return False
    except Exception as e:
        print_error(f"Erro ao ler config.json: {e}")
        return False

def validate_ngrok_installed():
    """Verifica se Ngrok está instalado"""
    print_header("4. VALIDAÇÃO DE NGROK INSTALADO")
    
    try:
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True, timeout=5)
        version_output = result.stdout.split('\n')[0]
        print_ok(f"Ngrok detectado: {version_output}")
        return True
    except FileNotFoundError:
        print_error("Ngrok não está instalado ou não está no PATH")
        print_info("Instalar com: choco install ngrok")
        return False
    except subprocess.TimeoutExpired:
        print_error("Timeout ao verificar Ngrok")
        return False
    except Exception as e:
        print_error(f"Erro ao verificar Ngrok: {e}")
        return False

def validate_port_available():
    """Verifica se porta 5000 está disponível"""
    print_header("5. VALIDAÇÃO DE PORTA")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 5000))
        sock.close()
        
        if result != 0:
            print_ok("Porta 5000: Disponível")
            return True
        else:
            print_warning("Porta 5000: Já está em uso")
            print_info("Isso é OK se Flask está rodando. Se não estiver, use: netstat -ano | findstr :5000")
            return True
    except Exception as e:
        print_error(f"Erro ao verificar porta: {e}")
        return False

def validate_gitignore():
    """Verifica se .env.ngrok e .ngrok/ estão em .gitignore"""
    print_header("6. VALIDAÇÃO DE .gitignore")
    
    try:
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
        
        checks = {
            '.env.ngrok': '.env.ngrok' in gitignore_content,
            '.ngrok/': '.ngrok/' in gitignore_content or '.ngrok' in gitignore_content,
        }
        
        for arquivo, in_gitignore in checks.items():
            if in_gitignore:
                print_ok(f"{arquivo} está protegido em .gitignore")
            else:
                print_warning(f"{arquivo} não está em .gitignore - não será compartilhado com git")
        
        return True
    except Exception as e:
        print_warning(f"Erro ao ler .gitignore: {e}")
        return True  # Não é crítico

def validate_logs_directory():
    """Verifica estrutura de logs"""
    print_header("7. VALIDAÇÃO DE LOGS")
    
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        print_error("Diretório logs/ não existe")
        print_info("Será criado automaticamente na primeira execução")
        logs_dir.mkdir(exist_ok=True)
        print_ok("Diretório logs/ criado")
    else:
        print_ok("Diretório logs/ existe")
        
        # Ver arquivo de logs
        security_log = logs_dir / 'ngrok_security.log'
        access_log = logs_dir / 'ngrok_access.json'
        
        if security_log.exists():
            linhas = sum(1 for _ in open(security_log))
            print_ok(f"ngrok_security.log: {linhas} linhas")
        
        if access_log.exists():
            linhas = sum(1 for _ in open(access_log))
            print_ok(f"ngrok_access.json: {linhas} registros")
    
    return True

def validate_flask_app():
    """Verifica se Flask app pode ser importado"""
    print_header("8. VALIDAÇÃO DE FLASK APP")
    
    try:
        from app import app
        print_ok("Flask app importado com sucesso")
        
        # Verificar se tem CSRF, Limiter, etc
        if hasattr(app, 'limiter'):
            print_ok("Flask-Limiter está configurado")
        if hasattr(app, 'talisman'):
            print_ok("Flask-Talisman está configurado")
        
        # Verificar rotas de autenticação
        routes_criticas = ['/auth/login', '/auth/logout', '/forgot-password', '/reset-password']
        has_routes = []
        
        for rule in app.url_map.iter_rules():
            if any(rota in str(rule) for rota in routes_criticas):
                has_routes.append(str(rule))
        
        if has_routes:
            print_ok(f"Rotas de autenticação encontradas: {len(has_routes)}")
        
        return True
    except Exception as e:
        print_error(f"Erro ao importar Flask app: {e}")
        return False

def validate_auth_module():
    """Verifica se auth_security.py existe"""
    print_header("9. VALIDAÇÃO DE MÓDULOS DE SEGURANÇA")
    
    files_check = {
        'auth_security.py': Path('auth_security.py').exists(),
        'ngrok_security.py': Path('ngrok_security.py').exists(),
        'models.py': Path('models.py').exists(),
    }
    
    for arquivo, existe in files_check.items():
        if existe:
            print_ok(f"{arquivo}")
        else:
            print_error(f"{arquivo}")
    
    return all(files_check.values())

def test_api_key_format():
    """Testa o formato de API Key"""
    print_header("10. TESTE DE FORMATO DE API KEY")
    
    load_dotenv('.env.ngrok')
    api_key = os.getenv('NGROK_API_KEY')
    
    if not api_key:
        print_error("NGROK_API_KEY não está configurada")
        return False
    
    # Validar formato
    if len(api_key) >= 20:
        print_ok(f"Comprimento: {len(api_key)} caracteres (mínimo 20)")
    else:
        print_error(f"Comprimento insuficiente: {len(api_key)} caracteres")
        return False
    
    if all(c.isalnum() or c in '-_' for c in api_key):
        print_ok("Caracteres válidos (alphanumeric + - _)")
    else:
        print_error("API Key contém caracteres inválidos")
        return False
    
    # Exemplificar header
    header_exemplo = f"Authorization: Bearer {api_key[:16]}...{api_key[-8:]}"
    print_ok(f"Header exemplo: {header_exemplo}")
    
    return True

def print_summary(results):
    """Imprime resumo dos testes"""
    print_header("RESUMO DA VALIDAÇÃO")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"{BLUE}Total de verificações: {total}")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {total - passed}{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}🎉 TUDO PRONTO! Você pode executar:{RESET}")
        print(f"{BLUE}  python start_with_ngrok.py{RESET}\n")
    else:
        print(f"{RED}⚠️  Existem problemas a resolver:{RESET}\n")
        for check, passed in results.items():
            status = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
            print(f"  {status} {check}")

def main():
    print(f"\n{BLUE}{'='*70}")
    print(f"  🔐 TESTE DE SEGURANÇA - NGROK")
    print(f"  BattleZone Flask")
    print(f"{'='*70}{RESET}")
    
    results = {
        'Setup de arquivos': validate_setup(),
        'Configuração .env.ngrok': validate_env_config(),
        'config.json': validate_config_json(),
        'Ngrok instalado': validate_ngrok_installed(),
        'Porta disponível': validate_port_available(),
        'Proteção .gitignore': validate_gitignore(),
        'Diretório de logs': validate_logs_directory(),
        'Flask app': validate_flask_app(),
        'Módulos de segurança': validate_auth_module(),
        'Formato de API Key': test_api_key_format(),
    }
    
    print_summary(results)
    
    # Exit status
    sys.exit(0 if all(results.values()) else 1)

if __name__ == '__main__':
    main()
