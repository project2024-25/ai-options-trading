"""
Database connection and management for Data Acquisition Service
"""

import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Global variables
_engine = None
_session_factory = None
_pg_pool = None


async def create_database_engine():
    """Create database engine"""
    global _engine
    
    if _engine is None:
        settings = get_settings()
        
        # Create async engine
        _engine = create_async_engine(
            settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.DEBUG_MODE,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour
        )
        
        logger.info("Database engine created successfully")
    
    return _engine


async def create_session_factory():
    """Create session factory"""
    global _session_factory
    
    if _session_factory is None:
        engine = await create_database_engine()
        _session_factory = async_sessionmaker(
            engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Session factory created successfully")
    
    return _session_factory


async def create_pg_pool():
    """Create asyncpg connection pool for direct SQL operations"""
    global _pg_pool
    
    if _pg_pool is None:
        settings = get_settings()
        
        _pg_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60,
            server_settings={
                'jit': 'off'  # Disable JIT for better performance with frequent connections
            }
        )
        
        logger.info("AsyncPG connection pool created successfully")
    
    return _pg_pool


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager"""
    session_factory = await create_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_database():
    """Get database connection (for health checks and simple operations)"""
    pool = await create_pg_pool()
    return pool


@asynccontextmanager
async def get_pg_connection():
    """Get direct PostgreSQL connection from pool"""
    pool = await create_pg_pool()
    
    async with pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            raise


async def execute_query(query: str, *args, fetch: str = "all") -> Optional[list]:
    """
    Execute a raw SQL query
    
    Args:
        query: SQL query string
        *args: Query parameters
        fetch: "all", "one", "val" (value), or "none"
    
    Returns:
        Query results based on fetch parameter
    """
    async with get_pg_connection() as conn:
        try:
            if fetch == "all":
                return await conn.fetch(query, *args)
            elif fetch == "one":
                return await conn.fetchrow(query, *args)
            elif fetch == "val":
                return await conn.fetchval(query, *args)
            elif fetch == "none":
                await conn.execute(query, *args)
                return None
            else:
                raise ValueError(f"Invalid fetch parameter: {fetch}")
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise


async def create_tables():
    """Create database tables if they don't exist"""
    async with get_pg_connection() as conn:
        try:
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            
            # Create market_data_candles table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data_candles (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    open DECIMAL(10,2) NOT NULL,
                    high DECIMAL(10,2) NOT NULL,
                    low DECIMAL(10,2) NOT NULL,
                    close DECIMAL(10,2) NOT NULL,
                    volume BIGINT NOT NULL DEFAULT 0,
                    oi BIGINT DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(symbol, timeframe, timestamp)
                );
            """)
            
            # Convert to hypertable for time-series optimization
            try:
                await conn.execute("""
                    SELECT create_hypertable('market_data_candles', 'timestamp', 
                                           if_not_exists => TRUE);
                """)
            except Exception as e:
                # Hypertable might already exist
                logger.warning(f"Hypertable creation warning: {e}")
            
            # Create options_chain table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS options_chain (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    expiry DATE NOT NULL,
                    strike DECIMAL(10,2) NOT NULL,
                    option_type VARCHAR(2) NOT NULL, -- CE or PE
                    timestamp TIMESTAMPTZ NOT NULL,
                    ltp DECIMAL(10,2),
                    bid DECIMAL(10,2),
                    ask DECIMAL(10,2),
                    volume BIGINT DEFAULT 0,
                    oi BIGINT DEFAULT 0,
                    delta DECIMAL(8,4),
                    gamma DECIMAL(8,4),
                    theta DECIMAL(8,4),
                    vega DECIMAL(8,4),
                    rho DECIMAL(8,4),
                    iv DECIMAL(6,2),
                    intrinsic_value DECIMAL(10,2),
                    time_value DECIMAL(10,2),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(symbol, expiry, strike, option_type, timestamp)
                );
            """)
            
            # Convert options_chain to hypertable
            try:
                await conn.execute("""
                    SELECT create_hypertable('options_chain', 'timestamp', 
                                           if_not_exists => TRUE);
                """)
            except Exception as e:
                logger.warning(f"Options chain hypertable creation warning: {e}")
            
            # Create trading_signals table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    symbol VARCHAR(20) NOT NULL,
                    strategy_type VARCHAR(50) NOT NULL,
                    signal_strength INTEGER CHECK (signal_strength >= 1 AND signal_strength <= 10),
                    recommended_trade JSONB,
                    entry_price_range JSONB,
                    stop_loss DECIMAL(10,2),
                    target_price DECIMAL(10,2),
                    expected_pnl JSONB,
                    greeks_analysis JSONB,
                    approval_status VARCHAR(20) DEFAULT 'pending',
                    execution_status VARCHAR(20) DEFAULT 'pending',
                    confidence_score DECIMAL(4,2),
                    market_conditions JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create active_positions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS active_positions (
                    id SERIAL PRIMARY KEY,
                    entry_datetime TIMESTAMPTZ NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    strategy VARCHAR(50) NOT NULL,
                    option_details JSONB NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price DECIMAL(10,2) NOT NULL,
                    current_price DECIMAL(10,2),
                    pnl_amount DECIMAL(12,2),
                    pnl_percentage DECIMAL(6,2),
                    delta DECIMAL(8,4),
                    gamma DECIMAL(8,4),
                    theta DECIMAL(8,4),
                    vega DECIMAL(8,4),
                    days_to_expiry INTEGER,
                    exit_conditions JSONB,
                    risk_status VARCHAR(20) DEFAULT 'normal',
                    is_active BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create historical_trades table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS historical_trades (
                    id SERIAL PRIMARY KEY,
                    trade_date DATE NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    strategy VARCHAR(50) NOT NULL,
                    entry_price DECIMAL(10,2) NOT NULL,
                    exit_price DECIMAL(10,2) NOT NULL,
                    quantity INTEGER NOT NULL,
                    hold_duration INTERVAL,
                    pnl_amount DECIMAL(12,2) NOT NULL,
                    pnl_percentage DECIMAL(6,2) NOT NULL,
                    max_drawdown DECIMAL(6,2),
                    strategy_effectiveness_score DECIMAL(4,2),
                    market_conditions JSONB,
                    entry_datetime TIMESTAMPTZ NOT NULL,
                    exit_datetime TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create system_config table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    id SERIAL PRIMARY KEY,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value JSONB NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    updated_by VARCHAR(50),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timeframe_timestamp 
                ON market_data_candles(symbol, timeframe, timestamp DESC);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_options_chain_symbol_expiry_timestamp 
                ON options_chain(symbol, expiry, timestamp DESC);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_options_chain_strike_type 
                ON options_chain(strike, option_type);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trading_signals_timestamp 
                ON trading_signals(timestamp DESC);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trading_signals_status 
                ON trading_signals(approval_status, execution_status);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_active_positions_symbol 
                ON active_positions(symbol, is_active);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_historical_trades_date 
                ON historical_trades(trade_date DESC);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_config_key 
                ON system_config(config_key) WHERE is_active = TRUE;
            """)
            
            logger.info("Database tables and indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise


async def insert_market_data(data: dict) -> bool:
    """Insert market data into database"""
    try:
        query = """
            INSERT INTO market_data_candles 
            (symbol, timeframe, timestamp, open, high, low, close, volume, oi)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (symbol, timeframe, timestamp) 
            DO UPDATE SET 
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                oi = EXCLUDED.oi
        """
        
        await execute_query(
            query,
            data['symbol'],
            data['timeframe'], 
            data['timestamp'],
            data['open'],
            data['high'],
            data['low'],
            data['close'],
            data.get('volume', 0),
            data.get('oi', 0),
            fetch="none"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error inserting market data: {e}")
        return False


async def insert_options_data(data: dict) -> bool:
    """Insert options chain data into database"""
    try:
        query = """
            INSERT INTO options_chain 
            (symbol, expiry, strike, option_type, timestamp, ltp, bid, ask, volume, oi,
             delta, gamma, theta, vega, rho, iv, intrinsic_value, time_value)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            ON CONFLICT (symbol, expiry, strike, option_type, timestamp)
            DO UPDATE SET 
                ltp = EXCLUDED.ltp,
                bid = EXCLUDED.bid,
                ask = EXCLUDED.ask,
                volume = EXCLUDED.volume,
                oi = EXCLUDED.oi,
                delta = EXCLUDED.delta,
                gamma = EXCLUDED.gamma,
                theta = EXCLUDED.theta,
                vega = EXCLUDED.vega,
                rho = EXCLUDED.rho,
                iv = EXCLUDED.iv,
                intrinsic_value = EXCLUDED.intrinsic_value,
                time_value = EXCLUDED.time_value
        """
        
        await execute_query(
            query,
            data['symbol'],
            data['expiry'],
            data['strike'],
            data['option_type'],
            data['timestamp'],
            data.get('ltp'),
            data.get('bid'),
            data.get('ask'),
            data.get('volume', 0),
            data.get('oi', 0),
            data.get('delta'),
            data.get('gamma'),
            data.get('theta'),
            data.get('vega'),
            data.get('rho'),
            data.get('iv'),
            data.get('intrinsic_value'),
            data.get('time_value'),
            fetch="none"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error inserting options data: {e}")
        return False


async def get_latest_candle_data(symbol: str, timeframe: str, limit: int = 100) -> list:
    """Get latest candle data for a symbol and timeframe"""
    try:
        query = """
            SELECT symbol, timeframe, timestamp, open, high, low, close, volume, oi
            FROM market_data_candles 
            WHERE symbol = $1 AND timeframe = $2
            ORDER BY timestamp DESC 
            LIMIT $3
        """
        
        result = await execute_query(query, symbol, timeframe, limit, fetch="all")
        
        return [dict(row) for row in result] if result else []
        
    except Exception as e:
        logger.error(f"Error getting candle data: {e}")
        return []


async def get_latest_options_chain(symbol: str, expiry: str = None, limit: int = 1000) -> list:
    """Get latest options chain data"""
    try:
        if expiry:
            query = """
                SELECT * FROM options_chain 
                WHERE symbol = $1 AND expiry = $2
                AND timestamp = (
                    SELECT MAX(timestamp) FROM options_chain 
                    WHERE symbol = $1 AND expiry = $2
                )
                ORDER BY strike, option_type
                LIMIT $3
            """
            result = await execute_query(query, symbol, expiry, limit, fetch="all")
        else:
            query = """
                SELECT DISTINCT ON (expiry, strike, option_type) *
                FROM options_chain 
                WHERE symbol = $1
                ORDER BY expiry, strike, option_type, timestamp DESC
                LIMIT $2
            """
            result = await execute_query(query, symbol, limit, fetch="all")
        
        return [dict(row) for row in result] if result else []
        
    except Exception as e:
        logger.error(f"Error getting options chain: {e}")
        return []


async def health_check_database() -> dict:
    """Perform database health check"""
    try:
        # Test basic connectivity
        result = await execute_query("SELECT 1 as test", fetch="val")
        if result != 1:
            return {"status": "unhealthy", "error": "Basic query failed"}
        
        # Test TimescaleDB extension
        try:
            await execute_query("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'", fetch="val")
            timescaledb_status = "enabled"
        except Exception:
            timescaledb_status = "disabled"
        
        # Get database stats
        stats_query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes
            FROM pg_stat_user_tables 
            WHERE tablename IN ('market_data_candles', 'options_chain', 'trading_signals')
        """
        stats = await execute_query(stats_query, fetch="all")
        
        return {
            "status": "healthy",
            "timescaledb": timescaledb_status,
            "table_stats": [dict(row) for row in stats] if stats else []
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def cleanup_old_data(days: int = 30):
    """Clean up old data to manage storage"""
    try:
        # Delete old candle data (keep more recent data)
        candle_query = """
            DELETE FROM market_data_candles 
            WHERE timestamp < NOW() - INTERVAL '%s days'
            AND timeframe IN ('1min', '5min')  -- Only clean up high-frequency data
        """
        
        # Delete old options chain data
        options_query = """
            DELETE FROM options_chain 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """
        
        await execute_query(candle_query % days, fetch="none")
        await execute_query(options_query % days, fetch="none")
        
        logger.info(f"Cleaned up data older than {days} days")
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")


async def close_connections():
    """Close all database connections"""
    global _engine, _session_factory, _pg_pool
    
    try:
        if _pg_pool:
            await _pg_pool.close()
            _pg_pool = None
            
        if _engine:
            await _engine.dispose()
            _engine = None
            
        _session_factory = None
        
        logger.info("Database connections closed successfully")
        
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Database initialization
async def init_database():
    """Initialize database with tables and basic configuration"""
    try:
        logger.info("Initializing database...")
        
        # Create tables
        await create_tables()
        
        # Insert default configuration
        default_configs = [
            {
                "config_key": "max_risk_per_trade",
                "config_value": {"value": 0.02, "type": "percentage"},
                "description": "Maximum risk per trade as percentage of account"
            },
            {
                "config_key": "max_portfolio_risk", 
                "config_value": {"value": 0.10, "type": "percentage"},
                "description": "Maximum portfolio risk as percentage of account"
            },
            {
                "config_key": "trading_enabled",
                "config_value": {"nifty": True, "banknifty": True},
                "description": "Enable/disable trading for different indices"
            }
        ]
        
        for config in default_configs:
            await execute_query(
                """
                INSERT INTO system_config (config_key, config_value, description)
                VALUES ($1, $2, $3)
                ON CONFLICT (config_key) DO NOTHING
                """,
                config["config_key"],
                config["config_value"],
                config["description"],
                fetch="none"
            )
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise