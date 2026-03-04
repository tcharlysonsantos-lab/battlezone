#!/usr/bin/env python
"""Create database tables on Railway"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        logger.info("[DB] Importing Flask app...")
        from app import app, db
        
        with app.app_context():
            logger.info("[DB] Creating all tables...")
            db.create_all()
            logger.info("[DB] All tables created successfully!")
            
    except Exception as e:
        logger.error(f"[DB] Error: {e}", exc_info=True)
        sys.exit(1)
