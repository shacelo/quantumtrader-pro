# models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración para base 'postgres'
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency para FastAPI/Flask"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def session_scope():
    """Context manager para sesiones de base de datos"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def create_tables():
    """Crear todas las tablas en la base de datos - solo si no existen"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas verificadas/creadas exitosamente")
    except Exception as e:
        print(f"⚠️  Error creando tablas: {e}")

def drop_tables():
    """Eliminar todas las tablas (solo desarrollo)"""
    Base.metadata.drop_all(bind=engine)