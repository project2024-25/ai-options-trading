-- AI Options Trading Database Schema
-- This schema stores your live NIFTY ₹24,833.6 data and 30+ Lakh OI options data

-- Enable TimescaleDB extension for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Market Data Candles Table
CREATE TABLE market_data_candles (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 5min, 15min, 1hr, daily
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(12,4) NOT NULL,
    high DECIMAL(12,4) NOT NULL,
    low DECIMAL(12,4) NOT NULL,
    close DECIMAL(12,4) NOT NULL, -- Your ₹24,833.6 NIFTY price
    volume BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timeframe, timestamp)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('market_data_candles', 'timestamp', if_not_exists => TRUE);

-- Options Chain Data Table
CREATE TABLE options_chain (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    expiry DATE NOT NULL,
    strike DECIMAL(10,2) NOT NULL,
    option_type VARCHAR(2) NOT NULL, -- CE/PE
    ltp DECIMAL(10,4),
    bid DECIMAL(10,4),
    ask DECIMAL(10,4),
    volume BIGINT DEFAULT 0,
    oi BIGINT DEFAULT 0, -- Your 30+ Lakh OI data
    delta DECIMAL(6,4),
    gamma DECIMAL(8,6),
    theta DECIMAL(8,4),
    vega DECIMAL(8,4),
    rho DECIMAL(8,4),
    iv DECIMAL(6,4), -- Implied Volatility
    intrinsic_value DECIMAL(10,4),
    time_value DECIMAL(10,4),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, expiry, strike, option_type, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('options_chain', 'timestamp', if_not_exists => TRUE);

-- Trading Signals Table
CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(50) NOT NULL, -- BULL_CALL_SPREAD, BEAR_PUT_SPREAD, etc.
    direction VARCHAR(10) NOT NULL, -- BULLISH/BEARISH/NEUTRAL
    entry_price DECIMAL(10,4),
    stop_loss DECIMAL(10,4),
    target_price DECIMAL(10,4),
    confidence_score DECIMAL(3,2), -- 0.00 to 10.00
    reasoning TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE/TRIGGERED/EXPIRED/CANCELLED
    timeframe VARCHAR(10),
    market_conditions JSONB, -- Store market context
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Active Positions Table
CREATE TABLE active_positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    entry_date TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL(10,4) NOT NULL,
    quantity INTEGER NOT NULL,
    current_price DECIMAL(10,4),
    unrealized_pnl DECIMAL(12,4),
    delta DECIMAL(6,4),
    gamma DECIMAL(8,6),
    theta DECIMAL(8,4),
    vega DECIMAL(8,4),
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN/CLOSED/PARTIAL
    option_details JSONB, -- Store complete option info
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historical Trades Table
CREATE TABLE historical_trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    entry_date TIMESTAMPTZ NOT NULL,
    exit_date TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL(10,4) NOT NULL,
    exit_price DECIMAL(10,4) NOT NULL,
    quantity INTEGER NOT NULL,
    realized_pnl DECIMAL(12,4) NOT NULL,
    hold_duration INTERVAL,
    win_loss VARCHAR(4), -- WIN/LOSS
    max_profit DECIMAL(12,4),
    max_drawdown DECIMAL(12,4),
    trade_details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System Configuration Table
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL, -- STRING/NUMBER/BOOLEAN/JSON
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- VIX Data Table
CREATE TABLE vix_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(8,4),
    high DECIMAL(8,4),
    low DECIMAL(8,4),
    close DECIMAL(8,4), -- Current VIX level
    volume BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp)
);

SELECT create_hypertable('vix_data', 'timestamp', if_not_exists => TRUE);

-- Technical Indicators Table (for caching calculated indicators)
CREATE TABLE technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    indicator_value DECIMAL(12,6),
    indicator_data JSONB, -- For complex indicators
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timeframe, timestamp, indicator_name)
);

SELECT create_hypertable('technical_indicators', 'timestamp', if_not_exists => TRUE);

-- Performance Metrics Table
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_pnl DECIMAL(12,4) NOT NULL,
    realized_pnl DECIMAL(12,4) NOT NULL,
    unrealized_pnl DECIMAL(12,4) NOT NULL,
    number_of_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2),
    avg_win DECIMAL(10,4),
    avg_loss DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    sharpe_ratio DECIMAL(6,4),
    portfolio_value DECIMAL(15,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date)
);

-- Indexes for Performance
CREATE INDEX idx_market_data_symbol_timeframe_timestamp 
ON market_data_candles(symbol, timeframe, timestamp DESC);

CREATE INDEX idx_market_data_timestamp 
ON market_data_candles(timestamp DESC);

CREATE INDEX idx_options_chain_symbol_expiry_strike 
ON options_chain(symbol, expiry, strike, option_type);

CREATE INDEX idx_options_chain_timestamp 
ON options_chain(timestamp DESC);

CREATE INDEX idx_options_chain_oi 
ON options_chain(oi DESC) WHERE oi > 0;

CREATE INDEX idx_trading_signals_symbol_status_created 
ON trading_signals(symbol, status, created_at DESC);

CREATE INDEX idx_trading_signals_status 
ON trading_signals(status) WHERE status = 'ACTIVE';

CREATE INDEX idx_active_positions_symbol_status 
ON active_positions(symbol, status);

CREATE INDEX idx_historical_trades_symbol_date 
ON historical_trades(symbol, entry_date DESC);

CREATE INDEX idx_technical_indicators_symbol_timeframe_timestamp 
ON technical_indicators(symbol, timeframe, timestamp DESC);

CREATE INDEX idx_vix_timestamp 
ON vix_data(timestamp DESC);

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('max_risk_per_trade', '2.0', 'NUMBER', 'Maximum risk percentage per trade'),
('max_portfolio_risk', '10.0', 'NUMBER', 'Maximum portfolio risk percentage'),
('min_days_to_expiry', '7', 'NUMBER', 'Minimum days to expiry for options'),
('max_days_to_expiry', '45', 'NUMBER', 'Maximum days to expiry for options'),
('min_delta', '0.15', 'NUMBER', 'Minimum delta for options'),
('max_delta', '0.85', 'NUMBER', 'Maximum delta for options'),
('trading_enabled', 'false', 'BOOLEAN', 'Enable/disable live trading'),
('data_collection_enabled', 'true', 'BOOLEAN', 'Enable/disable data collection'),
('notification_enabled', 'true', 'BOOLEAN', 'Enable/disable notifications');

-- Views for common queries
CREATE VIEW current_nifty_price AS
SELECT 
    close as current_price,
    timestamp as last_update,
    (close - LAG(close) OVER (ORDER BY timestamp)) as price_change,
    ((close - LAG(close) OVER (ORDER BY timestamp)) / LAG(close) OVER (ORDER BY timestamp)) * 100 as change_percent
FROM market_data_candles 
WHERE symbol = 'NIFTY' AND timeframe = '5min' 
ORDER BY timestamp DESC 
LIMIT 1;

CREATE VIEW nifty_options_summary AS
SELECT 
    symbol,
    expiry,
    option_type,
    COUNT(*) as total_strikes,
    SUM(oi) as total_oi,
    AVG(iv) as avg_iv,
    MAX(timestamp) as last_update
FROM options_chain 
WHERE symbol = 'NIFTY'
GROUP BY symbol, expiry, option_type
ORDER BY expiry, option_type;

CREATE VIEW max_pain_current AS
WITH pain_calculation AS (
    SELECT 
        strike as test_price,
        SUM(CASE 
            WHEN option_type = 'CE' AND strike < 24833.6 THEN (24833.6 - strike) * oi
            WHEN option_type = 'PE' AND strike > 24833.6 THEN (strike - 24833.6) * oi
            ELSE 0 
        END) as total_pain
    FROM options_chain 
    WHERE symbol = 'NIFTY' 
        AND expiry = (SELECT MIN(expiry) FROM options_chain WHERE expiry > CURRENT_DATE)
    GROUP BY strike
)
SELECT 
    test_price as max_pain_strike,
    total_pain
FROM pain_calculation 
ORDER BY total_pain ASC 
LIMIT 1;

-- Function to clean up old data (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_data() RETURNS void AS $$
BEGIN
    -- Keep 1 year of 5min data
    DELETE FROM market_data_candles 
    WHERE timeframe = '5min' AND timestamp < NOW() - INTERVAL '1 year';
    
    -- Keep 2 years of 15min+ data
    DELETE FROM market_data_candles 
    WHERE timeframe IN ('15min', '1hr', 'daily') AND timestamp < NOW() - INTERVAL '2 years';
    
    -- Keep 6 months of options data
    DELETE FROM options_chain 
    WHERE timestamp < NOW() - INTERVAL '6 months';
    
    -- Keep 3 months of technical indicators
    DELETE FROM technical_indicators 
    WHERE timestamp < NOW() - INTERVAL '3 months';
    
    RAISE NOTICE 'Old data cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (run monthly)
-- Note: You'll need to set up a cron job or use pg_cron extension

COMMENT ON TABLE market_data_candles IS 'Stores NIFTY/BANKNIFTY candle data across all timeframes';
COMMENT ON TABLE options_chain IS 'Stores complete options chain data with Greeks and OI';
COMMENT ON TABLE trading_signals IS 'Generated trading signals with confidence scores';
COMMENT ON TABLE active_positions IS 'Currently open positions with real-time P&L';
COMMENT ON TABLE historical_trades IS 'Completed trades for performance analysis';
COMMENT ON TABLE system_config IS 'System configuration parameters';
COMMENT ON TABLE technical_indicators IS 'Cached technical indicator values';
COMMENT ON TABLE performance_metrics IS 'Daily performance tracking';