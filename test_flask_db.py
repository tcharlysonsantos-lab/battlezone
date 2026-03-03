from app import app, db
print("App imported successfully")
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

with app.app_context():
    print("App context active")
    try:
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables found: {len(tables)}")
        for t in sorted(tables)[:5]:
            print(f"  - {t}")
        print("Database connection OK!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
