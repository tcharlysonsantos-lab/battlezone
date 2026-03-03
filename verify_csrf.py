#!/usr/bin/env python
import os
from pathlib import Path

templates_dir = Path('frontend/templates')
post_forms = []

for html_file in templates_dir.rglob('*.html'):
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if 'method' in content and 'POST' in content:
        has_csrf = 'csrf_token' in content or 'form.hidden_tag' in content
        post_forms.append((str(html_file), has_csrf))

post_forms.sort()
print("=" * 70)
print("CSRF TOKEN VERIFICATION REPORT")
print("=" * 70)
for file, has_csrf in post_forms:
    status = '✅' if has_csrf else '❌'
    print(f'{status} {file}')

missing = [f for f, c in post_forms if not c]
print("\n" + "=" * 70)
print(f'Total POST forms found: {len(post_forms)}')
if missing:
    print(f'❌ MISSING CSRF TOKENS: {len(missing)}')
    for f in missing:
        print(f'  - {f}')
else:
    print('✅ SUCCESS: All POST forms have CSRF tokens!')
print("=" * 70)
