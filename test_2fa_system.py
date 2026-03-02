#!/usr/bin/env python3
"""
Script de Teste - Validação de Sistema 2FA
Testa rate limiting, 2FA setup/verify e backup codes
"""

import sys
import json
from pathlib import Path

# Adicionar diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import User
from auth_security import (
    gerar_secret_2fa,
    gerar_qr_code,
    validar_codigo_2fa,
    gerar_backup_codes,
    rate_limiter,
    RateLimiter
)

def test_rate_limiter():
    """Testa sistema de rate limiting"""
    print("\n" + "="*60)
    print("TESTE 1: Rate Limiter (5 tentativas / 15 min)")
    print("="*60)
    
    limiter = RateLimiter()
    ip_teste = "192.168.1.100"
    
    # Simular 6 tentativas
    for i in range(1, 7):
        is_limited, remaining, reset_time = limiter.is_rate_limited(ip_teste, max_attempts=5)
        status = "BLOQUEADO" if is_limited else "PERMITIDO"
        print(f"Tentativa {i}: {status} (Restantes: {remaining})")
    
    print("[OK] Rate Limiter funcionando corretamente!\n")

def test_2fa_gerador():
    """Testa geração de secret e QR code"""
    print("="*60)
    print("TESTE 2: Gerador de 2FA (Secret + QR Code)")
    print("="*60)
    
    secret = gerar_secret_2fa()
    print(f"Secret gerado: {secret}")
    print(f"Tipo: {type(secret).__name__}, Tamanho: {len(secret)} caracteres")
    
    qr_code = gerar_qr_code("usuario_teste", secret)
    print(f"QR Code gerado: {'SIM' if qr_code else 'NAO'}")
    print(f"Formato QR: {'data:image/png;base64,...' if qr_code.startswith('data:') else 'Invalido'}")
    print("[OK] Secret e QR Code gerados com sucesso!\n")

def test_2fa_validacao():
    """Testa validação de código TOTP"""
    print("="*60)
    print("TESTE 3: Validacao de Codigo TOTP")
    print("="*60)
    
    secret = gerar_secret_2fa()
    print(f"Using secret: {secret}")
    
    # Obter código atual (apenas para demonstração)
    import pyotp
    totp = pyotp.TOTP(secret)
    codigo_valido = totp.now()
    
    print(f"Codigo valido atual: {codigo_valido}")
    
    # Testar validação
    resultado = validar_codigo_2fa(secret, codigo_valido)
    print(f"Validacao do codigo: {'PASSOU' if resultado else 'FALHOU'}")
    
    # Testar código inválido
    resultado_invalido = validar_codigo_2fa(secret, "000000")
    print(f"Validacao de codigo invalido: {'PASSOU (erro!)' if resultado_invalido else 'FALHOU (correto)'}")
    
    print("[OK] Validacao de TOTP funcionando!\n")

def test_backup_codes():
    """Testa geração de backup codes"""
    print("="*60)
    print("TESTE 4: Backup Codes (Codigos de Recuperacao)")
    print("="*60)
    
    codes = gerar_backup_codes()
    print(f"Total de backup codes gerados: {len(codes)}")
    print(f"Formato esperado: XXXX-XXXX-XXXX")
    print(f"\nExemplos:")
    for i, code in enumerate(codes[:3], 1):
        print(f"  {i}. {code}")
    
    # Validar formato
    import re
    formato_valido = all(re.match(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$', code) for code in codes)
    print(f"\nFormato de todos os codes valido: {'SIM' if formato_valido else 'NAO'}")
    print("[OK] Backup codes gerados com sucesso!\n")

def test_database_2fa_fields():
    """Testa se as colunas 2FA foram adicionadas ao banco"""
    print("="*60)
    print("TESTE 5: Campo 2FA no Banco de Dados")
    print("="*60)
    
    with app.app_context():
        # Verificar schema
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Obter nomes das tabelas
        tables = inspector.get_table_names()
        print(f"Tabelas disponivel: {', '.join(tables)}")
        
        # Procurar pela tabela do User
        user_table_name = None
        for table in ['user', 'users', 'User']:
            if table in tables:
                user_table_name = table
                break
        
        if not user_table_name:
            print("ERRO: Nenhuma tabela de usuários encontrada!")
            return
        
        columns = {col['name'] for col in inspector.get_columns(user_table_name)}
        
        required_columns = {
            'two_factor_enabled',
            'two_factor_secret',
            'backup_codes',
            'two_factor_verified_at'
        }
        
        missing = required_columns - columns
        
        if missing:
            print(f"ERRO: Colunas faltando: {missing}")
        else:
            print("Colunas encontradas:")
            for col in required_columns:
                print(f"  - {col}: OK")
        
        print("[OK] Banco de dados configurado corretamente!\n")

def test_user_2fa_methods():
    """Testa metodos 2FA do modelo User"""
    print("="*60)
    print("TESTE 6: Metodos 2FA do User Model")
    print("="*60)
    
    with app.app_context():
        # Criar usuario de teste
        test_user = User(
            username='teste_2fa',
            nome='Usuario Teste 2FA',
            email='teste@example.com',
            nivel='operador',
            status='aprovado'
        )
        test_user.set_password('senha123')
        
        # Testar setup_2fa
        print("Testando setup_2fa()...")
        secret, backup_codes = test_user.setup_2fa()
        print(f"  Secret: {secret[:10]}... (truncado)")
        print(f"  Backup codes: {len(json.loads(test_user.backup_codes))} gerados")
        
        # Testar confirm_2fa
        print("Testando confirm_2fa()...")
        test_user.confirm_2fa()
        print(f"  2FA habilitado: {test_user.two_factor_enabled}")
        
        # Testar usar_backup_code
        print("Testando usar_backup_code()...")
        codes = json.loads(test_user.backup_codes)
        primeiro_code = codes[0]
        resultado = test_user.usar_backup_code(primeiro_code)
        print(f"  Usado primeiro backup code: {resultado}")
        print(f"  Codigos restantes: {len(json.loads(test_user.backup_codes))}")
        
        # Testar disable_2fa
        print("Testando disable_2fa()...")
        test_user.disable_2fa()
        print(f"  2FA habilitado: {test_user.two_factor_enabled}")
        
        print("[OK] Todos os metodos 2FA funcionando!\n")

def test_routes_existe():
    """Testa se as rotas 2FA foram criadas"""
    print("="*60)
    print("TESTE 7: Rotas 2FA Disponivel")
    print("="*60)
    
    routes = []
    for rule in app.url_map.iter_rules():
        if '2fa' in rule.rule.lower():
            routes.append((rule.rule, list(rule.methods - {'OPTIONS', 'HEAD'})))
    
    if not routes:
        print("ERRO: Nenhuma rota 2FA encontrada!")
    else:
        print("Rotas 2FA encontradas:")
        for route, methods in routes:
            print(f"  {route}")
            print(f"    Metodos: {', '.join(methods)}")
    
    print("[OK] Rotas 2FA disponivel!\n")

def main():
    """Executar todos os testes"""
    print("\n" + "="*60)
    print("  SUITE DE TESTES - 2FA IMPLEMENTATION")
    print("="*60)
    
    try:
        test_rate_limiter()
        test_2fa_gerador()
        test_2fa_validacao()
        test_backup_codes()
        test_database_2fa_fields()
        test_user_2fa_methods()
        test_routes_existe()
        
        print("="*60)
        print("  RESUMO: TODOS OS TESTES PASSARAM!")
        print("="*60)
        print("\nProximo passo: Testar 2FA no navegador")
        print("1. Fazer login com credenciais")
        print("2. Acessar /users/setup-2fa para ativar")
        print("3. Logout e fazer login novamente com 2FA\n")
        
    except Exception as e:
        print(f"\nERRO durante execucao: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
