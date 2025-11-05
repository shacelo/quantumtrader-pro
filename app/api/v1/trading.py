# app/api/v1/trading.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

trading_bp = Blueprint('trading', __name__)

@trading_bp.route('/strategies', methods=['GET'])
@login_required
def get_strategies():
    """Obtiene las estrategias de trading disponibles"""
    try:
        strategies = [
            {
                'id': 1,
                'name': 'Media Movil Simple',
                'description': 'Estrategia basada en cruce de medias móviles',
                'parameters': {
                    'fast_ma': 5,
                    'slow_ma': 20
                }
            },
            {
                'id': 2, 
                'name': 'RSI',
                'description': 'Estrategia basada en indicador RSI',
                'parameters': {
                    'rsi_period': 14,
                    'rsi_oversold': 30,
                    'rsi_overbought': 70
                }
            }
        ]
        
        return jsonify({
            'success': True,
            'strategies': strategies
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estrategias: {e}")
        return jsonify({
            'success': False,
            'message': 'Error obteniendo estrategias'
        }), 500

@trading_bp.route('/market/data', methods=['GET'])
@login_required
def get_market_data():
    """Obtiene datos de mercado"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        timeframe = request.args.get('timeframe', '1h')
        limit = request.args.get('limit', 100, type=int)
        
        # Aquí integrarías con tu data_service
        from app.services.data_service import DataService
        data_service = DataService()
        market_data = data_service.get_market_data(symbol, timeframe, limit)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'timeframe': timeframe,
            'data': market_data or []
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de mercado: {e}")
        return jsonify({
            'success': False,
            'message': 'Error obteniendo datos de mercado'
        }), 500

@trading_bp.route('/portfolio', methods=['GET'])
@login_required
def get_portfolio():
    """Obtiene información del portfolio"""
    try:
        # Información de ejemplo - integrar con exchange real
        portfolio = {
            'total_balance': 1000.0,
            'available_balance': 800.0,
            'locked_balance': 200.0,
            'positions': [
                {
                    'symbol': 'BTCUSDT',
                    'quantity': 0.01,
                    'current_price': 35000.0,
                    'value': 350.0
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'portfolio': portfolio
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo portfolio: {e}")
        return jsonify({
            'success': False,
            'message': 'Error obteniendo portfolio'
        }), 500