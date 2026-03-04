#!/usr/bin/env python
"""Start Flask development server with proper output"""
import os
import sys

os.environ['PYTHONUNBUFFERED'] = '1'

if __name__ == '__main__':
    try:
        print("[STARTUP] Loading Flask app...", flush=True)
        from app import app
        
        print("[STARTUP] Flask app loaded successfully", flush=True)
        print("[STARTUP] Starting development server...", flush=True)
        print("[STARTUP] Access the app at: http://localhost:5000", flush=True)
        print("[STARTUP] Press Ctrl+C to stop", flush=True)
        print("="*70, flush=True)
        
        # Run development server with debug enabled for development
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server stopped by user", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
