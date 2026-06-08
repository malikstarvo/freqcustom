-- TimescaleDB Schema for Freqtrade Edge Study
-- Run this against your TimescaleDB instance

-- Enable the timescaledb extension (requires superuser)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- OHLCV Candles hypertable
CREATE TABLE IF NOT EXISTS candles (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open DECIMAL,
    high DECIMAL,
    low DECIMAL,
    close DECIMAL,
    volume DECIMAL,
    PRIMARY KEY (time, symbol, timeframe)
);

SELECT create_hypertable('candles', 'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Feature values hypertable (27 indicators + orderflow data)
CREATE TABLE IF NOT EXISTS feature_values (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    feature_set_id INTEGER NOT NULL DEFAULT 1,

    -- Technical indicators
    ema20 DECIMAL,
    ema50 DECIMAL,
    ema200 DECIMAL,
    rsi14 DECIMAL,
    atr14 DECIMAL,
    adx14 DECIMAL,
    volume_ema20 DECIMAL,
    volatility14 DECIMAL,

    -- OrderFlow features
    funding_rate DECIMAL,
    oi_delta_1_pct DECIMAL,
    ls_ratio DECIMAL,
    liq_long_usd DECIMAL,
    liq_short_usd DECIMAL,
    liq_imbalance DECIMAL,

    PRIMARY KEY (ts, symbol, timeframe, feature_set_id)
);

SELECT create_hypertable('feature_values', 'ts',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Labels table (future returns for supervised learning)
CREATE TABLE IF NOT EXISTS labels (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    feature_set_id INTEGER NOT NULL DEFAULT 1,

    -- Future return labels at different horizons (in bars)
    future_return_4 DECIMAL,
    future_return_12 DECIMAL,
    future_return_24 DECIMAL,
    future_direction_4 SMALLINT,   -- 1 = up, 0 = down
    future_direction_12 SMALLINT,
    future_direction_24 SMALLINT,

    PRIMARY KEY (ts, symbol, timeframe, feature_set_id)
);

SELECT create_hypertable('labels', 'ts',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Edge study research results (persisted output)
CREATE TABLE IF NOT EXISTS research_results (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    feature_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DECIMAL,
    samples INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_run
    ON research_results (run_id, feature_name, metric_name);

CREATE INDEX IF NOT EXISTS idx_feature_values_lookup
    ON feature_values (symbol, timeframe, feature_set_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_labels_lookup
    ON labels (symbol, timeframe, feature_set_id, ts DESC);

-- Paper Trading tables (from Phase 8)

CREATE TABLE IF NOT EXISTS paper_orders (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    requested_size DECIMAL,
    filled_size DECIMAL,
    fill_price DECIMAL,
    slippage_pct DECIMAL,
    commission DECIMAL,
    reason TEXT,
    open_ts TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS paper_fills (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES paper_orders(id),
    ts TIMESTAMPTZ NOT NULL,
    side TEXT NOT NULL,
    price DECIMAL NOT NULL,
    size DECIMAL NOT NULL,
    fee DECIMAL NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_positions (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_order_id BIGINT NOT NULL REFERENCES paper_orders(id),
    quantity DECIMAL NOT NULL,
    entry_price DECIMAL NOT NULL,
    entry_fee DECIMAL NOT NULL,
    stop_price DECIMAL NOT NULL,
    open_ts TIMESTAMPTZ NOT NULL,
    bars_held INTEGER DEFAULT 0,
    status TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS paper_trades (
    id BIGSERIAL PRIMARY KEY,
    position_id BIGINT NOT NULL REFERENCES paper_positions(id),
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_ts TIMESTAMPTZ NOT NULL,
    exit_ts TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL NOT NULL,
    exit_price DECIMAL NOT NULL,
    size DECIMAL NOT NULL,
    gross_pnl DECIMAL NOT NULL DEFAULT 0,
    commission DECIMAL NOT NULL DEFAULT 0,
    net_pnl DECIMAL NOT NULL DEFAULT 0,
    return_pct DECIMAL NOT NULL DEFAULT 0,
    holding_bars INTEGER DEFAULT 0,
    exit_reason TEXT,
    entry_reason TEXT,
    feature_snapshot TEXT
);

CREATE TABLE IF NOT EXISTS paper_account_snapshots (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    balance DECIMAL NOT NULL,
    equity DECIMAL NOT NULL,
    unrealized_pnl DECIMAL DEFAULT 0,
    day_pnl DECIMAL DEFAULT 0,
    day_trades INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS paper_topups (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    amount DECIMAL NOT NULL,
    balance_before DECIMAL NOT NULL,
    balance_after DECIMAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paper_orders_symbol ON paper_orders(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_paper_positions_open ON paper_positions(symbol, timeframe) WHERE status = 'open';
CREATE INDEX IF NOT EXISTS idx_paper_trades_symbol ON paper_trades(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_paper_snapshots_ts ON paper_account_snapshots(ts DESC);
CREATE INDEX IF NOT EXISTS idx_paper_topups_ts ON paper_topups(ts DESC);

-- Compression: auto-compress data older than 7 days
SELECT add_compression_policy('candles', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('feature_values', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('labels', INTERVAL '7 days', if_not_exists => TRUE);
