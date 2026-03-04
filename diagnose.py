#!/usr/bin/env python
"""Diagnostic script for Railway deployment"""
import os
import sys

print("\n" + "="*70)
print("BATTLEZONE - RAILWAY DEPLOYMENT DIAGNOSTIC")
print("="*70 + "\n")

print("[ENVIRONMENT]")
print(f"  Python version: {sys.version.split()[0]}")
print(f"  Platform: {sys.platform}")
print(f"  Current directory: {os.getcwd()}")
print(f"  Virtual env: {os.environ.get('VIRTUAL_ENV', 'Not detected')}")

print("\n[RAILWAY ENVIRONMENT]")
print(f"  PORT: {os.environ.get('PORT', 'NOT SET (will be set by Railway)')}")
print(f"  FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT SET')}")
print(f"  DATABASE_URL: {('SET' if 'DATABASE_URL' in os.environ else 'NOT SET (required for PostgreSQL)')}")
print(f"  SECRET_KEY: {('SET' if 'SECRET_KEY' in os.environ else 'NOT SET (CRITICAL!)')}")

print("\n[REQUIRED FILES]")
files = {
    'app.py': 'Main Flask application',
    'wsgi.py': 'WSGI entry point for Gunicorn',
    'Procfile': 'Railway startup configuration',
    'requirements.txt': 'Python dependencies',
    'seguranca.env': 'Environment variables (local only)',
    'config.py': 'Flask configuration'
}

for filename, description in files.items():
    exists = os.path.exists(filename)
    status = '[OK]' if exists else '[MISSING]'
    print(f"  {status} {filename:20} - {description}")

print("\n[DATABASE CONFIGURATION]")
try:
    from config import config
    db_type = getattr(config, 'DB_TYPE', 'Unknown')
    print(f"  Detected: {db_type}")
    if 'DATABASE_URL' in os.environ:
        print(f"  Using: PostgreSQL (Railway)")
    else:
        print(f"  Using: SQLite (local development)")
except Exception as e:
    print(f"  Error: {e}")

print("\n[GUNICORN TEST]")
try:
    import gunicorn
    print(f"  Gunicorn: {gunicorn.__version__} [OK]")
except ImportError:
    print(f"  Gunicorn: NOT INSTALLED [CRITICAL ERROR]")

print("\n[FLASK IMPORT TEST]")
try:
    print("  Importing Flask app...")
    from wsgi import application
    print(f"  SUCCESS - App loaded: {application}")
    print(f"  Debug mode: {application.debug}")
    env_mode = 'PRODUCTION' if not application.debug else 'DEVELOPMENT'
    print(f"  Mode: {env_mode}")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("\nTo start the app locally: python start.py")
print("To deploy to Railway: git push origin main")
print("")
