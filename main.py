# main.py - VERSIÓN CORREGIDA
import eventlet
eventlet.monkey_patch(os=True, select=True, socket=True, thread=True, time=True)

# Importaciones después del monkey patch
import os
import sys
import socket
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from flask_cors import CORS

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

# Configurar SocketIO con eventlet
socketio = SocketIO(app,
                   cors_allowed_origins="*",
                   async_mode='eventlet',
                   ping_timeout=10,
                   ping_interval=5,
                   always_connect=True,
                   logger=True,
                   engineio_logger=True)

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
    # Obtener usuario logueado
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "No autenticado"}), 401

    from app.models.bot_sessions import BotSession
    from app.models.trades import Trade
    from app.models.positions import Position
    from app.models.balance_history import BalanceHistory
    from app.models.users import User
    from app.models.orders import Order
    from app.models.base import session_scope

    with session_scope() as db:
        # Buscar la última sesión activa del usuario
        bot_session = db.query(BotSession).filter(BotSession.user_id == user_id).order_by(BotSession.start_time.desc()).first()
        if not bot_session:
            return jsonify({"success": True, "message": "No hay sesión de bot activa", "balance": {}, "trading": {}, "positions": {}, "session": {}})

        # Balance
        balance_history = db.query(BalanceHistory).filter(BalanceHistory.session_id == bot_session.id).order_by(BalanceHistory.timestamp.asc()).all()
        balance_list = [bh.to_dict() for bh in balance_history]
        current_balance = float(bot_session.final_balance) if bot_session.final_balance else float(bot_session.initial_balance)
        total_pnl = current_balance - float(bot_session.initial_balance)
        total_pnl_percent = (total_pnl / float(bot_session.initial_balance)) * 100 if bot_session.initial_balance else 0.0

        # Trades
        trades = db.query(Trade).filter(Trade.session_id == bot_session.id).order_by(Trade.entry_time.desc()).limit(10).all()
        recent_trades = []
        winning_trades = 0
        losing_trades = 0
        real_trades = 0
        simulated_trades = 0
        for t in trades:
            if t.pnl and t.pnl > 0:
                winning_trades += 1
            elif t.pnl and t.pnl < 0:
                losing_trades += 1
            if t.real_trade:
                real_trades += 1
            else:
                simulated_trades += 1
            recent_trades.append({
                "symbol": t.symbol,
                "entry_price": float(t.entry_price),
                "exit_price": float(t.exit_price) if t.exit_price else None,
                "pnl": float(t.pnl) if t.pnl else 0.0,
                "status": "WIN" if t.pnl and t.pnl > 0 else "LOSS",
                "real_trade": t.real_trade,
                "exit_time": t.exit_time.isoformat() if t.exit_time else None,
                "close_reason": t.close_reason
            })
        total_trades = len(trades)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0

        # Posiciones
        positions = db.query(Position).filter(Position.session_id == bot_session.id).all()
        active_positions = len(positions)
        positions_list = []
        for p in positions:
            positions_list.append({
                "symbol": p.symbol,
                "entry_price": float(p.entry_price),
                "current_price": float(p.current_price),
                "quantity": float(p.quantity),
                "unrealized_pnl": float(p.unrealized_pnl),
                "unrealized_pnl_percent": float(p.unrealized_pnl_percent),
                "stop_loss": float(p.stop_loss),
                "take_profit": float(p.take_profit),
                "real_trade": db.query(Trade).filter(Trade.id == p.trade_id).first().real_trade if p.trade_id else False
            })

        # Sesión
        session_info = {
            "status": bot_session.status,
            "trading_mode": bot_session.trading_mode
        }

        return jsonify({
            "success": True,
            "balance": {
                "current_balance": current_balance,
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent,
                "history": balance_list
            },
            "trading": {
                "total_trades": total_trades,
                "real_trades": real_trades,
                "simulated_trades": simulated_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "recent_trades": recent_trades
            },
            "positions": {
                "active_positions": active_positions,
                "positions": positions_list
            },
            "session": session_info,
            "timestamp": datetime.now().isoformat()
        })

# WebSocket events (simplificados)
@socketio.on('connect')
def handle_connect():
    """Manejador de conexión de clientes WebSocket"""
    logger.info('✅ Cliente conectado via WebSocket')
    socketio.emit('connection_status', {'status': 'connected'})
    return True

@socketio.on('disconnect')
def handle_disconnect(reason):
    """Manejador de desconexión de clientes WebSocket"""
    logger.info(f'🔌 Cliente desconectado: {reason}')

@socketio.event
def market_data_request(data):
    """Manejador de solicitudes de datos de mercado"""
    try:
        symbol = data.get('symbol', 'BTCUSDT')
        # Aquí implementaremos la lógica para enviar datos de mercado
        socketio.emit('market_data', {
            'symbol': symbol,
            'status': 'requesting_data'
        })
    except Exception as e:
        logger.error(f'❌ Error procesando solicitud de datos: {str(e)}')

@socketio.on_error()
def error_handler(e):
    """Manejador general de errores de WebSocket"""
    logger.error(f'❌ Error en WebSocket: {str(e)}')
    return False

@socketio.on_error_default
def default_error_handler(e):
    """Manejador por defecto de errores de WebSocket"""
    logger.error(f'❌ Error por defecto en WebSocket: {str(e)}')
    return False

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
    
    # Ejecutar con eventlet
    socketio.run(app,
                host='0.0.0.0', 
                port=PORT,
                debug=True)
    # Ejecuta la app con SocketIO y todos los endpoints registrados
    # Para iniciar, usa:
    #   python quantumtrader-pro/main.py