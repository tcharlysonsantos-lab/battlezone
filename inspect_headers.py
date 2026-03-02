import requests

session = requests.Session()

print("Fazendo GET /auth/login e inspecionando headers...")
r = session.get('http://192.168.0.100:5000/auth/login')

print(f"\nStatus: {r.status_code}")
print("\nHeaders de resposta importantes:")

for header in ['Set-Cookie', 'Content-Type', 'Strict-Transport-Security', 'X-Content-Type-Options']:
    value = r.headers.get(header)
    if value:
        print(f"  {header}: {value}")

print(f"\n\nCookie recebido:")
for cookie in r.cookies:
    print(f"  {cookie.name}:")
    print(f"    value: {str(cookie.value)[:50]}...")
    print(f"    domain: {cookie.domain}")
    print(f"    path: {cookie.path}")
    print(f"    secure: {cookie.secure}")
    print(f"    expires: {cookie.expires}")
    print(f"    samesite: {cookie._rest.get('SameSite')}")
