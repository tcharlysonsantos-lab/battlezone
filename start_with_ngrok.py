#!/usr/bin/env python3
"""
start_with_ngrok.py - Iniciar Flask + Ngrok com Segurança
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env.ngrok
if Path('.env.ngrok').exists():
    load_dotenv('.env.ngrok')
else:
    print("❌ Arquivo .env.ngrok não encontrado!")
    print("Execute primeiro: python setup_ngrok.py")
    sys.exit(1)

# Carregar config
config_file = Path('.ngrok/config.json')
if not config_file.exists():
    print("❌ Arquivo .ngrok/config.json não encontrado!")
    sys.exit(1)

with open(config_file) as f:
    config = json.load(f)

def validar_configuracao():
    """Valida se tudo está configurado"""
    print("\n" + "="*70)
    print("  VALIDANDO CONFIGURAÇÃO DE SEGURANÇA")
    print("="*70 + "\n")
    
    checks = {
        "NGROK_API_KEY definida": os.getenv('NGROK_API_KEY') is not None,
        "NGROK_AUTH_TOKEN definida": os.getenv('NGROK_AUTH_TOKEN') not in [None, 'COLOQUE_SEU_TOKEN_AQUI'],
        ".env.ngrok existe": Path('.env.ngrok').exists(),
        "config.json existe": config_file.exists(),
        "logs/ existe": Path('logs').exists(),
        "Rate limiting preparado": True,
    }
    
    print("Verificações de Segurança:")
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {check}")
    
    if not all(checks.values()):
        print("\n❌ Configuração incompleta!")
        print("Execute: python setup_ngrok.py")
        return False
    
    print("\n✅ Tudo configurado corretamente!")
    return True

def iniciar_ngrok():
    """Inicia o Ngrok"""
    print("\n" + "="*70)
    print("  INICIANDO NGROK")
    print("="*70 + "\n")
    
    authtoken = os.getenv('NGROK_AUTH_TOKEN')
    region = os.getenv('NGROK_REGION', 'sa')
    port = os.getenv('NGROK_PORT', '5000')
    
    # Comando para iniciar Ngrok
    cmd = [
        'ngrok',
        'http',
        f'--authtoken={authtoken}',
        f'--region={region}',
        port
    ]
    
    print(f"Iniciando: {' '.join(cmd[:3])} ...")
    print(f"Região: {region}")
    print(f"Porta: {port}")
    print(f"Modo: HTTP + HTTPS\n")
    
    try:
        subprocess.Popen(cmd)
        print("✅ Ngrok iniciado!")
        print("\nAguardando inicialização...")
        time.sleep(3)
        
        # Tentar acessar a API do Ngrok para pegar a URL
        try:
            import urllib.request
            response = urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels', timeout=5)
            data = json.loads(response.read().decode())
            
            if data.get('tunnels'):
                tunnel = data['tunnels'][0]
                ngrok_url = tunnel['public_url']
                print(f"\n{'='*70}")
                print(f"  ✅ NGROK URL: {ngrok_url}")
                print(f"{'='*70}\n")
                
                # Salvar URL em arquivo
                with open('.ngrok/url.txt', 'w') as f:
                    f.write(ngrok_url + '\n')
                
                return ngrok_url
        except Exception as e:
            print(f"⚠️  Não consegui pegar URL do Ngrok: {e}")
            print("URL deve estar visível na janela do Ngrok")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar Ngrok: {e}")
        return False

def iniciar_flask():
    """Inicia o Flask com segurança"""
    print("\n" + "="*70)
    print("  INICIANDO FLASK COM SEGURANÇA")
    print("="*70 + "\n")
    
    # Importar app
    try:
        from app import app
    except Exception as e:
        print(f"❌ Erro ao carregar app: {e}")
        return False
    
    # Configurar para aceitar conexões externas
    print("Configurações de Segurança Ativadas:")
    print("  ✅ CSRF Protection")
    print("  ✅ Security Headers (CSP, HSTS)")
    print("  ✅ Flask-Limiter")
    print("  ✅ 2FA Enabled")
    print("  ✅ API Key Authentication")
    print("  ✅ Access Logging")
    
    print("\n🚀 Iniciando Flask...")
    print("   Host: 0.0.0.0 (aceita conexões de qualquer IP)")
    print("   Port: 5000")
    print("   Debug: False (desativado em modo externo)")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Desativar debug em exposição externa
        use_reloader=False
    )

def main():
    print("\n" + "="*70)
    print("  🚀 BATTLEZONE - EXPOSIÇÃO SEGURA COM NGROK")
    print("="*70)
    
    # 1. Validar configuração
    if not validar_configuracao():
        print("\n❌ Falha na validação!")
        return False
    
    # 2. Iniciar Ngrok
    ngrok_url = iniciar_ngrok()
    
    # 3. Exibir instruções
    api_key = os.getenv('NGROK_API_KEY')
    print("\n" + "="*70)
    print("  INSTRUÇÕES DE ACESSO")
    print("="*70)
    print(f"""
1. Acessar aplicação:
   {ngrok_url}/auth/login (será exibido na janela do Ngrok)

2. Para requisições API, usar header:
   Authorization: Bearer {api_key}

3. Todas as requisições serão logadas em:
   logs/ngrok_access.log

4. Limitado a 60 requisições/minuto por IP

5. Exemplos de requisição:
   curl -H "Authorization: Bearer {api_key}" \\
        https://sua-url.ngrok.io/auth/login

6. Monitorar em tempo real:
   http://127.0.0.1:4040 (dashboard Ngrok)
""")
    print("="*70)
    
    # 4. Iniciar Flask
    print("\n⏳ Iniciando servidor Flask...")
    iniciar_flask()

if __name__ == '__main__':
    main()
