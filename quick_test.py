#!/usr/bin/env python
import sys
import os
os.chdir('d:\\Backup_Sistema\\Flask\\battlezone_flask')
sys.path.insert(0, '.')

print("TEST 1", file=sys.stderr)
sys.stderr.flush()

try:
    print("TEST 2", file=sys.stderr)
    from app import app
    print("✅ Import OK", file=sys.stderr)
except Exception as e:
    print(f"❌ Erro: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
