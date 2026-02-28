from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from datetime import datetime

def requer_permissao(recurso):
    """Decorator para verificar permissão de acesso"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Faça login para acessar esta página.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.tem_permissao(recurso):
                flash(f'Você não tem permissão para acessar: {recurso}', 'danger')
                return redirect(url_for('dashboard'))  # ← CORRIGIDO
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def operador_session_required(f):
    """Decorator para verificar timeout de sessão (APENAS PARA OPERADORES - 30 MINUTOS)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.nivel == 'operador':
            if not current_user.is_session_valid():
                from flask_login import logout_user
                logout_user()
                flash('Sessão expirada por inatividade (30 minutos). Faça login novamente.', 'warning')
                return redirect(url_for('auth.login'))
            current_user.update_activity()
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.nivel not in ['admin', 'gerente']:
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function