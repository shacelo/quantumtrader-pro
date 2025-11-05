import logging
import time
import os
from datetime import datetime
from typing import Optional, List
import json
import threading

from app import db, socketio
from app.models.bot_sessions import BotSession
from app.models.system_logs import SystemLog
from app.models.trades import Trade
from app.services.exchange_factory import ExchangeFactory
from app.services.data_service import DataService

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BotService:
    _active_bots = {}  # user_id -> bot instance
    
    def __init__(self, user_id: int, trading_mode: str = 'simulation', config_id: Optional[int] = None):
        self.user_id = user_id
        self.trading_mode = trading_mode
        self.config_id = config_id
        self.exchange = None
        self.data_service = DataService()
        self.is_running = False
        self.current_session = None
        self.trades = []
        self.websocket_manager = None
        self.last_kline_data = {}
        
        # Cargar variables de entorno
        from dotenv import load_dotenv
        load_dotenv()
        
        # Obtener credenciales de Binance
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.is_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        if not self.api_key or not self.api_secret:
            logger.error("❌ No se encontraron credenciales de Binance en .env")
            raise ValueError("Se requieren credenciales de Binance para operar")

        # Inicializar el exchange
        self.initialize_exchange()
        
        # Cargar config.yaml para estrategias
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config_yaml = yaml.safe_load(f)

        trading_cfg = self.config_yaml.get('trading', {})
        self.testnet = trading_cfg.get('testnet', True)
        self.real_trading = trading_cfg.get('real_trading', False)
        self.available_pairs = trading_cfg.get('available_pairs', ['BTCUSDT'])
        self.base_currency = trading_cfg.get('base_currency', 'USDT')
        self.max_simultaneous_positions = trading_cfg.get('max_simultaneous_positions', 3)

        strategies_cfg = self.config_yaml.get('strategies', {}).get('available', {})
        self.strategy_name = self.config_yaml.get('strategies', {}).get('default', 'quantum_v1')
        self.strategy_params = strategies_cfg.get(self.strategy_name, {})

        logger.info(f"BotService creado para user {user_id} modo {trading_mode} | testnet={self.testnet} | estrategia={self.strategy_name}")

    # ==================== LOGGING + SOCKET ====================

    def _emit_log(self, level, message):
        """
        Envía logs a BD + Websocket al dashboard
        """
        try:
            log_entry = SystemLog(
                user_id=self.user_id,
                session_id=self.current_session.id if self.current_session else None,
                level=level.upper(),
                source="bot_service",
                message=message
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error guardando log BD: {e}")

        try:
            socketio.emit(
                "bot_log",
                {
                    "user_id": self.user_id,
                    "session_id": self.current_session.id if self.current_session else None,
                    "level": level,
                    "message": message,
                    "time": datetime.utcnow().isoformat()
                },
                namespace=f"/logs/{self.user_id}"
            )
        except Exception as e:
            logger.error(f"Socket emit error: {e}")

    # ==================== START BOT ====================

    def start(self):
        try:
            # Crear sesión
            self.current_session = BotSession(
                user_id=self.user_id,
                trading_mode=self.trading_mode,
                config_id=self.config_id,
                status='starting',
                started_at=datetime.utcnow(),
                configuration=json.dumps({
                    'trading_mode': self.trading_mode,
                    'config_id': self.config_id,
                    'start_time': datetime.utcnow().isoformat()
                })
            )
            db.session.add(self.current_session)
            db.session.commit()

            self._emit_log("INFO", "Iniciando bot...")

            # Configurar modo testnet basado en trading_mode y config
            is_paper_trading = self.testnet or (self.trading_mode != 'real')
            
            # Solo inicializar exchange si no existe
            if not self.exchange:
                self.exchange = ExchangeFactory.create_exchange(
                    'binance',
                    self.api_key,
                    self.api_secret,
                    paper_trading=is_paper_trading
                )

            self.is_running = True
            self.current_session.status = 'running'
            db.session.commit()

            # Lanza loop en thread
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()

            self._emit_log("SUCCESS", "Bot iniciado correctamente")

            return {"success": True, "message": "Bot iniciado", "session_id": self.current_session.id}

        except Exception as e:
            err = f"Error iniciando bot: {e}"
            logger.error(err)
            self._emit_log("ERROR", err)

            if self.current_session:
                self.current_session.status = 'error'
                self.current_session.error_message = str(e)
                db.session.commit()

            return {"success": False, "message": err}

    # ==================== LOOP ====================

    def _trading_loop(self):
        self._emit_log("INFO", "Loop de trading iniciado")
        
        # Inicializar conexión con Binance
        if not self.initialize_exchange():
            self._emit_log("ERROR", "No se pudo iniciar la conexión con Binance")
            return

        iteration = 0
        wait_time = int(os.getenv("BOT_WAIT_TIME", 10))  # default 10s para pruebas

        while self.is_running:
            try:
                iteration += 1
                self._emit_log("INFO", f"Iteración #{iteration}")

                # Usar datos en tiempo real de Binance
                for symbol in self.available_pairs:
                    if symbol in self.last_kline_data:
                        kline_data = self.last_kline_data[symbol]
                        
                        # Obtener datos históricos para análisis
                        timeframes = self.strategy_params.get('timeframes', ['1h'])
                        for timeframe in timeframes:
                            # Combinar datos históricos con datos en tiempo real
                            historical_data = self.exchange.get_historical_klines(
                                symbol, 
                                timeframe, 
                                "1 day ago UTC"
                            )
                            
                            if not historical_data:
                                self._emit_log("WARNING", f"No hay datos históricos para {symbol} {timeframe}")
                                continue
                            
                            # Agregar el último dato en tiempo real
                            historical_data.append({
                                'open_time': kline_data['timestamp'],
                                'open': kline_data['open'],
                                'high': kline_data['high'],
                                'low': kline_data['low'],
                                'close': kline_data['close'],
                                'volume': kline_data['volume'],
                                'close_time': kline_data['timestamp'] + 60000,  # +1 minuto
                            })
                            
                            self._execute_strategy(symbol, historical_data, iteration)
                    else:
                        self._emit_log("WARNING", f"No hay datos en tiempo real para {symbol}")

                time.sleep(wait_time)

            except Exception as e:
                self._emit_log("ERROR", f"Error loop: {e}")
                time.sleep(wait_time)

    # ==================== STRATEGY ====================

    def _execute_strategy(self, symbol: str, data: List, iteration: int):
        try:
            current_price = float(data[-1]['close'])
            decision = self._make_trading_decision(symbol, data, iteration)

            if decision == 'BUY':
                self._place_order(symbol, 'BUY', 0.001, current_price)
            elif decision == 'SELL':
                self._place_order(symbol, 'SELL', 0.001, current_price)
            else:
                self._emit_log("INFO", f"HOLD @ {current_price}")

        except Exception as e:
            self._emit_log("ERROR", f"Estrategia error: {e}")

    def _make_trading_decision(self, symbol: str, data: List, iteration: int) -> str:
        try:
            closes = [float(c['close']) for c in data]

            # Usar parámetros de estrategia de config.yaml
            fast_period = self.strategy_params.get('indicators', {}).get('sma_fast', 5)
            slow_period = self.strategy_params.get('indicators', {}).get('sma_slow', 20)

            fast_ma = sum(closes[-fast_period:]) / fast_period
            slow_ma = sum(closes[-slow_period:]) / slow_period

            if fast_ma > slow_ma and iteration % 3 == 0:
                return "BUY"
            if fast_ma < slow_ma and iteration % 3 == 0:
                return "SELL"
            return "HOLD"

        except Exception as e:
            self._emit_log("ERROR", f"Error en decisión de trading: {e}")
            return "HOLD"

    # ==================== ORDERS ====================

    def _place_order(self, symbol: str, side: str, qty: float, price: float):
        try:
            if self.trading_mode == 'real':
                order = self.exchange.create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=qty
                )
                order_id = order['orderId']
                real = True
            else:
                order_id = f"SIM_{int(time.time())}"
                real = False

            self._emit_log("SUCCESS", f"Orden {side} {qty} {symbol} @ {price}")

            trade = Trade(
                session_id=self.current_session.id,
                symbol=symbol,
                side=side.lower(),
                entry_price=price,
                quantity=qty,
                real_trade=real,
                status='closed',
                entry_time=datetime.utcnow(),
                exit_time=datetime.utcnow(),
                pnl=0
            )
            db.session.add(trade)
            db.session.commit()

            self.trades.append({
                "symbol": symbol, "side": side, "price": price, "qty": qty, "id": order_id
            })

        except Exception as e:
            self._emit_log("ERROR", f"Error placing order: {e}")

    # ==================== STOP ====================

    def _handle_kline_message(self, msg):
        """Maneja los mensajes de kline del WebSocket de Binance"""
        try:
            if isinstance(msg, dict):
                if msg.get('e') == 'error':
                    self._emit_log("ERROR", f"Error WebSocket: {msg.get('m')}")
                    return
                    
                if msg.get('e') != 'kline':
                    return
                    
                # Extraer datos del kline
                kline = msg.get('k', {})
                symbol = msg.get('s')
                
                if not symbol or not kline:
                    self._emit_log("WARNING", "Mensaje de kline inválido")
                    return
                
                # Actualizar datos en tiempo real
                try:
                    self.last_kline_data[symbol] = {
                        'timestamp': kline['t'],
                        'open': float(kline['o']),
                        'high': float(kline['h']), 
                        'low': float(kline['l']),
                        'close': float(kline['c']),
                        'volume': float(kline['v'])
                    }
                    
                    # Emitir actualización de precio
                    price_data = {
                        'symbol': symbol,
                        'price': float(kline['c']),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    logger.info(f"Emitiendo price_update: {price_data}")
                    
                    # Emitir a diferentes namespaces para asegurar que llegue
                    socketio.emit('price_update', price_data)  # Default namespace
                    socketio.emit('price_update', price_data, namespace='/')  # Root namespace
                    socketio.emit('price_update', price_data, broadcast=True)  # Broadcast
                    
                    # Forzar envío inmediato
                    try:
                        socketio.sleep(0)
                    except:
                        pass
                        
                    logger.info("✅ Evento price_update emitido") # Asegurarnos que se emite al namespace correcto
                    
                    self._emit_log("DEBUG", f"Precio actualizado {symbol}: {kline['c']}")
                    
                except (KeyError, ValueError) as e:
                    self._emit_log("ERROR", f"Error procesando datos de kline: {e}")
            
        except Exception as e:
            self._emit_log("ERROR", f"Error procesando kline: {e}")
    
    def stop(self):
        """Detiene el bot y cierra conexiones"""
        self.is_running = False
        
        if self.websocket_manager:
            try:
                self.websocket_manager.close()
                self._emit_log("INFO", "WebSocket cerrado")
            except:
                pass

        if self.current_session:
            self.current_session.status = 'stopped'
            self.current_session.ended_at = datetime.utcnow()
            db.session.commit()

        self._emit_log("INFO", "Bot detenido")
        return {"success": True, "message": "Bot detenido"}

    # ==================== STATUS ====================

    def initialize_exchange(self):
        """Inicializa la conexión con Binance y configura WebSocket"""
        try:
            # Crear conexión con Binance
            self.exchange = ExchangeFactory.create_exchange(
                'binance',
                self.api_key,
                self.api_secret,
                paper_trading=self.is_testnet
            )
            
            # Inicializar WebSocket Manager de Binance
            from binance.streams import BinanceSocketManager
            self.websocket_manager = BinanceSocketManager(self.exchange)
            
            # Suscribirse a streams de precios para cada par
            for symbol in self.available_pairs:
                try:
                    # Obtener precio inicial
                    ticker = self.exchange.get_symbol_ticker(symbol=symbol)
                    price = float(ticker['price'])
                    logger.info(f"✅ {symbol}: ${price:.2f}")
                    
                    # Emitir precio inicial
                    socketio.emit('price_update', {
                        'symbol': symbol,
                        'price': price,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Suscribirse al stream de klines usando v2
                    stream_name = f"{symbol.lower()}@kline_1m"
                    self.websocket_manager.start_kline_socket(
                        callback=self._handle_kline_message,
                        symbol=symbol.lower(),
                        interval='1m'
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Error configurando {symbol}: {e}")
            
            # Iniciar WebSocket
            self.websocket_manager.start()
            logger.info("✅ WebSocket de Binance iniciado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando exchange: {e}")
            return False

    def get_status(self):
        if not self.current_session:
            return {"status": "not_started"}

        status_data = {
            "status": self.current_session.status,
            "running": self.is_running,
            "session_id": self.current_session.id,
            "trades": self.trades,
            "real_time_data": {}
        }

        # Agregar datos en tiempo real si están disponibles
        if self.last_kline_data:
            status_data["real_time_data"] = self.last_kline_data

        return status_data

    def _handle_kline_message(self, msg):
        """Maneja los mensajes de kline recibidos via websocket"""
        try:
            if msg['e'] == 'kline':
                symbol = msg['s']
                kline = msg['k']
                
                # Actualizar datos en tiempo real
                self.last_kline_data[symbol] = {
                    'symbol': symbol,
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v']),
                    'timestamp': kline['t'],
                    'is_closed': kline['x']
                }
                
                # Emitir datos via websocket a los clientes
                socketio.emit('kline_update', {
                    'data': self.last_kline_data[symbol],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Log para debugging
                logger.debug(f"Kline actualizado para {symbol}: {self.last_kline_data[symbol]['close']}")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje de kline: {e}")

    # ==================== STATIC API ====================

    @classmethod
    def start_bot(cls, user_id: int, trading_mode="simulation", config_id=None):
        if user_id in cls._active_bots:
            return {"success": False, "message": "Bot ya iniciado"}

        bot = cls(user_id, trading_mode, config_id)
        cls._active_bots[user_id] = bot
        return bot.start()

    @classmethod
    def stop_bot(cls, user_id: int):
        if user_id not in cls._active_bots:
            return {"success": False, "message": "No bot activo"}

        bot = cls._active_bots[user_id]
        res = bot.stop()
        del cls._active_bots[user_id]
        return res

    @classmethod
    def get_bot_status(cls, user_id: int):
        if user_id not in cls._active_bots:
            return {"status": "not_running"}
        return cls._active_bots[user_id].get_status()
