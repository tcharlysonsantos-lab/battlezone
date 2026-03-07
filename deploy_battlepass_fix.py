#!/usr/bin/env python
"""
🚀 Deploy Automático - Battlepass Fix para Railway
Executa correção automaticamente no servidor de produção
"""

import subprocess
import sys
import os
from pathlib import Path

def print_section(title):
    """Imprime seção com formatação"""
    print("\n" + "="*70)
    print(f"▶️  {title}")
    print("="*70 + "\n")

def run_command(cmd, description):
    """Executa comando e mostra resultado"""
    print(f"  ⏳ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"  ✅ {description} - OK")
            if result.stdout:
                print(f"\n{result.stdout}\n")
            return True
        else:
            print(f"  ❌ {description} - ERRO")
            if result.stderr:
                print(f"\n{result.stderr}\n")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"  ❌ {description} - ERRO: {e}")
        return False

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🚀 DEPLOY AUTOMÁTICO - Battlepass Fix".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # ETAPA 1: Verificar Railway CLI
    print_section("ETAPA 1: Verificar Railway CLI")
    
    railway_installed = run_command("railway --version", "Verificar Railway CLI")
    
    if not railway_installed:
        print("\n  ⚠️  Railway CLI não está instalado")
        print("  Instalando via npm...")
        run_command("npm install -g @railway/cli", "Instalar Railway CLI")
    
    # ETAPA 2: Login no Railway
    print_section("ETAPA 2: Conectar com Railway")
    print("  ℹ️  Você será redirecionado para fazer login no navegador")
    print("  Aguarde...")
    
    run_command("railway login", "Login no Railway")
    
    # ETAPA 3: Selecionar projeto
    print_section("ETAPA 3: Selecionar Projeto")
    print("  ℹ️  Selecione 'battlezone-production' ou projeto similar")
    
    run_command("railway link", "Selecionar projeto Railway")
    
    # ETAPA 4: Executar migração
    print_section("ETAPA 4: Executar Migração do Battlepass")
    print("  ⏳ Isto vai alterar o schema do banco PostgreSQL em produção...")
    print("  ⏳ Nenhum dado será perdido...\n")
    
    migração_ok = run_command(
        "railway run python fix_battlepass_column.py",
        "Executar fix_battlepass_column.py"
    )
    
    if migração_ok:
        print_section("ETAPA 5: Executar Validação")
        print("  ⏳ Verificando se migração foi bem-sucedida...\n")
        
        # Executar validação via railway
        run_command(
            "railway run python validate_battlepass_fix.py",
            "Executar validação"
        )
        
        print_section("✅ SUCESSO!")
        print("""
  🎉 Migração concluída com sucesso!
  
  Próximas ações:
  
  1️⃣  Acesse a produção: 
      https://battlezone-production.up.railway.app
  
  2️⃣  Teste criar/editar operador:
      - Vá para Operadores
      - Edite um operador
      - Tente definir Battlepass como 'Elite-Caveira'
      - Salve
  
  3️⃣  Teste equipe:
      - Vá para Equipes
      - Edite uma equipe
      - Adicione um operador
      - Salve
  
  4️⃣  Se tudo funcionar:
      ✅ Migração está 100% completa!
        """)
    else:
        print_section("❌ ERRO NA MIGRAÇÃO")
        print("""
  Algo deu errado durante a migração.
  
  Troubleshooting:
  1. Verifique logs em: Railway Dashboard → Logs
  2. Confirme que DATABASE_URL está setado
  3. Se necessário, restaure um backup
        """)
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
