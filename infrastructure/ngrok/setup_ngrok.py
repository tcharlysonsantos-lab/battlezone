#!/usr/bin/env python3
"""
Setup Seguro do Ngrok para Exposição External
Com autenticação por API Key e rate limiting agressivo
"""

import os
import secrets
import json
from pathlib import Path
from datetime import datetime

def setup_ngrok_seguro():
    """Setup completo e seguro do Ngrok"""
    
    print("\n" + "="*70)
    print("  SETUP NGROK SEGURO - BATTLEZONE")
    print("="*70 + "\n")
    
    # 1. Verificar se Ngrok está instalado
    print("📦 Verificando Ngrok...")
    try:
        import subprocess
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Ngrok encontrado: {result.stdout.strip()}")
        else:
            print("  ❌ Ngrok não instalado!")
            print("\n  Para instalar:")
            print("  1. Baixar em: https://ngrok.com/download")
            print("  2. Ou: choco install ngrok")
            return False
    except FileNotFoundError:
        print("  ❌ Ngrok não está no PATH!")
        print("  Instale de https://ngrok.com/download")
        return False
    
    # 2. Gerar API Key para autenticação
    print("\n🔐 Gerando API Key...")
    api_key = secrets.token_urlsafe(32)
    print(f"  ✅ API Key gerada: {api_key}")
    
    # 3. Gerar configuração
    config = {
        "api_key": api_key,
        "generated_at": datetime.now().isoformat(),
        "ngrok": {
            "authtoken": "COLOQUE_SEU_TOKEN_AQUI",
            "region": "sa",  # South America
            "protocol": "http",
            "port": 5000,
            "bind_tls": "both"  # HTTP + HTTPS
        },
        "security": {
            "rate_limit": {
                "enabled": True,
                "requests_per_minute": 60,
                "burst_size": 10
            },
            "ip_whitelist_enabled": False,
            "ip_whitelist": [],
            "require_api_key": True,
            "log_all_requests": True
        },
        "reminders": {
            "1": "⚠️  GUARDAR ESTA CHAVE EM LOCAL SEGURO!",
            "2": "⚠️  ADICIONAR authtoken do Ngrok (https://dashboard.ngrok.com/auth)",
            "3": "⚠️  NÃO compartilhar esta chave em repositório git!",
            "4": "⚠️  Alterar api_key regularmente"
        }
    }
    
    # 4. Criar pasta .ngrok se não existir
    ngrok_dir = Path('.ngrok')
    ngrok_dir.mkdir(exist_ok=True)
    
    # 5. Salvar configuração
    config_file = ngrok_dir / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n  ✅ Configuração salva em: {config_file}")
    
    # 6. Criar arquivo .env.ngrok
    env_file = Path('.env.ngrok')
    env_content = f"""# ==================== NGROK SECURITY CONFIG ====================
# Gerado em: {datetime.now().isoformat()}
# NUNCA commitar este arquivo no git!

NGROK_ENABLED=true
NGROK_API_KEY={api_key}
NGROK_AUTH_TOKEN=COLOQUE_SEU_TOKEN_AQUI
NGROK_REGION=sa
NGROK_PORT=5000

# Rate Limiting para acesso externo
EXTERNAL_RATE_LIMIT_ENABLED=true
EXTERNAL_RATE_LIMIT_PER_MINUTE=60
EXTERNAL_RATE_LIMIT_BURST=10

# Logging
LOG_EXTERNAL_REQUESTS=true
LOG_FILE=logs/ngrok_access.log

# Security Headers
SECURITY_HEADERS_ENABLED=true
REQUIRE_HTTPS=true

# IP Whitelist (opcional)
IP_WHITELIST_ENABLED=false
IP_WHITELIST=127.0.0.1,192.168.1.0/24
"""
    with open(env_file, 'w') as f:
        f.write(env_content)
    print(f"  ✅ Arquivo .env.ngrok criado")
    
    # 7. Adicionar ao .gitignore
    print("\n🔒 Atualizando .gitignore...")
    gitignore_path = Path('.gitignore')
    with open(gitignore_path, 'a') as f:
        f.write('\n# ==================== NGROK ====================\n')
        f.write('.env.ngrok\n')
        f.write('.ngrok/\n')
        f.write('logs/ngrok*.log\n')
    print("  ✅ .gitignore atualizado")
    
    # 8. Criar logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    print(f"  ✅ Diretório de logs criado")
    
    print("\n" + "="*70)
    print("  PRÓXIMOS PASSOS:")
    print("="*70)
    print(f"""
1. Criar conta no Ngrok (gratuita):
   https://ngrok.com/signup

2. Copiar seu authtoken de:
   https://dashboard.ngrok.com/auth

3. Adicionar ao .env.ngrok:
   NGROK_AUTH_TOKEN=seu_token_aqui

4. Guardar esta API Key em local seguro:
   {api_key}

5. Para iniciar o servidor com Ngrok:
   python start_with_ngrok.py

6. Sua URL será:
   https://seu-url-aleatoria.ngrok.io/
   
   Use a API Key no header:
   Authorization: Bearer {api_key}
""")
    
    print("="*70)
    print("  ✅ Setup concluído com sucesso!")
    print("="*70 + "\n")
    
    return True

if __name__ == '__main__':
    setup_ngrok_seguro()
