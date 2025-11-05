# app/models/positions.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    session_id = Column(Integer, ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"), nullable=False)
    
    # Información de la posición
    symbol = Column(String(20), nullable=False)
    quantity = Column(DECIMAL(15, 8), nullable=False)
    entry_price = Column(DECIMAL(15, 6), nullable=False)
    current_price = Column(DECIMAL(15, 6), nullable=False)
    
    # Métricas de P&L no realizado
    unrealized_pnl = Column(DECIMAL(15, 2), nullable=False)
    unrealized_pnl_percent = Column(DECIMAL(10, 4), nullable=False)
    
    # Niveles de riesgo
    stop_loss = Column(DECIMAL(15, 6), nullable=False)
    take_profit = Column(DECIMAL(15, 6), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    session = relationship("BotSession", back_populates="positions")
    trade = relationship("Trade", back_populates="position")

    def update_price(self, new_price: float):
        """
        Actualiza el precio actual y recalcula el P&L
        """
        self.current_price = new_price
        self.unrealized_pnl = (float(new_price) - float(self.entry_price)) * float(self.quantity)
        
        if float(self.entry_price) > 0:
            self.unrealized_pnl_percent = ((float(new_price) - float(self.entry_price)) / float(self.entry_price)) * 100
        else:
            self.unrealized_pnl_percent = 0
        
        self.updated_at = datetime.utcnow()

    def get_distance_to_stop_loss(self) -> float:
        """
        Calcula la distancia porcentual al stop loss
        """
        if self.stop_loss and self.current_price:
            return ((float(self.current_price) - float(self.stop_loss)) / float(self.current_price)) * 100
        return 0.0

    def get_distance_to_take_profit(self) -> float:
        """
        Calcula la distancia porcentual al take profit
        """
        if self.take_profit and self.current_price:
            return ((float(self.take_profit) - float(self.current_price)) / float(self.current_price)) * 100
        return 0.0

    def is_stop_loss_hit(self) -> bool:
        """
        Verifica si se alcanzó el stop loss
        """
        if self.stop_loss and self.current_price:
            return float(self.current_price) <= float(self.stop_loss)
        return False

    def is_take_profit_hit(self) -> bool:
        """
        Verifica si se alcanzó el take profit
        """
        if self.take_profit and self.current_price:
            return float(self.current_price) >= float(self.take_profit)
        return False

    def get_position_value(self) -> float:
        """
        Calcula el valor actual de la posición
        """
        return float(self.current_price) * float(self.quantity)

    def get_risk_reward_ratio(self) -> float:
        """
        Calcula el ratio riesgo/recompensa
        """
        if self.stop_loss and self.take_profit and self.entry_price:
            risk = abs(float(self.entry_price) - float(self.stop_loss))
            reward = abs(float(self.take_profit) - float(self.entry_price))
            
            if risk > 0:
                return reward / risk
        return 0.0

    def get_position_summary(self) -> dict:
        """
        Retorna un resumen completo de la posición
        """
        return {
            'id': self.id,
            'symbol': self.symbol,
            'quantity': float(self.quantity),
            'entry_price': float(self.entry_price),
            'current_price': float(self.current_price),
            'unrealized_pnl': float(self.unrealized_pnl),
            'unrealized_pnl_percent': float(self.unrealized_pnl_percent),
            'position_value': self.get_position_value(),
            'stop_loss': float(self.stop_loss),
            'take_profit': float(self.take_profit),
            'distance_to_sl': self.get_distance_to_stop_loss(),
            'distance_to_tp': self.get_distance_to_take_profit(),
            'risk_reward_ratio': self.get_risk_reward_ratio(),
            'is_stop_loss_hit': self.is_stop_loss_hit(),
            'is_take_profit_hit': self.is_take_profit_hit(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict(self) -> dict:
        """
        Convierte el objeto a diccionario para JSON
        """
        return {
            'id': self.id,
            'session_id': self.session_id,
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'quantity': float(self.quantity),
            'entry_price': float(self.entry_price),
            'current_price': float(self.current_price),
            'unrealized_pnl': float(self.unrealized_pnl),
            'unrealized_pnl_percent': float(self.unrealized_pnl_percent),
            'stop_loss': float(self.stop_loss),
            'take_profit': float(self.take_profit),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'position_value': self.get_position_value(),
            'risk_reward_ratio': self.get_risk_reward_ratio(),
            'is_profitable': float(self.unrealized_pnl) > 0
        }

    @classmethod
    def create_from_trade(cls, trade, current_price: float):
        """
        Crea una nueva posición a partir de un trade
        """
        # Calcular P&L inicial
        unrealized_pnl = (float(current_price) - float(trade.entry_price)) * float(trade.quantity)
        
        if float(trade.entry_price) > 0:
            unrealized_pnl_percent = ((float(current_price) - float(trade.entry_price)) / float(trade.entry_price)) * 100
        else:
            unrealized_pnl_percent = 0

        position = cls(
            session_id=trade.session_id,
            trade_id=trade.id,
            symbol=trade.symbol,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit
        )
        
        return position

    def __repr__(self):
        return f"<Position(id={self.id}, symbol='{self.symbol}', pnl={self.unrealized_pnl})>"