# models/orders.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    order_id = Column(String(100))  # ID de exchange
    client_order_id = Column(String(100))
    side = Column(String(10), nullable=False)  # BUY, SELL
    type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP_LOSS, etc.
    status = Column(String(20), default="open")  # open, filled, canceled, rejected
    quantity = Column(DECIMAL(15, 8), nullable=False)
    price = Column(DECIMAL(15, 6))
    stop_price = Column(DECIMAL(15, 6))
    executed_quantity = Column(DECIMAL(15, 8), default=0)
    executed_price = Column(DECIMAL(15, 6))
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    real_trade = Column(Boolean, default=False)

    # Relaciones
    session = relationship("BotSession", back_populates="orders")
    entry_trades = relationship("Trade", foreign_keys="Trade.entry_order_id", back_populates="entry_order")
    exit_trades = relationship("Trade", foreign_keys="Trade.exit_order_id", back_populates="exit_order")

    def is_filled(self):
        """Verifica si la orden está completamente ejecutada"""
        return self.status == "filled" and self.executed_quantity >= self.quantity

    def get_executed_value(self):
        """Obtiene el valor total ejecutado"""
        if self.executed_quantity and self.executed_price:
            return float(self.executed_quantity * self.executed_price)
        return 0.0

    def to_dict(self):
        """Convierte el objeto a dict"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "symbol": self.symbol,
            "order_id": self.order_id,
            "client_order_id": self.client_order_id,
            "side": self.side,
            "type": self.type,
            "status": self.status,
            "quantity": float(self.quantity),
            "price": float(self.price) if self.price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "executed_quantity": float(self.executed_quantity),
            "executed_price": float(self.executed_price) if self.executed_price else None,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "updated_time": self.updated_time.isoformat() if self.updated_time else None,
            "real_trade": self.real_trade,
            "executed_value": self.get_executed_value(),
            "is_filled": self.is_filled()
        }   