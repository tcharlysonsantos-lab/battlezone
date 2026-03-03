import sqlite3
import os

print(f"CWD: {os.getcwd()}")
print(f"DB path: instance/database.db")
print(f"Absolute: {os.path.abspath('instance/database.db')}")
print(f"Exists: {os.path.exists('instance/database.db')}")

try:
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables found: {len(tables)}")
    for t in sorted(tables)[:5]:
        print(f"  - {t}")
    conn.close()
    print("SUCCESS!")
except Exception as e:
    print(f"ERROR: {e}")
