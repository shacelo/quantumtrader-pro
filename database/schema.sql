-- =============================================================================
-- 🗄️ QUANTUMTRADER PRO - SCHEMA COMPLETO
-- =============================================================================

-- 👥 TABLA: Usuarios del sistema
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔑 TABLA: API Keys de Binance
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exchange VARCHAR(20) DEFAULT 'binance',
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    testnet BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    CONSTRAINT fk_api_keys_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ⚙️ TABLA: Configuración del bot
CREATE TABLE IF NOT EXISTS bot_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    config_name VARCHAR(50) DEFAULT 'default',
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bot_config_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 🕐 TABLA: Sesiones de trading
CREATE TABLE IF NOT EXISTS bot_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(100),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    initial_balance DECIMAL(15, 2) NOT NULL,
    final_balance DECIMAL(15, 2) NULL,
    status VARCHAR(20) DEFAULT 'running',
    trading_mode VARCHAR(20) DEFAULT 'simulation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bot_sessions_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 💰 TABLA: Historial de balances
CREATE TABLE IF NOT EXISTS balance_history (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES bot_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    balance DECIMAL(15, 2) NOT NULL,
    pnl DECIMAL(15, 2) NOT NULL,
    pnl_daily DECIMAL(15, 2) DEFAULT 0,
    equity DECIMAL(15, 2) NOT NULL,
    CONSTRAINT fk_balance_history_session FOREIGN KEY (session_id) REFERENCES bot_sessions(id)
);

-- 📈 TABLA: Órdenes de trading
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES bot_sessions(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    order_id VARCHAR(100),
    client_order_id VARCHAR(100),
    side VARCHAR(10) NOT NULL,
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    quantity DECIMAL(15, 8) NOT NULL,
    price DECIMAL(15, 6) NULL,
    stop_price DECIMAL(15, 6) NULL,
    executed_quantity DECIMAL(15, 8) DEFAULT 0,
    executed_price DECIMAL(15, 6) NULL,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    real_trade BOOLEAN DEFAULT false,
    CONSTRAINT fk_orders_session FOREIGN KEY (session_id) REFERENCES bot_sessions(id)
);

-- 💹 TABLA: Trades ejecutados
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES bot_sessions(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    entry_order_id INTEGER REFERENCES orders(id),
    exit_order_id INTEGER REFERENCES orders(id),
    entry_price DECIMAL(15, 6) NOT NULL,
    exit_price DECIMAL(15, 6) NULL,
    quantity DECIMAL(15, 8) NOT NULL,
    pnl DECIMAL(15, 2) NULL,
    pnl_percent DECIMAL(10, 4) NULL,
    status VARCHAR(20) DEFAULT 'open',
    close_reason VARCHAR(50) NULL,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP NULL,
    stop_loss DECIMAL(15, 6),
    take_profit DECIMAL(15, 6),
    signal_strength VARCHAR(100),
    real_trade BOOLEAN DEFAULT false,
    risk_metrics JSONB NULL,
    CONSTRAINT fk_trades_session FOREIGN KEY (session_id) REFERENCES bot_sessions(id),
    CONSTRAINT fk_trades_entry_order FOREIGN KEY (entry_order_id) REFERENCES orders(id),
    CONSTRAINT fk_trades_exit_order FOREIGN KEY (exit_order_id) REFERENCES orders(id)
);

-- 📊 TABLA: Posiciones activas
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES bot_sessions(id) ON DELETE CASCADE,
    trade_id INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15, 8) NOT NULL,
    entry_price DECIMAL(15, 6) NOT NULL,
    current_price DECIMAL(15, 6) NOT NULL,
    unrealized_pnl DECIMAL(15, 2) NOT NULL,
    unrealized_pnl_percent DECIMAL(10, 4) NOT NULL,
    stop_loss DECIMAL(15, 6) NOT NULL,
    take_profit DECIMAL(15, 6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_positions_session FOREIGN KEY (session_id) REFERENCES bot_sessions(id),
    CONSTRAINT fk_positions_trade FOREIGN KEY (trade_id) REFERENCES trades(id)
);

-- 📝 TABLA: Logs del sistema
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES bot_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(10) NOT NULL,
    source VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB NULL,
    CONSTRAINT fk_system_logs_session FOREIGN KEY (session_id) REFERENCES bot_sessions(id)
);

-- 🛡️ TABLA: Métricas de riesgo
CREATE TABLE IF NOT EXISTS risk_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES bot_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15, 6) NOT NULL,
    time_period VARCHAR(20) DEFAULT 'daily',
    CONSTRAINT fk_risk_metrics_session FOREIGN KEY (session_id) REFERENCES bot_sessions(id)
);

-- 📋 TABLA: Sesiones de auditoría
CREATE TABLE IF NOT EXISTS audit_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    action_details JSONB NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success',
    CONSTRAINT fk_audit_sessions_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- =============================================================================
-- 🎯 ÍNDICES PARA OPTIMIZACIÓN
-- =============================================================================

-- Users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- API Keys
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- Bot Config
CREATE INDEX IF NOT EXISTS idx_bot_config_user_id ON bot_config(user_id);
CREATE INDEX IF NOT EXISTS idx_bot_config_active ON bot_config(is_active);

-- Sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON bot_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON bot_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_trading_mode ON bot_sessions(trading_mode);
CREATE INDEX IF NOT EXISTS idx_sessions_time_range ON bot_sessions(start_time, end_time);

-- Trades
CREATE INDEX IF NOT EXISTS idx_trades_session_id ON trades(session_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_trades_real_trade ON trades(real_trade);
CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl);

-- Orders
CREATE INDEX IF NOT EXISTS idx_orders_session_id ON orders(session_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_side ON orders(side);
CREATE INDEX IF NOT EXISTS idx_orders_created_time ON orders(created_time);

-- Balance History
CREATE INDEX IF NOT EXISTS idx_balance_history_session_id ON balance_history(session_id);
CREATE INDEX IF NOT EXISTS idx_balance_history_timestamp ON balance_history(timestamp);

-- Positions
CREATE INDEX IF NOT EXISTS idx_positions_session_id ON positions(session_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_trade_id ON positions(trade_id);

-- Logs
CREATE INDEX IF NOT EXISTS idx_logs_session_id ON system_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_source ON system_logs(source);

-- Risk Metrics
CREATE INDEX IF NOT EXISTS idx_risk_metrics_session_id ON risk_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_timestamp ON risk_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_name ON risk_metrics(metric_name);

-- Audit
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_sessions(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON audit_sessions(action_type);

-- =============================================================================
-- 🔄 TRIGGERS Y FUNCIONES
-- =============================================================================

-- Función para actualizar timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bot_config_updated_at 
    BEFORE UPDATE ON bot_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at 
    BEFORE UPDATE ON positions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_time 
    BEFORE UPDATE ON orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Función para calcular métricas de riesgo automáticamente
CREATE OR REPLACE FUNCTION calculate_session_metrics(session_id INTEGER)
RETURNS TABLE(
    total_trades BIGINT,
    winning_trades BIGINT,
    losing_trades BIGINT,
    total_pnl DECIMAL,
    win_rate DECIMAL,
    avg_win DECIMAL,
    avg_loss DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_trades,
        COUNT(CASE WHEN t.pnl > 0 THEN 1 END) as winning_trades,
        COUNT(CASE WHEN t.pnl < 0 THEN 1 END) as losing_trades,
        COALESCE(SUM(t.pnl), 0) as total_pnl,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND(COUNT(CASE WHEN t.pnl > 0 THEN 1 END) * 100.0 / COUNT(*), 2)
            ELSE 0 
        END as win_rate,
        COALESCE(AVG(CASE WHEN t.pnl > 0 THEN t.pnl END), 0) as avg_win,
        COALESCE(AVG(CASE WHEN t.pnl < 0 THEN ABS(t.pnl) END), 0) as avg_loss
    FROM trades t
    WHERE t.session_id = $1 AND t.status = 'closed';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🔐 DATOS INICIALES
-- =============================================================================

-- Usuario administrador (password: admin123)
INSERT INTO users (username, password_hash, email, role) 
VALUES (
    'admin', 
    '$2b$12$LQv3c1yqB.WTg7Q7KQwKdOe9lZIjR8Xa8NcXkzJvJ6v8cJ1rV9SWS',
    'admin@quantumtrader.com',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Configuración por defecto
INSERT INTO bot_config (user_id, config_name, config_data) 
VALUES (
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
            "min_signal_strength": 4,
            "advanced_indicators": {
                "macd_enabled": true,
                "bollinger_bands_enabled": true,
                "stochastic_enabled": false
            }
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
            "risk_warnings": {
                "max_daily_trades": 10,
                "max_drawdown_percent": 10.0
            }
        },
        "logging": {
            "level": "INFO",
            "file": "logs/trading_bot.log",
            "encoding": "utf-8",
            "console_output": true
        },
        "notifications": {
            "enabled": true,
            "telegram": {
                "enabled": false,
                "bot_token": "",
                "chat_id": ""
            },
            "email": {
                "enabled": false,
                "smtp_server": "",
                "email_from": "",
                "email_to": ""
            }
        }
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- 📊 VISTAS ÚTILES
-- =============================================================================

-- Vista para dashboard principal
CREATE OR REPLACE VIEW dashboard_stats AS
SELECT 
    bs.id as session_id,
    bs.session_name,
    bs.status,
    bs.trading_mode,
    bs.start_time,
    bs.initial_balance,
    bh.balance as current_balance,
    bh.pnl as total_pnl,
    (bh.pnl / bs.initial_balance * 100) as total_pnl_percent,
    (SELECT COUNT(*) FROM trades t WHERE t.session_id = bs.id AND t.status = 'closed') as total_trades,
    (SELECT COUNT(*) FROM trades t WHERE t.session_id = bs.id AND t.status = 'closed' AND t.pnl > 0) as winning_trades,
    (SELECT COUNT(*) FROM trades t WHERE t.session_id = bs.id AND t.status = 'open') as active_positions
FROM bot_sessions bs
LEFT JOIN balance_history bh ON bh.session_id = bs.id
WHERE bh.timestamp = (SELECT MAX(timestamp) FROM balance_history WHERE session_id = bs.id)
AND bs.status = 'running';

-- Vista para métricas de performance
CREATE OR REPLACE VIEW performance_metrics AS
SELECT 
    bs.id as session_id,
    bs.session_name,
    bs.trading_mode,
    COUNT(t.id) as total_trades,
    COUNT(CASE WHEN t.pnl > 0 THEN 1 END) as winning_trades,
    COUNT(CASE WHEN t.real_trade = true THEN 1 END) as real_trades,
    COALESCE(SUM(t.pnl), 0) as total_pnl,
    CASE 
        WHEN COUNT(t.id) > 0 THEN 
            ROUND(COUNT(CASE WHEN t.pnl > 0 THEN 1 END) * 100.0 / COUNT(t.id), 2)
        ELSE 0 
    END as win_rate,
    COALESCE(AVG(CASE WHEN t.pnl > 0 THEN t.pnl END), 0) as avg_win,
    COALESCE(AVG(CASE WHEN t.pnl < 0 THEN ABS(t.pnl) END), 0) as avg_loss,
    COALESCE(MAX(t.pnl), 0) as best_trade,
    COALESCE(MIN(t.pnl), 0) as worst_trade
FROM bot_sessions bs
LEFT JOIN trades t ON t.session_id = bs.id AND t.status = 'closed'
GROUP BY bs.id, bs.session_name, bs.trading_mode;

-- =============================================================================
-- ✅ MENSAJE DE CONFIRMACIÓN
-- =============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '🎉 ESQUEMA QUANTUMTRADER PRO CREADO EXITOSAMENTE';
    RAISE NOTICE '📊 Tablas: 11 | Índices: 35 | Funciones: 2 | Vistas: 2';
    RAISE NOTICE '👤 Usuario por defecto: admin / admin123';
END $$;