#!/usr/bin/env python
"""
Script de Validação Pós-Correção - Battlepass Truncation Fix
Verifica se todas as correções foram aplicadas com sucesso
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text, inspect

# Carregar variáveis de ambiente
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from backend.models import Operador, Equipe

def validar_schema_banco():
    """Verifica se o schema do banco foi atualizado corretamente"""
    print("\n" + "="*70)
    print("[VALIDAÇÃO] 🔍 Verificando Schema do Banco de Dados")
    print("="*70)
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Verificar coluna battlepass em operadores
            operadores_columns = inspector.get_columns('operadores')
            operadores_battlepass = next((col for col in operadores_columns if col['name'] == 'battlepass'), None)
            
            # Verificar coluna battlepass em equipes
            equipes_columns = inspector.get_columns('equipes')
            equipes_battlepass = next((col for col in equipes_columns if col['name'] == 'battlepass'), None)
            
            print("\n📊 Schema Atual:")
            print(f"  operadores.battlepass: {operadores_battlepass['type'] if operadores_battlepass else 'NÃO ENCONTRADA'}")
            print(f"  equipes.battlepass:    {equipes_battlepass['type'] if equipes_battlepass else 'NÃO ENCONTRADA'}")
            
            # Validar se são VARCHAR(50)
            if operadores_battlepass and 'VARCHAR' in str(operadores_battlepass['type']):
                varchar_length = str(operadores_battlepass['type']).replace('VARCHAR(', '').replace(')', '')
                if int(varchar_length) >= 50:
                    print("\n  ✅ operadores.battlepass está VARCHAR(50) - CORRETO!")
                    resultado_operadores = True
                else:
                    print(f"\n  ❌ operadores.battlepass está VARCHAR({varchar_length}) - INCORRETO! Deve ser 50")
                    resultado_operadores = False
            else:
                print("\n  ❌ Tipo desconhecido para operadores.battlepass")
                resultado_operadores = False
            
            if equipes_battlepass and 'VARCHAR' in str(equipes_battlepass['type']):
                varchar_length = str(equipes_battlepass['type']).replace('VARCHAR(', '').replace(')', '')
                if int(varchar_length) >= 50:
                    print("  ✅ equipes.battlepass está VARCHAR(50) - CORRETO!")
                    resultado_equipes = True
                else:
                    print(f"  ❌ equipes.battlepass está VARCHAR({varchar_length}) - INCORRETO! Deve ser 50")
                    resultado_equipes = False
            else:
                print("  ❌ Tipo desconhecido para equipes.battlepass")
                resultado_equipes = False
            
            return resultado_operadores and resultado_equipes
            
        except Exception as e:
            print(f"\n  ❌ Erro ao verificar schema: {str(e)}")
            return False


def validar_dados_existentes():
    """Verifica se operadores podem ter battlepass longo"""
    print("\n" + "="*70)
    print("[VALIDAÇÃO] 📋 Testando Inserção de Dados")
    print("="*70)
    
    with app.app_context():
        try:
            # Contar operadores com battlepass longo
            operadores_com_battlepass = Operador.query.filter(
                Operador.battlepass.isnot(None)
            ).all()
            
            print(f"\n  Operadores com battlepass definido: {len(operadores_com_battlepass)}")
            
            if operadores_com_battlepass:
                for op in operadores_com_battlepass[:3]:  # Mostrar até 3
                    bp_info = op.get_battlepass_info()
                    print(f"    - {op.warname}: {op.battlepass} ({len(op.battlepass)} chars) → {bp_info}")
            
            # Testar UPDATE com valor longo
            print("\n  🧪 Testando UPDATE com 'ELITE_CAVEIRA'...")
            
            # Criar operador de teste se não existir
            test_op = Operador.query.filter_by(warname='TEST_BATTLEPASS_VALIDATOR').first()
            if not test_op:
                test_op = Operador(
                    warname='TEST_BATTLEPASS_VALIDATOR',
                    nome='Test Battlepass Validator',
                    battlepass=None
                )
                db.session.add(test_op)
                db.session.commit()
                print("    ✅ Operador de teste criado")
            
            # Tentar atualizar com valor longo
            test_op.battlepass = 'ELITE_CAVEIRA'
            db.session.commit()
            
            # Verificar se salvou
            reloaded = Operador.query.filter_by(warname='TEST_BATTLEPASS_VALIDATOR').first()
            if reloaded and reloaded.battlepass == 'ELITE_CAVEIRA':
                print("    ✅ UPDATE com 'ELITE_CAVEIRA' funciona corretamente!")
                bp_info = reloaded.get_battlepass_info()
                print(f"    ✅ get_battlepass_info() retorna: {bp_info}")
                return True
            else:
                print("    ❌ UPDATE falhou - valor não foi salvo")
                return False
                
        except Exception as e:
            print(f"\n  ❌ Erro ao testar dados: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def validar_upload_folder():
    """Verifica se UPLOAD_FOLDER está configurado corretamente"""
    print("\n" + "="*70)
    print("[VALIDAÇÃO] 📁 Verificando Configuração de Upload")
    print("="*70)
    
    with app.app_context():
        upload_folder = app.config.get('UPLOAD_FOLDER')
        print(f"\n  UPLOAD_FOLDER: {upload_folder}")
        
        # Verificar se existe
        if os.path.exists(upload_folder):
            print(f"  ✅ Folder existe no caminho: {upload_folder}")
            
            # Contar arquivos
            files = os.listdir(upload_folder)
            print(f"  📊 Arquivos no folder: {len(files)}")
            
            if files:
                for f in files[:5]:
                    file_path = os.path.join(upload_folder, f)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        print(f"    - {f} ({size:,} bytes)")
            
            return True
        else:
            print(f"  ❌ Folder NÃO existe: {upload_folder}")
            print(f"  ℹ️  Criando folder...")
            try:
                os.makedirs(upload_folder, exist_ok=True)
                print(f"  ✅ Folder criado com sucesso")
                return True
            except Exception as e:
                print(f"  ❌ Erro ao criar folder: {e}")
                return False


def gerar_relatorio_final(validacoes):
    """Gera relatório final da validação"""
    print("\n" + "="*70)
    print("[RESULTADO] 📊 Relatório Final de Validação")
    print("="*70)
    
    total = len(validacoes)
    sucesso = sum(1 for v in validacoes.values() if v)
    
    print(f"\n  ✅ Sucessos: {sucesso}/{total}")
    
    for nome, resultado in validacoes.items():
        emoji = "✅" if resultado else "❌"
        print(f"    {emoji} {nome}")
    
    if sucesso == total:
        print("\n" + "="*70)
        print("🎉 TODAS AS VALIDAÇÕES PASSARAM! Sistema está pronto para uso.")
        print("="*70)
        print("\nVocê pode agora:")
        print("  ✓ Adicionar operadores com 'ELITE_CAVEIRA'")
        print("  ✓ Editar equipes com battlepass")
        print("  ✓ Upload de imagens funcionando")
        return True
    else:
        print("\n" + "="*70)
        print("⚠️  ALGUNS TESTES FALHARAM - Verifique os erros acima")
        print("="*70)
        return False


if __name__ == '__main__':
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🔨 VALIDAÇÃO - Battlepass Truncation Fix".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    validacoes = {
        'Schema do Banco de Dados': validar_schema_banco(),
        'Dados e Inserções': validar_dados_existentes(),
        'Configuração de Upload': validar_upload_folder()
    }
    
    sucesso = gerar_relatorio_final(validacoes)
    
    sys.exit(0 if sucesso else 1)
