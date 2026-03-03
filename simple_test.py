#!/usr/bin/env python
import sys
import os
sys.path.insert(0, '.')
os.chdir('d:\\Backup_Sistema\\Flask\\battlezone_flask')

print("TEST_START")

try:
    from app import app
    print("IMPORT_APP_OK")
except Exception as e:
    print(f"IMPORT_APP_ERROR:{e}")
    sys.exit(1)

try:
    from backend.models import db, User
    print("IMPORT_MODELS_OK")
except Exception as e:
    print(f"IMPORT_MODELS_ERROR:{e}")
    sys.exit(1)

try:
    with app.test_client() as client:
        resp1 = client.get('/')
        print(f"ROUTE_HOME:{resp1.status_code}")
        resp2 = client.get('/auth/login')
        print(f"ROUTE_LOGIN:{resp2.status_code}")
except Exception as e:
    print(f"ROUTES_ERROR:{e}")
    sys.exit(1)

print("TEST_END_SUCCESS")
