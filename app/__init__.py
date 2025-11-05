# app/__init__.py - Factory de la aplicación
import os
from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_cors import CORS
import logging

# Extensions
socketio = SocketIO()
login_manager = LoginManager()
db = None  # Será inicializado según el ORM

def create_app(config_class=None):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración
    if config_class:
        app.config.from_object(config_class)
    else:
        # Configuración por defecto
        app.config.update(
            SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
            SQLALCHEMY_DATABASE_URI=(
                f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
                f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
            ),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SQLALCHEMY_ENGINE_OPTIONS={
                'pool_size': 20,
                'max_overflow': 30,
                'pool_pre_ping': True,
                'pool_recycle': 300
            }
        )
    
    # Inicializar extensiones
    initialize_extensions(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar handlers de error
    register_error_handlers(app)
    
    # Registrar comandos CLI
    register_commands(app)
    
    # Configurar logging
    setup_app_logging(app)
    
    return app

def initialize_extensions(app):
    """Inicializar todas las extensiones"""
    # CORS
    CORS(app)
    
    # Database
    from app.core.database import init_db
    global db
    db = init_db(app)
    
    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    
    # Socket.IO
    socketio.init_app(
        app, 
        cors_allowed_origins="*",
        async_mode='eventlet',
        ping_interval=int(os.getenv('WS_PING_INTERVAL', 25)),
        ping_timeout=int(os.getenv('WS_PING_TIMEOUT', 10))
    )
    
    # User loader para Flask-Login
    from app.models.users import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

def register_blueprints(app):
    """Registrar todos los blueprints de la API"""
    
    try:
        print("=== INICIANDO REGISTRO DE BLUEPRINTS ===")
        
        # Blueprints que SÍ existen
        from app.api.v1.auth import auth_bp
        from app.api.v1.bot_control import bot_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        print("✅ Blueprint auth registrado: /api/auth")
        
        app.register_blueprint(bot_bp, url_prefix='/api/bot')
        print("✅ Blueprint bot registrado: /api/bot")
        
        # Verificar rutas registradas
        print("Rutas registradas:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.rule} -> {rule.endpoint}")
        
        # Intentar registrar blueprints opcionales si existen
        try:
            from app.api.v1.trading import trading_bp
            app.register_blueprint(trading_bp, url_prefix='/api/trading')
            print("✅ Blueprint trading registrado: /api/trading")
        except ImportError as e:
            print(f"❌ Blueprint trading no encontrado - omitiendo: {e}")
            
        try:
            from app.api.v1.analysis import analysis_bp
            app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
            print("✅ Blueprint analysis registrado: /api/analysis")
        except ImportError as e:
            print(f"❌ Blueprint analysis no encontrado - omitiendo: {e}")
            
        try:
            from app.api.v1.portfolio import portfolio_bp
            app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
            print("✅ Blueprint portfolio registrado: /api/portfolio")
        except ImportError as e:
            print(f"❌ Blueprint portfolio no encontrado - omitiendo: {e}")
            
        print("=== REGISTRO DE BLUEPRINTS COMPLETADO ===")
            
    except Exception as e:
        print(f"❌ Error registrando blueprints: {e}")
        raise

def register_error_handlers(app):
    """Registrar handlers de error"""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Recurso no encontrado'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Error interno del servidor: {error}')
        return {'error': 'Error interno del servidor'}, 500
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'No autorizado'}, 401

def register_commands(app):
    """Registrar comandos CLI"""
    @app.cli.command('init-db')
    def init_db_command():
        """Inicializar la base de datos"""
        from app.core.database import init_db
        init_db(app)
        print('✅ Base de datos inicializada.')
    
    @app.cli.command('create-user')
    def create_user_command():
        """Crear un usuario nuevo"""
        from app.services.auth_service import AuthService
        # Implementar creación de usuario
        print('Comando create-user implementado.')

def setup_app_logging(app):
    """Configurar el sistema de logging para la aplicación"""
    import os
    from pathlib import Path
    
    # Crear directorio logs en la raíz del proyecto si no existe
    project_root = Path(__file__).parent.parent  # Raíz del proyecto
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / 'quantumtrader.log'
    
    # Configurar file handler
    try:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024 * 100,  # 100MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Agregar handler al logger de la app
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        
        app.logger.info(f"Logging configurado en: {log_file}")
        
    except Exception as e:
        # Si hay error con file logging, usar solo consola
        app.logger.warning(f"No se pudo configurar file logging: {e}")
        app.logger.info("Usando logging por consola solamente")

# Exportar la aplicación y socketio para uso externo
__all__ = ['create_app', 'socketio', 'db', 'login_manager']