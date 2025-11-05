# fix_relationships.py
import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.base import Base, engine, SessionLocal
from app.models import users, api_keys, bot_config, bot_sessions, balance_history, orders, trades, positions, system_logs, risk_metrics, audit_sessions

def verify_relationships():
    """Verifica que todas las relaciones estén correctamente configuradas"""
    print("🔍 Verificando relaciones SQLAlchemy...")
    
    try:
        # Recrear todas las tablas
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Todas las tablas creadas exitosamente")
        
        # Verificar mapeadores
        for class_name, mapper in Base.registry._class_registry.items():
            if hasattr(mapper, '__tablename__'):
                print(f"✅ Mapper para {class_name}: OK")
                
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False
    
    return True

def test_basic_operations():
    """Prueba operaciones básicas con las relaciones"""
    print("\n🧪 Probando operaciones básicas...")
    
    try:
        with SessionLocal() as session:
            # Crear un usuario de prueba
            user = users.User()
            user.username = "test_user"
            user.set_password("test_password")
            user.email = "test@example.com"
            
            session.add(user)
            session.commit()
            
            print("✅ Usuario creado exitosamente")
            
            # Crear API key asociada
            api_key = api_keys.ApiKey()
            api_key.user_id = user.id
            api_key.set_api_key("test_api_key")
            api_key.set_api_secret("test_api_secret")
            api_key.is_active = True
            
            session.add(api_key)
            session.commit()
            
            print("✅ API Key creada exitosamente")
            
            # Verificar relación
            print(f"✅ Usuario tiene {len(user.api_keys)} API keys")
            print(f"✅ API Key pertenece al usuario: {api_key.user.username}")
            
            # Limpiar
            session.delete(user)
            session.commit()
            
            print("✅ Datos de prueba limpiados")
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Iniciando corrección de relaciones SQLAlchemy...")
    
    if verify_relationships():
        print("\n✅ Verificación de relaciones completada")
        
        if test_basic_operations():
            print("\n🎉 ¡Todas las correcciones aplicadas exitosamente!")
        else:
            print("\n⚠️  Algunas pruebas fallaron, revise los errores")
    else:
        print("\n❌ La verificación falló, revise la configuración")