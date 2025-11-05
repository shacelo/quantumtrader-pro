# app/api/v1/dashboard.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.data_service import DataService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/data', methods=['GET'])
@login_required
def get_dashboard_data():
    """
    Obtiene todos los datos del dashboard
    """
    session_id = request.args.get('session_id', type=int)
    
    data = DataService.get_dashboard_data(current_user.id, session_id)
    return jsonify(data), 200

@dashboard_bp.route('/trading-history', methods=['GET'])
@login_required
def get_trading_history():
    """
    Obtiene el historial de trading
    """
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    history = DataService.get_trading_history(current_user.id, days, limit)
    
    return jsonify({
        'success': True,
        'history': history
    }), 200

@dashboard_bp.route('/performance', methods=['GET'])
@login_required
def get_performance_metrics():
    """
    Obtiene métricas de performance
    """
    days = request.args.get('days', 30, type=int)
    
    metrics = DataService.get_performance_metrics(current_user.id, days)
    
    return jsonify({
        'success': True,
        'metrics': metrics
    }), 200

@dashboard_bp.route('/balance-history', methods=['GET'])
@login_required
def get_balance_history():
    """
    Obtiene el historial de balance
    """
    session_id = request.args.get('session_id', type=int)
    hours = request.args.get('hours', 24, type=int)
    
    # Obtener sesión
    from app.models.bot_sessions import BotSession
    session = BotSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({
            'success': False,
            'message': 'Sesión no encontrada'
        }), 404
    
    # Obtener historial
    from app.models.balance_history import BalanceHistory
    from datetime import datetime, timedelta
    
    since_time = datetime.utcnow() - timedelta(hours=hours)
    history = BalanceHistory.query.filter(
        BalanceHistory.session_id == session_id,
        BalanceHistory.timestamp >= since_time
    ).order_by(BalanceHistory.timestamp.asc()).all()
    
    return jsonify({
        'success': True,
        'history': [bh.to_dict() for bh in history]
    }), 200

@dashboard_bp.route('/active-positions', methods=['GET'])
@login_required
def get_active_positions():
    """
    Obtiene posiciones activas
    """
    session_id = request.args.get('session_id', type=int)
    
    # Obtener sesión
    from app.models.bot_sessions import BotSession
    session = BotSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({
            'success': False,
            'message': 'Sesión no encontrada'
        }), 404
    
    # Obtener posiciones
    from app.models.positions import Position
    positions = Position.query.filter_by(session_id=session_id).all()
    
    return jsonify({
        'success': True,
        'positions': [position.to_dict() for position in positions]
    }), 200