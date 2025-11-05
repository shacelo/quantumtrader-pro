# models/api_keys.py - CON RELACIÓN
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from cryptography.fernet import Fernet
import os
import base64

def get_encryption_key():
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        key = Fernet.generate_key()
    return key

cipher_suite = Fernet(get_encryption_key())

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exchange = Column(String(20), default="binance")
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    testnet = Column(Boolean, default=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))

    # RELACIÓN CON USER
    user = relationship("User", back_populates="api_keys")

    def set_api_key(self, api_key: str):
        """Encripta y guarda la API key"""
        self.api_key = cipher_suite.encrypt(api_key.encode()).decode()

    def get_api_key(self) -> str:
        """Desencripta y retorna la API key"""
        return cipher_suite.decrypt(self.api_key.encode()).decode()

    def set_api_secret(self, api_secret: str):
        """Encripta y guarda el API secret"""
        self.api_secret = cipher_suite.encrypt(api_secret.encode()).decode()

    def get_api_secret(self) -> str:
        """Desencripta y retorna el API secret"""
        return cipher_suite.decrypt(self.api_secret.encode()).decode()

    def to_dict(self, include_secrets: bool = False):
        """Convierte el objeto a dict"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "exchange": self.exchange,
            "testnet": self.testnet,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
        
        if include_secrets:
            data["api_key"] = self.get_api_key()
            data["api_secret"] = self.get_api_secret()
        
        return data