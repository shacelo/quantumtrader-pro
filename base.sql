-- =============================================================================
-- 🗄️ ESQUEMA COMPLETO - QUANTUMTRADER PRO
-- =============================================================================

-- 👥 TABLA: Usuarios del sistema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'user'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔑 TABLA: API Keys de Binance (separadas por usuario)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exchange VARCHAR(20) DEFAULT 'binance',
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    testnet BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- ⚙️ TABLA: Configuración del bot por usuario
CREATE TABLE bot_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    config_name VARCHAR(50) DEFAULT 'default',
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🕐 TABLA: Sesiones de trading
CREATE TABLE bot_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(100),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    initial_balance DECIMAL(15, 2) NOT NULL,
    final_balance DECIMAL(15, 2) NULL,
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'stopped', 'paused', 'error'
    trading_mode VARCHAR(20) DEFAULT 'simulation', -- 'simulation', 'demo', 'real'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 💰 TABLA: Historial de balances por sesión
CREATE TABLE balance_history (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    balance DECIMAL(15, 2) NOT NULL,
    pnl DECIMAL(15, 2) NOT NULL, -- P&L acumulado
    pnl_daily DECIMAL(15, 2) DEFAULT 0, -- P&L del día
    equity DECIMAL(15, 2) NOT NULL
);

-- 📈 TABLA: Órdenes de trading
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    order_id VARCHAR(100), -- ID de orden en exchange
    client_order_id VARCHAR(100),
    side VARCHAR(10) NOT NULL, -- 'BUY', 'SELL'
    type VARCHAR(20) NOT NULL, -- 'MARKET', 'LIMIT', 'STOP_LOSS', etc.
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'filled', 'canceled', 'rejected'
    quantity DECIMAL(15, 8) NOT NULL,
    price DECIMAL(15, 6) NULL,
    stop_price DECIMAL(15, 6) NULL,
    executed_quantity DECIMAL(15, 8) DEFAULT 0,
    executed_price DECIMAL(15, 6) NULL,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    real_trade BOOLEAN DEFAULT false
);

-- 💹 TABLA: Trades ejecutados
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    entry_order_id INTEGER REFERENCES orders(id),
    exit_order_id INTEGER REFERENCES orders(id) NULL,
    entry_price DECIMAL(15, 6) NOT NULL,
    exit_price DECIMAL(15, 6) NULL,
    quantity DECIMAL(15, 8) NOT NULL,
    pnl DECIMAL(15, 2) NULL,
    pnl_percent DECIMAL(10, 4) NULL,
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'closed', 'cancelled'
    close_reason VARCHAR(50) NULL, -- 'take_profit', 'stop_loss', 'manual', 'signal'
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP NULL,
    stop_loss DECIMAL(15, 6),
    take_profit DECIMAL(15, 6),
    signal_strength VARCHAR(100),
    real_trade BOOLEAN DEFAULT false,
    risk_metrics JSONB NULL -- Métricas de riesgo específicas del trade
);

-- 📊 TABLA: Posiciones activas
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(id) ON DELETE CASCADE,
    trade_id INTEGER REFERENCES trades(id),
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15, 8) NOT NULL,
    entry_price DECIMAL(15, 6) NOT NULL,
    current_price DECIMAL(15, 6) NOT NULL,
    unrealized_pnl DECIMAL(15, 2) NOT NULL,
    unrealized_pnl_percent DECIMAL(10, 4) NOT NULL,
    stop_loss DECIMAL(15, 6) NOT NULL,
    take_profit DECIMAL(15, 6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 📉 TABLA: Datos de mercado (opcional para análisis)
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    open DECIMAL(15, 6) NOT NULL,
    high DECIMAL(15, 6) NOT NULL,
    low DECIMAL(15, 6) NOT NULL,
    close DECIMAL(15, 6) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    interval VARCHAR(10) NOT NULL -- '1m', '5m', '1h', '1d'
);

-- 📝 TABLA: Logs del sistema
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(10) NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    source VARCHAR(50) NOT NULL, -- 'trading', 'system', 'risk_management', 'strategy'
    message TEXT NOT NULL,
    details JSONB NULL -- Datos adicionales estructurados
);

-- 🛡️ TABLA: Métricas de riesgo
CREATE TABLE risk_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES bot_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_name VARCHAR(50) NOT NULL, -- 'sharpe_ratio', 'max_drawdown', 'volatility', etc.
    metric_value DECIMAL(15, 6) NOT NULL,
    time_period VARCHAR(20) DEFAULT 'daily' -- 'hourly', 'daily', 'weekly', 'session'
);

-- 📋 TABLA: Sesiones de auditoría (acciones del usuario)
CREATE TABLE audit_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- 'start_bot', 'stop_bot', 'config_change', 'api_key_update'
    action_details JSONB NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success' -- 'success', 'failed'
);

-- =============================================================================
-- 🎯 ÍNDICES PARA OPTIMIZACIÓN
-- =============================================================================

-- Índices para users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- Índices para sesiones
CREATE INDEX idx_sessions_user_id ON bot_sessions(user_id);
CREATE INDEX idx_sessions_status ON bot_sessions(status);
CREATE INDEX idx_sessions_trading_mode ON bot_sessions(trading_mode);
CREATE INDEX idx_sessions_time_range ON bot_sessions(start_time, end_time);

-- Índices para trades
CREATE INDEX idx_trades_session_id ON trades(session_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_exit_time ON trades(exit_time);
CREATE INDEX idx_trades_real_trade ON trades(real_trade);

-- Índices para órdenes
CREATE INDEX idx_orders_session_id ON orders(session_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_time ON orders(created_time);

-- Índices para balance history
CREATE INDEX idx_balance_history_session_id ON balance_history(session_id);
CREATE INDEX idx_balance_history_timestamp ON balance_history(timestamp);

-- Índices para logs
CREATE INDEX idx_logs_session_id ON system_logs(session_id);
CREATE INDEX idx_logs_timestamp ON system_logs(timestamp);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_source ON system_logs(source);

-- Índices para métricas de riesgo
CREATE INDEX idx_risk_metrics_session_id ON risk_metrics(session_id);
CREATE INDEX idx_risk_metrics_timestamp ON risk_metrics(timestamp);

-- Índices para auditoría
CREATE INDEX idx_audit_user_id ON audit_sessions(user_id);
CREATE INDEX idx_audit_timestamp ON audit_sessions(timestamp);
CREATE INDEX idx_audit_action_type ON audit_sessions(action_type);

-- =============================================================================
-- 🔐 DATOS INICIALES
-- =============================================================================

-- Insertar usuario administrador por defecto
INSERT INTO users (username, password_hash, email, role) VALUES (
    'admin', 
    '$2b$12$LQv3c1yqB.WTg7Q7KQwKdOe9lZIjR8Xa8NcXkzJvJ6v8cJ1rV9SWS', -- bcrypt hash de 'admin123'
    'admin@quantumtrader.com',
    'admin'
);

-- Insertar configuración por defecto
INSERT INTO bot_config (user_id, config_name, config_data) VALUES (
    1,
    'default',
    '{
        "bot": {
            "name": "QuantumTrader Pro",
            "version": "2.0",
            "check_interval": 120,
            "max_daily_loss_percent": 5.0,
            "cooldown_seconds": 300
        },
        "trading": {
            "pairs": ["ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT", "LTCUSDT", "XRPUSDT"],
            "base_currency": "USDT",
            "testnet": true,
            "real_trading": false,
            "max_simultaneous_positions": 3,
            "trading_mode": "simulation"
        },
        "strategy": {
            "interval": "1h",
            "sma_fast": 12,
            "sma_slow": 26,
            "volume_threshold": 1.5,
            "rsi_period": 14,
            "min_signal_strength": 4
        },
        "risk_management": {
            "stop_loss_percent": 1.5,
            "take_profit_percent": 3.0,
            "max_position_percent": 3.0,
            "trailing_stop": {
                "enabled": true,
                "activation": 1.5,
                "distance": 0.8
            },
            "partial_take_profit": {
                "enabled": true,
                "levels": [
                    {"percent": 1.5, "sell_percent": 40, "name": "TP1"},
                    {"percent": 2.5, "sell_percent": 40, "name": "TP2"},
                    {"percent": 3.5, "sell_percent": 20, "name": "TP3"}
                ]
            },
            "volatility_filter": {
                "enabled": true,
                "min_volatility": 0.6,
                "max_volatility": 2.0
            },
            "daily_limits": {
                "max_trades": 10,
                "max_drawdown_percent": 10.0
            }
        },
        "logging": {
            "level": "INFO",
            "file": "logs/trading_bot.log",
            "encoding": "utf-8"
        }
    }'
);

-- =============================================================================
-- 🔄 TRIGGERS PARA ACTUALIZACIÓN AUTOMÁTICA
-- =============================================================================

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a tablas que necesitan updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bot_config_updated_at BEFORE UPDATE ON bot_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();