# app/core/database.py
from flask_sqlalchemy import SQLAlchemy
import logging
import os
import sys

# Agregar el directorio app al path para importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# SQLAlchemy instance
db = SQLAlchemy()

def init_db(app=None):
    """Inicializar la base de datos"""
    global db
    
    if app:
        db.init_app(app)
        
        # Crear tablas si no existen
        with app.app_context():
            try:
                # Importaciones absolutas
                from app.models.base import Base
                from app.models.users import User
                from app.models.api_keys import ApiKey
                from app.models.bot_config import BotConfig
                from app.models.bot_sessions import BotSession
                from app.models.balance_history import BalanceHistory
                from app.models.orders import Order
                from app.models.trades import Trade
                from app.models.positions import Position
                from app.models.system_logs import SystemLog
                from app.models.risk_metrics import RiskMetric
                from app.models.audit_sessions import AuditSession
                
                # Crear todas las tablas
                Base.metadata.create_all(bind=db.engine)
                logger.info("Tablas de base de datos creadas/verificadas")
                
            except ImportError as e:
                logger.error(f"Error de importacion: {e}")
                logger.error("Verifica que todos los archivos de modelos existan")
                raise
            except Exception as e:
                logger.error(f"Error creando tablas: {e}")
                raise
    
    return db

def get_session():
    """Obtener sesión de base de datos"""
    return db.session

def close_session(exception=None):
    """Cerrar sesión de base de datos"""
    db.session.remove()