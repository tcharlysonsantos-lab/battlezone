#!/usr/bin/env python3
"""
Gitar.py - Script para automatizar BACKUP + COMMIT + PUSH no GitHub
Use: python gitar.py (após usar: python push.py)
Etapas: Backup → Commit → Push
"""

import subprocess
import sys
import os
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

def criar_backup_local(timestamp, timestamp_legivel):
    """Cria backup local ZIP com data/hora no formato dd/mm/aa/hhmm"""
    pasta_backups = "backups_local"
    
    # Criar pasta se não existir
    os.makedirs(pasta_backups, exist_ok=True)
    
    # Nome do backup com formato dd/mm/aa/hhmm -> dd_mm_aa_hhmm (adaptado para nome de arquivo)
    # Formato: dd_mm_aa_hhmm (03_03_26_0043)
    nome_backup = f"backup_{timestamp_legivel}.zip"
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
        arquivo_metadata = f"backups_local/metadata/backup_{timestamp_legivel}_metadata.json"
        
        metadata = {
            'data_hora': timestamp_legivel,
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
    print("║" + " "*15 + "🎯 GITAR.PY - Backup + Push" + " "*14 + "║")
    print("║" + " "*13 + "(Use 'python push.py' primeiro!)" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    
    # Gerar timestamp no formato dd/mm/aa/hhmm -> dd_mm_aa_hhmm
    agora = datetime.now()
    timestamp_legivel = agora.strftime('%d_%m_%y_%H%M')  # 03_03_26_0043
    timestamp_display = agora.strftime('%d/%m/%Y às %H:%M:%S')
    
    print(f"\n⏰ Data/Hora: {timestamp_display}")
    print(f"📌 Backup ID: {timestamp_legivel}")
    
    # ========== ETAPA 1: CRIAR BACKUP LOCAL ==========
    print("\n🔒 ETAPA 1: CRIAR BACKUP LOCAL")
    sucesso, caminho_backup = criar_backup_local(agora.strftime('%Y%m%d_%H%M%S'), timestamp_legivel)
    
    if not sucesso:
        print("\n❌ Falha ao criar backup! Abortando...")
        sys.exit(1)
    
    print(f"✅ Backup criado: {caminho_backup}")
    
    # ========== ETAPA 2: VERIFICAR MUDANÇAS ==========
    print("\n🔍 ETAPA 2: VERIFICAR MUDANÇAS LOCAIS")
    resultado = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    
    if not resultado.stdout.strip():
        print("✅ Nenhuma mudança detectada!")
        print(f"💾 Backup foi salvo em: {caminho_backup}")
        return
    
    print("📝 Mudanças detectadas:")
    print(resultado.stdout)
    
    # ========== ETAPA 3: PEDIR MENSAGEM DE COMMIT ==========
    print("\n" + "="*60)
    mensagem = input("📌 Digite a mensagem de commit (ou Enter para padrão): ").strip()
    
    if not mensagem:
        mensagem = f"chore: update {timestamp_display} - backup_{timestamp_legivel}"
    
    # ========== ETAPA 4: GIT ADD ==========
    print("\n📤 ETAPA 3: ADICIONAR ARQUIVOS")
    if not executar_comando("git add -A", "Adicionando arquivos..."):
        print("⚠️ Falha ao adicionar arquivos")
        sys.exit(1)
    
    # ========== ETAPA 5: GIT COMMIT ==========
    print("\n💾 ETAPA 4: FAZER COMMIT")
    if not executar_comando(f'git commit -m "{mensagem}"', "Comitando mudanças..."):
        print("⚠️ Commit falhou!")
        sys.exit(1)
    
    # ========== ETAPA 6: GIT PUSH ==========
    print("\n🚀 ETAPA 5: FAZER PUSH PARA GITHUB")
    if not executar_comando("git push origin main", "Enviando para GitHub..."):
        print("❌ Push falhou!")
        print(f"⚠️  Mas seu backup está salvo em: {caminho_backup}")
        sys.exit(1)
    
    # ========== SUCESSO! ==========
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*17 + "✅ SUCESSO COMPLETO!" + " "*20 + "║")
    print("║" + " "*58 + "║")
    print("║" + f"  📦 Backup: {caminho_backup}".ljust(59) + "║")
    print("║" + f"  📝 Commit: {mensagem[:47]}".ljust(59) + "║")
    print("║" + "  🚀 Push: GitHub ✅".ljust(59) + "║")
    print("║" + " "*58 + "║")
    print("║" + " "*12 + "✨ Dados salvos, commitados e enviados!" + " "*6 + "║")
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
