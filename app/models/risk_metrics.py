# app/models/risk_metrics.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class RiskMetric(Base):
    __tablename__ = "risk_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con la sesión
    session_id = Column(Integer, ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Métrica
    metric_name = Column(String(50), nullable=False)  # 'sharpe_ratio', 'max_drawdown', 'volatility', etc.
    metric_value = Column(DECIMAL(15, 6), nullable=False)
    
    # Periodo de tiempo
    time_period = Column(String(20), default='daily')  # 'hourly', 'daily', 'weekly', 'session'

    # Relación
    session = relationship("BotSession", back_populates="risk_metrics")

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metric_name': self.metric_name,
            'metric_value': float(self.metric_value),
            'time_period': self.time_period
        }

    def __repr__(self):
        return f"<RiskMetric(id={self.id}, name='{self.metric_name}', value={self.metric_value})>"