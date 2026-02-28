# Novo arquivo: transaction.py
from functools import wraps
from flask import flash
from models import db

def transactional(f):
    """Decorator para garantir que a operação seja atômica"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            flash(f'Erro na operação: {str(e)}', 'danger')
            raise
    return decorated_function