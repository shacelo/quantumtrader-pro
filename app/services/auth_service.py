# app/services/auth_service.py
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app
from flask_login import login_user, logout_user, current_user
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import db
from app.models.users import User
from app.models.audit_sessions import AuditSession

logger = logging.getLogger(__name__)

class AuthService:
    """Servicio para manejar autenticación y autorización"""
    
    @staticmethod
    def authenticate_user(username: str, password: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Autentica un usuario y registra la sesión de auditoría
        """
        try:
            # Buscar usuario activo
            user = User.query.filter_by(username=username, is_active=True).first()
            
            if not user:
                AuthService._log_audit_action(
                    user_id=None,
                    action_type='login_failed',
                    action_details={'username': username, 'reason': 'user_not_found'},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status='failed'
                )
                return {'success': False, 'message': 'Credenciales inválidas'}
            
            # Verificar contraseña
            if not user.check_password(password):
                AuthService._log_audit_action(
                    user_id=user.id,
                    action_type='login_failed',
                    action_details={'username': username, 'reason': 'invalid_password'},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status='failed'
                )
                return {'success': False, 'message': 'Credenciales inválidas'}
            
            # Actualizar último login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Iniciar sesión
            login_user(user)
            
            # Log de auditoría exitoso
            AuthService._log_audit_action(
                user_id=user.id,
                action_type='login_success',
                action_details={'username': username},
                ip_address=ip_address,
                user_agent=user_agent,
                status='success'
            )
            
            logger.info(f"✅ Usuario autenticado: {username}")
            return {
                'success': True,
                'message': 'Login exitoso',
                'user': user.to_dict()
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"❌ Error de base de datos en autenticación: {e}")
            return {'success': False, 'message': 'Error del sistema'}
        except Exception as e:
            logger.error(f"❌ Error inesperado en autenticación: {e}")
            return {'success': False, 'message': 'Error del sistema'}
    
    @staticmethod
    def logout_user(ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Cierra la sesión del usuario actual
        """
        try:
            if current_user.is_authenticated:
                user_id = current_user.id
                username = current_user.username
                
                # Log de auditoría
                AuthService._log_audit_action(
                    user_id=user_id,
                    action_type='logout',
                    action_details={'username': username},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status='success'
                )
                
                logout_user()
                logger.info(f"🔒 Usuario desconectado: {username}")
                return {'success': True, 'message': 'Logout exitoso'}
            else:
                return {'success': False, 'message': 'No hay usuario autenticado'}
                
        except Exception as e:
            logger.error(f"❌ Error en logout: {e}")
            return {'success': False, 'message': 'Error en logout'}
    
    @staticmethod
    def create_user(username: str, password: str, email: str, role: str = 'user') -> Dict[str, Any]:
        """
        Crea un nuevo usuario
        """
        try:
            # Verificar si el usuario ya existe
            if User.query.filter_by(username=username).first():
                return {'success': False, 'message': 'El usuario ya existe'}
            
            if email and User.query.filter_by(email=email).first():
                return {'success': False, 'message': 'El email ya está registrado'}
            
            # Crear nuevo usuario
            user = User(
                username=username,
                email=email,
                role=role
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"👤 Nuevo usuario creado: {username} ({role})")
            return {
                'success': True,
                'message': 'Usuario creado exitosamente',
                'user': user.to_dict()
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"❌ Error creando usuario: {e}")
            return {'success': False, 'message': 'Error creando usuario'}
    
    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Cambia la contraseña de un usuario
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'Usuario no encontrado'}
            
            # Verificar contraseña actual
            if not user.check_password(current_password):
                return {'success': False, 'message': 'Contraseña actual incorrecta'}
            
            # Establecer nueva contraseña
            user.set_password(new_password)
            db.session.commit()
            
            logger.info(f"🔑 Contraseña cambiada para usuario: {user.username}")
            return {'success': True, 'message': 'Contraseña cambiada exitosamente'}
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"❌ Error cambiando contraseña: {e}")
            return {'success': False, 'message': 'Error cambiando contraseña'}
    
    @staticmethod
    def _log_audit_action(user_id: Optional[int], action_type: str, action_details: Dict, 
                         ip_address: str = None, user_agent: str = None, status: str = 'success'):
        """
        Registra una acción en la auditoría
        """
        try:
            audit_log = AuditSession(
                user_id=user_id,
                action_type=action_type,
                action_details=action_details,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"❌ Error registrando auditoría: {e}")
            db.session.rollback()
    
    @staticmethod
    def get_user_sessions(user_id: int, days: int = 30) -> list:
        """
        Obtiene las sesiones de un usuario en los últimos días
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            sessions = AuditSession.query.filter(
                AuditSession.user_id == user_id,
                AuditSession.timestamp >= since_date,
                AuditSession.action_type.in_(['login_success', 'logout'])
            ).order_by(AuditSession.timestamp.desc()).all()
            
            return [session.to_dict() for session in sessions]
        except Exception as e:
            logger.error(f"❌ Error obteniendo sesiones: {e}")
            return []