# app/services/data_service.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, and_

from app.core.database import db
from app.models.bot_sessions import BotSession
from app.models.trades import Trade
from app.models.positions import Position
from app.models.balance_history import BalanceHistory
from app.models.risk_metrics import RiskMetric

logger = logging.getLogger(__name__)

class DataService:
    """Servicio para proporcionar datos al dashboard"""
    
    @staticmethod
    def get_dashboard_data(user_id: int, session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene todos los datos necesarios para el dashboard
        """
        try:
            # Obtener sesión activa o la más reciente
            session = DataService._get_user_session(user_id, session_id)
            if not session:
                return DataService._get_empty_dashboard()
            
            # Obtener datos en paralelo (en una app real podrían ser llamadas async)
            balance_data = DataService._get_balance_data(session.id)
            trading_data = DataService._get_trading_data(session.id)
            positions_data = DataService._get_positions_data(session.id)
            risk_data = DataService._get_risk_data(session.id)
            performance_data = DataService._get_performance_data(session.id)
            
            return {
                'success': True,
                'session': session.to_dict(),
                'balance': balance_data,
                'trading': trading_data,
                'positions': positions_data,
                'risk': risk_data,
                'performance': performance_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos del dashboard: {e}")
            return DataService._get_empty_dashboard()
    
    @staticmethod
    def get_trading_history(user_id: int, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de trading
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            trades = Trade.query.join(BotSession)\
                .filter(
                    BotSession.user_id == user_id,
                    Trade.status == 'closed',
                    Trade.exit_time >= since_date
                )\
                .order_by(Trade.exit_time.desc())\
                .limit(limit)\
                .all()
            
            return [trade.to_dict() for trade in trades]
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de trading: {e}")
            return []
    
    @staticmethod
    def get_performance_metrics(user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Obtiene métricas de performance
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Consulta para métricas agregadas
            result = db.session.query(
                func.count(Trade.id).label('total_trades'),
                func.count(Trade.id).filter(Trade.pnl > 0).label('winning_trades'),
                func.sum(Trade.pnl).label('total_pnl'),
                func.avg(Trade.pnl).filter(Trade.pnl > 0).label('avg_win'),
                func.avg(Trade.pnl).filter(Trade.pnl < 0).label('avg_loss'),
                func.max(Trade.pnl).label('best_trade'),
                func.min(Trade.pnl).label('worst_trade')
            ).join(BotSession)\
            .filter(
                BotSession.user_id == user_id,
                Trade.status == 'closed',
                Trade.exit_time >= since_date
            ).first()
            
            total_trades = result.total_trades or 0
            winning_trades = result.winning_trades or 0
            total_pnl = float(result.total_pnl or 0)
            avg_win = float(result.avg_win or 0)
            avg_loss = float(result.avg_loss or 0)
            best_trade = float(result.best_trade or 0)
            worst_trade = float(result.worst_trade or 0)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            profit_factor = (abs(avg_win) / abs(avg_loss)) if avg_loss != 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'best_trade': round(best_trade, 2),
                'worst_trade': round(worst_trade, 2),
                'profit_factor': round(profit_factor, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas de performance: {e}")
            return {}
    
    @staticmethod
    def _get_user_session(user_id: int, session_id: Optional[int] = None) -> Optional[BotSession]:
        """
        Obtiene la sesión del usuario
        """
        try:
            if session_id:
                # Sesión específica
                return BotSession.query.filter_by(id=session_id, user_id=user_id).first()
            else:
                # Sesión activa o la más reciente
                session = BotSession.query.filter_by(user_id=user_id, status='running').first()
                if not session:
                    session = BotSession.query.filter_by(user_id=user_id)\
                        .order_by(BotSession.created_at.desc())\
                        .first()
                return session
        except Exception as e:
            logger.error(f"❌ Error obteniendo sesión: {e}")
            return None
    
    @staticmethod
    def _get_balance_data(session_id: int) -> Dict[str, Any]:
        """
        Obtiene datos de balance
        """
        try:
            # Balance actual
            current_balance = BalanceHistory.query.filter_by(session_id=session_id)\
                .order_by(BalanceHistory.timestamp.desc())\
                .first()
            
            # Historial de balance (últimas 24 horas)
            since_time = datetime.utcnow() - timedelta(hours=24)
            balance_history = BalanceHistory.query.filter(
                BalanceHistory.session_id == session_id,
                BalanceHistory.timestamp >= since_time
            ).order_by(BalanceHistory.timestamp.asc()).all()
            
            balance_data = {
                'current_balance': float(current_balance.balance) if current_balance else 0,
                'total_pnl': float(current_balance.pnl) if current_balance else 0,
                'daily_pnl': float(current_balance.pnl_daily) if current_balance else 0,
                'history': [
                    {
                        'time': bh.timestamp.strftime('%H:%M'),
                        'balance': float(bh.balance),
                        'pnl': float(bh.pnl)
                    }
                    for bh in balance_history
                ]
            }
            
            return balance_data
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de balance: {e}")
            return {'current_balance': 0, 'total_pnl': 0, 'daily_pnl': 0, 'history': []}
    
    @staticmethod
    def _get_trading_data(session_id: int) -> Dict[str, Any]:
        """
        Obtiene datos de trading
        """
        try:
            # Estadísticas de trades
            trades_stats = db.session.query(
                func.count(Trade.id).label('total_trades'),
                func.count(Trade.id).filter(Trade.pnl > 0).label('winning_trades'),
                func.count(Trade.id).filter(Trade.real_trade == True).label('real_trades'),
                func.sum(Trade.pnl).label('total_pnl')
            ).filter(
                Trade.session_id == session_id,
                Trade.status == 'closed'
            ).first()
            
            total_trades = trades_stats.total_trades or 0
            winning_trades = trades_stats.winning_trades or 0
            real_trades = trades_stats.real_trades or 0
            simulated_trades = total_trades - real_trades
            total_pnl = float(trades_stats.total_pnl or 0)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Trades recientes
            recent_trades = Trade.query.filter_by(session_id=session_id, status='closed')\
                .order_by(Trade.exit_time.desc())\
                .limit(10)\
                .all()
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'real_trades': real_trades,
                'simulated_trades': simulated_trades,
                'win_rate': round(win_rate, 1),
                'total_pnl': round(total_pnl, 2),
                'recent_trades': [trade.to_dict() for trade in recent_trades]
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de trading: {e}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'real_trades': 0,
                'simulated_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'recent_trades': []
            }
    
    @staticmethod
    def _get_positions_data(session_id: int) -> Dict[str, Any]:
        """
        Obtiene datos de posiciones activas
        """
        try:
            positions = Position.query.filter_by(session_id=session_id).all()
            
            return {
                'active_positions': len(positions),
                'positions': [position.to_dict() for position in positions]
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de posiciones: {e}")
            return {'active_positions': 0, 'positions': []}
    
    @staticmethod
    def _get_risk_data(session_id: int) -> Dict[str, Any]:
        """
        Obtiene datos de riesgo
        """
        try:
            # Métricas de riesgo recientes
            risk_metrics = RiskMetric.query.filter_by(session_id=session_id)\
                .order_by(RiskMetric.timestamp.desc())\
                .limit(10)\
                .all()
            
            current_metrics = {}
            for metric in risk_metrics:
                if metric.metric_name not in current_metrics:
                    current_metrics[metric.metric_name] = {
                        'value': float(metric.metric_value),
                        'timestamp': metric.timestamp.isoformat()
                    }
            
            return {
                'metrics': current_metrics,
                'history': [metric.to_dict() for metric in risk_metrics]
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de riesgo: {e}")
            return {'metrics': {}, 'history': []}
    
    @staticmethod
    def _get_performance_data(session_id: int) -> Dict[str, Any]:
        """
        Obtiene datos de performance avanzados
        """
        try:
            # Calcular drawdown máximo
            balance_history = BalanceHistory.query.filter_by(session_id=session_id)\
                .order_by(BalanceHistory.timestamp.asc())\
                .all()
            
            max_drawdown = 0
            peak = 0
            
            for bh in balance_history:
                balance = float(bh.balance)
                if balance > peak:
                    peak = balance
                drawdown = (peak - balance) / peak * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            # Sharpe ratio (simulado)
            sharpe_ratio = 1.2  # En producción se calcularía con volatilidad real
            
            return {
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'calmar_ratio': round(sharpe_ratio / max_drawdown, 2) if max_drawdown > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de performance: {e}")
            return {
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'calmar_ratio': 0
            }
    
    @staticmethod
    def _get_empty_dashboard() -> Dict[str, Any]:
        """
        Retorna un dashboard vacío
        """
        return {
            'success': False,
            'message': 'No hay datos disponibles',
            'session': None,
            'balance': {'current_balance': 0, 'total_pnl': 0, 'daily_pnl': 0, 'history': []},
            'trading': {
                'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
                'real_trades': 0, 'simulated_trades': 0, 'win_rate': 0,
                'total_pnl': 0, 'recent_trades': []
            },
            'positions': {'active_positions': 0, 'positions': []},
            'risk': {'metrics': {}, 'history': []},
            'performance': {'max_drawdown': 0, 'sharpe_ratio': 0, 'calmar_ratio': 0},
            'timestamp': datetime.utcnow().isoformat()
        }