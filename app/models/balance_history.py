# models/balance_history.py - CON RELACIÓN
from sqlalchemy import Column, Integer, DateTime, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class BalanceHistory(Base):
    __tablename__ = "balance_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    balance = Column(DECIMAL(15, 2), nullable=False)
    pnl = Column(DECIMAL(15, 2), nullable=False)
    pnl_daily = Column(DECIMAL(15, 2), default=0)
    equity = Column(DECIMAL(15, 2), nullable=False)

    # RELACIÓN CON SESSION
    session = relationship("BotSession", back_populates="balance_history")

    def to_dict(self):
        """Convierte el objeto a dict"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "balance": float(self.balance),
            "pnl": float(self.pnl),
            "pnl_daily": float(self.pnl_daily),
            "equity": float(self.equity)
        }