# services/database/migrations.py
import asyncio
import asyncpg
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://trading_user:your_secure_password@localhost:5432/trading_db')
    
    async def run_migrations(self):
        """Run all database migrations"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Create migrations tracking table
            await self.create_migrations_table(conn)
            
            # List of all migrations
            migrations = [
                ('001_initial_schema', self.migration_001_initial_schema),
                ('002_add_indexes', self.migration_002_add_indexes),
                ('003_add_views', self.migration_003_add_views),
                ('004_add_functions', self.migration_004_add_functions),
            ]
            
            for migration_name, migration_func in migrations:
                if not await self.is_migration_applied(conn, migration_name):
                    logger.info(f"Running migration: {migration_name}")
                    await migration_func(conn)
                    await self.mark_migration_applied(conn, migration_name)
                    logger.info(f"Migration {migration_name} completed")
                else:
                    logger.info(f"Migration {migration_name} already applied, skipping")
            
            await conn.close()
            logger.info("All migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def create_migrations_table(self, conn):
        """Create table to track applied migrations"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    
    async def is_migration_applied(self, conn, migration_name: str) -> bool:
        """Check if migration has been applied"""
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = $1",
            migration_name
        )
        return result > 0
    
    async def mark_migration_applied(self, conn, migration_name: str):
        """Mark migration as applied"""
        await conn.execute(
            "INSERT INTO schema_migrations (migration_name) VALUES ($1)",
            migration_name
        )
    
    async def migration_001_initial_schema(self, conn):
        """Initial database schema - your live NIFTY ₹24,833.6 data structure"""
        
        # Enable TimescaleDB extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        
        # Market Data Candles Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data_candles (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                open DECIMAL(12,4) NOT NULL,
                high DECIMAL(12,4) NOT NULL,
                low DECIMAL(12,4) NOT NULL,
                close DECIMAL(12,4) NOT NULL,
                volume BIGINT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(symbol, timeframe, timestamp)
            )
        """)
        
        # Convert to hypertable
        try:
            await conn.execute("SELECT create_hypertable('market_data_candles', 'timestamp', if_not_exists => TRUE)")
        except Exception as e:
            logger.warning(f"Hypertable creation warning: {e}")
        
        # Options Chain Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS options_chain (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                expiry DATE NOT NULL,
                strike DECIMAL(10,2) NOT NULL,
                option_type VARCHAR(2) NOT NULL,
                ltp DECIMAL(10,4),
                bid DECIMAL(10,4),
                ask DECIMAL(10,4),
                volume BIGINT DEFAULT 0,
                oi BIGINT DEFAULT 0,
                delta DECIMAL(6,4),
                gamma DECIMAL(8,6),
                theta DECIMAL(8,4),
                vega DECIMAL(8,4),
                rho DECIMAL(8,4),
                iv DECIMAL(6,4),
                intrinsic_value DECIMAL(10,4),
                time_value DECIMAL(10,4),
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(symbol, expiry, strike, option_type, timestamp)
            )
        """)
        
        try:
            await conn.execute("SELECT create_hypertable('options_chain', 'timestamp', if_not_exists => TRUE)")
        except Exception as e:
            logger.warning(f"Options hypertable creation warning: {e}")
        
        # Trading Signals Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trading_signals (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                signal_type VARCHAR(50) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                entry_price DECIMAL(10,4),
                stop_loss DECIMAL(10,4),
                target_price DECIMAL(10,4),
                confidence_score DECIMAL(3,2),
                reasoning TEXT,
                status VARCHAR(20) DEFAULT 'ACTIVE',
                timeframe VARCHAR(10),
                market_conditions JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Active Positions Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS active_positions (
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
                status VARCHAR(20) DEFAULT 'OPEN',
                option_details JSONB,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Historical Trades Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS historical_trades (
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
                win_loss VARCHAR(4),
                max_profit DECIMAL(12,4),
                max_drawdown DECIMAL(12,4),
                trade_details JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # System Configuration Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(100) UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                config_type VARCHAR(20) NOT NULL,
                description TEXT,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # VIX Data Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS vix_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                open DECIMAL(8,4),
                high DECIMAL(8,4),
                low DECIMAL(8,4),
                close DECIMAL(8,4),
                volume BIGINT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(timestamp)
            )
        """)
        
        try:
            await conn.execute("SELECT create_hypertable('vix_data', 'timestamp', if_not_exists => TRUE)")
        except Exception as e:
            logger.warning(f"VIX hypertable creation warning: {e}")
        
        # Technical Indicators Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                indicator_name VARCHAR(50) NOT NULL,
                indicator_value DECIMAL(12,6),
                indicator_data JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(symbol, timeframe, timestamp, indicator_name)
            )
        """)
        
        try:
            await conn.execute("SELECT create_hypertable('technical_indicators', 'timestamp', if_not_exists => TRUE)")
        except Exception as e:
            logger.warning(f"Technical indicators hypertable creation warning: {e}")
        
        # Performance Metrics Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
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
            )
        """)
        
        # Insert default system configuration
        await conn.execute("""
            INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
            ('max_risk_per_trade', '2.0', 'NUMBER', 'Maximum risk percentage per trade'),
            ('max_portfolio_risk', '10.0', 'NUMBER', 'Maximum portfolio risk percentage'),
            ('min_days_to_expiry', '7', 'NUMBER', 'Minimum days to expiry for options'),
            ('max_days_to_expiry', '45', 'NUMBER', 'Maximum days to expiry for options'),
            ('min_delta', '0.15', 'NUMBER', 'Minimum delta for options'),
            ('max_delta', '0.85', 'NUMBER', 'Maximum delta for options'),
            ('trading_enabled', 'false', 'BOOLEAN', 'Enable/disable live trading'),
            ('data_collection_enabled', 'true', 'BOOLEAN', 'Enable/disable data collection'),
            ('notification_enabled', 'true', 'BOOLEAN', 'Enable/disable notifications')
            ON CONFLICT (config_key) DO NOTHING
        """)
    
    async def migration_002_add_indexes(self, conn):
        """Add performance indexes"""
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timeframe_timestamp ON market_data_candles(symbol, timeframe, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data_candles(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_options_chain_symbol_expiry_strike ON options_chain(symbol, expiry, strike, option_type)",
            "CREATE INDEX IF NOT EXISTS idx_options_chain_timestamp ON options_chain(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_options_chain_oi ON options_chain(oi DESC) WHERE oi > 0",
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_status_created ON trading_signals(symbol, status, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_status ON trading_signals(status) WHERE status = 'ACTIVE'",
            "CREATE INDEX IF NOT EXISTS idx_active_positions_symbol_status ON active_positions(symbol, status)",
            "CREATE INDEX IF NOT EXISTS idx_historical_trades_symbol_date ON historical_trades(symbol, entry_date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_timeframe_timestamp ON technical_indicators(symbol, timeframe, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_vix_timestamp ON vix_data(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_options_chain_strike_expiry ON options_chain(strike, expiry) WHERE oi > 1000"
        ]
        
        for index_sql in indexes:
            try:
                await conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
    
    async def migration_003_add_views(self, conn):
        """Add useful database views"""
        
        # Current NIFTY Price View
        await conn.execute("""
            CREATE OR REPLACE VIEW current_nifty_price AS
            SELECT 
                close as current_price,
                timestamp as last_update,
                (close - LAG(close) OVER (ORDER BY timestamp)) as price_change,
                ((close - LAG(close) OVER (ORDER BY timestamp)) / LAG(close) OVER (ORDER BY timestamp)) * 100 as change_percent
            FROM market_data_candles 
            WHERE symbol = 'NIFTY' AND timeframe = '5min' 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        
        # NIFTY Options Summary View
        await conn.execute("""
            CREATE OR REPLACE VIEW nifty_options_summary AS
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
            ORDER BY expiry, option_type
        """)
        
        # Max Pain Current View
        await conn.execute("""
            CREATE OR REPLACE VIEW max_pain_current AS
            WITH current_price AS (
                SELECT close as price FROM market_data_candles 
                WHERE symbol = 'NIFTY' AND timeframe = '5min' 
                ORDER BY timestamp DESC LIMIT 1
            ),
            pain_calculation AS (
                SELECT 
                    strike as test_price,
                    SUM(CASE 
                        WHEN option_type = 'CE' AND (SELECT price FROM current_price) > strike 
                        THEN ((SELECT price FROM current_price) - strike) * oi
                        WHEN option_type = 'PE' AND (SELECT price FROM current_price) < strike 
                        THEN (strike - (SELECT price FROM current_price)) * oi
                        ELSE 0 
                    END) as total_pain
                FROM options_chain 
                WHERE symbol = 'NIFTY' 
                    AND expiry = (SELECT MIN(expiry) FROM options_chain WHERE expiry > CURRENT_DATE)
                    AND timestamp = (
                        SELECT MAX(timestamp) FROM options_chain 
                        WHERE symbol = 'NIFTY' 
                        AND expiry = (SELECT MIN(expiry) FROM options_chain WHERE expiry > CURRENT_DATE)
                    )
                GROUP BY strike
            )
            SELECT 
                test_price as max_pain_strike,
                total_pain,
                (SELECT price FROM current_price) as current_price
            FROM pain_calculation 
            ORDER BY total_pain ASC 
            LIMIT 1
        """)
        
        # Portfolio Summary View
        await conn.execute("""
            CREATE OR REPLACE VIEW portfolio_summary AS
            SELECT 
                COUNT(*) as total_positions,
                SUM(unrealized_pnl) as total_unrealized_pnl,
                SUM(ABS(delta * quantity)) as total_delta_exposure,
                SUM(ABS(gamma * quantity)) as total_gamma_exposure,
                SUM(theta * quantity) as total_theta_decay,
                SUM(ABS(vega * quantity)) as total_vega_exposure,
                AVG(unrealized_pnl) as avg_position_pnl
            FROM active_positions 
            WHERE status = 'OPEN'
        """)
        
        # Daily Performance Summary View
        await conn.execute("""
            CREATE OR REPLACE VIEW daily_performance_summary AS
            SELECT 
                DATE(created_at) as trade_date,
                COUNT(*) as trades_count,
                SUM(CASE WHEN win_loss = 'WIN' THEN 1 ELSE 0 END) as winning_trades,
                SUM(realized_pnl) as daily_pnl,
                AVG(realized_pnl) as avg_trade_pnl,
                MAX(realized_pnl) as best_trade,
                MIN(realized_pnl) as worst_trade
            FROM historical_trades 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY trade_date DESC
        """)
        
        # High OI Strikes View
        await conn.execute("""
            CREATE OR REPLACE VIEW high_oi_strikes AS
            SELECT 
                symbol,
                expiry,
                strike,
                option_type,
                oi,
                ltp,
                iv,
                delta,
                ROW_NUMBER() OVER (PARTITION BY symbol, expiry ORDER BY oi DESC) as oi_rank
            FROM options_chain 
            WHERE oi > 10000 
                AND timestamp = (
                    SELECT MAX(timestamp) FROM options_chain o2 
                    WHERE o2.symbol = options_chain.symbol 
                    AND o2.expiry = options_chain.expiry
                )
            ORDER BY symbol, expiry, oi DESC
        """)
    
    async def migration_004_add_functions(self, conn):
        """Add useful database functions"""
        
        # Function to calculate Max Pain for any symbol/expiry
        await conn.execute("""
            CREATE OR REPLACE FUNCTION calculate_max_pain(
                p_symbol VARCHAR(20), 
                p_expiry DATE DEFAULT NULL
            ) RETURNS TABLE(max_pain_strike DECIMAL(10,2), total_pain DECIMAL(20,4)) AS $
            DECLARE
                target_expiry DATE;
                current_price DECIMAL(12,4);
            BEGIN
                -- Get target expiry
                IF p_expiry IS NULL THEN
                    SELECT MIN(expiry) INTO target_expiry 
                    FROM options_chain 
                    WHERE symbol = p_symbol AND expiry > CURRENT_DATE;
                ELSE
                    target_expiry := p_expiry;
                END IF;
                
                -- Get current price
                SELECT close INTO current_price 
                FROM market_data_candles 
                WHERE symbol = p_symbol AND timeframe = '5min'
                ORDER BY timestamp DESC 
                LIMIT 1;
                
                -- Calculate max pain
                RETURN QUERY
                WITH pain_calc AS (
                    SELECT 
                        strike as test_strike,
                        SUM(CASE 
                            WHEN option_type = 'CE' AND current_price > strike 
                            THEN (current_price - strike) * oi
                            WHEN option_type = 'PE' AND current_price < strike 
                            THEN (strike - current_price) * oi
                            ELSE 0 
                        END) as pain
                    FROM options_chain 
                    WHERE symbol = p_symbol 
                        AND expiry = target_expiry
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain 
                            WHERE symbol = p_symbol AND expiry = target_expiry
                        )
                    GROUP BY strike
                )
                SELECT test_strike, pain
                FROM pain_calc 
                ORDER BY pain ASC 
                LIMIT 1;
            END;
            $ LANGUAGE plpgsql;
        """)
        
        # Function to get PCR for any symbol/expiry
        await conn.execute("""
            CREATE OR REPLACE FUNCTION calculate_pcr(
                p_symbol VARCHAR(20), 
                p_expiry DATE DEFAULT NULL
            ) RETURNS TABLE(pcr_oi DECIMAL(6,4), pcr_volume DECIMAL(6,4), ce_oi BIGINT, pe_oi BIGINT) AS $
            DECLARE
                target_expiry DATE;
            BEGIN
                -- Get target expiry
                IF p_expiry IS NULL THEN
                    SELECT MIN(expiry) INTO target_expiry 
                    FROM options_chain 
                    WHERE symbol = p_symbol AND expiry > CURRENT_DATE;
                ELSE
                    target_expiry := p_expiry;
                END IF;
                
                RETURN QUERY
                WITH oi_summary AS (
                    SELECT 
                        option_type,
                        SUM(oi) as total_oi,
                        SUM(volume) as total_volume
                    FROM options_chain 
                    WHERE symbol = p_symbol 
                        AND expiry = target_expiry
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain 
                            WHERE symbol = p_symbol AND expiry = target_expiry
                        )
                    GROUP BY option_type
                ),
                ce_data AS (SELECT total_oi as ce_oi_val, total_volume as ce_vol FROM oi_summary WHERE option_type = 'CE'),
                pe_data AS (SELECT total_oi as pe_oi_val, total_volume as pe_vol FROM oi_summary WHERE option_type = 'PE')
                SELECT 
                    CASE WHEN ce_data.ce_oi_val > 0 THEN pe_data.pe_oi_val::DECIMAL / ce_data.ce_oi_val ELSE 0 END,
                    CASE WHEN ce_data.ce_vol > 0 THEN pe_data.pe_vol::DECIMAL / ce_data.ce_vol ELSE 0 END,
                    ce_data.ce_oi_val,
                    pe_data.pe_oi_val
                FROM ce_data, pe_data;
            END;
            $ LANGUAGE plpgsql;
        """)
        
        # Function to clean up old data
        await conn.execute("""
            CREATE OR REPLACE FUNCTION cleanup_old_data() RETURNS TEXT AS $
            DECLARE
                result_text TEXT := '';
                rows_deleted INTEGER;
            BEGIN
                -- Clean 5min market data (keep 1 year)
                DELETE FROM market_data_candles 
                WHERE timeframe = '5min' AND timestamp < NOW() - INTERVAL '1 year';
                GET DIAGNOSTICS rows_deleted = ROW_COUNT;
                result_text := result_text || 'Deleted ' || rows_deleted || ' 5min candles. ';
                
                -- Clean other timeframe data (keep 2 years)
                DELETE FROM market_data_candles 
                WHERE timeframe != '5min' AND timestamp < NOW() - INTERVAL '2 years';
                GET DIAGNOSTICS rows_deleted = ROW_COUNT;
                result_text := result_text || 'Deleted ' || rows_deleted || ' other timeframe candles. ';
                
                -- Clean options data (keep 6 months)
                DELETE FROM options_chain 
                WHERE timestamp < NOW() - INTERVAL '6 months';
                GET DIAGNOSTICS rows_deleted = ROW_COUNT;
                result_text := result_text || 'Deleted ' || rows_deleted || ' options records. ';
                
                -- Clean technical indicators (keep 3 months)
                DELETE FROM technical_indicators 
                WHERE timestamp < NOW() - INTERVAL '3 months';
                GET DIAGNOSTICS rows_deleted = ROW_COUNT;
                result_text := result_text || 'Deleted ' || rows_deleted || ' indicator records. ';
                
                -- Clean expired signals
                UPDATE trading_signals 
                SET status = 'EXPIRED' 
                WHERE status = 'ACTIVE' AND created_at < NOW() - INTERVAL '7 days';
                GET DIAGNOSTICS rows_deleted = ROW_COUNT;
                result_text := result_text || 'Expired ' || rows_deleted || ' old signals.';
                
                RETURN result_text;
            END;
            $ LANGUAGE plpgsql;
        """)
        
        # Function to get system health metrics
        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_system_health() RETURNS TABLE(
                metric_name TEXT,
                metric_value TEXT,
                status TEXT
            ) AS $
            BEGIN
                -- Market data freshness
                RETURN QUERY
                SELECT 
                    'market_data_freshness'::TEXT,
                    EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))::TEXT || ' seconds',
                    CASE 
                        WHEN MAX(timestamp) > NOW() - INTERVAL '10 minutes' THEN 'HEALTHY'
                        WHEN MAX(timestamp) > NOW() - INTERVAL '1 hour' THEN 'WARNING'
                        ELSE 'CRITICAL'
                    END
                FROM market_data_candles 
                WHERE symbol = 'NIFTY' AND timeframe = '5min';
                
                -- Options data freshness
                RETURN QUERY
                SELECT 
                    'options_data_freshness'::TEXT,
                    EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))::TEXT || ' seconds',
                    CASE 
                        WHEN MAX(timestamp) > NOW() - INTERVAL '10 minutes' THEN 'HEALTHY'
                        WHEN MAX(timestamp) > NOW() - INTERVAL '1 hour' THEN 'WARNING'
                        ELSE 'CRITICAL'
                    END
                FROM options_chain 
                WHERE symbol = 'NIFTY';
                
                -- Active positions count
                RETURN QUERY
                SELECT 
                    'active_positions'::TEXT,
                    COUNT(*)::TEXT,
                    CASE 
                        WHEN COUNT(*) < 10 THEN 'HEALTHY'
                        WHEN COUNT(*) < 20 THEN 'WARNING'
                        ELSE 'CRITICAL'
                    END
                FROM active_positions 
                WHERE status = 'OPEN';
                
                -- Database size
                RETURN QUERY
                SELECT 
                    'database_size'::TEXT,
                    pg_size_pretty(pg_database_size(current_database())),
                    'INFO'::TEXT;
                
                RETURN;
            END;
            $ LANGUAGE plpgsql;
        """)

async def run_initial_migration():
    """Run initial database migration"""
    try:
        migration = DatabaseMigration()
        await migration.run_migrations()
        print("✅ Database migration completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False

if __name__ == "__main__":
    # Run migrations when script is executed directly
    asyncio.run(run_initial_migration())