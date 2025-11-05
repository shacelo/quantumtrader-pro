# reset_database.py
import os
import sys
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

load_dotenv()

from app.models.base import Base, engine, drop_tables, create_tables

def reset_database():
    """Resetear completamente la base de datos"""
    print("🔄 Reseteando base de datos...")
    
    try:
        # Eliminar todas las tablas
        drop_tables()
        print("✅ Tablas eliminadas")
        
        # Crear tablas limpias
        create_tables()
        print("✅ Tablas creadas limpiamente")
        
        print("🎉 Base de datos reseteada exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_database()