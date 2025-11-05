# check_imports.py
import os
import sys

def check_all_imports():
    """Verifica que todas las importaciones funcionen"""
    print("🔍 Verificando importaciones...")
    
    # Agregar el directorio raíz al path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    imports_to_check = [
        "app.models.base",
        "app.models.users", 
        "app.models.api_keys",
        "app.models.bot_config",
        "app.models.bot_sessions",
        "app.models.balance_history",
        "app.models.orders",
        "app.models.trades",
        "app.models.positions",
        "app.models.system_logs",
        "app.models.risk_metrics",
        "app.models.audit_sessions",
        "app.core.database",
        "app.core.config"
    ]
    
    errors = []
    for import_path in imports_to_check:
        try:
            __import__(import_path)
            print(f"✅ {import_path}")
        except ImportError as e:
            print(f"❌ {import_path}: {e}")
            errors.append(f"{import_path}: {e}")
        except Exception as e:
            print(f"⚠️  {import_path}: {e}")
            errors.append(f"{import_path}: {e}")
    
    print(f"\n📊 Resultado: {len(errors)} errores de {len(imports_to_check)} importaciones")
    
    if errors:
        print("\n❌ Errores encontrados:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("🎉 ¡Todas las importaciones funcionan correctamente!")
        return True

if __name__ == "__main__":
    success = check_all_imports()
    sys.exit(0 if success else 1)