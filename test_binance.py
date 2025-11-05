import os
import sys
import asyncio
import json
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime
import logging
from dotenv import load_dotenv
import websockets
import signal

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BinanceTest:
    def __init__(self):
        self.client = None
        self.ws = None
        self.running = True
        
        # Configurar el manejo de señales para cerrar limpiamente
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        logger.info("Cerrando conexiones...")
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())
        sys.exit(0)

    async def test_rest_api(self):
        """Prueba la conexión REST API"""
        try:
            # Obtener tiempo del servidor
            server_time = self.client.get_server_time()
            logger.info(f"✅ Tiempo del servidor: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
            
            # Obtener información de la cuenta
            account = self.client.get_account()
            logger.info(f"✅ Tipo de cuenta: {account['accountType']}")
            
            # Obtener precios actuales
            prices = self.client.get_all_tickers()
            btc_price = next(price for price in prices if price['symbol'] == 'BTCUSDT')
            eth_price = next(price for price in prices if price['symbol'] == 'ETHUSDT')
            
            logger.info(f"💰 Precio BTC: ${float(btc_price['price']):.2f}")
            logger.info(f"💰 Precio ETH: ${float(eth_price['price']):.2f}")
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"❌ Error de Binance API: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return False

    async def handle_websocket(self):
        """Maneja la conexión WebSocket"""
        stream_url = "wss://testnet.binance.vision/ws/btcusdt@kline_1m/ethusdt@kline_1m"
        
        try:
            async with websockets.connect(stream_url) as websocket:
                self.ws = websocket
                logger.info("🔌 Conexión WebSocket establecida")
                
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        if data.get('e') == 'kline':
                            symbol = data['s']
                            kline = data['k']
                            close_price = float(kline['c'])
                            high_price = float(kline['h'])
                            low_price = float(kline['l'])
                            volume = float(kline['v'])
                            logger.info(f"📊 {symbol} - Precio: ${close_price:.2f} | Alto: ${high_price:.2f} | Bajo: ${low_price:.2f} | Vol: {volume:.2f}")
                            
                    except asyncio.TimeoutError:
                        # Timeout es normal, continuamos
                        continue
                    except Exception as e:
                        logger.error(f"❌ Error procesando mensaje: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"❌ Error de conexión WebSocket: {e}")
            return False
            
        return True

    async def run_tests(self):
        """Ejecuta todas las pruebas"""
        try:
            # Cargar variables de entorno
            load_dotenv()
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')  # Cambiado para coincidir con .env

            if not api_key or not api_secret:
                logger.error("❌ No se encontraron credenciales en .env")
                return False

            # Inicializar cliente
            self.client = Client(api_key, api_secret, testnet=True)
            logger.info("✅ Cliente Binance inicializado")

            # Probar REST API
            if not await self.test_rest_api():
                return False

            # Probar WebSocket
            logger.info("🔄 Iniciando prueba de WebSocket (durará 60 segundos)...")
            try:
                await asyncio.wait_for(self.handle_websocket(), timeout=60)
            except asyncio.TimeoutError:
                logger.info("✅ Prueba de WebSocket completada")

            return True

        except Exception as e:
            logger.error(f"❌ Error en las pruebas: {e}")
            return False

async def main():
    print("\n🔍 Iniciando pruebas de conexión con Binance...\n")
    
    tester = BinanceTest()
    success = await tester.run_tests()
    
    if success:
        print("\n✅ Todas las pruebas completadas exitosamente!")
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa los logs para más detalles.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")