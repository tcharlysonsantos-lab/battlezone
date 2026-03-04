#!/usr/bin/env python
"""
Test script that simulates Railway environment
This helps diagnose 502 Bad Gateway issues
"""
import os
import sys
import sqlite3

print("\n" + "="*70)
print("RAILWAY ENVIRONMENT SIMULATOR")
print("="*70 + "\n")

# Test 1: Check environment
print("[TEST 1] Environment Variables")
print("-" * 70)
print(f"  FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT SET')}")
print(f"  SECRET_KEY: {'SET' if 'SECRET_KEY' in os.environ else 'NOT SET (CRITICAL!)'}")
print(f"  DATABASE_URL: {'SET' if 'DATABASE_URL' in os.environ else 'NOT SET'}")
print(f"  PORT: {os.environ.get('PORT', 'NOT SET (Railway sets this)')}")

# Test 2: Try importing config
print("\n[TEST 2] Importing Config")
print("-" * 70)
try:
    from config import config
    print(f"  SUCCESS: Config loaded")
    print(f"  DB_TYPE: {getattr(config, 'DB_TYPE', 'Unknown')}")
    print(f"  DEBUG: {getattr(config, 'DEBUG', 'Unknown')}")
    print(f"  DATABASE_URI: {config.SQLALCHEMY_DATABASE_URI[:80]}...")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Try importing app without running it
print("\n[TEST 3] Importing Flask App")
print("-" * 70)
try:
    from app import app, db
    print(f"  SUCCESS: App imported")
    print(f"  App: {app}")
    print(f"  Debug: {app.debug}")
    print(f"  DB object: {db}")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Try creating app context and testing DB
print("\n[TEST 4] Testing Database Connection")
print("-" * 70)
try:
    with app.app_context():
        print(f"  App context created")
        
        # Try to execute a simple query
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1'))
        print(f"  Database test query executed: SUCCESS")
        
        # Try to ping database  
        print(f"  Attempting to list tables...")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"  Tables in database: {len(tables)}")
        if tables:
            print(f"  First few tables: {tables[:5]}")
        
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("ALL TESTS PASSED - App should work on Railway!")
print("="*70 + "\n")

# Test 5: WSGI module test
print("[TEST 5] WSGI Module")
print("-" * 70)
try:
    import wsgi
    if hasattr(wsgi, 'application'):
        print(f"  SUCCESS: wsgi.application is available")
        print(f"  Type: {type(wsgi.application)}")
    else:
        print(f"  FAILED: No 'application' object in wsgi module")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
