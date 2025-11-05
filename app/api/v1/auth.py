# app/api/v1/auth.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint para login de usuarios
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Datos JSON requeridos'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuario y contraseña requeridos'}), 400
    
    # Obtener información del cliente
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    result = AuthService.authenticate_user(username, password, ip_address, user_agent)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Endpoint para logout de usuarios
    """
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    result = AuthService.logout_user(ip_address, user_agent)
    return jsonify(result), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    Obtiene información del usuario actual
    """
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Cambia la contraseña del usuario actual
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Datos JSON requeridos'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Contraseñas requeridas'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
    
    result = AuthService.change_password(current_user.id, current_password, new_password)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@auth_bp.route('/sessions', methods=['GET'])
@login_required
def get_user_sessions():
    """
    Obtiene el historial de sesiones del usuario
    """
    days = request.args.get('days', 30, type=int)
    sessions = AuthService.get_user_sessions(current_user.id, days)
    
    return jsonify({
        'success': True,
        'sessions': sessions
    }), 200