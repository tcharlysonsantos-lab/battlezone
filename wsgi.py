# wsgi.py - Entry point para Gunicorn e Railway
from app import app

# Exportar app para Gunicorn/WSGI
application = app


