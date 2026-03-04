# db_health.py - Health check para manter conexão com banco SEMPRE ATIVA
import threading
import time
import logging
from datetime import datetime
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DatabaseHealthCheck:
    """Verifica saúde da conexão com banco de dados continuamente"""
    
    def __init__(self, app=None, db=None, interval=30):
        self.app = app
        self.db = db
        self.interval = interval  # segundos
        self.running = False
        self.thread = None
        self.last_check = None
        self.last_error = None
        self.connection_status = 'unknown'
        
    def init_app(self, app, db):
        """Inicializa o health check com a app e db"""
        self.app = app
        self.db = db
        
    def start(self):
        """Inicia o health check em thread separada"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.thread.start()
        logger.info(f"[OK] Database Health Check iniciado (intervalo: {self.interval}s)")
        
    def stop(self):
        """Para o health check"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("[STOP] Database Health Check parado")
        
    def _health_check_loop(self):
        """Loop principal que verifica conexão continuamente"""
        while self.running:
            try:
                # Executar health check
                self._perform_health_check()
                # Aguardar próxima verificação
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Erro no health check loop: {e}")
                time.sleep(5)  # Tentar novamente em 5s se erro
    
    def _perform_health_check(self):
        """Realiza o health check atual"""
        try:
            if not self.app or not self.db:
                return
                
            with self.app.app_context():
                # Executar query simples para testar conexão
                result = self.db.session.execute(text('SELECT 1'))
                result.close()
                
                self.connection_status = 'connected'
                self.last_check = datetime.now()
                self.last_error = None
                
        except Exception as e:
            self.connection_status = 'disconnected'
            self.last_error = str(e)
            self.last_check = datetime.now()
            logger.warning(f"[WARNING] Database desconectado: {e}")
            
            # Tentar reconectar
            try:
                self._attempt_reconnect()
            except Exception as reconnect_error:
                logger.error(f"Falha ao reconectar: {reconnect_error}")
    
    def _attempt_reconnect(self):
        """Tenta reconectar ao banco de dados"""
        try:
            with self.app.app_context():
                # Fechar conexões antigas
                self.db.session.close_all()
                # Tentar nova query
                self.db.session.execute(text('SELECT 1'))
                self.connection_status = 'reconnected'
                logger.info("[RECONNECTED] Reconectado com sucesso ao banco de dados")
        except Exception as e:
            logger.error(f"Falha na reconexão: {e}")
            raise
    
    def get_status(self):
        """Retorna status atual da conexão"""
        return {
            'status': self.connection_status,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_error': self.last_error,
            'healthy': self.connection_status == 'connected'
        }


# Instância global
db_health_check = DatabaseHealthCheck()
