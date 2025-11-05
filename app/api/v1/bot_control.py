# app/api/v1/bot_control.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.bot_service import BotService

bot_bp = Blueprint('bot', __name__)

@bot_bp.route('/start', methods=['POST'])
@login_required
def start_bot():
    """
    Inicia el bot de trading
    """
    data = request.get_json()
    
    trading_mode = data.get('trading_mode', 'simulation')
    config_id = data.get('config_id')
    
    # Validar modo de trading
    valid_modes = ['simulation', 'demo', 'real']
    if trading_mode not in valid_modes:
        return jsonify({
            'success': False,
            'message': f'Modo de trading inválido. Válidos: {", ".join(valid_modes)}'
        }), 400
    
    # Advertencia para trading real
    if trading_mode == 'real':
        confirm_real = data.get('confirm_real_trading', False)
        if not confirm_real:
            return jsonify({
                'success': False,
                'message': 'Se requiere confirmación para trading real',
                'requires_confirmation': True
            }), 400
    
    result = BotService.start_bot(current_user.id, trading_mode, config_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@bot_bp.route('/stop', methods=['POST'])
@login_required
def stop_bot():
    """
    Detiene el bot de trading
    """
    result = BotService.stop_bot(current_user.id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@bot_bp.route('/status', methods=['GET'])
@login_required
def get_bot_status():
    """
    Obtiene el estado actual del bot
    """
    result = BotService.get_bot_status(current_user.id)
    return jsonify(result), 200

@bot_bp.route('/sessions', methods=['GET'])
@login_required
def get_bot_sessions():
    """
    Obtiene el historial de sesiones del bot
    """
    sessions = BotService.get_user_bots(current_user.id)
    
    return jsonify({
        'success': True,
        'sessions': sessions
    }), 200

@bot_bp.route('/session/<int:session_id>', methods=['GET'])
@login_required
def get_session_details(session_id):
    """
    Obtiene detalles de una sesión específica
    """
    # Verificar que la sesión pertenece al usuario
    from app.models.bot_sessions import BotSession
    session = BotSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({
            'success': False,
            'message': 'Sesión no encontrada'
        }), 404
    
    return jsonify({
        'success': True,
        'session': session.to_dict(include_relations=True)
    }), 200

@bot_bp.route('/session/<int:session_id>/logs', methods=['GET'])
@login_required
def get_session_logs(session_id):
    """
    Obtiene los logs de una sesión específica
    """
    # Verificar que la sesión pertenece al usuario
    from app.models.bot_sessions import BotSession
    from app.models.system_logs import SystemLog
    
    session = BotSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({
            'success': False,
            'message': 'Sesión no encontrada'
        }), 404
    
    # Obtener logs
    level_filter = request.args.get('level')
    source_filter = request.args.get('source')
    limit = request.args.get('limit', 100, type=int)
    
    query = SystemLog.query.filter_by(session_id=session_id)
    
    if level_filter:
        query = query.filter_by(level=level_filter.upper())
    if source_filter:
        query = query.filter_by(source=source_filter)
    
    logs = query.order_by(SystemLog.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs]
    }), 200