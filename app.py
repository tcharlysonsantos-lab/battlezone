# app.py - BATTLEZONE SECURITY-FIRST EDITION
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timedelta
import os
import json
import logging
import calendar
from functools import lru_cache
from flask_login import current_user, logout_user
from sqlalchemy import func

# Importar configuração (NOVO)
from config import config as app_config

# Importar módulos do backend
from backend.models import db, User, Operador, Equipe, Partida, PartidaParticipante, Venda, Estoque, Log, Solicitacao, PagamentoOperador, Evento
from backend.auth import auth_bp
from backend.pagamentos_routes import pagamento_bp
from backend.decorators import requer_permissao, operador_session_required, admin_required
from backend.utils import get_valores_plano, get_modos_permitidos, PLANOS_WARFIELD, PLANOS_REDLINE
from backend.cloud_manager import CloudManager
from backend.forms import OperadorForm, EquipeForm, PartidaForm, VendaForm, EstoqueForm
from backend.security_utils import allowed_file_secure, safe_filename_with_timestamp, create_upload_directory
from backend.email_service import init_mail
from backend.health_check import db_health_check

# Importar segurança (NOVO)
from backend.security_middleware import (
    add_security_headers, 
    validar_entrada,
    log_security_event,
    verificar_rate_limit_login,
    registrar_tentativa_login
)
from backend.security_config import SESSION_CONFIG, RATELIMIT

# ==================== CRIAR PASTAS NECESSÁRIAS ====================
def criar_pastas_necessarias():
    """Cria pastas necessárias se não existirem"""
    pastas = [
        'logs',
        'backups_local/metadata',
        'frontend/static/uploads/galeria',
        'frontend/static/uploads/hero',
        'instance'
    ]
    
    for pasta in pastas:
        try:
            os.makedirs(pasta, exist_ok=True)
        except (OSError, FileExistsError) as e:
            # Se a pasta já existe, não é um erro
            if not os.path.isdir(pasta):
                print(f"[AVISO] Nao foi possivel criar {pasta}: {e}")

# Criar pastas na inicialização
criar_pastas_necessarias()

# ==================== CONFIGURAR LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== INICIALIZAR APP ====================
app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')

# CARREGAR CONFIGURAÇÃO DO config.py (NOVO)
app.config.from_object(app_config)

# ==================== CONFIGURAR PROXY FIX (RAILWAY/PRODUÇÃO) ====================
# Quando app está atrás de um proxy (Railway, Heroku, etc), precisa confiar nos headers
# X-Forwarded-For, X-Forwarded-Proto, X-Forwarded-Host para obter IP e esquema corretos
if not app.config['DEBUG']:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,           # Número de proxies para X-Forwarded-For
        x_proto=1,         # Número de proxies para X-Forwarded-Proto
        x_host=1,          # Número de proxies para X-Forwarded-Host
        x_port=1,          # Número de proxies para X-Forwarded-Port
        x_prefix=1         # Número de proxies para X-Forwarded-Prefix
    )

# ==================== INICIALIZAR SEGURANÇA ====================
# 1. CSRF Protection
csrf = CSRFProtect(app)

# CSRF Exemptions - rotas que não precisam de CSRF token
# OBS: DEVE ser feito AQUI, antes de qualquer request, não em before_request!
csrf._exempt_views.add('auth.forgot_password')

# 2. Headers de Segurança (NOVO)
# Configuração de CSP com todos os domínios necessários
csp_config = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "code.jquery.com"],
    'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com", "cdnjs.cloudflare.com"],
    'img-src': ["'self'", 'data:', 'https:'],
    'font-src': ["'self'", 'data:', 'fonts.gstatic.com', 'cdnjs.cloudflare.com', 'https:'],  # Permitir fontes HTTPS
    'connect-src': ["'self'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],  # Permitir source maps
}

# Em desenvolvimento, desabilitar algumas proteções do Talisman para permitir HTTP
if app.config['DEBUG']:
    # Desenvolvimento: permitir HTTP
    Talisman(app, 
        force_https=False,  # Permitir HTTP em desenvolvimento
        strict_transport_security=False,
        content_security_policy=csp_config
    )
else:
    # Produção: segurança completa com HTTPS
    Talisman(app, 
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,  # 1 ano
        content_security_policy=csp_config
    )

# 3. Rate Limiting (NOVO)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Em produção, usar Redis
)

# ==================== INICIALIZAR EXTENSÕES ====================
db.init_app(app)

# Inicializar Database Health Check (conexão persistente)
db_health_check.init_app(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'

# Inicializar Cloud Manager
cloud_manager = CloudManager(app)

# Inicializar Email Service (NOVO)
init_mail(app)

# Criar diretório de upload
create_upload_directory(app.config['UPLOAD_FOLDER'])

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(pagamento_bp, url_prefix='/pagamentos')

# ==================== MIDDLEWARE ====================
@app.before_request
def before_request():
    """Middleware para verificar sessão de operadores"""
    
    # Marcar sessão como permanente para renovar o timeout a cada requisição
    if current_user.is_authenticated:
        session.permanent = True
        
        if current_user.nivel == 'operador':
            if not current_user.is_session_valid():
                logout_user()
                session.clear()
                flash('Sessão expirada por inatividade (30 minutos).', 'warning')
                return redirect(url_for('auth.login'))
            
            # SÓ atualizar activity a cada 30 segundos (não a cada request!)
            time_since_last_update = (datetime.utcnow() - (current_user.last_activity or datetime.utcnow())).total_seconds()
            if time_since_last_update > 30:
                current_user.update_activity()

@app.after_request
def after_request(response):
    """✅ Consolidado: Batch commit + Security headers"""
    # 1. Fazer batch commit
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[COMMIT ERROR] {str(e)}", exc_info=True)
    
    # 2. Adicionar security headers
    response = add_security_headers(response)
    
    return response

# ==================== CSRF ERROR HANDLER ====================
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF errors with detailed logging"""
    logger.error(f"CSRF Error: {e.description}")
    logger.error(f"  Remote Addr: {request.remote_addr}")
    logger.error(f"  Method: {request.method}")
    logger.error(f"  Path: {request.path}")
    logger.error(f"  Secure: {request.is_secure}")
    logger.error(f"  X-Forwarded-Proto: {request.headers.get('X-Forwarded-Proto')}")
    logger.error(f"  X-Forwarded-For: {request.headers.get('X-Forwarded-For')}")
    logger.error(f"  Host: {request.host}")
    logger.error(f"  Cookies: {list(request.cookies.keys())}")
    
    flash('Erro de segurança: Token CSRF inválido. Tente novamente.', 'danger')
    return render_template('auth/login.html'), 400

# ==================== USER LOADER ====================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ==================== CONTEXT PROCESSOR ====================
@app.context_processor
def inject_now():
    """Injetar data atual nos templates"""
    return {'now': datetime.now()}

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/calendario-publico')
def calendario_publico():
    """Calendário público - MOSTRA CALENDÁRIO COMPLETO MAS SÓ PARTIDAS DE HOJE"""
    
    hoje = datetime.now()
    mes = hoje.month
    ano = hoje.year
    dia_hoje = hoje.day
    data_str = hoje.strftime('%d/%m/%Y')
    
    # ✅ OTIMIZAÇÃO: Filtrar datas NO SQL (não em Python!)
    # Usar eager loading para participantes
    partidas_hoje = Partida.query.filter_by(
        data=data_str,
        finalizada=False
    ).options(
        db.joinedload(Partida.participantes)  # Eager load participantes
    ).all()
    
    # Construir dicionário com vagas calculadas
    partidas_por_dia = {
        dia_hoje: [
            {
                'id': p.id,
                'nome': p.nome,
                'horario': p.horario,
                'campo': p.campo,
                'modo': p.modo,
                'vagas': 10 - len(p.participantes)  # Agora é rápido (já está em memória)
            }
            for p in partidas_hoje
        ]
    }
    
    # Gerar calendário completo do mês
    cal = calendar.monthcalendar(ano, mes)
    
    # Converter para JSON para passar ao template
    partidas_por_dia_json = json.dumps(partidas_por_dia)
    
    return render_template('public/calendario_publico.html',
                         cal=cal,
                         mes=mes,
                         ano=ano,
                         dia_hoje=dia_hoje,
                         mes_nome=calendar.month_name[mes],
                         partidas_por_dia=partidas_por_dia,
                         partidas_por_dia_json=partidas_por_dia_json,
                         data_hoje=data_str)

@app.route('/regras')
def regras():
    """Página pública de regras"""
    return render_template('public/regras.html')

@app.route('/dashboard')
@login_required
@operador_session_required
def dashboard():
    """Dashboard principal"""
    try:
        # ✅ OTIMIZAÇÃO: Criar operador background, não bloquear carregamento dashboard
        if current_user.nivel == 'operador':
            operador = Operador.query.filter_by(warname=current_user.username).first()
            if not operador:
                # Criar operador automaticamente
                operador = Operador(
                    nome=current_user.nome,
                    warname=current_user.username,
                    cpf=current_user.cpf or '',
                    email=current_user.email,
                    data_nascimento=current_user.data_nascimento or '',
                    idade=str(current_user.idade) if current_user.idade else '',
                    battlepass='NAO'
                )
                db.session.add(operador)
                # ✅ NÃO fazer commit aqui - deixar pro after_request fazer batch commit
        
        # ✅ OTIMIZAÇÃO: Uma única query com func.count() agregado
        stats = db.session.query(
            func.count(Operador.id).label('total_operadores'),
            func.count(Equipe.id).label('total_equipes')
        ).first()
        
        total_operadores = stats.total_operadores or 0
        total_equipes = stats.total_equipes or 0
        
        # ✅ OTIMIZAÇÃO: Data como string para comparação eficiente
        hoje = datetime.now().strftime("%d/%m/%Y")
        partidas_hoje = Partida.query.filter(Partida.data == hoje).count()
        
        # ✅ OTIMIZAÇÃO: Usar select() com limit para não carregar dados desnecessários
        itens_baixo = Estoque.query.filter(
            Estoque.quantidade <= Estoque.quantidade_minima,
            Estoque.ativo == True
        ).order_by(Estoque.quantidade).limit(10).all()
        
        # ✅ OTIMIZAÇÃO: Eager load para próximas partidas
        proximas_partidas = Partida.query.filter_by(finalizada=False).options(
            db.joinedload(Partida.criador)  # Eager load criador
        ).order_by(Partida.data, Partida.horario).limit(5).all()
        
        # ✅ OTIMIZAÇÃO: Calcular total de vendas no SQL (não em Python)
        vendas_resultado = db.session.query(
            func.sum(Venda.valor).label('total')
        ).filter(Venda.data == hoje, Venda.valor > 0).first()
        
        total_vendas_hoje = float(vendas_resultado.total or 0)
        
        # ✅ OTIMIZAÇÃO: Ordenar eventos no SQL (não em Python!)
        # Próximos eventos primeiro, depois eventos passados em ordem reversa
        todos_eventos = Evento.query.filter_by(
            ativo=True,
            deletado=False
        ).order_by(
            Evento.data_evento  # SQL faz o ordering
        ).limit(20).all()  # Limite para não sobrecarregar
        
        return render_template('dashboard.html',
                             total_operadores=total_operadores,
                             total_equipes=total_equipes,
                             partidas_hoje=partidas_hoje,
                             itens_baixo=itens_baixo,
                             proximas_partidas=proximas_partidas,
                             total_vendas_hoje=total_vendas_hoje,
                             todos_eventos=todos_eventos)
    
    except Exception as e:
        app.logger.error(f"[DASHBOARD ERROR] {str(e)}", exc_info=True)
        db.session.rollback()
        flash('Erro ao carregar dashboard. Tente novamente.', 'danger')
        return redirect(url_for('index'))

# ==================== ROTA PARA DELETAR USUÁRIO ====================
@app.route('/admin/usuario/<int:id>/deletar', methods=['POST'])
@login_required
@admin_required
def deletar_usuario(id):
    """Deleta um usuário e seu operador associado"""
    if current_user.nivel != 'admin':
        flash('Apenas administradores podem deletar usuários.', 'danger')
        return redirect(url_for('admin_usuarios'))
    
    if current_user.id == id:
        flash('Você não pode deletar seu próprio usuário!', 'danger')
        return redirect(url_for('admin_usuarios'))
    
    try:
        user = User.query.get_or_404(id)
        username = user.username
        
        # Buscar operador associado (pelo warname = username)
        operador = Operador.query.filter_by(warname=username).first()
        
        # Registrar log
        log = Log(
            usuario=current_user.username,
            acao='USUARIO_DELETADO',
            detalhes=f"Usuário: {username} (ID: {id})"
        )
        db.session.add(log)
        
        # DELETAR OPERADOR ASSOCIADO (SE EXISTIR)
        if operador:
            # Remover relacionamentos do operador
            if operador.membro_equipes:
                for equipe in operador.membro_equipes:
                    equipe.membros.remove(operador)
            
            partidas = PartidaParticipante.query.filter_by(operador_id=operador.id).all()
            if partidas:
                for part in partidas:
                    db.session.delete(part)
            
            db.session.delete(operador)
            mensagem_operador = f" e operador {operador.warname}"
        else:
            mensagem_operador = ""
        
        # DELETAR USUÁRIO
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Usuário {username}{mensagem_operador} deletado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao deletar usuário: {str(e)}')
        flash(f'Erro ao deletar usuário: {str(e)}', 'danger')
    
    return redirect(url_for('admin_usuarios'))

@app.route('/test-upload', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def test_upload():
    if request.method == 'POST':
        if 'foto' in request.files:
            file = request.files['foto']
            
            # Validar arquivo (NOVO)
            is_valid, msg = allowed_file_secure(
                filename=file.filename,
                max_size=app.config['MAX_CONTENT_LENGTH'],
                file_obj=file
            )
            
            if not is_valid:
                return f"❌ Erro: {msg}", 400
            
            # Gerar nome seguro (NOVO)
            safe_name = safe_filename_with_timestamp(file.filename)
            
            # Salvar arquivo
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], safe_name))
            return f"✅ Arquivo salvo: {safe_name}"
    
    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="foto" accept="image/*">
        <button type="submit">Enviar</button>
    </form>
    '''
# ==================== ROTAS DE OPERADORES ====================
@app.route('/operadores')
@login_required
@requer_permissao('operadores')
@operador_session_required
def listar_operadores():
    """Lista todos os operadores"""
    search = request.args.get('search', '')
    
    if search:
        operadores = Operador.query.filter(
            (Operador.nome.ilike(f'%{search}%')) | 
            (Operador.warname.ilike(f'%{search}%'))
        ).all()
    else:
        operadores = Operador.query.all()
    
    print(f"📋 Listando {len(operadores)} operadores")  # DEBUG
    
    return render_template('operadores/listar.html', operadores=operadores, search=search)

@app.route('/caixa')
@login_required
@requer_permissao('caixa')
def caixa():
    """Página do Caixa - Movimentação Financeira"""
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', datetime.now().strftime('%Y-%m-%d'))
    tipo = request.args.get('tipo', 'todos')
    status_filtro = request.args.get('status', 'todos')  # FILTRO DE STATUS
    
    # Converter datas
    inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
    fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
    
    # Buscar todas as vendas
    todas_vendas = Venda.query.all()
    movimentos = []
    
    for v in todas_vendas:
        try:
            data_venda = datetime.strptime(v.data, '%d/%m/%Y')
            if inicio <= data_venda <= fim:
                # Aplicar filtro de tipo
                if tipo == 'entrada' and v.valor < 0:
                    continue
                if tipo == 'saida' and v.valor > 0:
                    continue
                
                # APLICAR FILTRO DE STATUS
                if status_filtro != 'todos' and v.status != status_filtro:
                    continue
                
                movimentos.append(v)
        except:
            continue
    
    # Ordenar por data
    movimentos.sort(key=lambda x: datetime.strptime(x.data, '%d/%m/%Y'), reverse=True)
    
    # Cálculos
    saldo_atual = sum(v.valor for v in Venda.query.all() if v.status == 'Pago')
    
    hoje = datetime.now().strftime('%d/%m/%Y')
    movimentos_hoje = [v for v in Venda.query.all() if v.data == hoje]
    entradas_hoje = sum(v.valor for v in movimentos_hoje if v.valor > 0 and v.status == 'Pago')
    saidas_hoje = abs(sum(v.valor for v in movimentos_hoje if v.valor < 0 and v.status == 'Pago'))
    
    pendentes = Venda.query.filter_by(status='Pendente').all()
    a_receber = sum(v.valor for v in pendentes if v.valor > 0)
    a_pagar = abs(sum(v.valor for v in pendentes if v.valor < 0))
    total_pendente = a_receber - a_pagar  # ou a_receber + a_pagar dependendo da lógica
    
    saldo_periodo = sum(v.valor for v in movimentos if v.status == 'Pago')
    
    return render_template('caixa/index.html',
                         movimentos=movimentos,
                         saldo_atual=saldo_atual,
                         entradas_hoje=entradas_hoje,
                         saidas_hoje=saidas_hoje,
                         total_pendente=total_pendente,
                         saldo_periodo=saldo_periodo,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         tipo=tipo,
                         status_filtro=status_filtro)

# ==================== ROTAS DE ESTATÍSTICAS ====================

# ==================== ROTAS DE ESTATÍSTICAS ====================

@app.route('/estatisticas')
@login_required
@requer_permissao('estatisticas')
def estatisticas():
    """Página de estatísticas completa com todos os módulos"""
    
    # Pegar parâmetros
    aba_ativa = request.args.get('aba', 'operadores')
    
    # ===== RANKING DE OPERADORES COM FILTROS =====
    operadores = Operador.query.all()
    operadores_ranking = []
    
    for op in operadores:
        operadores_ranking.append({
            'id': op.id,
            'nome': op.nome,
            'warname': op.warname,
            'total_kills': op.total_kills or 0,
            'total_deaths': op.total_deaths or 0,
            'total_capturas': op.total_capturas or 0,
            'total_plantas_bomba': op.total_plantas_bomba or 0,
            'total_desarmes_bomba': op.total_desarmes_bomba or 0,
            'total_refens': op.total_refens or 0,
            'total_cacos': op.total_cacos or 0,
            'total_vitorias': op.total_vitorias or 0,
            'total_derrotas': op.total_derrotas or 0,
            'total_mvps': op.total_mvps or 0,
            'kd': (op.total_kills or 0) / (op.total_deaths or 1) if op.total_deaths else (op.total_kills or 0)
        })
    
    # FILTROS DE OPERADORES
    search_operador = request.args.get('search_operador', '').lower()
    ordenar_por = request.args.get('ordenar_por', 'kd')
    ordem = request.args.get('ordem', 'desc')
    
    # Aplicar busca
    if search_operador:
        operadores_ranking = [op for op in operadores_ranking 
                            if search_operador in op['nome'].lower() 
                            or search_operador in op['warname'].lower()]
    
    # Ordenar operadores
    reverse = ordem == 'desc'
    if ordenar_por == 'kd':
        operadores_ranking.sort(key=lambda x: x['kd'], reverse=reverse)
    elif ordenar_por == 'kills':
        operadores_ranking.sort(key=lambda x: x['total_kills'], reverse=reverse)
    elif ordenar_por == 'deaths':
        operadores_ranking.sort(key=lambda x: x['total_deaths'], reverse=reverse)
    elif ordenar_por == 'capturas':
        operadores_ranking.sort(key=lambda x: x['total_capturas'], reverse=reverse)
    elif ordenar_por == 'plantas':
        operadores_ranking.sort(key=lambda x: x['total_plantas_bomba'], reverse=reverse)
    elif ordenar_por == 'desarmes':
        operadores_ranking.sort(key=lambda x: x['total_desarmes_bomba'], reverse=reverse)
    elif ordenar_por == 'refens':
        operadores_ranking.sort(key=lambda x: x['total_refens'], reverse=reverse)
    elif ordenar_por == 'cacos':
        operadores_ranking.sort(key=lambda x: x['total_cacos'], reverse=reverse)
    elif ordenar_por == 'vitorias':
        operadores_ranking.sort(key=lambda x: x['total_vitorias'], reverse=reverse)
    elif ordenar_por == 'derrotas':
        operadores_ranking.sort(key=lambda x: x['total_derrotas'], reverse=reverse)
    elif ordenar_por == 'mvps':
        operadores_ranking.sort(key=lambda x: x['total_mvps'], reverse=reverse)
    
    # ===== ESTATÍSTICAS DE EQUIPES =====
    from backend.models import Equipe
    
    # Primeiro, buscar TODAS as partidas finalizadas de equipe
    partidas_equipe = Partida.query.filter_by(tipo_participacao='equipe', finalizada=True).all()
    
    # Extrair todas as equipes únicas que realmente participaram de partidas
    equipes_participantes = set()
    for partida in partidas_equipe:
        for participante in partida.participantes:
            if participante.equipe:
                equipes_participantes.add(participante.equipe.lower())
    
    # Inicializar estatísticas com as equipes que realmente participaram
    estatisticas_equipes = []
    for equipe_nome in sorted(equipes_participantes):
        # Tentar encontrar a equipe no banco para pegar o ID
        equipe_db = Equipe.query.filter(Equipe.nome.ilike(equipe_nome)).first()
        
        estatisticas_equipes.append({
            'id': equipe_db.id if equipe_db else None,
            'nome': equipe_nome.upper() if equipe_nome in ['gta', 'spartas'] else equipe_nome,  # Manter maiúscula para GTA e SPARTAS
            'total_partidas': 0,
            'vitorias': 0,
            'derrotas': 0,
            'empates': 0,
            'total_kills': 0
        })
    
    print(f"\n🏆 DEBUG Estatísticas de Equipes:")
    print(f"  Equipes participantes: {equipes_participantes}")
    print(f"  Total de partidas de equipe: {len(partidas_equipe)}")
    
    for partida in partidas_equipe:
        # Contar kills por equipe dinamicamente
        kills_por_equipe = {}
        
        # Extrair equipes únicas e contar kills
        for participante in partida.participantes:
            if participante.equipe:
                equipe_lower = participante.equipe.lower()
                if equipe_lower not in kills_por_equipe:
                    kills_por_equipe[equipe_lower] = 0
                kills_por_equipe[equipe_lower] += participante.kills or 0
        
        print(f"  - Partida {partida.id}: {partida.nome} | Vencedora: {partida.equipe_vencedora} | Kills: {kills_por_equipe}")
        
        equipe_vencedora_lower = partida.equipe_vencedora.lower() if partida.equipe_vencedora else None
        
        # Atualizar estatísticas para TODAS as equipes que participaram (dinâmico)
        for eq in estatisticas_equipes:
            eq_nome_lower = eq['nome'].lower()
            
            # Se esta equipe participou da partida
            if eq_nome_lower in kills_por_equipe:
                eq['total_partidas'] += 1
                eq['total_kills'] += kills_por_equipe[eq_nome_lower]
                
                if equipe_vencedora_lower == eq_nome_lower:
                    eq['vitorias'] += 1
                elif equipe_vencedora_lower and equipe_vencedora_lower != eq_nome_lower:
                    eq['derrotas'] += 1
                else:
                    eq['empates'] += 1
    
    # FILTROS DE EQUIPES
    search_equipe = request.args.get('search_equipe', '').lower()
    ordenar_equipe = request.args.get('ordenar_equipe', 'vitorias')
    ordem_equipe = request.args.get('ordem_equipe', 'desc')
    
    if search_equipe:
        estatisticas_equipes = [eq for eq in estatisticas_equipes 
                               if search_equipe in eq['nome'].lower()]
    
    reverse_equipe = ordem_equipe == 'desc'
    if ordenar_equipe == 'vitorias':
        estatisticas_equipes.sort(key=lambda x: x['vitorias'], reverse=reverse_equipe)
    elif ordenar_equipe == 'derrotas':
        estatisticas_equipes.sort(key=lambda x: x['derrotas'], reverse=reverse_equipe)
    elif ordenar_equipe == 'total_kills':
        estatisticas_equipes.sort(key=lambda x: x['total_kills'], reverse=reverse_equipe)
    elif ordenar_equipe == 'aproveitamento':
        for eq in estatisticas_equipes:
            eq['aproveitamento'] = (eq['vitorias'] / eq['total_partidas'] * 100) if eq['total_partidas'] > 0 else 0
        estatisticas_equipes.sort(key=lambda x: x['aproveitamento'], reverse=reverse_equipe)
    
    # ===== PARTIDAS FINALIZADAS =====
    tipo_partida = request.args.get('tipo_partida', 'todas')
    search = request.args.get('search', '')
    periodo = request.args.get('periodo', 'todas')
    
    query = Partida.query.filter_by(finalizada=True)
    
    if tipo_partida != 'todas':
        query = query.filter_by(tipo_participacao=tipo_partida)
    
    partidas = query.all()
    
    # Ordenar por ID descendente (mais recentes primeiro)
    partidas.sort(key=lambda p: p.id, reverse=True)
    
    print(f"DEBUG: Total de partidas em estatísticas: {len(partidas)}")
    if partidas:
        for i, p in enumerate(partidas[:3]):
            print(f"  {i+1}. ID={p.id} | {p.data} {p.horario} - {p.nome}")
    
    # Filtrar por período
    hoje = datetime.now()
    
    if periodo != 'todas':
        partidas_filtradas = []
        for p in partidas:
            try:
                data_p = datetime.strptime(p.data, '%d/%m/%Y')
                if periodo == 'hoje' and p.data == hoje.strftime('%d/%m/%Y'):
                    partidas_filtradas.append(p)
                elif periodo == 'semana' and (hoje - data_p).days <= 7:
                    partidas_filtradas.append(p)
                elif periodo == 'mes' and (hoje - data_p).days <= 30:
                    partidas_filtradas.append(p)
                else:
                    partidas_filtradas.append(p)
            except:
                if periodo == 'todas':
                    partidas_filtradas.append(p)
        partidas = partidas_filtradas
    
    # Filtrar por busca
    if search:
        search_lower = search.lower()
        partidas_filtradas = []
        for p in partidas:
            if search_lower in p.nome.lower():
                partidas_filtradas.append(p)
                continue
            for part in p.participantes:
                if search_lower in part.warname.lower():
                    partidas_filtradas.append(p)
                    break
        partidas = partidas_filtradas
    
    return render_template('estatisticas/index.html',
                         operadores_ranking=operadores_ranking,
                         estatisticas_equipes=estatisticas_equipes,
                         partidas_finalizadas=partidas,
                         aba_ativa=aba_ativa,
                         tipo_partida=tipo_partida,
                         search=search,
                         periodo=periodo,
                         search_operador=search_operador,
                         ordenar_por=ordenar_por,
                         ordem=ordem,
                         search_equipe=search_equipe,
                         ordenar_equipe=ordenar_equipe,
                         ordem_equipe=ordem_equipe)

@app.route('/estatisticas/operador/<int:id>')
@login_required
@requer_permissao('estatisticas')
def ver_estatisticas_operador(id):
    """Visualiza as estatísticas detalhadas de um operador com filtros"""
    operador = Operador.query.get_or_404(id)
    
    # Pegar filtros da URL
    periodo = request.args.get('periodo', 'Todas')
    search = request.args.get('search', '')
    resultado_filtro = request.args.get('resultado', 'todos')
    
    # Pegar todas as partidas do operador
    participacoes = PartidaParticipante.query.filter_by(operador_id=id).join(Partida).filter(Partida.finalizada==True).all()
    
    # Calcular estatísticas totais
    stats = {
        'nome': operador.nome,
        'warname': operador.warname,
        'total_kills': operador.total_kills or 0,
        'total_deaths': operador.total_deaths or 0,
        'total_capturas': operador.total_capturas or 0,
        'total_plantas_bomba': operador.total_plantas_bomba or 0,
        'total_desarmes_bomba': operador.total_desarmes_bomba or 0,
        'total_refens': operador.total_refens or 0,
        'total_cacos': operador.total_cacos or 0,
        'total_vitorias': operador.total_vitorias or 0,
        'total_derrotas': operador.total_derrotas or 0,
        'total_mvps': operador.total_mvps or 0,
        'total_partidas': operador.total_partidas or 0,
    }
    
    # Calcular K/D
    stats['kd'] = stats['total_kills'] / stats['total_deaths'] if stats['total_deaths'] > 0 else stats['total_kills']
    
    # Processar histórico
    partidas_historico = []
    hoje = datetime.now()
    
    for part in participacoes:
        if part.partida and part.partida.finalizada:
            # Aplicar filtro de busca
            if search and search.lower() not in part.partida.nome.lower():
                continue
            
            # Aplicar filtro de resultado
            if resultado_filtro != 'todos' and part.resultado != resultado_filtro:
                continue
            
            # Aplicar filtro de período
            if periodo != 'Todas':
                try:
                    data_partida = datetime.strptime(part.partida.data, '%d/%m/%Y')
                    dias_atras = (hoje - data_partida).days
                    
                    if periodo == 'Hoje' and part.partida.data != hoje.strftime('%d/%m/%Y'):
                        continue
                    elif periodo == '7d' and dias_atras > 7:
                        continue
                    elif periodo == '30d' and dias_atras > 30:
                        continue
                    elif periodo == '3m' and dias_atras > 90:
                        continue
                except ValueError:
                    continue
            
            partidas_historico.append({
                'partida_id': part.partida_id,
                'nome_partida': part.partida.nome,
                'modo': part.partida.modo,
                'data': part.partida.data,
                'horario': part.partida.horario,
                'kills': part.kills or 0,
                'deaths': part.deaths or 0,
                'capturas': part.capturas or 0,
                'plantas': part.plantou_bomba or 0,
                'desarmes': part.desarmou_bomba or 0,
                'refens': part.refens or 0,
                'cacadas': part.cacou or 0,
                'resultado': part.resultado or '-',
                'mvp': part.mvp or False
            })
    
    # Ordenar por data mais recente
    partidas_historico.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y') if x['data'] else datetime.now(), reverse=True)
    
    return render_template('estatisticas/operador.html',
                         operador=operador,
                         stats=stats,
                         partidas_historico=partidas_historico,
                         periodo=periodo,
                         search=search,
                         resultado_filtro=resultado_filtro)

@app.route('/partidas/<int:id>/finalizar', methods=['GET'])
@login_required
@requer_permissao('partidas')
def formulario_finalizar_partida(id):
    """Exibe o formulário para finalizar partida (GET)"""
    partida = Partida.query.get_or_404(id)
    
    # Se for modo equipe, extrair as equipes reais que participaram
    equipes_partida = []
    if partida.tipo_participacao == 'equipe':
        # Pegar todas as equipes únicas da partida
        equipes_unicas = set()
        for p in partida.participantes:
            if p.equipe:
                equipes_unicas.add(p.equipe)
        equipes_partida = sorted(list(equipes_unicas))
    
    return render_template('partidas/finalizar.html', 
                         partida=partida,
                         equipes_partida=equipes_partida)

@app.route('/operadores/<int:id>/perfil')
@login_required
def perfil_operador(id):
    """Página de perfil do operador com filtros"""
    operador = Operador.query.get_or_404(id)
    
    # Pegar filtros da URL
    search = request.args.get('search', '')
    resultado_filtro = request.args.get('resultado', 'todos')
    periodo = request.args.get('periodo', 'Todas')
    
    # Verificar se é o próprio operador ou admin
    é_proprio = (current_user.nivel == 'operador' and 
                 current_user.username == operador.warname)
    é_admin = current_user.nivel == 'admin'
    
    # Buscar participações em partidas
    participacoes = PartidaParticipante.query.filter_by(operador_id=id).all()
    
    # Filtrar partidas
    partidas_filtradas = []
    hoje = datetime.now()
    
    for p in participacoes:
        if p.partida and p.partida.finalizada:
            incluir = True
            
            # Filtro de busca por nome ou modo
            if search:
                search_lower = search.lower()
                if (search_lower not in p.partida.nome.lower() and 
                    search_lower not in p.partida.modo.lower()):
                    incluir = False
            
            # Filtro de resultado
            if resultado_filtro != 'todos' and p.resultado != resultado_filtro:
                incluir = False
            
            # Filtro de período
            if periodo != 'Todas':
                try:
                    data_partida = datetime.strptime(p.partida.data, '%d/%m/%Y')
                    dias_atras = (hoje - data_partida).days
                    
                    if periodo == 'Hoje' and p.partida.data != hoje.strftime('%d/%m/%Y'):
                        incluir = False
                    elif periodo == '7d' and dias_atras > 7:
                        incluir = False
                    elif periodo == '30d' and dias_atras > 30:
                        incluir = False
                except:
                    pass
            
            if incluir:
                partidas_filtradas.append(p)
    
    # Buscar compras (vendas) - apenas se for o próprio operador ou admin
    compras = []
    if é_proprio or é_admin:
        compras = Venda.query.filter(
            (Venda.warname == operador.warname) | 
            (Venda.cliente == operador.nome)
        ).order_by(Venda.data.desc()).all()
    
    # Calcular estatísticas
    total_kills = 0
    total_deaths = 0
    vitorias = 0
    derrotas = 0
    empates = 0
    
    for p in participacoes:
        total_kills += p.kills or 0
        total_deaths += p.deaths or 0
        if p.resultado == 'vitoria':
            vitorias += 1
        elif p.resultado == 'derrota':
            derrotas += 1
        else:
            empates += 1
    
    total_partidas = len(participacoes)
    kd_ratio = total_kills / total_deaths if total_deaths > 0 else total_kills
    
    return render_template('operadores/perfil.html',
                         operador=operador,
                         partidas=participacoes,
                         partidas_filtradas=partidas_filtradas,
                         compras=compras,
                         é_proprio=é_proprio,
                         é_admin=é_admin,
                         total_kills=total_kills,
                         total_deaths=total_deaths,
                         kd_ratio=kd_ratio,
                         total_partidas=total_partidas,
                         vitorias=vitorias,
                         derrotas=derrotas,
                         empates=empates,
                         search=search,
                         resultado_filtro=resultado_filtro,
                         periodo=periodo)
                         
@app.route('/')
def index():
    """Página inicial pública"""
    try:
        logger.info("[INDEX] Iniciando rota /")
        
        agora = datetime.now()
        data_hoje = agora.strftime("%d/%m/%Y")
        hora_atual = agora.strftime("%H:%M")
        
        # Buscar partidas de hoje com horário futuro
        logger.info("[INDEX] Executando query para partidas")
        todas_partidas = Partida.query.filter_by(finalizada=False).all()
        logger.info(f"[INDEX] Query retornou {len(todas_partidas)} partidas")
        partidas_hoje = []
        
        for p in todas_partidas:
            if p.data == data_hoje and p.horario > hora_atual:
                partidas_hoje.append({
                    'nome': p.nome,
                    'horario': p.horario,
                    'campo': p.campo,
                    'modo': p.modo,
                    'total_participantes': len(p.participantes)
                })
        
        # Ordenar por horário
        partidas_hoje.sort(key=lambda x: x['horario'])
        
        # Gerar horários disponíveis (a cada 10 minutos)
        horarios_disponiveis = []
        agora = datetime.now()
        hora_atual_num = agora.hour * 60 + agora.minute
        # Horário de funcionamento: 15:30 às 22:00
        inicio = 15 * 60 + 30  # 15:30 em minutos
        fim = 22 * 60  # 22:00 em minutos

        for minuto_total in range(inicio, fim, 10):  # a cada 10 minutos
            if minuto_total > hora_atual_num + 1:  # +1 minuto de tolerância
                hora = minuto_total // 60
                minuto = minuto_total % 60
                horarios_disponiveis.append(f"{hora:02d}:{minuto:02d}")
        
        from backend.utils import PLANOS_WARFIELD, PLANOS_REDLINE
        
        logger.info(f"[INDEX] Renderizando template com {len(partidas_hoje)} partidas")
        return render_template('public/index.html',
                             partidas_hoje=partidas_hoje,
                             horarios_disponiveis=horarios_disponiveis,
                             planos_warfield=PLANOS_WARFIELD,
                             planos_redline=PLANOS_REDLINE)
    except Exception as e:
        logger.error(f"[INDEX] ERRO: {e}", exc_info=True)
        print(f"Erro: {e}")
        from backend.utils import PLANOS_WARFIELD, PLANOS_REDLINE
        return render_template('public/index.html',
                             partidas_hoje=[],
                             horarios_disponiveis=['15:30', '16:30', '17:30', '18:30', '19:30', '20:30', '21:30'],
                             planos_warfield=PLANOS_WARFIELD,
                             planos_redline=PLANOS_REDLINE)
    
@app.route('/partidas/<int:id>/salvar-resultado', methods=['POST'])
@login_required
@requer_permissao('partidas')
def salvar_resultado_partida(id):
    """Salva o resultado da partida (POST)"""
    partida = Partida.query.get_or_404(id)
    
    try:
        # Se for Redline, apenas finalizar sem processar estatísticas
        if partida.campo == 'Redline':
            partida.status = 'Finalizada'
            partida.finalizada = True
            db.session.commit()
            flash('[OK] Partida Redline finalizada com sucesso!', 'success')
            return redirect(url_for('ver_partida', id=id))
        
        # Dicionário para somar kills por equipe (dinâmico - suporta qualquer equipe)
        kills_por_equipe = {}
        
        # Se for modo equipe, processar resultado da partida
        if partida.tipo_participacao == 'equipe':
            partida.equipe_vencedora = request.form.get('equipe_vencedora')
            # Extrair equipes únicas que participam
            for p in partida.participantes:
                if p.equipe:
                    equipe_lower = p.equipe.lower()
                    if equipe_lower not in kills_por_equipe:
                        kills_por_equipe[equipe_lower] = 0
        
        # Processar estatísticas de cada participante
        for participante in partida.participantes:
            # Se for modo equipe, atualizar a equipe do participante (editável)
            if partida.tipo_participacao == 'equipe':
                equipe_selecionada = request.form.get(f'equipe_{participante.id}')
                if equipe_selecionada:
                    participante.equipe = equipe_selecionada
            
            # Estatísticas básicas
            kills = int(request.form.get(f'kills_{participante.id}', 0))
            deaths = int(request.form.get(f'deaths_{participante.id}', 0))
            
            participante.kills = kills
            participante.deaths = deaths
            
            # Somar kills por equipe (para modo equipe - dinâmico para ANY equipe)
            if partida.tipo_participacao == 'equipe' and participante.equipe:
                equipe_lower = participante.equipe.lower()
                if equipe_lower not in kills_por_equipe:
                    kills_por_equipe[equipe_lower] = 0
                kills_por_equipe[equipe_lower] += kills
            
            # Novas estatísticas
            participante.capturas = int(request.form.get(f'capturas_{participante.id}', 0))
            participante.plantou_bomba = int(request.form.get(f'plantou_{participante.id}', 0))
            participante.desarmou_bomba = int(request.form.get(f'desarmou_{participante.id}', 0))
            participante.refens = int(request.form.get(f'refens_{participante.id}', 0))
            participante.cacou = int(request.form.get(f'cacou_{participante.id}', 0))
            
            # Resultado e MVP
            participante.resultado = request.form.get(f'resultado_{participante.id}', 'empate')
            participante.mvp = request.form.get(f'mvp_{participante.id}') == '1'
            
            if participante.mvp:
                partida.mvp_id = participante.operador_id
            
            # ===== ATUALIZAR ESTATÍSTICAS DO OPERADOR =====
            operador = participante.operador
            if operador:
                # Inicializar campos se não existirem
                if not hasattr(operador, 'total_kills') or operador.total_kills is None:
                    operador.total_kills = 0
                if not hasattr(operador, 'total_deaths') or operador.total_deaths is None:
                    operador.total_deaths = 0
                if not hasattr(operador, 'total_capturas') or operador.total_capturas is None:
                    operador.total_capturas = 0
                if not hasattr(operador, 'total_plantas_bomba') or operador.total_plantas_bomba is None:
                    operador.total_plantas_bomba = 0
                if not hasattr(operador, 'total_desarmes_bomba') or operador.total_desarmes_bomba is None:
                    operador.total_desarmes_bomba = 0
                if not hasattr(operador, 'total_refens') or operador.total_refens is None:
                    operador.total_refens = 0
                if not hasattr(operador, 'total_cacos') or operador.total_cacos is None:
                    operador.total_cacos = 0
                if not hasattr(operador, 'total_partidas') or operador.total_partidas is None:
                    operador.total_partidas = 0
                if not hasattr(operador, 'total_vitorias') or operador.total_vitorias is None:
                    operador.total_vitorias = 0
                if not hasattr(operador, 'total_derrotas') or operador.total_derrotas is None:
                    operador.total_derrotas = 0
                if not hasattr(operador, 'total_mvps') or operador.total_mvps is None:
                    operador.total_mvps = 0
                
                # Somar estatísticas
                operador.total_kills += kills
                operador.total_deaths += deaths
                operador.total_capturas += participante.capturas
                operador.total_plantas_bomba += participante.plantou_bomba
                operador.total_desarmes_bomba += participante.desarmou_bomba
                operador.total_refens += participante.refens
                operador.total_cacos += participante.cacou
                operador.total_partidas += 1
                
                # Atualizar vitórias/derrotas
                if participante.resultado == 'vitoria':
                    operador.total_vitorias += 1
                elif participante.resultado == 'derrota':
                    operador.total_derrotas += 1
                
                # Atualizar MVPs
                if participante.mvp:
                    operador.total_mvps += 1
        
        # Se for modo equipe, definir o placar baseado nas kills somadas (dinâmico)
        if partida.tipo_participacao == 'equipe' and kills_por_equipe:
            equipes_sorted = sorted(kills_por_equipe.keys())
            if len(equipes_sorted) >= 1:
                partida.placar_equipe1 = kills_por_equipe.get(equipes_sorted[0], 0)
            if len(equipes_sorted) >= 2:
                partida.placar_equipe2 = kills_por_equipe.get(equipes_sorted[1], 0)
        
        partida.status = 'Finalizada'
        partida.finalizada = True
        db.session.commit()
        
        flash('[OK] Partida finalizada com sucesso!', 'success')
        return redirect(url_for('ver_partida', id=id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao finalizar: {str(e)}', 'danger')
        return redirect(url_for('formulario_finalizar_partida', id=id))
            
@app.route('/operadores/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('operadores')
def novo_operador():
    """Cria novo operador com validação especial de CPF"""
    form = OperadorForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Verificações básicas
                if Operador.query.filter_by(warname=form.warname.data).first():
                    flash('❌ Warname já existe!', 'danger')
                    return render_template('operadores/form.html', form=form, titulo='Novo Operador')
                
                if Operador.query.filter_by(email=form.email.data).first():
                    flash('❌ Email já existe!', 'danger')
                    return render_template('operadores/form.html', form=form, titulo='Novo Operador')
                
                if Operador.query.filter_by(nome=form.nome.data).first():
                    flash('❌ Nome já existe!', 'danger')
                    return render_template('operadores/form.html', form=form, titulo='Novo Operador')
                
                # VERIFICAÇÃO ESPECIAL DE CPF
                operador_cpf = Operador.query.filter_by(cpf=form.cpf.data).first()
                
                if operador_cpf:
                    # CPF já existe em outro operador
                    usuario_cpf = User.query.filter_by(username=operador_cpf.warname).first()
                    
                    if usuario_cpf:
                        # CPF já pertence a um operador COM usuário
                        flash('⚠️ Este CPF já pertence a outro operador. Entre em contato com a BATTLEZONE para resolver!', 'warning')
                        return render_template('operadores/form.html', form=form, titulo='Novo Operador')
                    else:
                        # CPF pertence a operador SEM usuário - vamos vincular
                        flash('ℹ️ CPF encontrado em operador sem usuário. Vinculando automaticamente...', 'info')
                        
                        # Atualizar dados do operador existente
                        operador_cpf.nome = form.nome.data
                        operador_cpf.warname = form.warname.data
                        operador_cpf.email = form.email.data
                        operador_cpf.telefone = form.telefone.data
                        operador_cpf.data_nascimento = form.data_nascimento.data
                        operador_cpf.idade = form.idade.data
                        operador_cpf.battlepass = form.battlepass.data
                        
                        db.session.commit()
                        
                        flash(f'✅ Operador {operador_cpf.nome} atualizado e vinculado!', 'success')
                        return redirect(url_for('listar_operadores'))
                
                # Se chegou aqui, pode criar novo operador
                operador = Operador(
                    nome=form.nome.data,
                    warname=form.warname.data,
                    cpf=form.cpf.data,
                    email=form.email.data,
                    telefone=form.telefone.data,
                    data_nascimento=form.data_nascimento.data,
                    idade=form.idade.data,
                    battlepass=form.battlepass.data
                )
                
                db.session.add(operador)
                db.session.commit()
                
                flash('✅ Operador criado com sucesso!', 'success')
                return redirect(url_for('listar_operadores'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'❌ Erro ao salvar: {str(e)}', 'danger')
    
    return render_template('operadores/form.html', form=form, titulo='Novo Operador')

@app.route('/operadores/<int:id>')
@login_required
@requer_permissao('operadores')
def ver_operador(id):
    """Visualiza detalhes do operador"""
    operador = Operador.query.get_or_404(id)
    return render_template('operadores/ver.html', operador=operador)

@app.route('/operadores/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('operadores')
def editar_operador(id):
    """Edita operador"""
    operador = Operador.query.get_or_404(id)
    form = OperadorForm(obj=operador)
    
    # Passar o ID para o formulário
    form.id = id
    
    if request.method == 'POST':
        print("\n" + "="*50)
        print("🔍 EDITANDO OPERADOR")
        print(f"ID: {id}")
        print(f"Form data: {dict(request.form)}")
        print("="*50)
        
        if form.validate_on_submit():
            try:
                # Atualizar operador
                form.populate_obj(operador)
                db.session.commit()
                
                flash('✅ Operador atualizado com sucesso!', 'success')
                return redirect(url_for('listar_operadores'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'❌ Erro ao atualizar: {str(e)}', 'danger')
        else:
            print(f"❌ Erros de validação: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')
    
    return render_template('operadores/form.html', form=form, titulo='Editar Operador')

@app.route('/operadores/<int:id>/deletar', methods=['POST'])
@login_required
@requer_permissao('operadores')
def deletar_operador(id):
    """Deleta operador e seu usuário associado"""
    try:
        operador = Operador.query.get_or_404(id)
        
        # Buscar usuário associado (pelo warname ou pelo operador_id)
        usuario = User.query.filter(
            (User.username == operador.warname) | 
            (User.operador_id == operador.id)
        ).first()
        
        # Nome para mensagem
        nome_operador = operador.nome
        warname = operador.warname
        
        print("\n" + "="*50)
        print("🔍 DELETANDO OPERADOR")
        print(f"Operador: {nome_operador} (ID: {id})")
        print(f"Warname: {warname}")
        print(f"Usuário encontrado: {usuario.username if usuario else 'Nenhum'}")
        print("="*50)
        
        # ===== REMOVER DE EQUIPES =====
        if operador.membro_equipes:
            for equipe in operador.membro_equipes:
                equipe.membros.remove(operador)
                print(f"  ✅ Removido da equipe: {equipe.nome}")
        
        # ===== REMOVER DE PARTIDAS =====
        from backend.models import PartidaParticipante
        partidas = PartidaParticipante.query.filter_by(operador_id=id).all()
        for part in partidas:
            db.session.delete(part)
            print(f"  ✅ Removido da partida ID: {part.partida_id}")
        
        # ===== DELETAR USUÁRIO ASSOCIADO (SE EXISTIR) =====
        if usuario:
            db.session.delete(usuario)
            print(f"  ✅ Usuário {usuario.username} deletado")
            mensagem_usuario = f" e usuário {usuario.username}"
        else:
            mensagem_usuario = ""
        
        # ===== DELETAR OPERADOR =====
        db.session.delete(operador)
        
        # ===== COMMIT FINAL =====
        db.session.commit()
        
        # ===== REGISTRAR LOG =====
        log = Log(
            usuario=current_user.username,
            acao='OPERADOR_DELETADO',
            detalhes=f"Operador: {nome_operador} (ID: {id}){mensagem_usuario}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'✅ Operador {nome_operador}{mensagem_usuario} deletado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'❌ Erro ao deletar operador: {str(e)}')
        flash(f'❌ Erro ao deletar operador: {str(e)}', 'danger')
    
    return redirect(url_for('listar_operadores'))
    
# ==================== ROTAS DE EQUIPES ====================
@app.route('/equipes')
@login_required
@requer_permissao('equipes')
@operador_session_required
def listar_equipes():
    """Lista todas as equipes"""
    search = request.args.get('search', '')
    
    if search:
        equipes = Equipe.query.filter(Equipe.nome.ilike(f'%{search}%')).all()
    else:
        equipes = Equipe.query.all()
    
    operadores = Operador.query.all()
    return render_template('equipes/listar.html', equipes=equipes, operadores=operadores, search=search)

@app.route('/equipes/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('equipes')
def nova_equipe():
    """Cria nova equipe"""
    form = EquipeForm()
    
    # Carregar operadores para o select
    operadores = Operador.query.all()
    form.capitao_id.choices = [(0, '-- Sem capitão --')] + [(op.id, f"{op.warname} ({op.nome})") for op in operadores]
    
    if request.method == 'POST':
        print("="*50)
        print("🔍 TENTANDO CRIAR EQUIPE")
        print(f"Nome: {request.form.get('nome')}")
        print(f"Battlepass: {request.form.get('battlepass')}")
        print(f"Capitão: {request.form.get('capitao_id')}")
        print(f"Arquivos: {request.files}")
        
        # Pegar dados do formulário
        nome = request.form.get('nome')
        battlepass = request.form.get('battlepass', 'NAO')
        capitao_id = request.form.get('capitao_id')
        if capitao_id == '0':
            capitao_id = None
        
        # Processar foto (ATUALIZADO PARA SEGURANÇA)
        foto_filename = None
        if 'foto' in request.files:
            file = request.files['foto']
            
            if file and file.filename != '':
                # Validar arquivo (NOVO)
                is_valid, msg = allowed_file_secure(
                    filename=file.filename,
                    max_size=app.config['MAX_CONTENT_LENGTH'],
                    file_obj=file
                )
                
                if is_valid:
                    # Gerar nome seguro com timestamp (NOVO)
                    foto_filename = safe_filename_with_timestamp(file.filename)
                    
                    # Salvar arquivo
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))
                    print(f"✅ Foto salva como: {foto_filename}")
                else:
                    # Log de tentativa de upload malicioso
                    logger.warning(f"Upload rejeitado para equipe: {msg} - IP: {request.remote_addr}")
                    flash(f"❌ Arquivo rejeitado: {msg}", 'danger')
        
        # Criar equipe
        equipe = Equipe(
            nome=nome,
            foto=foto_filename,
            battlepass=battlepass,
            capitao_id=capitao_id
        )
        
        db.session.add(equipe)
        db.session.commit()
        print(f"✅ Equipe criada: {nome}")
        print("="*50)
        
        flash('Equipe criada com sucesso!', 'success')
        return redirect(url_for('listar_equipes'))
    
    return render_template('equipes/form.html', form=form, titulo='Nova Equipe')


@app.route('/equipes/<int:id>')
@login_required
@requer_permissao('equipes')
def ver_equipe(id):
    """Visualiza detalhes da equipe"""
    equipe = Equipe.query.get_or_404(id)
    operadores = Operador.query.all()
    return render_template('equipes/ver.html', equipe=equipe, operadores=operadores)

@app.route('/equipes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('equipes')
def editar_equipe(id):
    """Edita equipe"""
    equipe = Equipe.query.get_or_404(id)
    form = EquipeForm(obj=equipe)
    
    # Carregar operadores para o select
    operadores = Operador.query.all()
    form.capitao_id.choices = [(0, '-- Sem capitão --')] + [(op.id, f"{op.warname} ({op.nome})") for op in operadores]
    
    if form.validate_on_submit():
        equipe.nome = form.nome.data
        equipe.battlepass = form.battlepass.data
        equipe.capitao_id = form.capitao_id.data if form.capitao_id.data != 0 else None
        
        # Processar nova foto SOMENTE se enviada (ATUALIZADO)
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                # Validar arquivo (NOVO)
                is_valid, msg = allowed_file_secure(
                    filename=file.filename,
                    max_size=app.config['MAX_CONTENT_LENGTH'],
                    file_obj=file
                )
                
                if is_valid:
                    # Gerar nome seguro (NOVO)
                    foto_filename = safe_filename_with_timestamp(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))
                    equipe.foto = foto_filename
                else:
                    logger.warning(f"Upload rejeitado para editar equipe: {msg} - IP: {request.remote_addr}")
                    flash(f"❌ Arquivo rejeitado: {msg}", 'danger')
            # Se não enviou foto, mantém a foto existente (não faz nada)
        
        db.session.commit()
        
        flash('Equipe atualizada!', 'success')
        return redirect(url_for('listar_equipes'))
    
    return render_template('equipes/form.html', form=form, titulo='Editar Equipe')

@app.route('/equipes/<int:id>/membros', methods=['POST'])
@login_required
@requer_permissao('equipes')
def gerenciar_membros(id):
    """Adiciona ou remove membros da equipe"""
    equipe = Equipe.query.get_or_404(id)
    
    operador_id = request.form.get('operador_id', type=int)
    acao = request.form.get('acao')
    
    print(f"Ação: {acao}, Operador ID: {operador_id}")  # DEBUG
    
    if acao == 'adicionar':
        if operador_id:
            operador = Operador.query.get(operador_id)
            if operador and operador not in equipe.membros:
                equipe.membros.append(operador)
                db.session.commit()
                flash(f'{operador.warname} adicionado à equipe!', 'success')
                print(f"Adicionado: {operador.warname}")  # DEBUG
    
    elif acao == 'remover':
        if operador_id:
            operador = Operador.query.get(operador_id)
            if operador and operador in equipe.membros:
                # Remove da equipe
                equipe.membros.remove(operador)
                db.session.commit()
                flash(f'{operador.warname} removido da equipe!', 'success')
                print(f"Removido: {operador.warname}")  # DEBUG
    
    return redirect(url_for('ver_equipe', id=id))

@app.route('/equipes/<int:id>/deletar', methods=['POST'])
@login_required
@requer_permissao('equipes')
def deletar_equipe(id):
    """Deleta equipe"""
    equipe = Equipe.query.get_or_404(id)
    
    try:
        # Remover relacionamentos primeiro
        equipe.membros = []  # Remove todos os membros
        db.session.commit()
        
        # Agora deleta a equipe
        db.session.delete(equipe)
        db.session.commit()
        
        flash('Equipe deletada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar equipe: {str(e)}', 'danger')
    
    return redirect(url_for('listar_equipes'))

# ==================== ROTAS DE PARTIDAS ====================
@app.route('/partidas')
@login_required
@requer_permissao('partidas')
@operador_session_required
def listar_partidas():
    """Lista todas as partidas - VERSÃO SEGURA"""
    try:
        print("\n" + "="*50)
        print("🔍 DEBUG - listar_partidas")
        print(f"Usuário: {current_user.username}")
        print(f"Nível: {current_user.nivel}")
        print(f"Autenticado: {current_user.is_authenticated}")
        print("="*50)
        
        # Pegar filtros da URL
        status = request.args.get('status', 'Todos')
        periodo = request.args.get('periodo', 'Todas')
        search = request.args.get('search', '')
        
        print(f"Filtros - status: {status}, periodo: {periodo}, search: {search}")
        
        # Query base - MAIS SEGURA
        query = Partida.query
        
        # Aplicar filtros de forma segura
        if search and search.strip():
            query = query.filter(Partida.nome.ilike(f'%{search}%'))
        
        if status != 'Todos':
            query = query.filter_by(status=status)
        
        # Buscar todas as partidas
        todas_partidas = query.all()
        
        # Ordenar por ID descendente (mais recentes primeiro)
        todas_partidas.sort(key=lambda p: p.id, reverse=True)
        
        print(f"DEBUG: Total de partidas: {len(todas_partidas)}")
        if todas_partidas:
            for i, p in enumerate(todas_partidas[:3]):
                print(f"  {i+1}. ID={p.id} | {p.data} {p.horario} - {p.nome}")
        
        # Aplicar filtro de período MANUALMENTE (evita erros de conversão)
        if periodo != 'Todas':
            hoje = datetime.now()
            amanha = hoje + timedelta(days=1)
            partidas_filtradas = []
            
            for p in todas_partidas:
                try:
                    data_p = datetime.strptime(p.data, '%d/%m/%Y')
                    
                    if periodo == 'Hoje':
                        if p.data == hoje.strftime('%d/%m/%Y'):
                            partidas_filtradas.append(p)
                    
                    elif periodo == 'Amanha':
                        if p.data == amanha.strftime('%d/%m/%Y'):
                            partidas_filtradas.append(p)
                    
                    elif periodo == '7d':
                        # Próximos 7 dias (futuro)
                        dias_diff = (data_p - hoje).days
                        if 1 <= dias_diff <= 7:
                            partidas_filtradas.append(p)
                    
                    elif periodo == '30d':
                        # Últimos 30 dias (passado)
                        dias_diff = (hoje - data_p).days
                        if 0 <= dias_diff <= 30:
                            partidas_filtradas.append(p)
                    
                    else:  # 'Todas'
                        partidas_filtradas.append(p)
                        
                except Exception as e:
                    print(f"Erro ao processar data {p.data}: {e}")
                    # Se der erro na data, inclui mesmo assim
                    if periodo == 'Todas':
                        partidas_filtradas.append(p)
            
            partidas = partidas_filtradas
        else:
            partidas = todas_partidas
        
        print(f"✅ Total de partidas encontradas: {len(partidas)}")
        
        # Renderizar template com as partidas
        return render_template('partidas/listar.html', partidas=partidas, status=status, periodo=periodo, search=search)
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO em listar_partidas: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Em vez de dar erro, mostra uma mensagem amigável
        flash(f'Erro ao carregar partidas: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

# ==================== ROTAS DE BACKUP ====================

# ==================== ROTAS DE BACKUP ====================

@app.route('/admin/backups')
@login_required
@admin_required
def admin_backups():
    """Lista todos os backups"""
    backups = cloud_manager.listar_backups()
    return render_template('admin/backups.html', backups=backups)


@app.route('/admin/backup/criar', methods=['POST'])
@login_required
@admin_required
def admin_backup_criar():  # Nome ÚNICO
    """Cria um novo backup automático"""
    sucesso, mensagem = cloud_manager.criar_backup_local()
    if sucesso:
        flash(f'[OK] {mensagem}', 'success')
    else:
        flash(f'Erro: {mensagem}', 'danger')
    return redirect(url_for('admin_backups'))

@app.route('/admin/backup/criar-manual', methods=['POST'])
@login_required
@admin_required
def admin_backup_criar_manual():
    """Cria um novo backup com nome personalizado"""
    nome_personalizado = request.form.get('nome_backup', '').strip()
    
    if not nome_personalizado:
        flash('Nome do backup é obrigatório!', 'danger')
        return redirect(url_for('admin_backups'))
    
    sucesso, mensagem = cloud_manager.criar_backup_manual(nome_personalizado)
    if sucesso:
        flash(f'[OK] {mensagem}', 'success')
    else:
        flash(f'Erro: {mensagem}', 'danger')
    return redirect(url_for('admin_backups'))


@app.route('/admin/backup/restaurar/<nome>', methods=['POST'])
@login_required
@admin_required
def admin_backup_restaurar(nome):  # Nome ÚNICO
    """Restaura um backup específico"""
    sucesso, mensagem = cloud_manager.restaurar_backup(nome)
    
    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')
    
    return redirect(url_for('admin_backups'))


@app.route('/admin/backup/deletar/<nome>', methods=['POST'])
@login_required
@admin_required
def admin_backup_deletar(nome):  # Nome ÚNICO
    """Deleta um backup específico"""
    sucesso, mensagem = cloud_manager.deletar_backup(nome)
    
    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')
    
    return redirect(url_for('admin_backups'))


@app.route('/admin/sincronizar', methods=['POST'])
@login_required
@admin_required
def admin_sincronizar():  # Nome ÚNICO
    """Força sincronização com a nuvem"""
    cloud_manager.sincronizar_todos()
    flash('Sincronização concluída!', 'success')
    return redirect(url_for('admin_backups'))

@app.route('/admin/backup/restaurar/<nome>', methods=['POST'])
@login_required
@admin_required
def restaurar_backup(nome):
    """Restaura um backup"""
    sucesso, msg = cloud_manager.restaurar_backup(nome)
    if sucesso:
        flash(msg, 'success')
    else:
        flash(f'Erro: {msg}', 'danger')
    return redirect(url_for('admin_backups'))

@app.route('/api/equipe/<int:id>/membros')
@login_required
def api_equipe_membros(id):
    """Retorna os membros de uma equipe"""
    equipe = Equipe.query.get_or_404(id)
    membros = []
    for m in equipe.membros.all():
        membros.append({
            'id': m.id,
            'nome': m.nome,
            'warname': m.warname
        })
    return jsonify({
        'id': equipe.id,
        'nome': equipe.nome,
        'membros': membros,
        'total': len(membros)
    })

@app.route('/partidas/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('partidas')
def nova_partida():
    """
    Cria nova partida com validações completas e transação atômica
    Versão otimizada - 2024
    Inclui validação de pagamento de operadores
    """
    from datetime import datetime
    
    # ===== VARIÁVEIS DO TEMPLATE =====
    titulo = 'Nova Partida'
    now = datetime.now()
    
    # ===== INÍCIO - LOG E DEBUG =====
    app.logger.info(f"📝 Usuário {current_user.username} acessando nova partida")
    
    # Carregar dados para o template
    operadores = Operador.query.order_by(Operador.nome).all()
    equipes = Equipe.query.all()
    
    # Validação inicial
    if not operadores:
        flash('⚠️ Cadastre pelo menos um operador antes de criar uma partida!', 'warning')
        return redirect(url_for('listar_operadores'))
    
    form = PartidaForm()
    
    # ===== PROCESSAMENTO POST =====
    if request.method == 'POST':
        try:
            # DEBUG - mostrar dados recebidos (remover em produção)
            app.logger.debug(f"Dados recebidos: {dict(request.form)}")
            
            # ===== VALIDAÇÕES BÁSICAS =====
            nome = request.form.get('nome', '').strip()
            if not nome or len(nome) < 3:
                flash('❌ Nome da partida deve ter pelo menos 3 caracteres!', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            # Validar data
            data = request.form.get('data', '')
            # Formato esperado: DD/MM/YYYY (10 caracteres)
            if not data:
                flash('❌ Data é obrigatória!', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            # Validar horário
            horario = request.form.get('horario', '')
            if not horario:
                flash('❌ Horário é obrigatório!', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            if ':' not in horario:
                flash('❌ Horário deve estar no formato HH:MM!', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            campo = request.form.get('campo', '')
            if campo not in ['Warfield', 'Redline']:
                flash('❌ Campo inválido!', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            tipo_participacao = request.form.get('tipo_participacao', 'individual')
            
            # Ler plano, tempo, modo based on modo
            if tipo_participacao == 'equipe':
                plano = request.form.get('plano_equipe', '')
                tempo = request.form.get('tempo_equipe', '')
                modo = request.form.get('modo_equipe', '')
                pagamento = request.form.get('pagamento_equipe', 'Pendente')
            else:
                plano = request.form.get('plano', '')
                tempo = request.form.get('tempo', '')
                modo = request.form.get('modo', '')
                pagamento = request.form.get('pagamento', 'Pendente')
            
            # ===== VALIDAÇÃO ESPECIAL PARA CAÇADA NOTURNA =====
            # CAÇADA NOTURNA é indicada pelo preenchimento de cacada_tipo
            cacada_tipo = request.form.get('cacada_tipo', '')
            is_cacada_noturna = bool(cacada_tipo)  # Se cacada_tipo for preenchido, é CAÇADA NOTURNA
            
            if is_cacada_noturna:
                if cacada_tipo not in ['3', '30']:
                    flash('❌ Selecione o tipo de Caçada Noturna (R$3 ou R$30)!', 'danger')
                    return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
                
                bbs_por_pessoa = 0  # Sem custo de BBS na caçada
                tempo = '10 min'  # Sempre 10 minutos na caçada
                modo = 'CAÇADA NOTURNA'  # Modo padrão para caçada
            else:
                # Buscar valores do plano
                valor_total, bbs_por_pessoa = get_valores_plano(campo, plano, tempo)
                if valor_total <= 0:
                    flash('❌ Valores de plano inválidos!', 'danger')
                    return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            # ===== VALIDAÇÃO DE EQUIPES (MODO EQUIPE) - ANTES DE PROCESSAR PARTICIPANTES =====
            equipe1 = None
            equipe2 = None
            
            if tipo_participacao == 'equipe':
                equipe1_id = request.form.get('equipe1_id')
                equipe2_id = request.form.get('equipe2_id')
                
                if not equipe1_id or not equipe2_id:
                    flash('❌ Selecione as duas equipes!', 'danger')
                    return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
                
                if equipe1_id == equipe2_id:
                    flash('❌ As equipes devem ser diferentes!', 'danger')
                    return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
                
                equipe1 = db.session.get(Equipe, int(equipe1_id))
                equipe2 = db.session.get(Equipe, int(equipe2_id))
                
                if not equipe1 or not equipe2:
                    flash('❌ Equipes não encontradas!', 'danger')
                    return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            # ===== PROCESSAR PARTICIPANTES =====
            # Para modo equipe, ler separadamente por equipe
            # Para modo individual, ler do campo único
            if tipo_participacao == 'equipe':
                # Ler participantes de cada equipe (vêm como strings separadas por vírgula)
                participantes_eq1_str = request.form.get('participantes-eq1', '')
                participantes_eq2_str = request.form.get('participantes-eq2', '')
                
                # Dividir e converter para lista
                participantes_eq1_ids = [id.strip() for id in participantes_eq1_str.split(',') if id.strip()]
                participantes_eq2_ids = [id.strip() for id in participantes_eq2_str.split(',') if id.strip()]
                
                # Combinar para contagem total
                participantes_ids = participantes_eq1_ids + participantes_eq2_ids
                
                # Mapa de equipe para cada participante - USAR OS NOMES REAIS DAS EQUIPES SELECIONADAS
                map_participante_equipe = {
                    **{id: equipe1.nome for id in participantes_eq1_ids},
                    **{id: equipe2.nome for id in participantes_eq2_ids}
                }
                
                print(f"DEBUG: Equipe 1: {equipe1.nome} (ID: {equipe1_id}), Equipe 2: {equipe2.nome} (ID: {equipe2_id})")
                print(f"DEBUG: Mapa de participantes: {map_participante_equipe}")
            else:
                # Modo individual - ler do campo único (também vem como string com vírgulas)
                participantes_str = request.form.get('participantes', '')
                participantes_ids = [id.strip() for id in participantes_str.split(',') if id.strip()]
                map_participante_equipe = {}  # Não há equipe em modo individual
            
            if not participantes_ids:
                flash('❌ Selecione pelo menos um participante!', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            print(f"DEBUG nova_partida: Tipo {tipo_participacao}, Participantes: {participantes_ids}")
            print(f"DEBUG nova_partida: Mapa de equipes: {map_participante_equipe}")
            
            # Validar participantes duplicados
            if len(participantes_ids) != len(set(participantes_ids)):
                flash('❌ Participantes duplicados não são permitidos!', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            num_participantes = len(participantes_ids)
            
            # ===== CALCULAR VALORES =====
            if is_cacada_noturna:
                # CAÇADA NOTURNA - mantém lógica especial
                if cacada_tipo == '3':
                    # Caçada individual - cada um paga R$3
                    valor_por_participante = 3.0
                    valor_total = 3.0 * num_participantes
                elif cacada_tipo == '30':
                    # Caçada em grupo - R$30 dividido
                    valor_por_participante = 30.0 / num_participantes
                    valor_total = 30.0
            else:
                # LÓGICA GERAL (não é CAÇADA NOTURNA)
                if valor_total < 80:
                    # Valor < R$ 80: cada operador paga o valor total (taxa de entrada)
                    valor_por_participante = valor_total
                else:
                    # Valor >= R$ 80: divide entre os operadores
                    valor_por_participante = valor_total / num_participantes if num_participantes > 0 else valor_total
            
            total_bbs = bbs_por_pessoa * num_participantes
            
            # DEBUG - mostrar cálculo de valores
            print(f"\n💰 DEBUG - Cálculo de Valores:")
            print(f"  Partida: {nome}")
            print(f"  Valor Total: R$ {valor_total:.2f}")
            print(f"  Operadores: {num_participantes}")
            print(f"  Valor por Participante: R$ {valor_por_participante:.2f}")
            print(f"  Total de Vendas: {num_participantes} x R$ {valor_por_participante:.2f} = R$ {valor_por_participante * num_participantes:.2f}")
            
            if is_cacada_noturna:
                print(f"  👉 MODO: CAÇADA NOTURNA (R$ {cacada_tipo})")
            else:
                print(f"  👉 MODO: REGULAR - {'Taxa de entrada' if valor_total < 80 else 'Dividido por cabeça'}")
            print()
            
            # ===== VERIFICAR ESTOQUE DE BBS =====
            item_bbs = Estoque.query.filter(Estoque.nome.ilike('%BBs%')).first()
            if not item_bbs:
                flash('⚠️ Item "BBs" não encontrado no estoque! Cadastre primeiro.', 'warning')
            elif item_bbs.quantidade < total_bbs:
                flash(f'❌ Estoque insuficiente de BBs! Disponível: {item_bbs.quantidade} unidades', 'danger')
                return render_template('partidas/form.html', form=form, operadores=operadores, equipes=equipes, titulo=titulo, now=now)
            
            # ===== PAGAMENTO =====
            pagamento = request.form.get('pagamento', 'Pendente')
            
            # ===== INÍCIO DA TRANSAÇÃO =====
            try:
                # 1. CRIAR PARTIDA
                partida = Partida(
                    nome=nome,
                    data=data,
                    horario=horario,
                    campo=campo,
                    plano=plano,
                    tempo=tempo,
                    modo=modo,
                    tipo_participacao=tipo_participacao,
                    valor_total=valor_total,
                    valor_por_participante=valor_por_participante,
                    bbs_por_pessoa=bbs_por_pessoa,
                    total_bbs=total_bbs,
                    pagamento=pagamento,
                    created_by=current_user.id,
                    status='Agendada',
                    finalizada=False
                )
                
                db.session.add(partida)
                db.session.flush()  # Para obter o ID
                
                # 2. ADICIONAR PARTICIPANTES E CRIAR VENDAS
                participantes_adicionados = 0
                participantes_erro = 0
                
                for pid in participantes_ids:
                    try:
                        operador = db.session.get(Operador, int(pid))
                        if not operador:
                            participantes_erro += 1
                            app.logger.warning(f"Operador ID {pid} não encontrado")
                            continue
                        
                        # Determinar equipe do participante (modo equipe)
                        equipe_participante = None
                        if tipo_participacao == 'equipe':
                            # Usar o mapa preparado anteriormente
                            equipe_participante = map_participante_equipe.get(pid)
                        
                        # Adicionar participante
                        participante = PartidaParticipante(
                            partida_id=partida.id,
                            operador_id=operador.id,
                            warname=operador.warname,
                            nome_operador=operador.nome,
                            equipe=equipe_participante
                        )
                        db.session.add(participante)
                        
                        # Criar venda
                        venda = Venda(
                            partida_id=partida.id,
                            warname=operador.warname,
                            nome_operador=operador.nome,
                            nome_partida=partida.nome,
                            produto=f"{campo} - {plano}",
                            cliente=operador.nome,  # Mantém para compatibilidade, mas o nome é do operador
                            descricao=f"Partida: {nome} - {data} - {tempo}",
                            valor=round(valor_por_participante, 2),
                            status='Pendente',
                            tipo='Partida',
                            data=data,
                            pagamento=pagamento if pagamento != 'Pendente' else 'A definir',
                            bbs=bbs_por_pessoa
                        )
                        db.session.add(venda)
                        participantes_adicionados += 1
                        
                    except Exception as e:
                        participantes_erro += 1
                        app.logger.error(f'❌ Erro ao processar participante {pid}: {str(e)}')
                        continue
                
                # 3. ATUALIZAR ESTOQUE DE BBS (se aplicável)
                if bbs_por_pessoa > 0 and total_bbs > 0:
                    item_bbs = Estoque.query.filter(Estoque.nome.ilike('%BBs%')).first()
                    if item_bbs and item_bbs.quantidade >= total_bbs:
                        item_bbs.quantidade -= total_bbs
                        
                        # Criar venda de saída do estoque
                        venda_estoque = Venda(
                            produto="BBs",
                            quantidade=total_bbs,
                            unidade="un",
                            valor=-float(bbs_por_pessoa * 0.5),  # Custo aproximado
                            tipo="Estoque",
                            pagamento="Sistema",
                            data=data,
                            cliente="Sistema",
                            descricao=f"Consumo de BBs - Partida {partida.nome}",
                            status="Pago"
                        )
                        db.session.add(venda_estoque)
                
                # 4. REGISTRAR LOG
                log = Log(
                    usuario=current_user.username,
                    acao='PARTIDA_CRIADA',
                    detalhes=f"Partida: {nome} - Data: {data} - Participantes: {participantes_adicionados}"
                )
                db.session.add(log)
                
                # 5. COMMIT FINAL
                db.session.commit()
                
                # ===== SUCESSO =====
                if participantes_erro > 0:
                    flash(f'⚠️ Partida criada com {participantes_adicionados} participantes. {participantes_erro} participantes ignorados.', 'warning')
                else:
                    flash(f'✅ Partida criada com {participantes_adicionados} participantes!', 'success')
                    
                # Notificar APENAS não-operadores sobre nova partida
                if current_user.nivel != 'operador':
                    # Notificação será visível para gerentes e admins 
                    pass
                
                app.logger.info(f"✅ Partida {partida.id} criada por {current_user.username}")
                return redirect(url_for('listar_partidas'))
                
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'❌ Erro crítico ao criar partida: {str(e)}')
                flash(f'❌ Erro ao criar partida: {str(e)}', 'danger')
                return render_template('partidas/form.html', 
                                     form=form, 
                                     operadores=operadores, 
                                     equipes=equipes,
                                     titulo=titulo,
                                     now=now)
        
        except Exception as e:
            app.logger.error(f'❌ Erro no processamento: {str(e)}')
            flash(f'❌ Erro no processamento: {str(e)}', 'danger')
            return render_template('partidas/form.html', 
                                 form=form, 
                                 operadores=operadores, 
                                 equipes=equipes,
                                 titulo=titulo,
                                 now=now)
    
    # ===== GET - mostrar formulário =====
    return render_template('partidas/form.html', 
                         form=form, 
                         operadores=operadores, 
                         equipes=equipes,
                         titulo=titulo,
                         now=now)

@app.route('/estatisticas/equipe/<int:id>')
@login_required
@requer_permissao('estatisticas')
def ver_estatisticas_equipe(id):
    """Visualiza estatísticas detalhadas de uma equipe com filtros"""
    
    equipe = Equipe.query.get_or_404(id)
    
    # Pegar filtros
    search = request.args.get('search', '')
    resultado_filtro = request.args.get('resultado', 'todos')
    periodo = request.args.get('periodo', 'todas')
    
    # Buscar partidas em modo equipe
    partidas_equipe = Partida.query.filter_by(
        tipo_participacao='equipe',
        finalizada=True
    ).order_by(Partida.data.desc(), Partida.horario.desc()).all()
    
    partidas = []
    total_vitorias = 0
    total_derrotas = 0
    total_empates = 0
    total_kills = 0
    total_deaths = 0
    hoje = datetime.now()
    
    for partida in partidas_equipe:
        # Verificar se a equipe participou (case-insensitive comparison)
        participantes_equipe = [p for p in partida.participantes if p.equipe and p.equipe.lower() == equipe.nome.lower()]
        
        if participantes_equipe:
            # Calcular kills da equipe
            kills_time = sum(p.kills or 0 for p in participantes_equipe)
            deaths_time = sum(p.deaths or 0 for p in participantes_equipe)
            
            # Determinar resultado (case-insensitive comparison)
            equipe_vencedora_lower = partida.equipe_vencedora.lower() if partida.equipe_vencedora else None
            equipe_nome_lower = equipe.nome.lower()
            
            if equipe_vencedora_lower == equipe_nome_lower:
                resultado = 'vitoria'
                total_vitorias += 1
            elif partida.equipe_vencedora and equipe_vencedora_lower != equipe_nome_lower:
                resultado = 'derrota'
                total_derrotas += 1
            else:
                resultado = 'empate'
                total_empates += 1
            
            total_kills += kills_time
            total_deaths += deaths_time
            
            # Aplicar filtros
            incluir = True
            
            # Filtro de busca
            if search and search.lower() not in partida.nome.lower():
                incluir = False
            
            # Filtro de resultado
            if resultado_filtro != 'todos' and resultado != resultado_filtro:
                incluir = False
            
            # Filtro de período
            if periodo != 'todas':
                try:
                    data_p = datetime.strptime(partida.data, '%d/%m/%Y')
                    if periodo == 'hoje' and partida.data != hoje.strftime('%d/%m/%Y'):
                        incluir = False
                    elif periodo == 'semana' and (hoje - data_p).days > 7:
                        incluir = False
                    elif periodo == 'mes' and (hoje - data_p).days > 30:
                        incluir = False
                except:
                    pass
            
            if incluir:
                partidas.append({
                    'id': partida.id,
                    'nome': partida.nome,
                    'data': partida.data,
                    'horario': partida.horario,
                    'campo': partida.campo,
                    'modo': partida.modo,
                    'resultado': resultado,
                    'kills_time': kills_time,
                    'deaths_time': deaths_time,
                    'participantes': participantes_equipe,
                    'equipe_vencedora': partida.equipe_vencedora
                })
    
    # Membros da equipe
    membros = equipe.membros.all()
    total_partidas = total_vitorias + total_derrotas + total_empates
    
    return render_template('estatisticas/equipe.html',
                         equipe=equipe,
                         membros=membros,
                         partidas=partidas,
                         total_partidas=total_partidas,
                         vitorias=total_vitorias,
                         derrotas=total_derrotas,
                         empates=total_empates,
                         total_kills=total_kills,
                         total_deaths=total_deaths,
                         search=search,
                         resultado_filtro=resultado_filtro,
                         periodo=periodo)

@app.route('/partidas/<int:id>')
@login_required
@requer_permissao('partidas')
@operador_session_required
def ver_partida(id):
    """Visualiza detalhes da partida com dados processados"""
    partida = Partida.query.get_or_404(id)
    
    # RESTRIÇÃO: Se for OPERADOR, não pode fazer ações
    é_operador = current_user.nivel == 'operador'
    
    # Processar dados da partida
    dados_partida = {
        'id': partida.id,
        'nome': partida.nome,
        'data': partida.data,
        'horario': partida.horario,
        'campo': partida.campo,
        'plano': partida.plano,
        'tempo': partida.tempo,
        'modo': partida.modo,
        'tipo_participacao': partida.tipo_participacao,
        'valor_total': partida.valor_total,
        'valor_por_participante': partida.valor_por_participante,
        'bbs_por_pessoa': partida.bbs_por_pessoa,
        'status': 'Finalizada' if partida.finalizada else 'Agendada',
        'finalizada': partida.finalizada,
        'participantes': []
    }
    
    # Processar participantes
    if partida.participantes:
        for p in partida.participantes:
            dados_partida['participantes'].append({
                'id': p.id,
                'operador_id': p.operador_id,
                'nome_operador': p.nome_operador,
                'warname': p.warname,
                'equipe': p.equipe,
                'kills': p.kills or 0,
                'deaths': p.deaths or 0,
                'kd': (p.kills or 0) / (p.deaths or 1) if p.deaths else (p.kills or 0),
                'mvp': p.mvp or False,
                'resultado': p.resultado or '-'
            })
    
    # Estatísticas por equipe (se modo equipe) - DINÂMICO para ANY equipe
    stats_equipe = {}
    if partida.tipo_participacao == 'equipe' and partida.participantes:
        for p in partida.participantes:
            if p.equipe:
                # Usar a equipe com case original
                equipe_key = p.equipe  # Manter case original para dict
                if equipe_key not in stats_equipe:
                    stats_equipe[equipe_key] = {
                        'nome': equipe_key,
                        'kills': 0,
                        'deaths': 0,
                        'participantes': 0,
                        'mvps': 0
                    }
                stats_equipe[equipe_key]['kills'] += p.kills or 0
                stats_equipe[equipe_key]['deaths'] += p.deaths or 0
                stats_equipe[equipe_key]['participantes'] += 1
                if p.mvp:
                    stats_equipe[equipe_key]['mvps'] += 1
    
    # Se partida tem equipe_vencedora gravada, usar ela
    equipe_vencedora = partida.equipe_vencedora if partida.equipe_vencedora else None
    
    # Buscar vendas associadas (OPERADOR NÃO VÊ)
    vendas = Venda.query.filter_by(partida_id=partida.id).all() if not é_operador else []
    
    return render_template('partidas/ver.html',
                         partida=partida,
                         dados_partida=dados_partida,
                         stats_equipe=stats_equipe,
                         equipe_vencedora=equipe_vencedora,
                         vendas=vendas,
                         é_operador=é_operador)



@app.route('/partidas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('partidas')
def editar_partida(id):
    """Edita uma partida com validações de permissão"""
    from datetime import datetime
    
    partida = Partida.query.get_or_404(id)
    
    # ===== VALIDAÇÃO DE PERMISSÃO =====
    é_operador = current_user.nivel == 'operador'
    é_staff = current_user.nivel in ['admin', 'gerente']
    
    if é_operador:
        # Operador só pode editar até 10 minutos antes da partida
        try:
            data_hora_str = f"{partida.data} {partida.horario}"
            data_hora = datetime.strptime(data_hora_str, '%d/%m/%Y %H:%M')
            tempo_falta = (data_hora - datetime.now()).total_seconds() / 60  # em minutos
            
            if tempo_falta <= 10:
                flash('❌ Operadores só podem editar partidas até 10 minutos antes da data/hora!', 'danger')
                return redirect(url_for('ver_partida', id=id))
        except Exception as e:
            app.logger.error(f'Erro ao calcular tempo: {str(e)}')
            flash('❌ Erro ao validar horário da partida', 'danger')
            return redirect(url_for('ver_partida', id=id))
    
    # ===== PROCESSAMENTO GET - Mostrar formulário =====
    if request.method == 'GET':
        return render_template('partidas/editar.html',
                             partida=partida,
                             é_staff=é_staff)
    
    # ===== PROCESSAMENTO POST - Salvar alterações =====
    try:
        # Atualizar campos permitidos
        partida.nome = request.form.get('nome', '').strip() or partida.nome
        partida.data = request.form.get('data', '') or partida.data
        partida.horario = request.form.get('horario', '') or partida.horario
        partida.modo = request.form.get('modo', '') or partida.modo
        partida.pagamento = request.form.get('pagamento', 'Pendente')
        
        # Log da edição
        log = Log(
            usuario=current_user.username,
            acao='PARTIDA_EDITADA',
            detalhes=f"Partida: {partida.nome} - ID: {partida.id}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash('✅ Partida atualizada com sucesso!', 'success')
        return redirect(url_for('ver_partida', id=id))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'❌ Erro ao editar partida: {str(e)}')
        flash(f'❌ Erro ao editar partida: {str(e)}', 'danger')
        return render_template('partidas/editar.html',
                             partida=partida,
                             é_staff=é_staff)



@app.route('/partidas/<int:id>/deletar', methods=['POST'])
@login_required
@requer_permissao('partidas')
def deletar_partida(id):
    """Deleta uma partida, devolve BBs, remove vendas e remove estatísticas dos operadores"""
    try:
        from backend.utils import remover_estadisticas_partida
        
        partida = Partida.query.get_or_404(id)
        
        # 1. REMOVER ESTATÍSTICAS DOS OPERADORES (SE PARTIDA FINALIZADA)
        if partida.finalizada:
            remover_estadisticas_partida(partida)
            app.logger.info(f"📊 Estatísticas da partida {partida.nome} removidas dos operadores")
        
        # 2. DEVOLVER BBs AO ESTOQUE
        if partida.total_bbs > 0:
            item_bbs = Estoque.query.filter(Estoque.nome.ilike('%BBs%')).first()
            if item_bbs:
                item_bbs.quantidade += partida.total_bbs
                app.logger.info(f"✅ Devolvidos {partida.total_bbs} BBs ao estoque")
        
        # 3. REMOVER TODAS AS VENDAS ASSOCIADAS À PARTIDA
        vendas = Venda.query.filter_by(partida_id=partida.id).all()
        for venda in vendas:
            app.logger.info(f"🗑️ Removendo venda ${venda.valor} - {venda.nome_operador}")
            db.session.delete(venda)
        
        # 4. DELETAR A PARTIDA (cascade remove participantes)
        db.session.delete(partida)
        db.session.commit()
        
        flash(f'✅ Partida deletada! {len(vendas)} venda(s) removida(s) e BBs devolvidos ao estoque.', 'success')
        return redirect(url_for('listar_partidas'))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'❌ Erro ao deletar partida: {str(e)}')
        flash(f'❌ Erro ao deletar partida: {str(e)}', 'danger')
        return redirect(url_for('listar_partidas'))

# ==================== ROTAS DE VENDAS ====================
@app.route('/vendas')
@login_required
@requer_permissao('vendas')
@operador_session_required
def listar_vendas():
    """Lista todas as vendas"""
    status = request.args.get('status', 'Todos')
    periodo = request.args.get('periodo', 'Todas')
    search = request.args.get('search', '')
    
    query = Venda.query
    
    if search:
        query = query.filter(
            (Venda.cliente.ilike(f'%{search}%')) |
            (Venda.produto.ilike(f'%{search}%'))
        )
    
    if status != 'Todos':
        query = query.filter_by(status=status)
    
    vendas = query.order_by(Venda.data.desc(), Venda.id.desc()).all()
    
    # Totais
    total_entradas = sum(v.valor for v in vendas if v.valor > 0)
    total_saidas = abs(sum(v.valor for v in vendas if v.valor < 0))
    saldo = total_entradas - total_saidas
    
    return render_template('vendas/listar.html', 
                         vendas=vendas, 
                         total_entradas=total_entradas,
                         total_saidas=total_saidas,
                         saldo=saldo)

@app.route('/vendas/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('vendas')
def nova_venda():
    """Cria nova venda"""
    form = VendaForm()
    operadores = Operador.query.all()
    
    if form.validate_on_submit():
        venda = Venda(
            produto=form.produto.data,
            quantidade=form.quantidade.data,
            unidade=form.unidade.data,
            valor=form.valor.data,
            tipo=form.tipo.data,
            pagamento=form.pagamento.data,
            data=form.data.data,
            cliente=form.cliente.data,
            descricao=form.descricao.data,
            status='Pago'  # Venda manual já é paga
        )
        
        db.session.add(venda)
        
        # Se for venda de estoque, atualizar quantidade
        if form.tipo.data == 'Estoque' and form.quantidade.data > 0:
            item = Estoque.query.filter_by(nome=form.produto.data).first()
            if item:
                item.quantidade -= form.quantidade.data
        
        db.session.commit()
        
        flash('Venda registrada!', 'success')
        return redirect(url_for('listar_vendas'))
    
    return render_template('vendas/form.html', form=form, operadores=operadores)

@app.route('/vendas/<int:id>/status', methods=['POST'])
@login_required
@requer_permissao('vendas')
def atualizar_status_venda(id):
    """Atualiza status da venda"""
    venda = Venda.query.get_or_404(id)
    novo_status = request.form.get('status')
    
    if novo_status in ['Pendente', 'Pago']:
        venda.status = novo_status
        db.session.commit()
        flash('Status atualizado!', 'success')
    
    return redirect(url_for('listar_vendas'))

@app.route('/vendas/<int:id>/atualizar-valores', methods=['POST'])
@login_required
@requer_permissao('vendas')
def atualizar_valores_venda(id):
    """Atualiza valores unitário e total da venda"""
    venda = Venda.query.get_or_404(id)
    
    try:
        valor_unitario = float(request.form.get('valor_unitario', 0))
        valor_total = float(request.form.get('valor_total', 0))
        
        # Se a venda tem quantidade, calcula o total
        if venda.quantidade > 0:
            venda.valor = valor_total  # Ou valor_unitario * venda.quantidade
        else:
            venda.valor = valor_total
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Valores atualizados'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/vendas/<int:id>/pagamento', methods=['POST'])
@login_required
@requer_permissao('vendas')
def atualizar_pagamento_venda(id):
    """Atualiza forma de pagamento"""
    venda = Venda.query.get_or_404(id)
    novo_pagamento = request.form.get('pagamento')
    
    if novo_pagamento:
        venda.pagamento = novo_pagamento
        db.session.commit()
        flash('Pagamento atualizado!', 'success')
    
    return redirect(url_for('listar_vendas'))

@app.route('/vendas/<int:id>/deletar', methods=['POST'])
@login_required
@requer_permissao('vendas')
def deletar_venda(id):
    """Deleta uma venda"""
    try:
        venda = Venda.query.get_or_404(id)
        
        # Se for venda de estoque, devolver quantidade
        if venda.tipo == 'Estoque' and venda.quantidade > 0:
            item = Estoque.query.filter_by(nome=venda.produto).first()
            if item:
                item.quantidade += venda.quantidade
        
        venda_descricao = f"{venda.produto if venda.produto else 'Sem descrição'} - R${venda.valor}"
        db.session.delete(venda)
        db.session.commit()
        
        # Registrar log
        log = Log(
            usuario=current_user.username,
            acao='VENDA_DELETADA',
            detalhes=f"Venda ID: {id} - {venda_descricao}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Venda deletada!', 'success')
        return redirect(url_for('listar_vendas'))
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao deletar venda: {str(e)}')
        flash(f'Erro ao deletar venda: {str(e)}', 'danger')
        return redirect(url_for('listar_vendas'))

@app.route('/vendas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('vendas')
def editar_venda(id):
    """Edita uma venda existente"""
    venda = Venda.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Atualizar campos da venda
            venda.produto = request.form.get('produto', venda.produto)
            venda.cliente = request.form.get('cliente', venda.cliente)
            venda.descricao = request.form.get('descricao', venda.descricao)
            venda.status = request.form.get('status', venda.status)
            venda.pagamento = request.form.get('pagamento', venda.pagamento)
            venda.tipo = request.form.get('tipo', venda.tipo)
            venda.bbs = int(request.form.get('bbs', venda.bbs or 0))
            venda.quantidade = float(request.form.get('quantidade', venda.quantidade or 0))
            venda.unidade = request.form.get('unidade', venda.unidade or 'un')
            venda.data = request.form.get('data', venda.data)
            
            # APENAS ADMIN PODE EDITAR O VALOR
            if current_user.nivel == 'admin':
                novo_valor = float(request.form.get('valor', venda.valor))
                if novo_valor != venda.valor:
                    log_detalhes = f"Venda ID: {id} - {venda.produto} - Valor anterior: R${venda.valor:.2f} → Novo valor: R${novo_valor:.2f}"
                    venda.valor = novo_valor
                else:
                    log_detalhes = f"Venda ID: {id} - {venda.produto} - Status atualizado"
            else:
                log_detalhes = f"Venda ID: {id} - {venda.produto} - Informações atualizadas"
            
            db.session.commit()
            
            # Registrar log
            log = Log(
                usuario=current_user.username,
                acao='VENDA_EDITADA',
                detalhes=log_detalhes
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Venda atualizada com sucesso!', 'success')
            return redirect(url_for('listar_vendas'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro ao editar venda: {str(e)}')
            flash(f'Erro ao editar venda: {str(e)}', 'danger')
    
    is_admin = current_user.nivel == 'admin'
    return render_template('vendas/editar.html', venda=venda, is_admin=is_admin)

# ==================== ROTAS DE ESTOQUE ====================
@app.route('/estoque')
@login_required
@requer_permissao('estoque')
def listar_estoque():
    """Lista itens do estoque"""
    search = request.args.get('search', '')
    
    if search:
        itens = Estoque.query.filter(Estoque.nome.ilike(f'%{search}%')).all()
    else:
        itens = Estoque.query.all()
    
    return render_template('estoque/listar.html', itens=itens, search=search)

@app.route('/estoque/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('estoque')
def novo_item():
    """Adiciona item ao estoque"""
    form = EstoqueForm()
    
    if form.validate_on_submit():
        try:
            # Validar entrada
            if not form.nome.data or not form.nome.data.strip():
                flash('Nome do item é obrigatório!', 'danger')
                return render_template('estoque/form.html', form=form, titulo='Novo Item')
            
            if form.quantidade.data < 0 or form.custo.data < 0 or form.preco_venda.data < 0:
                flash('Quantidade, custo e preço de venda não podem ser negativos!', 'danger')
                return render_template('estoque/form.html', form=form, titulo='Novo Item')
            
            # Verificar se item já existe
            item_existente = Estoque.query.filter_by(nome=form.nome.data.strip()).first()
            
            if item_existente:
                # Atualizar quantidade e custo médio
                quant_anterior = item_existente.quantidade
                custo_total_anterior = quant_anterior * item_existente.custo
                custo_total_novo = form.quantidade.data * form.custo.data
                quantidade_total = quant_anterior + form.quantidade.data
                
                item_existente.quantidade = quantidade_total
                item_existente.custo = (custo_total_anterior + custo_total_novo) / quantidade_total if quantidade_total > 0 else 0
                item_existente.preco_venda = form.preco_venda.data
                item_existente.quantidade_minima = form.quantidade_minima.data
                item_existente.descricao = form.descricao.data
                
                mensagem = f"Item existente! Quantidade atualizada de {quant_anterior} para {quantidade_total}"
            else:
                # Criar novo item
                item_existente = Estoque(
                    nome=form.nome.data.strip(),
                    quantidade=form.quantidade.data,
                    unidade=form.unidade.data,
                    quantidade_minima=form.quantidade_minima.data,
                    custo=form.custo.data,
                    preco_venda=form.preco_venda.data,
                    descricao=form.descricao.data,
                    data=form.data.data
                )
                db.session.add(item_existente)
                mensagem = "Novo item adicionado!"
            
            db.session.commit()
            
            # Criar venda de saída (custo) - apenas se custo > 0
            if form.custo.data > 0:
                venda = Venda(
                    produto=form.nome.data.strip(),
                    quantidade=form.quantidade.data,
                    unidade=form.unidade.data,
                    valor=-form.custo.data,
                    tipo='Estoque',
                    pagamento='Dinheiro',
                    data=form.data.data,
                    cliente='Sistema',
                    descricao=f"Compra de {form.nome.data.strip()}",
                    status='Pago'
                )
                db.session.add(venda)
                db.session.commit()
            
            flash(mensagem, 'success')
            return redirect(url_for('listar_estoque'))
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro ao adicionar item ao estoque: {str(e)}')
            flash(f'Erro ao adicionar item: {str(e)}', 'danger')
            return render_template('estoque/form.html', form=form, titulo='Novo Item')
    
    return render_template('estoque/form.html', form=form, titulo='Novo Item')

@app.route('/estoque/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('estoque')
def editar_item(id):
    """Edita item do estoque"""
    item = Estoque.query.get_or_404(id)
    form = EstoqueForm(obj=item)
    
    if form.validate_on_submit():
        form.populate_obj(item)
        db.session.commit()
        flash('Item atualizado!', 'success')
        return redirect(url_for('listar_estoque'))
    
    return render_template('estoque/form.html', form=form, titulo='Editar Item')

@app.route('/estoque/<int:id>/deletar', methods=['POST'])
@login_required
@requer_permissao('estoque')
def deletar_item(id):
    """Deleta item do estoque"""
    item = Estoque.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    
    flash('Item deletado!', 'success')
    return redirect(url_for('listar_estoque'))

# ==================== ROTAS DE CALENDÁRIO ====================
@app.route('/calendario')
@login_required
@requer_permissao('calendario')
@operador_session_required
def calendario():
    """Visualização em calendário"""
    import calendar
    import json
    
    # Parâmetros
    mes = request.args.get('mes', type=int, default=datetime.now().month)
    ano = request.args.get('ano', type=int, default=datetime.now().year)
    
    # Validar
    if not (1 <= mes <= 12):
        mes = datetime.now().month
    if ano < 2000 or ano > 2100:
        ano = datetime.now().year
    
    # RESTRIÇÃO: Se for OPERADOR, só mostra as partidas de HOJE
    é_operador = current_user.nivel == 'operador'
    hoje_str = datetime.now().strftime('%d/%m/%Y')
    
    # Buscar partidas do mês
    todas_partidas = Partida.query.all()
    partidas = []
    partidas_por_dia = {}
    
    for p in todas_partidas:
        try:
            data_p = datetime.strptime(p.data, '%d/%m/%Y')
            
            # Se for operador, só mostra partidas de hoje
            if é_operador and p.data != hoje_str:
                continue
            
            if data_p.month == mes and data_p.year == ano:
                partidas.append(p)
                dia = data_p.day
                if dia not in partidas_por_dia:
                    partidas_por_dia[dia] = []
                
                # Adicionar objeto da partida
                partidas_por_dia[dia].append(p)
        except:
            continue
    
    # Gerar calendário
    cal = calendar.monthcalendar(ano, mes)
    
    return render_template('calendario.html',
                         cal=cal,
                         mes=mes,
                         ano=ano,
                         mes_nome=calendar.month_name[mes],
                         partidas_por_dia=partidas_por_dia)

@app.route('/api/partida/<int:id>')
@login_required
def api_partida(id):
    """Retorna dados da partida em JSON"""
    partida = Partida.query.get_or_404(id)
    return jsonify({
        'id': partida.id,
        'nome': partida.nome,
        'data': partida.data,
        'horario': partida.horario,
        'campo': partida.campo,
        'modo': partida.modo,
        'num_participantes': len(partida.participantes),
        'valor_total': partida.valor_total,
        'status': partida.status
    })

# ==================== ROTAS DE SORTEIOS - BATTLEPASS ====================
@app.route('/historico-sorteios')
@login_required
@operador_session_required
def historico_sorteios():
    """Página de histórico de sorteios com navegação de mês"""
    from backend.models import Battlepass, Sorteio, Operador, Equipe
    from datetime import datetime as dt, timedelta
    import calendar
    
    # Parâmetros
    tipo = request.args.get('tipo', 'operador')  # 'operador' ou 'equipe'
    battlepass_id = request.args.get('battlepass_id', type=int)
    mes = request.args.get('mes', type=int, default=dt.now().month)
    ano = request.args.get('ano', type=int, default=dt.now().year)
    
    # Validar
    if not (1 <= mes <= 12):
        mes = dt.now().month
    if ano < 2000 or ano > 2100:
        ano = dt.now().year
    
    # Buscar battlepass
    battlepass = Battlepass.query.get_or_404(battlepass_id)
    
    # Calcular mês anterior e próximo
    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    
    mes_proximo = mes + 1 if mes < 12 else 1
    ano_proximo = ano if mes < 12 else ano + 1
    
    # Nome do mês
    meses_nomes = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nome_mes = meses_nomes[mes]
    
    # Buscar histórico
    if tipo == 'operador':
        # Buscar sorteios semanais para operadores
        sorteios = Sorteio.query.filter_by(
            battlepass_id=battlepass_id,
            mes=mes,
            ano=ano,
            deletado=False
        ).order_by(Sorteio.semana.asc()).all()
        
        historico = []
        for semana_num in range(1, 6):
            sorteio_semana = next((s for s in sorteios if s.semana == semana_num), None)
            historico.append({
                'semana': semana_num,
                'operador': sorteio_semana.operador.nome if sorteio_semana and sorteio_semana.operador else None,
                'operador_warname': sorteio_semana.operador.warname if sorteio_semana and sorteio_semana.operador else None,
                'data': sorteio_semana.sorteado_em.strftime('%d/%m/%Y %H:%M') if sorteio_semana and sorteio_semana.sorteado_em else 'Não sorteado',
                'sorteio_id': sorteio_semana.id if sorteio_semana else None
            })
    else:
        # Buscar sorteios mensais para equipes
        sorteio = Sorteio.query.filter_by(
            battlepass_id=battlepass_id,
            mes=mes,
            ano=ano,
            semana=None,
            deletado=False
        ).first()
        
        historico = [{
            'mes': mes,
            'equipe': sorteio.equipe.nome if sorteio and sorteio.equipe else None,
            'data': sorteio.sorteado_em.strftime('%d/%m/%Y %H:%M') if sorteio and sorteio.sorteado_em else 'Não sorteado',
            'sorteio_id': sorteio.id if sorteio else None
        }]
    
    # Verificar permissão
    é_admin_gerente = current_user.nivel in ['admin', 'gerente']
    
    return render_template('historico_sorteios.html',
                         tipo=tipo,
                         battlepass=battlepass,
                         mes=mes,
                         ano=ano,
                         nome_mes=nome_mes,
                         mes_anterior=mes_anterior,
                         ano_anterior=ano_anterior,
                         mes_proximo=mes_proximo,
                         ano_proximo=ano_proximo,
                         historico=historico,
                         é_admin_gerente=é_admin_gerente,
                         meses_nomes=meses_nomes)


@app.route('/sorteios')
@login_required
@operador_session_required
def sorteios():
    """Página de Sorteios - Battlepass (RENOMEADO PARA EVENTOS)"""
    from backend.models import Battlepass, Sorteio, Evento
    from datetime import datetime as dt, timedelta
    
    # Parâmetros
    semana = request.args.get('semana', type=int, default=None)
    ano = request.args.get('ano', type=int, default=datetime.now().year)
    mes = request.args.get('mes', type=int, default=datetime.now().month)
    
    # Se não especificou semana, calcular semana atual (semana do mês)
    if semana is None:
        hoje = dt.now()
        import math
        semana = math.ceil(hoje.day / 7)  # Semana do mês (1-5)
    
    # Validar
    if not (1 <= semana <= 5):
        hoje = dt.now()
        import math
        semana = math.ceil(hoje.day / 7)
    if ano < 2000 or ano > 2100:
        ano = datetime.now().year
    
    # Function to sort eventos: próximos em primeiro (ASC), depois passados (DESC)
    def sort_eventos_by_proximity(eventos):
        from datetime import datetime
        today = datetime.now()
        
        # Separate into future and past events
        future_events = []
        past_events = []
        
        for e in eventos:
            if e.data_evento:
                # Converter para date se for datetime para comparação
                evento_date = e.data_evento.date() if isinstance(e.data_evento, datetime) else e.data_evento
                today_date = today.date()
                
                if evento_date >= today_date:
                    future_events.append(e)
                else:
                    past_events.append(e)
        
        # Sort each group
        future_events.sort(key=lambda e: e.data_evento)  # Próximos primeiro (ASC)
        past_events.sort(key=lambda e: e.data_evento, reverse=True)  # Mais recentes passados primeiro (DESC)
        
        # Combine: future first, then past
        return future_events + past_events
    
    # Buscar eventos por campo
    eventos_warfield_raw = Evento.query.filter_by(
        campo='Warfield',
        ativo=True,
        deletado=False
    ).all()
    eventos_warfield = sort_eventos_by_proximity(eventos_warfield_raw)
    
    eventos_redline_raw = Evento.query.filter_by(
        campo='Redline',
        ativo=True,
        deletado=False
    ).all()
    eventos_redline = sort_eventos_by_proximity(eventos_redline_raw)
    
    eventos_geral_raw = Evento.query.filter_by(
        campo='GERAL',
        ativo=True,
        deletado=False
    ).all()
    eventos_geral = sort_eventos_by_proximity(eventos_geral_raw)
    
    # Buscar battlepasses
    battlepasses_operador = Battlepass.query.filter(
        Battlepass.categoria == 'operador',
        Battlepass.ativo == True
    ).all()
    
    battlepasses_equipe = Battlepass.query.filter(
        Battlepass.categoria == 'equipe',
        Battlepass.ativo == True
    ).all()
    
    # Preparar dados de sorteios
    sorteios_data = {
        'operador': {
            'semana_atual': {}
        },
        'equipe': {
            'mes': {}
        }
    }
    
    # Preencher sorteios de operadores (SEMANAIS)
    for bp in battlepasses_operador:
        sorteio_semana = Sorteio.query.filter_by(
            battlepass_id=bp.id,
            ano=ano,
            semana=semana,
            deletado=False
        ).first()
        
        sorteios_data['operador']['semana_atual'][bp.id] = sorteio_semana
    
    # Preencher sorteios de equipes (MENSAIS)
    for bp in battlepasses_equipe:
        sorteio_mes = Sorteio.query.filter_by(
            battlepass_id=bp.id,
            mes=mes,  # ← Usar 'mes' do parâmetro, não datetime.now().month
            ano=ano,
            semana=None,
            deletado=False
        ).first()
        
        sorteios_data['equipe']['mes'][bp.id] = sorteio_mes
    
    # Verificar se é admin/gerente
    é_admin_gerente = current_user.nivel in ['admin', 'gerente']
    
    return render_template('eventos.html',
                         semana=semana,
                         mes=mes,
                         ano=ano,
                         eventos_warfield=eventos_warfield,
                         eventos_redline=eventos_redline,
                         eventos_geral=eventos_geral,
                         battlepasses_operador=battlepasses_operador,
                         battlepasses_equipe=battlepasses_equipe,
                         sorteios_data=sorteios_data,
                         é_admin_gerente=é_admin_gerente,
                         current_user=current_user)

# ==================== ROTAS DE ADMIN ====================
@app.route('/admin/usuarios')
@login_required
@admin_required
def admin_usuarios():
    """Gerenciar usuários e solicitações"""
    search = request.args.get('search', '')
    
    # Buscar usuários com filtro
    query = User.query.filter_by(status='aprovado')
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.nome.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    usuarios = query.all()
    solicitacoes = Solicitacao.query.filter_by(status='pendente').all()
    
    return render_template('admin/usuarios.html', 
                         usuarios=usuarios, 
                         solicitacoes=solicitacoes,
                         search=search)


@app.route('/admin/solicitacao/<int:id>/<acao>', methods=['POST'])
@login_required
@admin_required
def aprovar_solicitacao(id, acao):
    """Aprova ou rejeita solicitação"""
    try:
        solicitacao = Solicitacao.query.get_or_404(id)
        
        if acao not in ['aprovar', 'rejeitar']:
            flash('Ação inválida!', 'danger')
            return redirect(url_for('admin_usuarios'))
        
        if acao == 'aprovar':
            # Verificar se usuário já existe
            if User.query.filter_by(username=solicitacao.usuario).first():
                flash(f'Usuário {solicitacao.usuario} já existe!', 'warning')
                solicitacao.status = 'rejeitado'
                db.session.commit()
                return redirect(url_for('admin_usuarios'))
            
            # Criar usuário
            user = User(
                username=solicitacao.usuario,
                nome=solicitacao.nome,
                email=solicitacao.email,
                cpf=solicitacao.cpf,
                data_nascimento=solicitacao.data_nascimento,
                idade=solicitacao.idade,
                nivel=solicitacao.nivel,
                salt=solicitacao.salt,
                password_hash=solicitacao.password_hash,
                status='aprovado',
                approved_at=datetime.utcnow(),
                approved_by=current_user.username
            )
            db.session.add(user)
            db.session.flush()  # Para obter o ID do usuário
            
            # ===== CRIAR OPERADOR AUTOMATICAMENTE =====
            operador = Operador(
                nome=solicitacao.nome,
                warname=solicitacao.usuario,  # Usa o username como warname
                cpf=solicitacao.cpf,
                email=solicitacao.email,
                data_nascimento=solicitacao.data_nascimento,
                idade=str(solicitacao.idade),  # Converte para string
                battlepass='NAO'
            )
            db.session.add(operador)
            
            solicitacao.status = 'aprovado'
            mensagem = f'Solicitação de {solicitacao.nome} aprovada!'
        
        elif acao == 'rejeitar':
            solicitacao.status = 'rejeitado'
            mensagem = f'Solicitação de {solicitacao.nome} rejeitada.'
        
        solicitacao.approved_at = datetime.utcnow()
        solicitacao.approved_by = current_user.username
        db.session.commit()
        
        log = Log(
            usuario=current_user.username,
            acao=f'SOLICITACAO_{acao.upper()}',
            detalhes=f"Solicitação ID: {id} - {solicitacao.nome}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash(mensagem, 'success')
        return redirect(url_for('admin_usuarios'))
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao processar solicitação: {str(e)}')
        flash(f'Erro ao processar solicitação: {str(e)}', 'danger')
        return redirect(url_for('admin_usuarios'))


@app.route('/admin/sincronizar', methods=['POST'])
@login_required
@admin_required
def sincronizar_agora():
    """Força sincronização com a nuvem"""
    cloud_manager.sincronizar_todos()
    flash('Sincronização concluída!', 'success')
    return redirect(url_for('admin_backups'))


# ==================== SINCRONIZAÇÃO DE ESTATÍSTICAS ====================
@app.route('/admin/sincronizar-estatisticas', methods=['GET', 'POST'])
@login_required
@admin_required
def sincronizar_estatisticas_admin():
    """
    Sincroniza as estatísticas dos operadores.
    Remove registros órfãos e recalcula stats de todos os operadores.
    """
    if request.method == 'GET':
        # Mostrar página de confirmação
        return render_template('admin/sincronizar_estatisticas.html')
    
    # POST: executar sincronização
    from backend.utils import sincronizar_estatisticas_operadores
    
    resultado = sincronizar_estatisticas_operadores()
    
    if resultado['sucesso']:
        flash(resultado['mensagem'], 'success')
    else:
        flash(resultado['mensagem'], 'danger')
    
    return redirect(url_for('admin_usuarios'))



@app.route('/meu-perfil')
@login_required
def meu_perfil():
    """Página de perfil do usuário logado"""
    # Buscar o operador associado ao usuário (pelo warname = username)
    operador = Operador.query.filter_by(warname=current_user.username).first()
    
    if operador:
        # Se encontrou, redireciona para o perfil do operador
        return redirect(url_for('perfil_operador', id=operador.id))
    
    # Se não encontrou, criar um operador automaticamente? (opcional)
    # Para admin/gerente, pode não ter operador
    flash('Perfil de operador não encontrado para este usuário.', 'warning')
    return redirect(url_for('dashboard'))


# ==================== ROTA PARA ALTERAR NÍVEL DE USUÁRIO ====================
@app.route('/admin/usuario/<int:id>/alterar-nivel', methods=['POST'])
@login_required
@admin_required
def alterar_nivel_usuario(id):
    """Altera o nível de acesso de um usuário"""
    if current_user.nivel != 'admin':
        return jsonify({'error': 'Apenas admin pode alterar níveis'}), 403
    
    user = User.query.get_or_404(id)
    novo_nivel = request.form.get('nivel')
    
    if novo_nivel in ['admin', 'gerente', 'operador', 'financeiro']:
        user.nivel = novo_nivel
        db.session.commit()
        
        log = Log(
            usuario=current_user.username,
            acao='NIVEL_ALTERADO',
            detalhes=f"Usuário {user.username} agora é {novo_nivel}"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'error': 'Nível inválido'}), 400


# ==================== API ROUTES ====================
@app.route('/setup/test-api')
def test_api():
    """Test if all APIs are working"""
    from backend.utils import PLANOS_WARFIELD, PLANOS_REDLINE
    
    return jsonify({
        'warfield_planos': list(PLANOS_WARFIELD.keys()),
        'redline_planos': list(PLANOS_REDLINE.keys()),
        'warfield_avulso_tempos': PLANOS_WARFIELD.get('Avulso', {}).get('tempos', []),
        'redline_rifle_tempos': PLANOS_REDLINE.get('Rifle', {}).get('tempos', []),
        'status': 'OK'
    })


@app.route('/api/planos/<campo>')
def api_planos(campo):
    if campo == 'Warfield':
        return jsonify(list(PLANOS_WARFIELD.keys()))
    elif campo == 'Redline':
        return jsonify(list(PLANOS_REDLINE.keys()))
    return jsonify([])


@app.route('/api/tempos')
def api_tempos():
    campo = request.args.get('campo')
    plano = request.args.get('plano')
    
    if campo == 'Warfield' and plano in PLANOS_WARFIELD:
        return jsonify(PLANOS_WARFIELD[plano]['tempos'])
    elif campo == 'Redline' and plano in PLANOS_REDLINE:
        return jsonify(PLANOS_REDLINE[plano]['tempos'])
    return jsonify([])


@app.route('/api/valores')
def api_valores():
    campo = request.args.get('campo')
    plano = request.args.get('plano')
    tempo = request.args.get('tempo')
    
    valor, bbs = get_valores_plano(campo, plano, tempo)
    return jsonify({'valor': valor, 'bbs': bbs})


@app.route('/api/modos')
def api_modos():
    tempo = request.args.get('tempo', '')
    plano = request.args.get('plano', '')
    modos = get_modos_permitidos(tempo, plano)
    return jsonify(modos)


# ==================== NOVOS ENDPOINTS DE API ====================

@app.route('/api/operadores/search')
def api_operadores_search():
    """Busca operadores por nome ou warname - para autocomplete"""
    q = request.args.get('q', '').lower()
    limite = int(request.args.get('limit', 10))
    
    if q and len(q) < 2:
        return jsonify([])
    
    query = Operador.query
    
    if q:
        query = query.filter(
            (Operador.nome.ilike(f'%{q}%')) | 
            (Operador.warname.ilike(f'%{q}%'))
        )
    
    operadores = query.limit(limite).all()
    
    return jsonify([{
        'id': op.id,
        'nome': op.nome,
        'warname': op.warname,
        'texto': f"{op.nome} (@{op.warname})"
    } for op in operadores])


@app.route('/api/equipes/<int:equipe_id>/membros/search')
def api_equipe_membros_search(equipe_id):
    """Busca membros de uma equipe específica"""
    q = request.args.get('q', '').lower()
    
    equipe = Equipe.query.get_or_404(equipe_id)
    membros = equipe.membros.all()
    
    if q:
        membros = [m for m in membros if q in m.nome.lower() or q in m.warname.lower()]
    
    return jsonify([{
        'id': m.id,
        'nome': m.nome,
        'warname': m.warname,
        'texto': f"{m.nome} (@{m.warname})"
    } for m in membros])


# ==================== APIS DE SORTEIOS - BATTLEPASS ====================
@app.route('/api/sortear-operador', methods=['POST'])
@login_required
@admin_required
def api_sortear_operador():
    """Sorteia um operador para um battlepass - TOTALMENTE ALEATÓRIO"""
    from backend.models import Battlepass, Sorteio
    import random
    
    data = request.get_json()
    battlepass_id = data.get('battlepass_id')
    semana = data.get('semana')
    mes = data.get('mes')
    ano = data.get('ano')
    
    try:
        # Validar parâmetros
        if not all([battlepass_id, semana, mes, ano]):
            return jsonify({'success': False, 'error': 'Parâmetros incompletos'}), 400
        
        battlepass = Battlepass.query.get_or_404(battlepass_id)
        
        # Mapear tipo de battlepass para o tipo de operador esperado
        tipo_map = {
            'operador_basico': 'OPERADOR',
            'operador_elite': 'ELITE_CAVEIRA'
        }
        
        tipo_operador = tipo_map.get(battlepass.tipo)
        if not tipo_operador:
            return jsonify({'success': False, 'error': 'Tipo de battlepass inválido'}), 400
        
        # Buscar TODOS os operadores com este tipo de battlepass (sem filtros de semana)
        operadores = Operador.query.filter_by(battlepass=tipo_operador).all()
        
        if not operadores:
            return jsonify({
                'success': False, 
                'error': f'Nenhum operador com Battlepass {tipo_operador}'
            }), 400
        
        # SORTEAR ALEATORIAMENTE - completamente aleatório, sem restrições
        operador_sorteado = random.choice(operadores)
        
        # Verificar se já existe sorteio para esta semana/battlepass
        sorteio_existente = Sorteio.query.filter_by(
            battlepass_id=battlepass_id,
            semana=semana,
            mes=mes,
            ano=ano,
            deletado=False
        ).first()
        
        if sorteio_existente:
            # Se já existe, substituir por um novo sorteio
            db.session.delete(sorteio_existente)
        
        # Criar novo registro de sorteio
        sorteio = Sorteio(
            battlepass_id=battlepass_id,
            mes=mes,
            ano=ano,
            semana=semana,
            operador_id=operador_sorteado.id,
            sorteado_por=current_user.id
        )
        
        db.session.add(sorteio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sorteado': {
                'id': operador_sorteado.id,
                'nome': operador_sorteado.nome,
                'warname': operador_sorteado.warname
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sortear-equipe', methods=['POST'])
@login_required
@admin_required
def api_sortear_equipe():
    """Sorteia uma equipe para um battlepass - TOTALMENTE ALEATÓRIO"""
    from backend.models import Battlepass, Sorteio
    import random
    
    data = request.get_json()
    battlepass_id = data.get('battlepass_id')
    mes = data.get('mes')
    ano = data.get('ano')
    
    try:
        # Validar parâmetros
        if not all([battlepass_id, mes, ano]):
            return jsonify({'success': False, 'error': 'Parâmetros incompletos'}), 400
        
        battlepass = Battlepass.query.get_or_404(battlepass_id)
        
        # Mapear tipo de battlepass para o tipo de equipe esperado
        tipo_map = {
            'equipe_basica': 'EQUIPE_BASICA'
        }
        
        tipo_equipe = tipo_map.get(battlepass.tipo)
        if not tipo_equipe:
            return jsonify({'success': False, 'error': 'Tipo de battlepass inválido'}), 400
        
        # Buscar TODAS as equipes com este tipo de battlepass (sem filtros de mês)
        equipes = Equipe.query.filter_by(battlepass=tipo_equipe).all()
        
        if not equipes:
            return jsonify({
                'success': False, 
                'error': f'Nenhuma equipe com Battlepass {tipo_equipe}'
            }), 400
        
        # SORTEAR ALEATORIAMENTE - completamente aleatório, sem restrições
        equipe_sorteada = random.choice(equipes)
        
        # Verificar se já existe sorteio para este mês/battlepass
        sorteio_existente = Sorteio.query.filter_by(
            battlepass_id=battlepass_id,
            semana=None,  # Sorteios de equipe não têm semana
            mes=mes,
            ano=ano,
            deletado=False
        ).first()
        
        if sorteio_existente:
            # Se já existe, substituir por um novo sorteio
            db.session.delete(sorteio_existente)
        
        # Criar novo registro de sorteio
        sorteio = Sorteio(
            battlepass_id=battlepass_id,
            mes=mes,
            ano=ano,
            semana=None,  # Equipe não tem semana
            equipe_id=equipe_sorteada.id,
            sorteado_por=current_user.id
        )
        
        db.session.add(sorteio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sorteado': {
                'id': equipe_sorteada.id,
                'nome': equipe_sorteada.nome
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sorteio/<int:sorteio_id>', methods=['GET', 'DELETE'])
@login_required
def api_sorteio(sorteio_id):
    """Obtém info ou deleta um sorteio"""
    from backend.models import Sorteio
    
    sorteio = Sorteio.query.get_or_404(sorteio_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': sorteio.id,
            'sorteado_por': sorteio.usuario_sorteio.username if sorteio.usuario_sorteio else 'N/A',
            'sorteado_em': sorteio.sorteado_em.strftime('%d/%m/%Y %H:%M') if sorteio.sorteado_em else 'N/A'
        })
    
    elif request.method == 'DELETE':
        # Apenas admin/gerente pode deletar
        if current_user.nivel not in ['admin', 'gerente']:
            return jsonify({'success': False, 'error': 'Permissão negada'}), 403
        
        try:
            sorteio.deletado = True
            sorteio.deletado_por = current_user.id
            sorteio.deletado_em = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500


# ==================== APIs DE HISTÓRICO DE SORTEIOS ====================
@app.route('/api/historico-sorteios-operador')
@login_required
def api_historico_sorteios_operador():
    """Retorna histórico de sorteios de operadores para um mês/ano"""
    from backend.models import Sorteio, Battlepass
    from datetime import datetime as dt
    
    battlepass_id = request.args.get('battlepass_id', type=int)
    mes = request.args.get('mes', type=int, default=dt.now().month)
    ano = request.args.get('ano', type=int, default=dt.now().year)
    
    try:
        sorteios = Sorteio.query.filter_by(
            battlepass_id=battlepass_id,
            mes=mes,
            ano=ano,
            deletado=False
        ).order_by(Sorteio.semana.asc()).all()
        
        historico = []
        for sorteio in sorteios:
            if sorteio.operador:
                historico.append({
                    'semana': sorteio.semana,
                    'operador_nome': sorteio.operador.nome,
                    'operador_warname': sorteio.operador.warname,
                    'data_sorteio': sorteio.sorteado_em.strftime('%d/%m/%Y %H:%M') if sorteio.sorteado_em else 'N/A'
                })
        
        return jsonify({'success': True, 'historico': historico})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/historico-sorteios-equipe')
@login_required
def api_historico_sorteios_equipe():
    """Retorna histórico de sorteios de equipes para um mês/ano"""
    from backend.models import Sorteio, Battlepass
    from datetime import datetime as dt
    
    battlepass_id = request.args.get('battlepass_id', type=int)
    mes = request.args.get('mes', type=int, default=dt.now().month)
    ano = request.args.get('ano', type=int, default=dt.now().year)
    
    try:
        sorteios = Sorteio.query.filter_by(
            battlepass_id=battlepass_id,
            mes=mes,
            ano=ano,
            semana=None,  # Sorteios de equipe (sem semana)
            deletado=False
        ).order_by(Sorteio.sorteado_em.desc()).all()
        
        historico = []
        for sorteio in sorteios:
            if sorteio.equipe:
                historico.append({
                    'equipe_nome': sorteio.equipe.nome,
                    'data_sorteio': sorteio.sorteado_em.strftime('%d/%m/%Y %H:%M') if sorteio.sorteado_em else 'N/A'
                })
        
        return jsonify({'success': True, 'historico': historico})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== APIs DE EVENTOS ====================
@app.route('/api/eventos/criar', methods=['POST'])
@login_required
@admin_required
def api_criar_evento():
    """Cria um novo evento com fotos e brindes"""
    from backend.models import Evento, EventoBrinde
    from datetime import datetime as dt
    import json
    
    try:
        data = request.form.to_dict()
        
        # Validar campos obrigatórios
        if not all([data.get('nome'), data.get('data_evento'), data.get('campo')]):
            return jsonify({'success': False, 'error': 'Campos obrigatórios faltando'}), 400
        
        # Processar fotos (base64 string no campo fotos)
        fotos = []
        if 'fotos' in request.files:
            files = request.files.getlist('fotos')
            for file in files[:5]:  # Máximo 5 fotos
                if file and file.filename:
                    import base64
                    fotos.append(base64.b64encode(file.read()).decode())
        
        # Criar evento
        evento = Evento(
            nome=data.get('nome'),
            descricao=data.get('descricao', ''),
            data_evento=dt.strptime(data.get('data_evento'), '%Y-%m-%d %H:%M'),
            campo=data.get('campo'),
            valor_pessoa=float(data.get('valor_pessoa', 0)),
            valor_individual=float(data.get('valor_individual', 0)),
            fotos=json.dumps(fotos) if fotos else None,
            criado_por=current_user.id,
            ativo=True
        )
        
        db.session.add(evento)
        db.session.flush()
        
        # Adicionar brindes - usar getlist do request.form, não do dict
        brindes = request.form.getlist('brindes')
        for idx, brinde_desc in enumerate(brindes):
            if brinde_desc.strip():
                brinde = EventoBrinde(
                    evento_id=evento.id,
                    descricao=brinde_desc,
                    ordem=idx
                )
                db.session.add(brinde)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'evento_id': evento.id,
            'message': 'Evento criado com sucesso!'
        })
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao criar evento: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/eventos/<int:evento_id>/editar', methods=['POST'])
@login_required
@admin_required
def api_editar_evento(evento_id):
    """Edita um evento existente"""
    from backend.models import Evento, EventoBrinde
    from datetime import datetime as dt
    import json
    
    try:
        evento = Evento.query.get_or_404(evento_id)
        data = request.form.to_dict()
        
        # Atualizar campos
        if 'nome' in data:
            evento.nome = data['nome']
        if 'descricao' in data:
            evento.descricao = data['descricao']
        if 'data_evento' in data:
            evento.data_evento = dt.strptime(data['data_evento'], '%Y-%m-%d %H:%M')
        if 'campo' in data:
            evento.campo = data['campo']
        if 'valor_pessoa' in data:
            evento.valor_pessoa = float(data['valor_pessoa'] or 0)
        if 'valor_individual' in data:
            evento.valor_individual = float(data['valor_individual'] or 0)
        
        # Processar fotos
        if 'fotos' in request.files:
            files = request.files.getlist('fotos')
            fotos = []
            for file in files[:5]:
                if file and file.filename:
                    import base64
                    fotos.append(base64.b64encode(file.read()).decode())
            if fotos:
                evento.fotos = json.dumps(fotos)
        
        # Atualizar brindes
        EventoBrinde.query.filter_by(evento_id=evento_id).delete()
        brindes = request.form.getlist('brindes')
        for idx, brinde_desc in enumerate(brindes):
            if brinde_desc.strip():
                brinde = EventoBrinde(
                    evento_id=evento_id,
                    descricao=brinde_desc,
                    ordem=idx
                )
                db.session.add(brinde)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Evento atualizado!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/eventos/<int:evento_id>', methods=['GET', 'DELETE'])
@login_required
def api_evento_detail(evento_id):
    """Obtém detalhes ou deleta um evento"""
    from backend.models import Evento
    
    evento = Evento.query.get_or_404(evento_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': evento.id,
            'nome': evento.nome,
            'descricao': evento.descricao,
            'data_evento': evento.data_evento.strftime('%Y-%m-%d'),
            'campo': evento.campo,
            'valor_pessoa': evento.valor_pessoa,
            'valor_individual': evento.valor_individual,
            'fotos': evento.fotos or [],
            'brindes': [{'id': b.id, 'descricao': b.descricao, 'ordem': b.ordem} for b in evento.brindes],
            'ativo': evento.ativo
        })
    
    elif request.method == 'DELETE':
        if current_user.nivel not in ['admin', 'gerente']:
            return jsonify({'success': False, 'error': 'Permissão negada'}), 403
        
        try:
            evento.deletado = True
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500


# ==================== INICIALIZAÇÃO ====================
@app.cli.command("reset-database")
def reset_database():
    """Reset entire database - delete all data"""
    confirm = input("⚠️  This will DELETE ALL DATA! Type 'reset' to confirm: ").strip().lower()
    
    if confirm != 'reset':
        print("Cancelled.")
        return
    
    try:
        # Delete in correct order (respecting foreign keys)
        from backend.models import (
            PagamentoOperador, PartidaParticipante, Partida, Venda, 
            Estoque, Log, Solicitacao, EquipeMembros, Equipe, Operador, User
        )
        
        print("Deleting data...")
        PagamentoOperador.query.delete()
        print("  ✓ pagamento_operador")
        PartidaParticipante.query.delete()
        print("  ✓ partida_participantes")
        Partida.query.delete()
        print("  ✓ partidas")
        Venda.query.delete()
        print("  ✓ vendas")
        Estoque.query.delete()
        print("  ✓ estoque")
        Log.query.delete()
        print("  ✓ logs")
        Solicitacao.query.delete()
        print("  ✓ solicitacoes")
        EquipeMembros.query.delete()
        print("  ✓ equipe_membros")
        Equipe.query.delete()
        print("  ✓ equipes")
        Operador.query.delete()
        print("  ✓ operadores")
        User.query.delete()
        print("  ✓ users")
        
        db.session.commit()
        print("\n✅ Database reset successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")


@app.cli.command("delete-all-users")
def delete_all_users():
    """Delete all users from database"""
    confirm = input("⚠️  This will delete ALL users! Type 'yes' to confirm: ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    try:
        count = User.query.count()
        User.query.delete()
        db.session.commit()
        print(f"✅ Deleted {count} users successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")


@app.cli.command("list-users")
def list_users():
    """List all users"""
    users = User.query.all()
    
    if not users:
        print("No users found!")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<5} {'Username':<20} {'Nome':<30} {'Nivel':<10} {'Status':<10}")
    print("="*80)
    
    for user in users:
        print(f"{user.id:<5} {user.username:<20} {user.nome:<30} {user.nivel:<10} {user.status:<10}")
    
    print("="*80 + "\n")


@app.cli.command("create-keno-admin")
def create_keno_admin():
    """Create Keno as admin user"""
    
    # Check if Keno already exists
    if User.query.filter_by(username='Keno').first():
        print('❌ Keno already exists!')
        return
    
    password = input('Enter password for Keno: ').strip()
    email = input('Enter email for Keno: ').strip()
    
    import secrets
    
    # Create Keno admin
    salt = secrets.token_hex(16)
    keno = User(
        username='Keno',
        nome='Keno',
        email=email,
        nivel='admin',
        status='aprovado',
        salt=salt,
        terms_accepted=True,
        terms_accepted_date=datetime.utcnow()
    )
    keno.set_password(password)
    
    db.session.add(keno)
    db.session.commit()
    
    print(f'✅ Keno admin created successfully!')
    print(f'   Username: Keno')
    print(f'   Email: {email}')


@app.cli.command("create-admin")
def create_admin():
    """Create an admin user"""
    import secrets
    from werkzeug.security import generate_password_hash
    
    username = input('Username: ').strip()
    email = input('Email: ').strip()
    password = input('Password: ').strip()
    nome = input('Full name: ').strip()
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print(f'❌ User {username} already exists!')
        return
    
    if User.query.filter_by(email=email).first():
        print(f'❌ Email {email} already exists!')
        return
    
    # Create admin user
    salt = secrets.token_hex(16)
    admin = User(
        username=username,
        nome=nome,
        email=email,
        nivel='admin',
        status='aprovado',
        salt=salt,
        terms_accepted=True,
        terms_accepted_date=datetime.utcnow()
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f'✅ Admin user created successfully!')
    print(f'   Username: {username}')
    print(f'   Email: {email}')


@app.cli.command("init-db")
def init_db():
    db.create_all()
    
    from werkzeug.security import generate_password_hash
    import secrets
    
    salt = secrets.token_hex(16)
    admin = User(
        username='admin',
        nome='Administrador',
        email='admin@battlezone.com',
        nivel='admin',
        status='aprovado',
        salt=salt,
        password_hash=generate_password_hash('admin123' + salt)
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print("Banco de dados inicializado!")
    print("Usuário admin criado: admin / admin123")


@app.cli.command("init-battlepasses")
def init_battlepasses():
    """Inicializa os battlepasses padrão no banco de dados"""
    from backend.models import Battlepass
    
    battlepasses_data = [
        # Operadores
        {
            'tipo': 'OPERADOR',
            'nome': 'Battlepass Operador',
            'descricao': 'Battlepass básico para operadores',
            'categoria': 'operador',
            'ativo': True
        },
        {
            'tipo': 'ELITE_CAVEIRA',
            'nome': 'Battlepass Elite-Caveira',
            'descricao': 'Battlepass elite com Caveira',
            'categoria': 'operador',
            'ativo': True
        },
        # Equipes
        {
            'tipo': 'EQUIPE_BASICA',
            'nome': 'Battlepass Equipe Basica',
            'descricao': 'Battlepass básico para equipes',
            'categoria': 'equipe',
            'ativo': True
        }
    ]
    
    for bp_data in battlepasses_data:
        # Verificar se já existe
        existente = Battlepass.query.filter_by(tipo=bp_data['tipo']).first()
        
        if existente:
            print(f"✓ {bp_data['nome']} já existe")
            continue
        
        # Criar novo battlepass
        bp = Battlepass(
            tipo=bp_data['tipo'],
            nome=bp_data['nome'],
            descricao=bp_data['descricao'],
            categoria=bp_data['categoria'],
            ativo=bp_data['ativo']
        )
        
        db.session.add(bp)
        print(f"✓ Criado: {bp_data['nome']}")
    
    db.session.commit()
    print("\n✓ Battlepasses inicializados com sucesso!")


@app.cli.command("migrar-json")
def migrar_json():
    import json
    import os
    
    if os.path.exists('data/operadores.json'):
        with open('data/operadores.json', 'r') as f:
            operadores_json = json.load(f)
        
        for op_json in operadores_json:
            if Operador.query.filter_by(warname=op_json.get('warname')).first():
                continue
            
            operador = Operador(
                old_id=op_json.get('id'),
                nome=op_json.get('nome', ''),
                warname=op_json.get('warname', ''),
                cpf=op_json.get('cpf', ''),
                email=op_json.get('email', ''),
                telefone=op_json.get('telefone', ''),
                data_nascimento=op_json.get('data_nascimento', ''),
                idade=op_json.get('idade', ''),
                battlepass=op_json.get('battlepass', 'NAO')
            )
            db.session.add(operador)
        
        db.session.commit()
        print(f"Operadores migrados: {len(operadores_json)}")
    
    print("Migração concluída!")


@app.route('/setup/info')
def setup_info():
    """Show current database setup"""
    import os
    from backend.models import db
    
    try:
        info = {
            'flask_env': os.environ.get('FLASK_ENV', 'NOT SET'),
            'database_url_set': 'DATABASE_URL' in os.environ,
            'database_uri': str(db.engine.url),
            'debug_mode': app.debug,
            'tables': db.inspect(db.engine).get_table_names() if db.inspect(db.engine) else []
        }
        
        # Test connection
        try:
            result = db.session.execute(db.text('SELECT 1'))
            info['connection_status'] = 'OK'
        except Exception as e:
            info['connection_status'] = f'ERROR: {str(e)}'
        
        return jsonify(info), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/setup/init-database/<secret_key>')
def init_database_setup(secret_key):
    """Initialize database tables - use SECRET_KEY from environment"""
    import os
    
    # Security: require correct secret key
    if secret_key != os.environ.get('SECRET_KEY', ''):
        return jsonify({'error': 'Invalid secret key'}), 403
    
    try:
        from backend.init_db import init_database
        init_database(app)
        
        return jsonify({
            'success': True,
            'message': 'Database initialized successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/setup/make-keno-full-admin/<secret_key>')
def setup_make_keno_full_admin(secret_key):
    """Make Keno a full admin with all permissions"""
    import os
    
    # Security: require correct secret key
    if secret_key != os.environ.get('SECRET_KEY', ''):
        return jsonify({'error': 'Invalid secret key'}), 403
    
    try:
        keno = User.query.filter_by(username='Keno').first()
        
        if not keno:
            return jsonify({'error': 'Keno not found'}), 404
        
        # Set full admin permissions
        keno.nivel = 'admin'
        keno.status = 'aprovado'
        keno.approved_at = datetime.utcnow()
        keno.approved_by = 'system'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Keno is now a full admin',
            'username': 'Keno',
            'nivel': 'admin',
            'status': 'aprovado'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/setup/set-keno-password/<secret_key>/<password>')
def setup_set_keno_password(secret_key, password):
    """Set Keno password - use SECRET_KEY for security"""
    import os
    
    # Security: require correct secret key
    if secret_key != os.environ.get('SECRET_KEY', ''):
        return jsonify({'error': 'Invalid secret key'}), 403
    
    try:
        keno = User.query.filter_by(username='Keno').first()
        
        if not keno:
            return jsonify({'error': 'Keno not found'}), 404
        
        # Set new password
        keno.set_password(password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Keno password set successfully',
            'username': 'Keno',
            'password': password
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/setup/create-keno/<secret_key>')
def setup_create_keno(secret_key):
    """Create Keno as admin - use SECRET_KEY for security"""
    import os
    
    # Security: require correct secret key
    if secret_key != os.environ.get('SECRET_KEY', ''):
        return jsonify({'error': 'Invalid secret key'}), 403
    
    try:
        # Check if Keno already exists
        if User.query.filter_by(username='Keno').first():
            return jsonify({'error': 'Keno already exists'}), 400
        
        import secrets
        
        # Create Keno admin
        salt = secrets.token_hex(16)
        keno = User(
            username='Keno',
            nome='Keno',
            email='keno@battlezone.com',
            nivel='admin',
            status='aprovado',
            salt=salt,
            terms_accepted=True,
            terms_accepted_date=datetime.utcnow()
        )
        keno.set_password('12345678')  # Default password
        
        db.session.add(keno)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Keno admin created successfully',
            'username': 'Keno',
            'password': '12345678',
            'email': 'keno@battlezone.com'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/setup/db-stats')
def db_stats():
    """Show data count in each table"""
    try:
        from backend.models import db, User, Operador, Equipe, Partida, PartidaParticipante, Venda, Estoque, Log, Solicitacao, PagamentoOperador
        
        # Count records in each table
        stats = {
            'timestamp': datetime.now().isoformat(),
            'database_type': 'PostgreSQL' if 'postgresql' in str(db.engine.url) else 'SQLite',
            'data_counts': {
                'users': User.query.count(),
                'operadores': Operador.query.count(),
                'equipes': Equipe.query.count(),
                'partidas': Partida.query.count(),
                'partida_participantes': PartidaParticipante.query.count(),
                'vendas': Venda.query.count(),
                'estoque': Estoque.query.count(),
                'logs': Log.query.count(),
                'solicitacoes': Solicitacao.query.count(),
                'pagamento_operador': PagamentoOperador.query.count(),
            },
            'total_records': sum([
                User.query.count(),
                Operador.query.count(),
                Equipe.query.count(),
                Partida.query.count(),
                PartidaParticipante.query.count(),
                Venda.query.count(),
                Estoque.query.count(),
                Log.query.count(),
                Solicitacao.query.count(),
                PagamentoOperador.query.count(),
            ])
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/setup/criar-partidas-teste')
def criar_partidas_teste():
    """Cria partidas de teste para todas as combinações de campo, plano e tempo"""
    try:
        from datetime import datetime, timedelta
        
        # 1. Criar ou obter operadores Keno e Tete
        keno = Operador.query.filter_by(nome='Keno').first()
        if not keno:
            keno = Operador(nome='Keno', warname='Keno', email='keno@battlezone.com')
            db.session.add(keno)
            db.session.flush()
        
        tete = Operador.query.filter_by(nome='Tete').first()
        if not tete:
            tete = Operador(nome='Tete', warname='Tete', email='tete@battlezone.com')
            db.session.add(tete)
            db.session.flush()
        
        db.session.commit()
        
        # 2. Buscar usuário criador (Keno)
        keno_user = User.query.filter_by(username='Keno').first()
        creator_id = keno_user.id if keno_user else None
        
        # 3. Gerar lista de combinações
        partidas_criar = []
        
        # Warfield
        for plano in ['Avulso', 'Equipe', 'Sua Arma']:
            tempos = PLANOS_WARFIELD[plano]['tempos']
            for tempo in tempos:
                partidas_criar.append({
                    'campo': 'Warfield',
                    'plano': plano,
                    'tempo': tempo
                })
        
        # Redline
        for plano in ['Rifle', 'Pistola']:
            tempos = PLANOS_REDLINE[plano]['tempos']
            for tempo in tempos:
                partidas_criar.append({
                    'campo': 'Redline',
                    'plano': plano,
                    'tempo': tempo
                })
        
        # 4. Criar partidas
        counter = 100
        data_base = datetime.now()
        resultado = []
        
        for config in partidas_criar:
            campo = config['campo']
            plano = config['plano']
            tempo = config['tempo']
            
            # Obter modo (primeiro disponível) e valores
            modos = get_modos_permitidos(tempo, plano)
            modo = modos[0] if modos else 'PVP INFINITY'
            
            valor, bbs = get_valores_plano(campo, plano, tempo)
            
            # Criar partida
            partida = Partida(
                nome=str(counter),
                data=(data_base + timedelta(days=counter-100)).strftime('%Y-%m-%d'),
                horario='18:00',
                campo=campo,
                plano=plano,
                tempo=tempo,
                modo=modo,
                tipo_participacao='individual',
                valor_total=valor,
                valor_por_participante=valor / 2,
                bbs_por_pessoa=bbs,
                total_bbs=bbs * 2,
                status='Agendada',
                created_by=creator_id
            )
            db.session.add(partida)
            db.session.flush()
            
            # Adicionar participantes
            part_keno = PartidaParticipante(partida_id=partida.id, operador_id=keno.id)
            part_tete = PartidaParticipante(partida_id=partida.id, operador_id=tete.id)
            
            db.session.add(part_keno)
            db.session.add(part_tete)
            
            resultado.append({
                'numero': counter,
                'campo': campo,
                'plano': plano,
                'tempo': tempo,
                'modo': modo,
                'data': (data_base + timedelta(days=counter-100)).strftime('%Y-%m-%d')
            })
            
            counter += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'total_criadas': len(resultado),
            'operadores': {
                'operador1': f'Keno (ID: {keno.id})',
                'operador2': f'Tete (ID: {tete.id})'
            },
            'partidas': resultado
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500


if __name__ == '__main__':
    # Em desenvolvimento, apenas rodar
    app.run(debug=False, host='0.0.0.0', port=5000)




@app.cli.command("migrar-json")
def migrar_json():
    """Migra dados dos arquivos JSON para o banco"""
    import json
    import os
    
    # Migrar operadores
    if os.path.exists('data/operadores.json'):
        with open('data/operadores.json', 'r') as f:
            operadores_json = json.load(f)
        
        for op_json in operadores_json:
            # Verificar se já existe
            if Operador.query.filter_by(warname=op_json.get('warname')).first():
                continue
            
            operador = Operador(
                old_id=op_json.get('id'),
                nome=op_json.get('nome', ''),
                warname=op_json.get('warname', ''),
                cpf=op_json.get('cpf', ''),
                email=op_json.get('email', ''),
                telefone=op_json.get('telefone', ''),
                data_nascimento=op_json.get('data_nascimento', ''),
                idade=op_json.get('idade', ''),
                battlepass=op_json.get('battlepass', 'NAO')
            )
            db.session.add(operador)
        
        db.session.commit()
        print(f"Operadores migrados: {len(operadores_json)}")
    
    print("Migração concluída!")