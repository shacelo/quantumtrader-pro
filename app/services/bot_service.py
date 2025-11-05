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

        self.api_key = os.getenv('BINANCE_API_KEY', '')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY', '')

        logger.info(f"BotService creado para user {user_id} modo {trading_mode}")

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

            # Exchange real/simulado
            self.exchange = ExchangeFactory.create_exchange(
                'binance',
                self.api_key,
                self.secret_key,
                paper_trading=(self.trading_mode != 'real')
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

        iteration = 0
        wait_time = int(os.getenv("BOT_WAIT_TIME", 10))  # default 10s para pruebas

        while self.is_running:
            try:
                iteration += 1
                self._emit_log("INFO", f"Iteración #{iteration}")

                symbol = "BTCUSDT"
                timeframe = "1h"

                data = self.data_service.get_market_data(symbol, timeframe, limit=100)

                if not data:
                    self._emit_log("WARNING", "No hay datos de mercado")
                    time.sleep(wait_time)
                    continue

                self._execute_strategy(symbol, data, iteration)
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

            fast_ma = sum(closes[-5:]) / 5
            slow_ma = sum(closes[-20:]) / 20

            if fast_ma > slow_ma and iteration % 3 == 0:
                return "BUY"
            if fast_ma < slow_ma and iteration % 3 == 0:
                return "SELL"
            return "HOLD"

        except:
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

    def stop(self):
        self.is_running = False

        if self.current_session:
            self.current_session.status = 'stopped'
            self.current_session.ended_at = datetime.utcnow()
            db.session.commit()

        self._emit_log("INFO", "Bot detenido")
        return {"success": True, "message": "Bot detenido"}

    # ==================== STATUS ====================

    def get_status(self):
        if not self.current_session:
            return {"status": "not_started"}

        return {
            "status": self.current_session.status,
            "running": self.is_running,
            "session_id": self.current_session.id,
            "trades": self.trades
        }

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
