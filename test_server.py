import urllib.request
import sys

try:
    response = urllib.request.urlopen('http://localhost:5000/', timeout=5)
    print(f"✓ Server responded: {response.status}")
    content = response.read().decode('utf-8')
    if 'Dashboard' in content or 'dashboard' in content.lower():
        print("✓ Page loaded correctly")
    else:
        print("⚠ Page loaded but content may have errors")
        print(f"First 200 chars: {content[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
