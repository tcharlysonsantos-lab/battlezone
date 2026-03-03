#!/usr/bin/env python3
"""
Gitar.py - Script para automatizar BACKUP + COMMIT + PUSH no GitHub
Use: python gitar.py
Etapas: Backup → Pull → Commit → Push
"""

import subprocess
import sys
import os
import shutil
import zipfile
import json
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

def criar_backup_local(timestamp):
    """Cria backup local ZIP com data/hora"""
    pasta_backups = "backups_local"
    
    # Criar pasta se não existir
    os.makedirs(pasta_backups, exist_ok=True)
    
    # Nome do backup
    nome_backup = f"backup_{timestamp}.zip"
    caminho_backup = os.path.join(pasta_backups, nome_backup)
    
    print(f"\n📦 Criando backup: {nome_backup}")
    
    try:
        # Arquivos a incluir no backup
        arquivos_importante = [
            'app.py',
            'config.py',
            'requirements.txt',
            'backend/',
            'frontend/templates/',
            'frontend/static/',
            'infrastructure/',
        ]
        
        # Banco de dados também se existir
        if os.path.exists('instance/battlezone.db'):
            arquivos_importante.append('instance/battlezone.db')
        
        # Criar ZIP
        with zipfile.ZipFile(caminho_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in arquivos_importante:
                if os.path.isfile(item):
                    zipf.write(item)
                    print(f"  ✓ {item}")
                elif os.path.isdir(item) and os.path.exists(item):
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            filepath = os.path.join(root, file)
                            arcname = filepath
                            zipf.write(filepath, arcname)
                    print(f"  ✓ {item}/")
        
        # Obter tamanho do backup
        tamanho_mb = os.path.getsize(caminho_backup) / (1024 * 1024)
        print(f"  📊 Tamanho: {tamanho_mb:.2f} MB")
        
        # Salvar metadados
        os.makedirs('backups_local/metadata', exist_ok=True)
        arquivo_metadata = f"backups_local/metadata/backup_{timestamp}_metadata.json"
        
        metadata = {
            'data_hora': timestamp,
            'timestamp_unix': int(datetime.now().timestamp()),
            'arquivo': os.path.basename(caminho_backup),
            'tamanho_bytes': os.path.getsize(caminho_backup),
            'tamanho_mb': tamanho_mb
        }
        
        with open(arquivo_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return True, caminho_backup
        
    except Exception as e:
        print(f"❌ Erro ao criar backup: {str(e)}")
        return False, None

def main():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*12 + "🔒 GITAR.PY - Backup + Git Automático" + " "*8 + "║")
    print("╚" + "="*58 + "╝")
    
    # Gerar timestamp
    agora = datetime.now()
    timestamp = agora.strftime('%Y%m%d_%H%M%S')
    timestamp_legivel = agora.strftime('%d/%m/%Y às %H:%M:%S')
    
    print(f"\n⏰ Data/Hora: {timestamp_legivel}")
    
    # ========== 1. CRIAR BACKUP ==========
    print("\n🔒 ETAPA 1: CRIAR BACKUP LOCAL")
    sucesso, caminho_backup = criar_backup_local(timestamp)
    
    if not sucesso:
        print("\n❌ Falha ao criar backup! Abortando...")
        sys.exit(1)
    
    print(f"✅ Backup criado: {caminho_backup}")
    
    # ========== 2. SINCRONIZAR COM O SERVIDOR ==========
    print("\n🔄 ETAPA 2: SINCRONIZAR COM SERVIDOR (PULL)")
    if not executar_comando("git pull origin main", "Puxando mudanças do servidor"):
        print("⚠️ Falha ao sincronizar, mas continuando...")
    
    # ========== 3. VERIFICAR MUDANÇAS ==========
    print("\n🔍 ETAPA 3: VERIFICAR MUDANÇAS")
    resultado = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    
    if not resultado.stdout.strip():
        print("✅ Nenhuma mudança detectada!")
        print(f"💾 Mas seu backup foi salvo em: {caminho_backup}")
        return
    
    print("📝 Mudanças detectadas:")
    print(resultado.stdout)
    
    # ========== 4. PEDIR MENSAGEM DE COMMIT ==========
    print("\n" + "="*60)
    mensagem = input("📌 Digite a mensagem de commit (ou Enter para padrão): ").strip()
    
    if not mensagem:
        mensagem = f"chore: update {timestamp_legivel} (com backup)"
    
    # ========== 5. GIT ADD ==========
    print("\n📤 ETAPA 4: ADICIONAR ARQUIVOS")
    if not executar_comando("git add -A", "Adicionando arquivos..."):
        print("⚠️ Falha ao adicionar arquivos")
        sys.exit(1)
    
    # ========== 6. GIT COMMIT ==========
    print("\n💾 ETAPA 5: FAZER COMMIT")
    if not executar_comando(f'git commit -m "{mensagem}"', "Comitando mudanças..."):
        print("⚠️ Commit falhou!")
        sys.exit(1)
    
    # ========== 7. GIT PUSH ==========
    print("\n🚀 ETAPA 6: FAZER PUSH PARA GITHUB")
    if not executar_comando("git push origin main", "Enviando para GitHub..."):
        print("❌ Push falhou!")
        print(f"⚠️  Mas seu backup estava salvo em: {caminho_backup}")
        sys.exit(1)
    
    # ========== 8. SUCESSO! ==========
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*17 + "✅ SUCESSO COMPLETO!" + " "*20 + "║")
    print("║" + " "*58 + "║")
    print("║" + f"  🔒 Backup: backups_local/backup_{timestamp}.zip".ljust(59) + "║")
    print("║" + f"  📝 Commit: {mensagem[:46]}".ljust(59) + "║")
    print("║" + "  🚀 Push: GitHub ✅".ljust(59) + "║")
    print("║" + " "*58 + "║")
    print("║" + " "*15 + "✨ Dados backup + enviados com segurança!" + " "*3 + "║")
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

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)
