#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ANÁLISE COMPLETA DO SISTEMA BATTLEZONE
Verifica funcionalidades, erros e inconsistências
"""

from app import app, db
from models import User, Operador, Equipe, Partida, Solicitacao, Log
import requests
from bs4 import BeautifulSoup
from datetime import datetime

print("\n" + "="*70)
print("🔍 ANÁLISE COMPLETA DO SISTEMA BATTLEZONE")
print("="*70)

with app.app_context():
    # ===================  VERIFICAÇÃO 1: BANCO DE DADOS  ===================
    print("\n1️⃣  VERIFICAÇÃO DO BANCO DE DADOS")
    print("-" * 70)
    
    total_users = User.query.count()
    total_operadores = Operador.query.count()
    total_equipes = Equipe.query.count()
    total_partidas = Partida.query.count()
    total_solicitacoes = Solicitacao.query.count()
    total_logs = Log.query.count()
    
    print(f"   ✅ Usuários: {total_users}")
    print(f"   ✅ Operadores: {total_operadores}")
    print(f"   ✅ Equipes: {total_equipes}")
    print(f"   ✅ Partidas: {total_partidas}")
    print(f"   ✅ Solicitações: {total_solicitacoes}")
    print(f"   ✅ Logs: {total_logs}")
    
    # ===================  VERIFICAÇÃO 2: USUÁRIOS  ===================
    print("\n2️⃣  VERIFICAÇÃO DE USUÁRIOS")
    print("-" * 70)
    
    usuarios = User.query.all()
    if usuarios:
        print(f"   Total: {len(usuarios)} usuários\n")
        for u in usuarios[:5]:  # Mostrar apenas os primeiros 5
            status_2fa = "✅ Ativado" if u.two_factor_enabled else "❌ Desativado"
            print(f"   • {u.username} ({u.nivel}) - Status: {u.status}, 2FA: {status_2fa}")
    else:
        print("   ⚠️  Nenhum usuário encontrado!")
    
    # ===================  VERIFICAÇÃO 3: OPERADORES  ===================
    print("\n3️⃣  VERIFICAÇÃO DE OPERADORES")
    print("-" * 70)
    
    operadores = Operador.query.all()
    if operadores:
        print(f"   Total: {len(operadores)} operadores\n")
        for o in operadores[:5]:
            usuario_vinculado = "✅ Sim" if o.usuario else "❌ Não"
            print(f"   • {o.warname} ({o.nome}) - Usuário vinculado: {usuario_vinculado}")
    else:
        print("   ⚠️  Nenhum operador encontrado!")
    
    # ===================  VERIFICAÇÃO 4: EQUIPES  ===================
    print("\n4️⃣  VERIFICAÇÃO DE EQUIPES")
    print("-" * 70)
    
    equipes = Equipe.query.all()
    if equipes:
        print(f"   Total: {len(equipes)} equipes\n")
        for e in equipes[:5]:
            try:
                membros_count = e.membros.count() if hasattr(e.membros, 'count') else len(e.membros)
                total_partidas = getattr(e, 'total_vitoria', 0) + getattr(e, 'total_derrota', 0)
            except:
                membros_count = 0
                total_partidas = 0
            print(f"   • {e.nome} - Membros: {membros_count}, Partidas: {total_partidas}")
    else:
        print("   ⚠️  Nenhuma equipe encontrada!")
    
    # ===================  VERIFICAÇÃO 5: TESTES DE SERVIDOR  ===================
    print("\n5️⃣  TESTES DE SERVIDOR (HTTP)")
    print("-" * 70)
    
    try:
        # Teste 1: Acessibilidade
        r = requests.get('http://192.168.0.100:5000/auth/login', timeout=5)
        if r.status_code == 200:
            print("   ✅ Servidor respondendo em 192.168.0.100:5000")
        else:
            print(f"   ❌ Servidor respondendo com status {r.status_code}")
        
        # Teste 2: Login admin
        session = requests.Session()
        r_login = session.get('http://192.168.0.100:5000/auth/login', timeout=5)
        soup = BeautifulSoup(r_login.text, 'html.parser')
        csrf = soup.find('input', {'name': 'csrf_token'})
        
        if csrf:
            print("   ✅ CSRF token presente no formulário")
            
            # Tentar login
            login_data = {
                'csrf_token': csrf.get('value'),
                'username': 'admin',
                'password': 'F6yTVRPZC0KPhh3r'
            }
            r_post = session.post('http://192.168.0.100:5000/auth/login', 
                                 data=login_data, allow_redirects=True, timeout=5)
            
            if 'dashboard' in r_post.url:
                print("   ✅ Login admin funcionando")
            else:
                print(f"   ❌ Login falhou - URL: {r_post.url}")
        else:
            print("   ❌ CSRF token não encontrado")
            
    except Exception as e:
        print(f"   ⚠️  Erro ao testar servidor: {str(e)}")
    
    # ===================  VERIFICAÇÃO 6: INTEGRIDADE DE DADOS  ===================
    print("\n6️⃣  INTEGRIDADE DE DADOS")
    print("-" * 70)
    
    # Usuários sem senha
    users_sem_senha = User.query.filter(
        (User.password_hash == None) | (User.password_hash == '')
    ).count()
    if users_sem_senha > 0:
        print(f"   ⚠️  {users_sem_senha} usuários sem senha!")
    else:
        print("   ✅ Todos os usuários têm senha")
    
    # Operadores sem vinculação com usuário
    operadores_sem_user = Operador.query.filter(~Operador.usuario.any()).count()
    print(f"   ℹ️  {operadores_sem_user} operadores sem usuário vinculado (normal)")
    
    # Verificar duplicatas
    nome_duplicados = db.session.query(User.nome, db.func.count()).group_by(User.nome).having(db.func.count() > 1).count()
    if nome_duplicados > 0:
        print(f"   ⚠️  {nome_duplicados} nomes de usuário duplicados!")
    else:
        print("   ✅ Nenhum nome duplicado")

print("\n" + "="*70)
print("✅ ANÁLISE CONCLUÍDA")
print("="*70 + "\n")
