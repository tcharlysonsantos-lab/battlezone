from app import app, db
from backend.models import Equipe, User, Operador  # ← IMPORT ADICIONADO!
from sqlalchemy import inspect, text

with app.app_context():
    print("[INFO] Iniciando atualização do banco de dados...\n")
    
    # =============== ATUALIZAR TABELA: equipes ===============
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('equipes')]
        
        if 'foto' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE equipes ADD COLUMN foto VARCHAR(200)'))
                conn.commit()
            print("[OK] Coluna 'foto' adicionada em equipes!")
        else:
            print("[OK] Coluna 'foto' já existe em equipes!")
            
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar equipes: {e}")
    
    # =============== ADICIONAR COLUNA OPERADOR_ID ===============
    print("\n[INFO] Verificando tabela users...")
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'operador_id' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN operador_id INTEGER REFERENCES operadores(id)'))
                conn.commit()
            print("[OK] Coluna 'operador_id' adicionada em users!")
            
            # Atualizar usuários existentes
            users = User.query.filter_by(status='aprovado').all()
            count = 0
            for user in users:
                operador = Operador.query.filter_by(warname=user.username).first()
                if operador:
                    user.operador_id = operador.id
                    count += 1
                    print(f"  ✅ Vinculado {user.username} -> {operador.warname}")
            
            db.session.commit()
            print(f"[OK] {count} usuários atualizados!")
        else:
            print("[OK] Coluna 'operador_id' já existe em users!")
            
    except Exception as e:
        print(f"[ERRO] Erro ao adicionar operador_id: {e}")
        db.session.rollback()

    # =============== ATUALIZAR TABELA: partida_participantes ===============
    print("\n[INFO] Verificando tabela partida_participantes...")
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('partida_participantes')]
        
        colunas_esperadas = ['equipe', 'kills', 'deaths', 'capturas', 'plantou_bomba', 
                            'desarmou_bomba', 'refens', 'cacou', 'resultado', 'mvp']
        
        with db.engine.connect() as conn:
            for col in colunas_esperadas:
                if col not in columns:
                    if col == 'equipe':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN equipe VARCHAR(50)'))
                    elif col == 'kills':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN kills INTEGER DEFAULT 0'))
                    elif col == 'deaths':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN deaths INTEGER DEFAULT 0'))
                    elif col == 'capturas':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN capturas INTEGER DEFAULT 0'))
                    elif col == 'plantou_bomba':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN plantou_bomba INTEGER DEFAULT 0'))
                    elif col == 'desarmou_bomba':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN desarmou_bomba INTEGER DEFAULT 0'))
                    elif col == 'refens':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN refens INTEGER DEFAULT 0'))
                    elif col == 'cacou':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN cacou INTEGER DEFAULT 0'))
                    elif col == 'resultado':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN resultado VARCHAR(20)'))
                    elif col == 'mvp':
                        conn.execute(text('ALTER TABLE partida_participantes ADD COLUMN mvp BOOLEAN DEFAULT 0'))
                    print(f"[OK] Coluna '{col}' adicionada em partida_participantes!")
                else:
                    print(f"[OK] Coluna '{col}' já existe em partida_participantes!")
            
            conn.commit()
        
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar partida_participantes: {e}")
        db.session.rollback()
    
    # =============== ATUALIZAR TABELA: operadores ===============
    print("\n[INFO] Verificando tabela operadores...")
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('operadores')]
        
        colunas_novos = ['total_capturas', 'total_plantas_bomba', 'total_desarmes_bomba', 
                        'total_refens', 'total_cacos', 'total_partidas']
        
        with db.engine.connect() as conn:
            for col in colunas_novos:
                if col not in columns:
                    conn.execute(text(f'ALTER TABLE operadores ADD COLUMN {col} INTEGER DEFAULT 0'))
                    print(f"[OK] Coluna '{col}' adicionada em operadores!")
                else:
                    print(f"[OK] Coluna '{col}' já existe em operadores!")
            
            conn.commit()
        
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar operadores: {e}")
        db.session.rollback()

    # =============== ATUALIZAR TABELA: solicitacoes ===============
    print("\n[INFO] Verificando tabela solicitacoes...")
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('solicitacoes')]
        
        with db.engine.connect() as conn:
            if 'telefone' not in columns:
                conn.execute(text('ALTER TABLE solicitacoes ADD COLUMN telefone VARCHAR(20)'))
                print(f"[OK] Coluna 'telefone' adicionada em solicitacoes!")
            else:
                print(f"[OK] Coluna 'telefone' já existe em solicitacoes!")
            
            if 'cpf' not in columns:
                conn.execute(text('ALTER TABLE solicitacoes ADD COLUMN cpf VARCHAR(20)'))
                print(f"[OK] Coluna 'cpf' adicionada em solicitacoes!")
            else:
                print(f"[OK] Coluna 'cpf' já existe em solicitacoes!")
            
            conn.commit()
        
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar solicitacoes: {e}")
        db.session.rollback()

print("\n[OK] Atualização concluída!")