# cloud_manager.py
import os
import shutil
import threading
import time
from datetime import datetime
import json
import hashlib

class CloudManager:
    """Gerenciador de sincronização com Google Drive e backups"""
    
    def __init__(self, app=None):
        self.app = app
        self.CAMINHO_LOCAL = os.path.dirname(os.path.abspath(__file__))
        self.CAMINHO_NUVEM = self.encontrar_pasta_nuvem()
        self.sincronizacao_ativa = True
        self.backup_em_andamento = False
        
        # Criar pastas necessárias
        os.makedirs('backups', exist_ok=True)
        os.makedirs('instance', exist_ok=True)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        # Iniciar threads automáticas
        if not app.debug:
            self.iniciar_sincronizacao_automatica()
            self.iniciar_backup_automatico()  # NOVA FUNÇÃO
    
    def encontrar_pasta_nuvem(self):
        """Tenta encontrar a pasta do Google Drive"""
        possiveis_caminhos = [
            "G:/Meu Drive/Battlezone",
            "G:/Meu Drive",
            os.path.expanduser("~/Google Drive/Battlezone"),
            os.path.expanduser("~/Google Drive"),
            os.path.join(self.CAMINHO_LOCAL, 'backups_drive')
        ]
        
        for caminho in possiveis_caminhos:
            if os.path.exists(caminho):
                return caminho
        
        # Se não encontrar, cria pasta local de backup
        backup_path = os.path.join(self.CAMINHO_LOCAL, 'backups_drive')
        os.makedirs(backup_path, exist_ok=True)
        return backup_path
    
    def calcular_hash(self, arquivo):
        """Calcula hash MD5 do arquivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(arquivo, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
    
    def sincronizar_para_nuvem(self, arquivo):
        """Copia um arquivo para a nuvem com verificação de hash"""
        if not self.sincronizacao_ativa:
            return False
        
        try:
            origem = os.path.join(self.CAMINHO_LOCAL, 'instance', arquivo)
            destino = os.path.join(self.CAMINHO_NUVEM, 'data', arquivo)
            
            if not os.path.exists(origem):
                return False
            
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            
            hash_origem = self.calcular_hash(origem)
            
            if os.path.exists(destino):
                hash_destino = self.calcular_hash(destino)
                if hash_origem == hash_destino:
                    return True
            
            shutil.copy2(origem, destino + '.tmp')
            
            hash_tmp = self.calcular_hash(destino + '.tmp')
            if hash_origem == hash_tmp:
                shutil.move(destino + '.tmp', destino)
                return True
            else:
                os.remove(destino + '.tmp')
                return False
                
        except Exception as e:
            print(f"Erro ao sincronizar {arquivo}: {e}")
            return False
    
    # ========== NOVA FUNÇÃO: BACKUP AUTOMÁTICO ==========
    def criar_backup_local(self):
        """Cria backup do banco de dados na pasta local (AUTOMÁTICO)"""
        try:
            # Nome do arquivo com data/hora
            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_backup = f"database_{data_hora}.db"
            
            origem = os.path.join(self.CAMINHO_LOCAL, 'instance', 'database.db')
            destino = os.path.join(self.CAMINHO_LOCAL, 'backups', nome_backup)
            
            if not os.path.exists(origem):
                return False, "Banco de dados não encontrado"
            
            # Copiar arquivo
            shutil.copy2(origem, destino)
            
            # Criar arquivo de metadados
            metadata = {
                'data': data_hora,
                'origem': 'automático',
                'hash': self.calcular_hash(origem),
                'tamanho': os.path.getsize(origem)
            }
            
            with open(os.path.join(self.CAMINHO_LOCAL, 'backups', f'metadata_{data_hora}.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Manter apenas os últimos 20 backups automáticos
            self.limpar_backups_antigos(manter=20, tipo='automático')
            
            return True, f"Backup criado: {nome_backup}"
            
        except Exception as e:
            return False, str(e)
    
    def criar_backup_manual(self, nome_personalizado):
        """Cria backup do banco de dados com nome personalizado (MANUAL)"""
        try:
            # Sanitizar nome
            nome_personalizado = "".join(c for c in nome_personalizado if c.isalnum() or c in "- _")
            if not nome_personalizado:
                return False, "Nome de backup inválido"
            
            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_backup = f"backup_{nome_personalizado}_{data_hora}.db"
            
            origem = os.path.join(self.CAMINHO_LOCAL, 'instance', 'database.db')
            destino = os.path.join(self.CAMINHO_LOCAL, 'backups', nome_backup)
            
            if not os.path.exists(origem):
                return False, "Banco de dados não encontrado"
            
            # Copiar arquivo
            shutil.copy2(origem, destino)
            
            # Criar arquivo de metadados
            metadata = {
                'data': data_hora,
                'origem': 'manual',
                'nome': nome_personalizado,
                'hash': self.calcular_hash(origem),
                'tamanho': os.path.getsize(origem)
            }
            
            with open(os.path.join(self.CAMINHO_LOCAL, 'backups', f'metadata_{data_hora}_manual.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True, f"Backup Manual criado: {nome_backup}"
            
        except Exception as e:
            return False, str(e)
    
    def limpar_backups_antigos(self, manter=20, tipo='automático'):
        """Mantém apenas os últimos 'manter' backups"""
        try:
            backups = []
            for arquivo in os.listdir('backups'):
                if arquivo.startswith('database_') and arquivo.endswith('.db'):
                    # Pegar metadados para verificar origem
                    data = arquivo.replace('database_', '').replace('.db', '')
                    meta_path = os.path.join('backups', f'metadata_{data}.json')
                    
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, 'r') as f:
                                metadata = json.load(f)
                                if metadata.get('origem') == 'automático':
                                    caminho = os.path.join('backups', arquivo)
                                    backups.append((os.path.getmtime(caminho), caminho, data))
                        except:
                            pass
            
            if not backups:
                return
            
            # Ordenar por data (mais recente primeiro)
            backups.sort(reverse=True)
            
            # Remover backups automáticos antigos (manuais não são removidos)
            for i, (_, caminho, data) in enumerate(backups):
                if i >= manter:
                    os.remove(caminho)
                    meta_path = os.path.join('backups', f'metadata_{data}.json')
                    if os.path.exists(meta_path):
                        os.remove(meta_path)
                    
            print(f"[OK] Limpeza concluída: mantidos {min(len(backups), manter)} backups automáticos")
            
        except Exception as e:
            print(f"Erro ao limpar backups antigos: {e}")
    
    def listar_backups(self):
        """Lista todos os backups disponíveis com separação por tipo"""
        backups_automaticos = []
        backups_manuais = []
        try:
            # Listar backups automáticos (database_*.db)
            for arquivo in os.listdir('backups'):
                if arquivo.startswith('database_') and arquivo.endswith('.db'):
                    caminho = os.path.join('backups', arquivo)
                    data_str = arquivo.replace('database_', '').replace('.db', '')
                    
                    try:
                        data = datetime.strptime(data_str, "%Y%m%d_%H%M%S")
                        data_formatada = data.strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        data_formatada = data_str
                    
                    backups_automaticos.append({
                        'arquivo': arquivo,
                        'caminho': caminho,
                        'data': data_formatada,
                        'tamanho': os.path.getsize(caminho),
                        'tipo': 'automático'
                    })
                
                # Listar backups manuais (backup_*.db)
                elif arquivo.startswith('backup_') and arquivo.endswith('.db'):
                    caminho = os.path.join('backups', arquivo)
                    
                    # Extrair data do nome
                    partes = arquivo.replace('backup_', '').replace('.db', '').split('_')
                    data_str = f"{partes[-2]}_{partes[-1]}"
                    
                    try:
                        data = datetime.strptime(data_str, "%Y%m%d_%H%M%S")
                        data_formatada = data.strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        data_formatada = data_str
                    
                    # Encontrar nome personalizado
                    nome_personalizado = '_'.join(partes[:-2]) if len(partes) > 2 else 'Sem nome'
                    
                    backups_manuais.append({
                        'arquivo': arquivo,
                        'caminho': caminho,
                        'data': data_formatada,
                        'tamanho': os.path.getsize(caminho),
                        'tipo': 'manual',
                        'nome': nome_personalizado
                    })
            
            # Ordenar por data (mais recente primeiro)
            backups_automaticos.sort(key=lambda x: x['arquivo'], reverse=True)
            backups_manuais.sort(key=lambda x: x['arquivo'], reverse=True)
            
            return {
                'automáticos': backups_automaticos,
                'manuais': backups_manuais
            }
            
        except Exception as e:
            print(f"Erro ao listar backups: {e}")
            return {'automáticos': [], 'manuais': []}
    
    def restaurar_backup(self, nome_backup):
        """Restaura um backup específico"""
        try:
            origem = os.path.join('backups', nome_backup)
            destino = os.path.join('instance', 'database.db')
            
            if not os.path.exists(origem):
                return False, "Backup não encontrado"
            
            # Fazer backup do atual antes de restaurar
            self.criar_backup_local()
            
            # Restaurar
            shutil.copy2(origem, destino)
            return True, f"Backup {nome_backup} restaurado com sucesso!"
            
        except Exception as e:
            return False, str(e)
    
    def deletar_backup(self, nome_backup):
        """Deleta um backup específico"""
        try:
            caminho = os.path.join('backups', nome_backup)
            
            if not os.path.exists(caminho):
                return False, "Backup não encontrado"
            
            # Remover arquivo
            os.remove(caminho)
            
            # Remover metadados associados
            data_str = nome_backup.replace('database_', '').replace('backup_', '').replace('.db', '')
            meta_path = os.path.join('backups', f'metadata_{data_str}.json')
            if os.path.exists(meta_path):
                os.remove(meta_path)
            
            return True, f"Backup {nome_backup} deletado com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao deletar backup: {str(e)}"
    
    def sincronizar_todos(self):
        """Sincroniza todos os arquivos do banco"""
        if not self.sincronizacao_ativa:
            return
        
        arquivos = ['database.db']
        for arquivo in arquivos:
            self.sincronizar_para_nuvem(arquivo)
    
    # ========== THREADS AUTOMÁTICAS ==========
    def iniciar_sincronizacao_automatica(self):
        """Inicia sincronização automática em segundo plano"""
        def sync_loop():
            while True:
                time.sleep(300)  # 5 minutos
                if self.sincronizacao_ativa:
                    self.sincronizar_todos()
        
        thread = threading.Thread(target=sync_loop, daemon=True)
        thread.start()
        print("[OK] Sincronização automática iniciada (a cada 5 minutos)")
    
    def iniciar_backup_automatico(self):
        """Inicia backup automático em segundo plano"""
        def backup_loop():
            while True:
                time.sleep(300)  # 5 minutos
                if not self.backup_em_andamento:
                    self.backup_em_andamento = True
                    sucesso, msg = self.criar_backup_local()
                    if sucesso:
                        print(f"[OK] Backup automático: {msg}")
                    self.backup_em_andamento = False
        
        thread = threading.Thread(target=backup_loop, daemon=True)
        thread.start()
        print("[OK] Backup automático iniciado (a cada 5 minutos)")
