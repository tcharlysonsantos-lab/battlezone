from app import app
from models import Equipe, Operador

with app.app_context():
    print("="*50)
    print("🔍 DIAGNÓSTICO DO SISTEMA")
    print("="*50)
    
    # Verificar pasta de uploads
    import os
    upload_folder = 'static/uploads'
    if os.path.exists(upload_folder):
        print(f"✅ Pasta de uploads existe: {os.path.abspath(upload_folder)}")
        files = os.listdir(upload_folder)
        print(f"   Arquivos encontrados: {len(files)}")
        for f in files:
            print(f"   - {f}")
    else:
        print(f"❌ Pasta de uploads NÃO existe! Criando...")
        os.makedirs(upload_folder)
        print(f"✅ Pasta criada: {os.path.abspath(upload_folder)}")
    
    # Verificar equipes
    equipes = Equipe.query.all()
    print(f"\n📊 Equipes no banco: {len(equipes)}")
    for eq in equipes:
        print(f"   - ID: {eq.id}, Nome: {eq.nome}, Foto: {eq.foto}, Membros: {eq.membros.count()}")
    
    # Verificar operadores
    ops = Operador.query.all()
    print(f"\n📊 Operadores no banco: {len(ops)}")
    for op in ops:
        print(f"   - ID: {op.id}, Nome: {op.nome}, Warname: {op.warname}")
      print("="*50)