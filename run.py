#!/usr/bin/env python3
"""
Script principal para ejecutar QuantumTrader Pro
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging (SOLO CONSOLA)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def main():
    """Función principal"""
    try:
        logger.info("Iniciando QuantumTrader Pro...")
        
        # Verificar variables de entorno críticas
        required_vars = ['SECRET_KEY', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                logger.warning(f"Variable de entorno {var} no configurada")
            else:
                if 'PASSWORD' in var:
                    logger.info(f"Variable {var} configurada: [OK]")
                else:
                    logger.info(f"Variable {var} configurada: {value}")
        
        # Importar y crear la aplicación
        from app import create_app, socketio
        
        logger.info("Creando aplicación Flask...")
        app = create_app()
        
        # Verificar conexión a la base de datos (sin crear tablas)
        with app.app_context():
            from app.core.database import db
            from sqlalchemy import text
            
            # Solo verificar que podemos conectar
            try:
                db.session.execute(text("SELECT 1"))
                logger.info("Conexión a base de datos verificada")
            except Exception as e:
                logger.error(f"Error conectando a la base de datos: {e}")
                sys.exit(1)
        
        # Iniciar servidor Flask con Socket.IO
        host = os.getenv('HOST', '127.0.0.1')
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Servidor iniciado en http://{host}:{port}")
        logger.info("Dashboard disponible en /dashboard")
        logger.info("Socket.IO habilitado con eventlet")
        
        # Usar socketio.run() en lugar de app.run() para WebSockets
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        logger.error(f"Error iniciando la aplicacion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()