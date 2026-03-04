# health_check.py - Database connection health check
import threading
import time
import logging
from datetime import datetime
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DatabaseHealthCheck:
    """Monitors database connection health continuously"""
    
    def __init__(self, app=None, db=None, interval=30):
        self.app = app
        self.db = db
        self.interval = interval  # seconds
        self.running = False
        self.thread = None
        self.last_check = None
        self.last_error = None
        self.connection_status = 'unknown'
        
    def init_app(self, app, db):
        """Initialize health check with app and db instances"""
        self.app = app
        self.db = db
        
    def start(self):
        """Start health check in background thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.thread.start()
        logger.info(f"[OK] Database Health Check started (interval: {self.interval}s)")
        
    def stop(self):
        """Stop health check"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("[STOP] Database Health Check stopped")
        
    def _health_check_loop(self):
        """Main loop that performs health checks continuously"""
        while self.running:
            try:
                # Perform health check
                self._perform_health_check()
                # Wait for next check
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                time.sleep(5)  # Retry after 5s if error
    
    def _perform_health_check(self):
        """Perform current health check"""
        try:
            if not self.app or not self.db:
                return
                
            with self.app.app_context():
                # Execute simple query to test connection
                result = self.db.session.execute(text('SELECT 1'))
                result.close()
                
                self.connection_status = 'connected'
                self.last_check = datetime.now()
                self.last_error = None
                
        except Exception as e:
            self.connection_status = 'disconnected'
            self.last_error = str(e)
            self.last_check = datetime.now()
            logger.warning(f"[WARNING] Database disconnected: {e}")
            
            # Try to reconnect
            try:
                self._attempt_reconnect()
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {reconnect_error}")
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to database"""
        try:
            with self.app.app_context():
                # Close old connections
                self.db.session.close_all()
                # Try new query
                self.db.session.execute(text('SELECT 1'))
                self.connection_status = 'reconnected'
                logger.info("[RECONNECTED] Successfully reconnected to database")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            raise
    
    def get_status(self):
        """Return current connection status"""
        return {
            'status': self.connection_status,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_error': self.last_error,
            'healthy': self.connection_status == 'connected'
        }


# Global instance
db_health_check = DatabaseHealthCheck()
