# app/models/audit_sessions.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, INET
from .base import Base

class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el usuario
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Información de la acción
    action_type = Column(String(50), nullable=False)  # 'login', 'logout', 'start_bot', 'stop_bot', 'config_change'
    action_details = Column(JSONB, nullable=False)
    
    # Información del cliente
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Timestamp y estado
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default='success')  # 'success', 'failed'

    # Relación
    user = relationship("User", back_populates="audit_sessions")

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'action_details': self.action_details,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status
        }

    def __repr__(self):
        return f"<AuditSession(id={self.id}, action='{self.action_type}', status='{self.status}')>"