# models/bot_config.py - VERSIÓN CON RELACIÓN
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
import json

class BotConfig(Base):
    __tablename__ = "bot_config"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    config_name = Column(String(50), default="default")
    config_data = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relación
    user = relationship("User", back_populates="bot_configs")

    def get_config_value(self, key: str, default=None):
        """Obtiene un valor específico de la configuración"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set_config_value(self, key: str, value):
        """Establece un valor específico en la configuración"""
        keys = key.split('.')
        config = self.config_data.copy() if self.config_data else {}
        current = config
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self.config_data = config

    def to_dict(self):
        """Convierte el objeto a dict"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "config_name": self.config_name,
            "config_data": self.config_data,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }