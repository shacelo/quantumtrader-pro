# app/models/trades.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base
from datetime import datetime  # ✅ IMPORTACIÓN FALTANTE

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con la sesión
    session_id = Column(Integer, ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Información básica del trade
    symbol = Column(String(20), nullable=False)
    
    # Relaciones con órdenes
    entry_order_id = Column(Integer, ForeignKey("orders.id"))
    exit_order_id = Column(Integer, ForeignKey("orders.id"))
    
    # Precios
    entry_price = Column(DECIMAL(15, 6), nullable=False)
    exit_price = Column(DECIMAL(15, 6))
    
    # Cantidad y métricas
    quantity = Column(DECIMAL(15, 8), nullable=False)
    pnl = Column(DECIMAL(15, 2))  # Profit & Loss en USDT
    pnl_percent = Column(DECIMAL(10, 4))  # Profit & Loss en porcentaje
    
    # Estado y razón de cierre
    status = Column(String(20), default="open")  # 'open', 'closed', 'cancelled'
    close_reason = Column(String(50))  # 'take_profit', 'stop_loss', 'manual', 'signal', 'trailing_stop'
    
    # Timestamps
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True))
    
    # Niveles de riesgo
    stop_loss = Column(DECIMAL(15, 6))
    take_profit = Column(DECIMAL(15, 6))
    
    # Información de la señal
    signal_strength = Column(String(100))  # Fuerza de la señal que generó el trade
    
    # Tipo de trade
    real_trade = Column(Boolean, default=False)  # True = trade real, False = simulado
    
    # Métricas de riesgo adicionales
    risk_metrics = Column(JSONB)  # Datos estructurados de riesgo

    # Relaciones
    session = relationship("BotSession", back_populates="trades")
    entry_order = relationship("Order", foreign_keys=[entry_order_id], back_populates="entry_trades")
    exit_order = relationship("Order", foreign_keys=[exit_order_id], back_populates="exit_trades")
    position = relationship("Position", back_populates="trade", uselist=False)

    def calculate_pnl(self, current_price: float = None) -> dict:
        """
        Calcula el P&L del trade
        """
        if self.status == "open" and current_price:
            # P&L no realizado
            unrealized_pnl = (float(current_price) - float(self.entry_price)) * float(self.quantity)
            unrealized_pnl_percent = ((float(current_price) - float(self.entry_price)) / float(self.entry_price)) * 100
            
            return {
                'unrealized_pnl': round(unrealized_pnl, 2),
                'unrealized_pnl_percent': round(unrealized_pnl_percent, 2),
                'current_price': current_price
            }
        
        elif self.status == "closed" and self.exit_price and self.pnl is not None:
            # P&L realizado
            return {
                'realized_pnl': float(self.pnl),
                'realized_pnl_percent': float(self.pnl_percent) if self.pnl_percent else 0,
                'exit_price': float(self.exit_price)
            }
        
        return {'unrealized_pnl': 0, 'unrealized_pnl_percent': 0}

    def close_trade(self, exit_price: float, close_reason: str, exit_time: datetime = None):
        """
        Cierra el trade y calcula el P&L final
        """
        self.exit_price = exit_price
        self.close_reason = close_reason
        self.exit_time = exit_time or datetime.utcnow()
        self.status = "closed"
        
        # Calcular P&L
        self.pnl = (float(exit_price) - float(self.entry_price)) * float(self.quantity)
        self.pnl_percent = ((float(exit_price) - float(self.entry_price)) / float(self.entry_price)) * 100
        
        # Métricas de riesgo adicionales
        self.risk_metrics = {
            'holding_period': (self.exit_time - self.entry_time).total_seconds() / 3600,  # Horas
            'max_favorable_excursion': self._calculate_mfe(),
            'max_adverse_excursion': self._calculate_mae(),
            'close_type': close_reason
        }

    def _calculate_mfe(self) -> float:
        """
        Calcula Max Favorable Excursion (mejor precio alcanzado)
        """
        # En una implementación real, esto vendría del historial de precios
        # Por ahora, usamos el exit_price como aproximación
        if self.exit_price and self.entry_price:
            return max(0, (float(self.exit_price) - float(self.entry_price)) / float(self.entry_price) * 100)
        return 0.0

    def _calculate_mae(self) -> float:
        """
        Calcula Max Adverse Excursion (peor precio alcanzado)
        """
        # En una implementación real, esto vendría del historial de precios
        # Por ahora, usamos una aproximación basada en el stop loss
        if self.stop_loss and self.entry_price:
            return min(0, (float(self.stop_loss) - float(self.entry_price)) / float(self.entry_price) * 100)
        return 0.0

    def get_trade_summary(self) -> dict:
        """
        Retorna un resumen completo del trade
        """
        pnl_data = self.calculate_pnl()
        
        return {
            'id': self.id,
            'symbol': self.symbol,
            'status': self.status,
            'side': 'LONG',  # Por defecto, podrías añadir campo para SHORT
            'entry_price': float(self.entry_price),
            'exit_price': float(self.exit_price) if self.exit_price else None,
            'quantity': float(self.quantity),
            'pnl': float(self.pnl) if self.pnl else pnl_data.get('unrealized_pnl', 0),
            'pnl_percent': float(self.pnl_percent) if self.pnl_percent else pnl_data.get('unrealized_pnl_percent', 0),
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'close_reason': self.close_reason,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'signal_strength': self.signal_strength,
            'real_trade': self.real_trade,
            'holding_period_hours': (self.exit_time - self.entry_time).total_seconds() / 3600 if self.exit_time and self.entry_time else None,
            'risk_metrics': self.risk_metrics or {}
        }

    def is_winning_trade(self) -> bool:
        """
        Determina si el trade fue ganador
        """
        return self.pnl is not None and self.pnl > 0

    def is_open(self) -> bool:
        """
        Verifica si el trade está abierto
        """
        return self.status == "open"

    def update_stop_loss(self, new_stop_loss: float):
        """
        Actualiza el stop loss del trade
        """
        self.stop_loss = new_stop_loss

    def update_take_profit(self, new_take_profit: float):
        """
        Actualiza el take profit del trade
        """
        self.take_profit = new_take_profit

    def to_dict(self) -> dict:
        """
        Convierte el objeto a diccionario para JSON
        """
        return {
            'id': self.id,
            'session_id': self.session_id,
            'symbol': self.symbol,
            'entry_order_id': self.entry_order_id,
            'exit_order_id': self.exit_order_id,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'exit_price': float(self.exit_price) if self.exit_price else None,
            'quantity': float(self.quantity) if self.quantity else None,
            'pnl': float(self.pnl) if self.pnl else None,
            'pnl_percent': float(self.pnl_percent) if self.pnl_percent else None,
            'status': self.status,
            'close_reason': self.close_reason,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'signal_strength': self.signal_strength,
            'real_trade': self.real_trade,
            'risk_metrics': self.risk_metrics,
            'is_winning': self.is_winning_trade() if self.pnl is not None else None,
            'is_open': self.is_open()
        }

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol='{self.symbol}', status='{self.status}', pnl={self.pnl})>"