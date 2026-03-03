#!/usr/bin/env python3
"""
Script para criar backup customizado com nome personalizado
"""

import zipfile
import os
import json
from datetime import datetime

def criar_backup_customizado(nome_backup):
    """Cria backup local ZIP com nome customizado"""
    pasta_backups = "backups_local"
    
    # Criar pasta se não existir
    os.makedirs(pasta_backups, exist_ok=True)
    
    # Sanitizar nome (remover caracteres inválidos)
    nome_sanitizado = "".join(c if c.isalnum() or c in (' ', '_', '-') else '' for c in nome_backup)
    nome_arquivo = f"backup_{nome_sanitizado}.zip"
    caminho_backup = os.path.join(pasta_backups, nome_arquivo)
    
    print(f"\n{'='*60}")
    print(f"📦 Criando backup customizado: {nome_arquivo}")
    print(f"{'='*60}\n")
    
    try:
        # Arquivos a incluir no backup
        arquivos_importante = [
            'app.py',
            'config.py',
            'requirements.txt',
            'run.py',
            'backend/',
            'frontend/templates/',
            'frontend/static/',
            'infrastructure/',
        ]
        
        # Banco de dados também se existir
        if os.path.exists('instance/battlezone.db'):
            arquivos_importante.append('instance/battlezone.db')
        
        # Criar ZIP
        print("📝 Adicionando arquivos:")
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
                    print(f"  ✓ {item}/ ({len(files)} arquivos)")
        
        # Obter tamanho do backup
        tamanho_bytes = os.path.getsize(caminho_backup)
        tamanho_mb = tamanho_bytes / (1024 * 1024)
        print(f"\n  📊 Tamanho: {tamanho_mb:.2f} MB ({tamanho_bytes} bytes)")
        
        # Salvar metadados
        os.makedirs('backups_local/metadata', exist_ok=True)
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo_metadata = f"backups_local/metadata/backup_{nome_sanitizado}_{timestamp_file}_metadata.json"
        
        metadata = {
            'nome_customizado': nome_backup,
            'arquivo': os.path.basename(caminho_backup),
            'data_criacao': datetime.now().strftime('%d/%m/%Y às %H:%M:%S'),
            'tamanho_bytes': tamanho_bytes,
            'tamanho_mb': round(tamanho_mb, 2)
        }
        
        with open(arquivo_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Backup criado com sucesso!")
        print(f"📂 Local: {caminho_backup}")
        print(f"📋 Metadados: {arquivo_metadata}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao criar backup: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*12 + "🎯 CRIAR BACKUP CUSTOMIZADO" + " "*18 + "║")
    print("╚" + "="*58 + "╝")
    
    nome = "servidor caiu"
    print(f"\n📌 Nome do backup: '{nome}'")
    
    sucesso = criar_backup_customizado(nome)
    
    if sucesso:
        print("\n" + "="*60)
        print("✨ BACKUP COMPLETO!")
        print("="*60 + "\n")
    else:
        print("\n❌ Falha ao criar backup!\n")
        exit(1)
