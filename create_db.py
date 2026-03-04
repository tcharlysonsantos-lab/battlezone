#!/usr/bin/env python
"""Create all database tables - run this ONCE before first deployment"""
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*70)
    logger.info("DATABASE INITIALIZATION SCRIPT")
    logger.info("="*70)
    
    try:
        logger.info("Step 1: Loading environment variables...")
        from config import config as app_config
        logger.info(f"  - DATABASE_URL: {'SET' if 'DATABASE_URL' in os.environ else 'NOT SET'}")
        logger.info(f"  - FLASK_ENV: {os.environ.get('FLASK_ENV', 'development')}")
        
        logger.info("\nStep 2: Importing Flask app...")
        from app import app, db
        logger.info("  - Flask app imported successfully")
        
        logger.info("\nStep 3: Creating application context...")
        with app.app_context():
            logger.info("  - Application context created")
            
            logger.info("\nStep 4: Checking existing tables...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"  - Found {len(existing_tables)} existing tables")
            
            if existing_tables:
                logger.info(f"  - Tables: {', '.join(existing_tables[:3])}...")
                logger.info("\nDatabase already initialized. Skipping table creation.")
                return 0
            
            logger.info("\nStep 5: Creating all database tables...")
            db.create_all()
            logger.info("  - Tables created successfully")
            
            logger.info("\nStep 6: Verifying tables...")
            inspector = inspect(db.engine)
            new_tables = inspector.get_table_names()
            logger.info(f"  - Total tables: {len(new_tables)}")
            
            if new_tables:
                logger.info(f"  - Tables created: {', '.join(new_tables[:5])}...")
            
            logger.info("\n" + "="*70)
            logger.info("SUCCESS: Database initialized successfully!")
            logger.info("="*70)
            return 0
            
    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        logger.error("="*70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
