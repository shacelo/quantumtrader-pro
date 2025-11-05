# app/models/system_logs.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con la sesión
    session_id = Column(Integer, ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Nivel y fuente del log
    level = Column(String(10), nullable=False)  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    source = Column(String(50), nullable=False)  # 'trading', 'system', 'risk_management', 'strategy', 'bot'
    
    # Mensaje y detalles
    message = Column(Text, nullable=False)
    details = Column(JSONB)  # Datos adicionales estructurados

    # Relación
    session = relationship("BotSession", back_populates="system_logs")

    @classmethod
    def create_info_log(cls, session_id: int, source: str, message: str, details: dict = None):
        """Crea un log de nivel INFO"""
        return cls(
            session_id=session_id,
            level='INFO',
            source=source,
            message=message,
            details=details
        )

    @classmethod
    def create_warning_log(cls, session_id: int, source: str, message: str, details: dict = None):
        """Crea un log de nivel WARNING"""
        return cls(
            session_id=session_id,
            level='WARNING',
            source=source,
            message=message,
            details=details
        )

    @classmethod
    def create_error_log(cls, session_id: int, source: str, message: str, error: Exception = None, details: dict = None):
        """Crea un log de nivel ERROR"""
        error_details = details or {}
        if error:
            error_details['error_type'] = type(error).__name__
            error_details['error_message'] = str(error)
            error_details['error_traceback'] = getattr(error, '__traceback__', None)
        
        return cls(
            session_id=session_id,
            level='ERROR',
            source=source,
            message=message,
            details=error_details
        )

    @classmethod
    def create_debug_log(cls, session_id: int, source: str, message: str, details: dict = None):
        """Crea un log de nivel DEBUG"""
        return cls(
            session_id=session_id,
            level='DEBUG',
            source=source,
            message=message,
            details=details
        )

    @classmethod
    def create_critical_log(cls, session_id: int, source: str, message: str, details: dict = None):
        """Crea un log de nivel CRITICAL"""
        return cls(
            session_id=session_id,
            level='CRITICAL',
            source=source,
            message=message,
            details=details
        )

    def get_log_color(self) -> str:
        """Retorna el color correspondiente al nivel del log"""
        colors = {
            'DEBUG': 'text-blue-400',
            'INFO': 'text-green-400',
            'WARNING': 'text-yellow-400',
            'ERROR': 'text-orange-400',
            'CRITICAL': 'text-red-400'
        }
        return colors.get(self.level, 'text-gray-400')

    def get_log_icon(self) -> str:
        """Retorna el icono correspondiente al nivel del log"""
        icons = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '💥'
        }
        return icons.get(self.level, '📝')

    def is_error_level(self) -> bool:
        """Verifica si el log es de nivel error o superior"""
        return self.level in ['ERROR', 'CRITICAL']

    def to_dict(self) -> dict:
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'details': self.details,
            'color': self.get_log_color(),
            'icon': self.get_log_icon(),
            'is_error': self.is_error_level()
        }

    def to_websocket_format(self) -> dict:
        """Formato optimizado para WebSocket"""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level.lower(),
            'source': self.source,
            'message': self.message,
            'details': self.details
        }

    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', source='{self.source}')>"