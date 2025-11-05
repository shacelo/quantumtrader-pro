# test_database.py
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.base import SessionLocal, create_tables
from app.models.users import User

print("🔍 DIAGNÓSTICO DE BASE DE DATOS")

try:
    # Crear tablas
    print("🔄 Creando tablas...")
    create_tables()
    print("✅ Tablas creadas")
    
    # Verificar conexión
    with SessionLocal() as db:
        print("✅ Conexión a BD exitosa")
        
        # Verificar usuarios
        users = db.query(User).all()
        print(f"👥 Usuarios en BD: {len(users)}")
        
        for user in users:
            print(f"   - {user.username} ({user.email})")
            
        # Crear usuario admin si no existe
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("👤 Creando usuario admin...")
            admin = User(
                username="admin",
                email="admin@example.com", 
                role="admin",
                is_active=True
            )
            admin.set_password("admin123")
            db.add(admin)
            db.commit()
            print("✅ Usuario admin creado")
        else:
            print("✅ Usuario admin ya existe")
            
except Exception as e:
    print(f"❌ Error en base de datos: {e}")
    import traceback
    traceback.print_exc()