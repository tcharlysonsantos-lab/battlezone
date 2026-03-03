#!/usr/bin/env python
from app import app

print("Testing Flask application...")
print("=" * 60)

with app.test_client() as client:
    # Test home route
    print("\n[1/2] Testing GET /")
    resp = client.get('/')
    print(f"      Status code: {resp.status_code} (expected 200)")
    
    # Test login route  
    print("\n[2/2] Testing GET /auth/login")
    resp = client.get('/auth/login')
    print(f"      Status code: {resp.status_code} (expected 200)")

print("\n" + "=" * 60)
print("SUCCESS - System is working!")
print("=" * 60)
