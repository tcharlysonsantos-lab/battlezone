#!/usr/bin/env python3
"""
Gitar.py - Script para automatizar commits e push no GitHub
Use: python gitar.py
"""

import subprocess
import sys
import os
from datetime import datetime

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
    print("║" + " "*15 + "🎯 GITAR.PY - Git Automático" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    
    # 0. SINCRONIZAR COM O SERVIDOR PRIMEIRO!
    print("\n🔄 Sincronizando com o servidor...")
    if not executar_comando("git pull origin main", "Puxando mudanças do servidor"):
        print("⚠️ Falha ao sincronizar, mas continuando...")
    
    # 1. Verificar status do git
    print("\n🔍 Verificando status do repositório...")
    resultado = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    
    if not resultado.stdout.strip():
        print("✅ Nenhuma mudança detectada!")
        print("💡 Não há nada para commit.")
        return
    
    print("📝 Mudanças detectadas:")
    print(resultado.stdout)
    
    # 2. Pedir mensagem de commit
    print("\n" + "="*60)
    mensagem = input("📌 Digite a mensagem de commit (ou Enter para padrão): ").strip()
    
    if not mensagem:
        mensagem = f"chore: update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 3. Git Add
    if not executar_comando("git add -A", "📤 Adicionando arquivos..."):
        sys.exit(1)
    
    # 4. Git Commit
    if not executar_comando(f'git commit -m "{mensagem}"', "💾 Fazendo commit..."):
        print("⚠️ Commit falhou ou nenhuma mudança para commitar")
        sys.exit(1)
    
    # 5. Git Push
    if not executar_comando("git push origin main", "🚀 Fazendo push..."):
        print("❌ Push falhou!")
        sys.exit(1)
    
    # 6. Sucesso!
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*20 + "✅ SUCESSO!" + " "*27 + "║")
    print("║" + f" Commit: {mensagem[:52]:<52} " + "║")
    print("║" + " "*58 + "║")
    print("║" + " "*15 + "✨ Alterações enviadas para o repositório!" + " "*3 + "║")
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
