# main.py - VERSIÓN CORREGIDA
import os
import sys
import socket
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la ruta ABSOLUTA del directorio actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

print("🚀 INICIANDO QUANTUMTRADER PRO")
print(f"📁 Directorio base: {BASE_DIR}")
print(f"📁 Templates: {TEMPLATES_DIR}")
print(f"📁 Static: {STATIC_DIR}")

# Configuración de la aplicación Flask
app = Flask(__name__, 
           template_folder=TEMPLATES_DIR,
           static_folder=STATIC_DIR)

app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key-for-dev-12345')

# Configurar SocketIO SIN eventlet
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading')  # Usar threading en lugar de eventlet

CORS(app)

# Importar modelos
try:
    from app.models.base import get_db, create_tables, session_scope
    from app.models.users import User
    print("✅ Modelos importados correctamente")
except Exception as e:
    print(f"❌ Error importando modelos: {e}")
    sys.exit(1)

# CONTEXT PROCESSOR PARA INYECTAR 'now' EN TODOS LOS TEMPLATES
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Crear tablas al inicio
@app.before_request
def create_tables_on_startup():
    """Crear tablas si no existen"""
    try:
        if not hasattr(app, 'tables_created'):
            print("🔄 Creando tablas de base de datos...")
            create_tables()
            print("✅ Tablas creadas exitosamente")
            
            # Crear usuario demo si no existe
            try:
                with session_scope() as db:
                    user = db.query(User).filter(User.username == "admin").first()
                    if not user:
                        print("👤 Creando usuario demo...")
                        demo_user = User(
                            username="admin",
                            email="admin@example.com",
                            role="admin",
                            is_active=True
                        )
                        demo_user.set_password("admin123")
                        db.add(demo_user)
                        print("✅ Usuario demo creado: admin/admin123")
            except Exception as e:
                print(f"⚠️  Error creando usuario demo: {e}")
            
            app.tables_created = True
            logger.info("✅ Sistema de base de datos inicializado")
    except Exception as e:
        logger.error(f"❌ Error crítico en base de datos: {e}")

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# API Routes
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "QuantumTrader Pro",
        "timestamp": datetime.now().isoformat()
    })

# ENDPOINT DE LOGIN
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Endpoint de autenticación"""
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Content-Type debe ser application/json"}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Datos JSON requeridos"}), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        logger.info(f"🔐 Intento de login para: {username}")
        
        if not username or not password:
            return jsonify({"success": False, "message": "Usuario y contraseña requeridos"}), 400
        
        try:
            with session_scope() as db:
                user = db.query(User).filter(User.username == username).first()
                
                if not user:
                    logger.warning(f"❌ Usuario no encontrado: {username}")
                    return jsonify({"success": False, "message": "Credenciales inválidas"}), 401
                
                if not user.check_password(password):
                    logger.warning(f"❌ Contraseña incorrecta para: {username}")
                    return jsonify({"success": False, "message": "Credenciales inválidas"}), 401
                
                if not user.is_active:
                    return jsonify({"success": False, "message": "Usuario desactivado"}), 401
                    
                # Login exitoso
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                
                # Actualizar último login
                user.last_login = datetime.utcnow()
                
                logger.info(f"✅ Login exitoso: {username} (ID: {user.id})")
                
                return jsonify({
                    "success": True,
                    "message": "Login exitoso",
                    "user": user.to_dict()
                })
                
        except Exception as db_error:
            logger.error(f"❌ Error de base de datos en login: {db_error}")
            return jsonify({"success": False, "message": "Error de base de datos"}), 500
                
    except Exception as e:
        logger.error(f"❌ Error inesperado en login: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Error interno del servidor"}), 500

@app.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logout exitoso"})

# Endpoints básicos para el dashboard
@app.route('/api/v1/bot/start', methods=['POST'])
def start_bot():
    return jsonify({
        "success": True,
        "message": "Bot iniciado en modo simulation",
        "session_id": 1,
        "status": "running"
    })

@app.route('/api/v1/bot/stop', methods=['POST'])
def stop_bot():
    return jsonify({
        "success": True,
        "message": "Bot detenido",
        "status": "stopped"
    })

# ENDPOINT CORREGIDO - dashboard.js espera /dashboard/data
@app.route('/dashboard/data')
def dashboard_data():
    """Endpoint que espera dashboard.js"""
    return jsonify({
        "success": True,
        "balance": {
            "current_balance": 10250.50,
            "total_pnl": 250.50,
            "total_pnl_percent": 2.5,
            "history": [
                {"time": "09:00", "balance": 10000, "pnl": 0},
                {"time": "10:00", "balance": 10050, "pnl": 50},
                {"time": "11:00", "balance": 10100, "pnl": 100},
                {"time": "12:00", "balance": 10180, "pnl": 180},
                {"time": "13:00", "balance": 10250.50, "pnl": 250.50}
            ]
        },
        "trading": {
            "total_trades": 15,
            "real_trades": 5,
            "simulated_trades": 10,
            "winning_trades": 9,
            "losing_trades": 6,
            "win_rate": 60.0,
            "recent_trades": [
                {
                    "symbol": "BTCUSDT",
                    "entry_price": 34500.50,
                    "exit_price": 34620.75,
                    "pnl": 120.25,
                    "status": "WIN",
                    "real_trade": True,
                    "exit_time": datetime.now().isoformat(),
                    "close_reason": "TP_HIT"
                },
                {
                    "symbol": "ETHUSDT",
                    "entry_price": 1850.25,
                    "exit_price": 1840.50,
                    "pnl": -9.75,
                    "status": "LOSS",
                    "real_trade": False,
                    "exit_time": datetime.now().isoformat(),
                    "close_reason": "SL_HIT"
                }
            ]
        },
        "positions": {
            "active_positions": 2,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "entry_price": 34520.25,
                    "current_price": 34650.80,
                    "quantity": 0.002,
                    "unrealized_pnl": 26.11,
                    "unrealized_pnl_percent": 0.38,
                    "stop_loss": 34300.00,
                    "take_profit": 34800.00,
                    "real_trade": True
                },
                {
                    "symbol": "ETHUSDT",
                    "entry_price": 1845.50,
                    "current_price": 1852.25,
                    "quantity": 0.05,
                    "unrealized_pnl": 0.34,
                    "unrealized_pnl_percent": 0.04,
                    "stop_loss": 1830.00,
                    "take_profit": 1870.00,
                    "real_trade": False
                }
            ]
        },
        "session": {
            "status": "stopped",
            "trading_mode": "simulation"
        },
        "timestamp": datetime.now().isoformat()
    })

# WebSocket events (simplificados)
@socketio.on('connect')
def handle_connect():
    logger.info('✅ Cliente conectado via WebSocket')
    return {'status': 'connected'}

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('🔌 Cliente desconectado')

def find_available_port(start_port=5000, max_port=5010):
    """Encuentra un puerto disponible"""
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise OSError("No se encontró ningún puerto disponible")

if __name__ == '__main__':
    logger.info("🚀 Iniciando QuantumTrader Pro...")
    
    # Encontrar puerto disponible
    PORT = find_available_port()
    logger.info(f"🌐 Usando puerto: {PORT}")
    
    print(f"\n📍 ACCESO A LA APLICACIÓN:")
    print(f"   📱 Local: http://localhost:{PORT}")
    print(f"   🔧 Debug: http://localhost:{PORT}/debug")
    print(f"   🔐 Login: http://localhost:{PORT}/login")
    print(f"   📊 Dashboard: http://localhost:{PORT}/dashboard")
    print(f"   ❤️  Health: http://localhost:{PORT}/api/health")
    print(f"\n👤 Credenciales de prueba:")
    print(f"   Usuario: admin")
    print(f"   Contraseña: admin123")
    
    # Ejecutar SIN eventlet
    socketio.run(app, 
                host='0.0.0.0', 
                port=PORT, 
                debug=True, 
                allow_unsafe_werkzeug=True)
    
    # Al final de main.py agregar:
def main():
    """Función principal para run.py"""
    # El código de inicialización que ya tienes
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = main()
    app.run(host='127.0.0.1', port=5000, debug=True)