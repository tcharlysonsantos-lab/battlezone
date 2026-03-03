#!/usr/bin/env python3
"""
push.py - Sincroniza com o servidor (PULL/Download) ANTES de começar
Use: python push.py
Objetivo: Garantir que você tem os dados mais atualizados antes de mexer no código
"""

import subprocess
import sys

def executar_comando(comando, descricao=""):
    """Executa um comando e mostra o resultado"""
    try:
        print(f"\n{'='*60}")
        if descricao:
            print(f"📋 {descricao}")
        print(f"{'='*60}")
        
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        if resultado.stdout:
            print(resultado.stdout)
        if resultado.stderr:
            print(resultado.stderr)
        
        if resultado.returncode != 0:
            print(f"❌ Erro ao executar comando!")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def main():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*18 + "📥 PUSH.PY - Sincronizar" + " "*16 + "║")
    print("║" + " "*10 + "Baixa os dados mais atualizados do servidor" + " "*5 + "║")
    print("╚" + "="*58 + "╝")
    
    # ========== ETAPA CRÍTICA 1: PULL DO SERVIDOR ==========
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*12 + "🔴 SINCRONIZANDO COM GITHUB - PULL 🔴" + " "*7 + "║")
    print("║" + " "*15 + "Baixando dados mais recentes..." + " "*13 + "║")
    print("╚" + "="*58 + "╝")
    
    if not executar_comando("git pull origin main", "Sincronizando com servidor"):
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*14 + "❌ ERRO AO SINCRONIZAR - ABORTANDO" + " "*10 + "║")
        print("║" + " "*58 + "║")
        print("║" + "  Possíveis causas:".ljust(59) + "║")
        print("║" + "  • Sem conexão com internet".ljust(59) + "║")
        print("║" + "  • Conflito com arquivos locais".ljust(59) + "║")
        print("║" + "  • GitHub indisponível".ljust(59) + "║")
        print("║" + " "*58 + "║")
        print("║" + "  Tente resolver os conflitos e tente novamente!".ljust(59) + "║")
        print("╚" + "="*58 + "╝\n")
        sys.exit(1)
    
    # ========== SUCESSO ==========
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*17 + "✅ SINCRONIZADO COM SUCESSO!" + " "*12 + "║")
    print("║" + " "*58 + "║")
    print("║" + " "*11 + "📥 Você tem os dados mais atualizados!" + " "*9 + "║")
    print("║" + " "*58 + "║")
    print("║" + " "*16 + "👉 Agora você pode mexer no código!" + " "*6 + "║")
    print("║" + " "*58 + "║")
    print("║" + " "*12 + "Quando terminar, execute: python gitar.py" + " "*6 + "║")
    print("╚" + "="*58 + "╝\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)
