# app/websocket/connection_manager.py
import logging
from typing import Dict, Set
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.user_rooms: Dict[int, Set[str]] = {}  # user_id -> set of rooms
        self.setup_handlers()
    
    def setup_handlers(self):
        """Configura los handlers de WebSocket"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Maneja conexión de cliente"""
            if not current_user.is_authenticated:
                return False
            
            user_id = current_user.id
            user_room = f"user_{user_id}"
            
            join_room(user_room)
            
            # Registrar sala del usuario
            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(user_room)
            
            logger.info(f"🔗 Cliente WebSocket conectado - Usuario: {current_user.username}")
            emit('connection_status', {'status': 'connected', 'user_id': user_id})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Maneja desconexión de cliente"""
            if current_user.is_authenticated:
                user_id = current_user.id
                logger.info(f"🔌 Cliente WebSocket desconectado - Usuario: {current_user.username}")
                
                # Limpiar salas
                if user_id in self.user_rooms:
                    for room in self.user_rooms[user_id]:
                        leave_room(room)
                    del self.user_rooms[user_id]
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            """Une al cliente a una sala de sesión específica"""
            if not current_user.is_authenticated:
                return
            
            session_id = data.get('session_id')
            if session_id:
                room_name = f"session_{session_id}"
                join_room(room_name)
                
                user_id = current_user.id
                if user_id not in self.user_rooms:
                    self.user_rooms[user_id] = set()
                self.user_rooms[user_id].add(room_name)
                
                logger.info(f"📊 Usuario {user_id} unido a sesión: {session_id}")
                emit('session_joined', {'session_id': session_id})
    
    def send_to_user(self, user_id: int, event: str, data: dict):
        """Envía un evento a un usuario específico"""
        user_room = f"user_{user_id}"
        self.socketio.emit(event, data, room=user_room)
    
    def send_to_session(self, session_id: int, event: str, data: dict):
        """Envía un evento a todos los clientes de una sesión"""
        session_room = f"session_{session_id}"
        self.socketio.emit(event, data, room=session_room)
    
    def broadcast_log(self, session_id: int, log_data: dict):
        """Transmite un log en tiempo real"""
        self.send_to_session(session_id, 'log_entry', log_data)
    
    def broadcast_trade(self, session_id: int, trade_data: dict):
        """Transmite una operación en tiempo real"""
        self.send_to_session(session_id, 'trade_update', trade_data)
    
    def broadcast_balance(self, session_id: int, balance_data: dict):
        """Transmite actualización de balance"""
        self.send_to_session(session_id, 'balance_update', balance_data)