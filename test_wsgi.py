#!/usr/bin/env python
"""Test wsgi.py initialization like Gunicorn would"""
import os
import sys

os.environ['PYTHONUNBUFFERED'] = '1'

print("[TEST] Simulating Gunicorn WSGI initialization", flush=True)
print("[TEST] Working directory:", os.getcwd(), flush=True)
print("[TEST] Python version:", sys.version, flush=True)

try:
    print("[TEST] Importing wsgi module...", flush=True)
    import wsgi
    
    print("[TEST] Checking application object...", flush=True)
    if hasattr(wsgi, 'application'):
        app = wsgi.application
        print(f"[SUCCESS] application object found: {app}", flush=True)
        print(f"[SUCCESS] App debug mode: {app.debug}", flush=True)
        print(f"[SUCCESS] App name: {app.name}", flush=True)
        
        # Try to get info
        print("[SUCCESS] App is ready to serve requests!", flush=True)
    else:
        print("[ERROR] No 'application' object found in wsgi module", flush=True)
        sys.exit(1)
    
except Exception as e:
    print(f"[FATAL ERROR] {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[RESULT] WSGI module loads successfully!", flush=True)
