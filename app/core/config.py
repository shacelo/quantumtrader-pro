# app/core/config.py - Configuración centralizada
import os
from typing import Dict, Any, List
import yaml
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base"""
    # App
    APP_NAME = os.getenv('APP_NAME', 'QuantumTrader Pro')
    APP_ENV = os.getenv('APP_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('APP_DEBUG', 'true').lower() == 'true'
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'quantumtrader')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Trading
    TRADING_MODE = os.getenv('TRADING_MODE', 'simulation')
    DEFAULT_EXCHANGE = os.getenv('DEFAULT_EXCHANGE', 'binance')
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', 3))
    BASE_CURRENCY = os.getenv('BASE_CURRENCY', 'USDT')
    
    # Risk Management
    MAX_DAILY_LOSS_PERCENT = float(os.getenv('MAX_DAILY_LOSS_PERCENT', 5.0))
    MAX_DRAWDOWN_PERCENT = float(os.getenv('MAX_DRAWDOWN_PERCENT', 10.0))
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', 20))
    
    # WebSocket
    WS_ENABLED = os.getenv('WS_ENABLED', 'true').lower() == 'true'
    WS_PING_INTERVAL = int(os.getenv('WS_PING_INTERVAL', 25))
    WS_PING_TIMEOUT = int(os.getenv('WS_PING_TIMEOUT', 10))
    
    @classmethod
    def load_trading_config(cls) -> Dict[str, Any]:
        """Cargar configuración de trading desde YAML"""
        config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            return cls.get_default_trading_config()
    
    @classmethod
    def get_default_trading_config(cls) -> Dict[str, Any]:
        """Configuración por defecto si no hay archivo YAML"""
        return {
            'trading': {
                'pairs': ['ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT', 'LTCUSDT', 'XRPUSDT'],
                'testnet': True,
                'real_trading': False,
                'max_simultaneous_positions': 3
            },
            'risk_management': {
                'stop_loss_percent': 1.5,
                'take_profit_percent': 3.0,
                'max_position_percent': 3.0
            }
        }
    
    @classmethod
    def get_available_pairs(cls) -> List[str]:
        """Obtener pares disponibles para trading"""
        config = cls.load_trading_config()
        return config.get('trading', {}).get('pairs', [])

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

def get_config():
    """Obtener configuración según entorno"""
    env = os.getenv('APP_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    return configs.get(env, DevelopmentConfig)