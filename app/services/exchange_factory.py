import logging
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class ExchangeFactory:
    @staticmethod
    def create_exchange(exchange_name, api_key=None, secret_key=None, paper_trading=True):
        """
        Crea conexión real con Binance
        """
        # Si no se pasan keys, intentar cargar de .env
        if not api_key:
            api_key = os.getenv('BINANCE_API_KEY', '')
        if not secret_key:
            secret_key = os.getenv('BINANCE_API_SECRET', '')  # Nombre correcto de la variable
        
        if not api_key or not secret_key:
            raise ValueError("Se requieren API Key y Secret Key para Binance")
        
        try:
            if paper_trading:
                # TESTNET - Modo simulación/demo
                client = Client(api_key, secret_key, testnet=True)
                logger.info("🔶 Conectado a Binance TESTNET (modo simulación/demo)")
            else:
                # BINANCE REAL - Trading en vivo
                client = Client(api_key, secret_key, testnet=False)
                logger.info("🚀 Conectado a Binance REAL (trading en vivo)")
            
            # Verificar conexión
            account_info = client.get_account()
            logger.info(f"Cuenta conectada: {account_info['accountType']}")
            return client
            
        except BinanceAPIException as e:
            logger.error(f"❌ Error de Binance: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise