# models/bot_sessions.py - CON RELACIONES
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from decimal import Decimal

class BotSession(Base):
    __tablename__ = "bot_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_name = Column(String(100))
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    initial_balance = Column(DECIMAL(15, 2), nullable=False)
    final_balance = Column(DECIMAL(15, 2))
    status = Column(String(20), default="running")  # running, stopped, paused, error
    trading_mode = Column(String(20), default="simulation")  # simulation, demo, real
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONES
    user = relationship("User", back_populates="bot_sessions")
    orders = relationship("Order", back_populates="session", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="session", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="session", cascade="all, delete-orphan")
    balance_history = relationship("BalanceHistory", back_populates="session", cascade="all, delete-orphan")
    system_logs = relationship("SystemLog", back_populates="session", cascade="all, delete-orphan")
    risk_metrics = relationship("RiskMetric", back_populates="session", cascade="all, delete-orphan")

    def get_current_balance(self):
        """Obtiene el balance más reciente"""
        return float(self.initial_balance)  # Simplificado por ahora

    def get_total_pnl(self):
        """Calcula el P&L total"""
        current_balance = self.get_current_balance()
        return float(current_balance - self.initial_balance)

    def get_total_pnl_percent(self):
        """Calcula el porcentaje de P&L"""
        if self.initial_balance > 0:
            return (self.get_total_pnl() / float(self.initial_balance)) * 100
        return 0.0

    def to_dict(self, include_relations: bool = False):
        """Convierte el objeto a dict"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "session_name": self.session_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "initial_balance": float(self.initial_balance),
            "final_balance": float(self.final_balance) if self.final_balance else None,
            "status": self.status,
            "trading_mode": self.trading_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "current_balance": self.get_current_balance(),
            "total_pnl": self.get_total_pnl(),
            "total_pnl_percent": self.get_total_pnl_percent()
        }

        if include_relations:
            data["total_trades"] = len(self.trades) if self.trades else 0
            data["active_trades"] = len([t for t in self.trades if t.status == "open"]) if self.trades else 0
            data["winning_trades"] = len([t for t in self.trades if t.pnl and t.pnl > 0]) if self.trades else 0

        return data