# test_postgres.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Configuración para base 'postgres'
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def test_postgres_connection():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            print(f"✅ PostgreSQL version: {result.fetchone()[0]}")
            
            # Verificar si las tablas existen
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"📊 Tablas existentes: {tables}")
            
        return True
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    test_postgres_connection()