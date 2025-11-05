# Copilot / AI assistant instructions for QuantumTrader Pro

This file gives focused, actionable guidance so an AI coding assistant can be productive quickly in this repository.

- Purpose: QuantumTrader Pro is a Flask-based trading dashboard and bot framework (simulation, demo, real) for Binance. Key subsystems are: web/API (Flask + Socket.IO), bot runtime (BotService + exchange adapters), data service, and SQLAlchemy models.

- Quick entry points:
  - Primary runner: `run.py` — verifies env vars, connects to DB, and starts Flask + Socket.IO (uses eventlet via `socketio.run`).
  - Local dev: `run-dev.bat` / `run.bat` exist in repo root for Windows; alternatively run `python run.py` (ensure env vars set).
  - Database helpers: `reset_database.py`, `check_structure.py`, `fix_relationships.py` are present for schema tasks. The DDL is in `database/schema.sql`.

- Config and environment:
  - Central config: `app/core/config.py`. It builds `SQLALCHEMY_DATABASE_URI` from env vars: SECRET_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD. Config also loads `config.yaml` for trading pairs.
  - Important env vars used at startup: SECRET_KEY, DB_*, REDIS_*, BINANCE_API_KEY, BINANCE_SECRET_KEY, HOST, PORT, FLASK_DEBUG, APP_ENV.

- Database and models:
  - DB instance: `app/core/database.py` exposes `db`, `init_db()` which calls `Base.metadata.create_all()` — typical pattern: call `init_db(app)` inside app factory.
  - Model files live under `app/models/` (users, api_keys, bot_sessions, trades, positions, etc.). `SystemLog` model is used by bots to persist logs.

- Bot runtime and integrations:
  - `app/services/bot_service.py` contains `BotService` which manages bot lifecycle (start/stop), emits logs to DB and Socket.IO, and runs `_trading_loop` in a thread.
  - Exchange adapters: `app/services/exchange_factory.py` provides adapter creation (e.g., Binance) — prefer using `ExchangeFactory.create_exchange(...)` rather than directly instantiating exchanges.
  - Market data: `app/services/data_service.py` is the integration point for fetching market candles; many endpoints and the trading loop call `DataService.get_market_data()`.
  - Real vs simulated trades: `BotService` uses `trading_mode` ('simulation'|'real') to toggle between actual exchange orders and simulated orders (SIM_ ids).

- Web/API and real-time messaging:
  - Blueprints: `app/api/v1/` contains endpoints such as `trading.py` (strategies, market/data, portfolio). Endpoints use `flask_login` for authentication.
  - Socket.IO: socket events and namespaces are used for logs and dashboard updates. Bots emit to namespace `/logs/{user_id}`.

- Tests and CI hints:
  - Tests visible: `test_installation.py`, `test_database.py`, `test_postgres.py`. Run tests with the project's Python environment; tests expect env vars and DB/migrations to be available or use testing config.

- Conventions & patterns to follow when editing code:
  - App factory pattern: import `create_app` from `app` package and use `app.app_context()` when touching DB outside requests.
  - Keep long-running bot logic off the request thread: use threads or background workers (current code uses threading + Socket.IO). If adding background jobs, follow existing patterns (see `rq`/`huey` in requirements).
  - Persist logs to `SystemLog` and emit via Socket.IO for dashboard visibility — mirror existing fields (user_id, session_id, level, message, time).
  - Use `app/core/config.py` for any configuration values and `config.yaml` for trading parameters/pairs.

- Files to reference for concrete examples:
  - Runner & startup: `run.py`
  - Config: `app/core/config.py`
  - DB init: `app/core/database.py`
  - Bot lifecycle: `app/services/bot_service.py`
  - Trading API: `app/api/v1/trading.py`
  - Models: `app/models/*` (especially `system_logs.py`, `bot_sessions.py`, `trades.py`)

- Safety notes for AI edits:
  - Do not add real API keys into code. Use env vars or `generate_key.py` where appropriate.
  - Changing database migrations or DDL should be done carefully; prefer adding migrations under `database/migrations/versions/`.

If any of these sections are unclear or you want me to expand a specific area (for example, provide exact run commands for Windows PowerShell, or include example env var values), tell me which part and I will iterate.
