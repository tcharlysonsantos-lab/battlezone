#!/usr/bin/env python
"""
🚀 Deploy Interativo - Battlepass Fix
Pede SECRET_KEY do usuário e executa em Railway
"""

import requests
import json
import time
import getpass

def main():
    print("\n" + "="*70)
    print("🚀 DEPLOY INTERATIVO - Battlepass Fix")
    print("="*70 + "\n")
    
    # Pedir SECRET_KEY ao usuário
    print("ℹ️  Para executar a correção em Railway, preciso da SECRET_KEY de Produção\n")
    print("📝 Como obter a SECRET_KEY:")
    print("   1. Acesse: https://railway.app")
    print("   2. Selecione projeto: 'battlezone-production'")
    print("   3. Guia: Variables")
    print("   4. Procure a variável 'SECRET_KEY'")
    print("   5. Copie o valor inteiro (incluindo os 'sk_' prefixo se tiver)\n")
    
    SECRET_KEY = input("🔑 Cole a SECRET_KEY aqui: ").strip()
    
    if not SECRET_KEY or len(SECRET_KEY) < 20:
        print("\n❌ SECRET_KEY inválida ou muito curta!")
        return
    
    # Mascarar exibição da chave
    masked_key = SECRET_KEY[:10] + "..." + SECRET_KEY[-10:]
    print(f"\n✅ Chave recebida: {masked_key}\n")
    
    # URL de produção
    BASE_URL = "https://battlezone-production.up.railway.app"
    FIX_URL = f"{BASE_URL}/setup/corrigir-colunas-force/{SECRET_KEY}"
    
    print(f"📡 Enviando requisição para Railway...")
    print(f"⏳ Isto pode levar alguns minutos (máximo 2 min)...\n")
    
    try:
        # Fazer requisição com timeout de 180 segundos
        response = requests.get(FIX_URL, timeout=180, verify=False)
        
        print(f"\n📊 Status Code: {response.status_code}\n")
        
        # Tentar parsear como JSON
        try:
            dados = response.json()
            print("✅ Resposta do Servidor:\n")
            print(json.dumps(dados, indent=2, ensure_ascii=False))
        except:
            print("📝 Resposta do Servidor:\n")
            print(response.text[:500])  # Primeiros 500 caracteres
        
        if response.status_code == 200:
            sucesso = False
            try:
                dados = response.json()
                sucesso = dados.get('sucesso', False)
            except:
                pass
            
            if sucesso:
                print("\n" + "="*70)
                print("✅ SUCESSO! Migration foi executada!")
                print("="*70 + "\n")
                print("""
  🎉 Colunas do banco de dados foram corrigidas!
  
  ✅ Alterações realizadas:
     - operadores.battlepass: VARCHAR(10) → VARCHAR(50)
     - equipes.battlepass: VARCHAR(10) → VARCHAR(50)
  
  📝 Próximas ações:
     1. Aguarde 30 segundos por Railway reiniciar
     2. Acesse: https://battlezone-production.up.railway.app
     3. Teste adicionar um operador com 'Elite-Caveira'
     4. Teste editar uma equipe
  
  ✨ Tudo pronto para usar Battlepass!
                """)
            else:
                print("\n⚠️  Migration foi enviada mas houve um problema")
                print("Verifique os detalhes acima na resposta do servidor")
        
        elif response.status_code == 403:
            print("\n❌ ERRO: Invalid secret key")
            print("A SECRET_KEY fornecida não está correta")
            print("Verifique se copiou idêntico do Railway Dashboard")
        
        else:
            print(f"\n⚠️  Resposta inesperada (status {response.status_code})")
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Servidor demorou demais")
        print("   Railway pode estar processando ainda")
        print("   Tente novamente em alguns minutos")
    
    except requests.exceptions.ConnectionError:
        print("❌ ERRO DE CONEXÃO")
        print("   Verifique sua internet")
        print("   Ou tente via CLI:")
        print("   railway run python fix_battlepass_column.py")
    
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada")

