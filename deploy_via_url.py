#!/usr/bin/env python
"""
🚀 Deploy Automático via URL - Battlepass Fix
Chama a rota de correção em Railway sem usar CLI
"""

import requests
import json
import time
from urllib.parse import urljoin

def main():
    print("\n" + "="*70)
    print("🚀 DEPLOY BATTLEPASS FIX - Via URL")
    print("="*70 + "\n")
    
    # SECRET_KEY local (será usada para chamar produção)
    SECRET_KEY = "f1d1d6cf9b094d32a572684df79cf44501c58c908e5cb0957b0978f0004bf346"
    
    # URL de produção
    BASE_URL = "https://battlezone-production.up.railway.app"
    FIX_URL = f"{BASE_URL}/setup/corrigir-colunas-force/{SECRET_KEY}"
    
    print(f"📡 Enviando requisição para:")
    print(f"   {FIX_URL}\n")
    print("⏳ Aguardando resposta do servidor...\n")
    
    try:
        # Fazer requisição com timeout de 120 segundos
        response = requests.get(FIX_URL, timeout=120)
        
        print(f"📊 Status Code: {response.status_code}\n")
        
        # Tentar parsear como JSON
        try:
            dados = response.json()
            print("✅ Resposta recebida (JSON):\n")
            print(json.dumps(dados, indent=2, ensure_ascii=False))
        except:
            print("📝 Resposta recebida (Texto):\n")
            print(response.text)
        
        if response.status_code == 200:
            print("\n" + "="*70)
            print("✅ SUCESSO!")
            print("="*70 + "\n")
            print("""
  🎉 Migração foi enviada para Railway!
  
  ⏳ Railway vai:
     1. Conectar ao banco PostgreSQL
     2. Alterar VARCHAR(10) → VARCHAR(50)
     3. Registrar logs de execução
  
  📝 Próximas ações:
     1. Aguarde 1-2 minutos pela conclusão
     2. Acesse: https://battlezone-production.up.railway.app/operadores
     3. Teste criar um operador com 'Elite-Caveira'
     4. Teste editar uma equipe
  
  💡 Se der erro 500:
     - Railway ainda está processando
     - Aguarde mais um pouco
     - Tente F5 (refresh)
     - Se persistir, verifique Railway Logs
            """)
        else:
            print("\n⚠️  Resposta com status não esperado!")
            print("Verifique os detalhes acima")
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Servidor demorou muito para responder")
        print("   Railroad pode estar processando ainda")
        print("   Tente novamente em alguns minutos")
    
    except requests.exceptions.ConnectionError:
        print("❌ ERRO DE CONEXÃO")
        print("   Verifique sua conexão com internet")
        print("   Ou tente via Railway Dashboard:")
        print("   https://railway.app → Seu projeto → CLI")
    
    except Exception as e:
        print(f"❌ ERRO: {e}")
        print("\nTente manualmente:")
        print(f"1. Abra: {FIX_URL}")
        print("2. Copie a resposta para análise")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada")

