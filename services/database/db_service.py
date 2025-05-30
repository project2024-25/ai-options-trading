# services/database/db_service.py
import asyncio
import asyncpg
import json
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging
import os
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:your_secure_password@localhost:5432/trading_db')
        self.pool = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            await self.test_connection()
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def test_connection(self):
        """Test database connection"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval('SELECT 1')
            if result != 1:
                raise Exception("Database connection test failed")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        async with self.pool.acquire() as conn:
            yield conn
    
    # Market Data Methods
    async def store_market_data(self, symbol: str, timeframe: str, candle_data: Dict) -> bool:
        """Store your live NIFTY ₹24,833.6 data"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO market_data_candles 
                    (symbol, timeframe, timestamp, open, high, low, close, volume) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (symbol, timeframe, timestamp) 
                    DO UPDATE SET 
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """, 
                symbol, timeframe, candle_data['timestamp'], 
                Decimal(str(candle_data['open'])), Decimal(str(candle_data['high'])),
                Decimal(str(candle_data['low'])), Decimal(str(candle_data['close'])),
                candle_data['volume']
                )
            logger.info(f"Stored {symbol} {timeframe} data: ₹{candle_data['close']}")
            return True
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
            return False
    
    async def store_bulk_market_data(self, symbol: str, timeframe: str, candles_data: List[Dict]) -> bool:
        """Store multiple candles at once for better performance"""
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    for candle in candles_data:
                        await conn.execute("""
                            INSERT INTO market_data_candles 
                            (symbol, timeframe, timestamp, open, high, low, close, volume) 
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
                        """, 
                        symbol, timeframe, candle['timestamp'], 
                        Decimal(str(candle['open'])), Decimal(str(candle['high'])),
                        Decimal(str(candle['low'])), Decimal(str(candle['close'])),
                        candle['volume']
                        )
            logger.info(f"Stored {len(candles_data)} {symbol} {timeframe} candles")
            return True
        except Exception as e:
            logger.error(f"Error storing bulk market data: {e}")
            return False
    
    async def get_market_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict]:
        """Get historical market data"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT timestamp, open, high, low, close, volume
                    FROM market_data_candles 
                    WHERE symbol = $1 AND timeframe = $2
                    ORDER BY timestamp DESC 
                    LIMIT $3
                """, symbol, timeframe, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return []
    
    async def get_market_data_range(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get market data for specific date range"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT timestamp, open, high, low, close, volume
                    FROM market_data_candles 
                    WHERE symbol = $1 AND timeframe = $2 
                    AND timestamp BETWEEN $3 AND $4
                    ORDER BY timestamp ASC
                """, symbol, timeframe, start_date, end_date)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting market data range: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from latest 5min data"""
        try:
            async with self.get_connection() as conn:
                price = await conn.fetchval("""
                    SELECT close FROM market_data_candles 
                    WHERE symbol = $1 AND timeframe = '5min'
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, symbol)
                return price
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get the most recent candle"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM market_data_candles 
                    WHERE symbol = $1 AND timeframe = $2
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, symbol, timeframe)
                
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting latest candle: {e}")
            return None
    
    # Options Chain Methods
    async def store_options_chain(self, options_data: List[Dict]) -> bool:
        """Store your 30+ Lakh OI options data"""
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    for option in options_data:
                        await conn.execute("""
                            INSERT INTO options_chain 
                            (symbol, expiry, strike, option_type, ltp, bid, ask, volume, oi,
                             delta, gamma, theta, vega, rho, iv, intrinsic_value, time_value, timestamp) 
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
                        """, 
                        option['symbol'], option['expiry'], Decimal(str(option['strike'])),
                        option['option_type'], Decimal(str(option.get('ltp', 0))),
                        Decimal(str(option.get('bid', 0))), Decimal(str(option.get('ask', 0))),
                        option.get('volume', 0), option.get('oi', 0),
                        Decimal(str(option.get('delta', 0))), Decimal(str(option.get('gamma', 0))),
                        Decimal(str(option.get('theta', 0))), Decimal(str(option.get('vega', 0))),
                        Decimal(str(option.get('rho', 0))), Decimal(str(option.get('iv', 0))),
                        Decimal(str(option.get('intrinsic_value', 0))), 
                        Decimal(str(option.get('time_value', 0))),
                        option.get('timestamp', datetime.now())
                        )
            
            total_oi = sum(opt.get('oi', 0) for opt in options_data)
            logger.info(f"Stored options chain data. Total OI: {total_oi:,}")
            return True
        except Exception as e:
            logger.error(f"Error storing options data: {e}")
            return False
    
    async def get_options_chain(self, symbol: str, expiry: Optional[date] = None) -> List[Dict]:
        """Get current options chain data"""
        try:
            async with self.get_connection() as conn:
                if expiry:
                    query = """
                        SELECT * FROM options_chain 
                        WHERE symbol = $1 AND expiry = $2
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain 
                            WHERE symbol = $1 AND expiry = $2
                        )
                        ORDER BY strike, option_type
                    """
                    rows = await conn.fetch(query, symbol, expiry)
                else:
                    query = """
                        SELECT * FROM options_chain 
                        WHERE symbol = $1
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain WHERE symbol = $1
                        )
                        ORDER BY expiry, strike, option_type
                    """
                    rows = await conn.fetch(query, symbol)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting options chain: {e}")
            return []
    
    async def get_options_by_strike_range(self, symbol: str, min_strike: float, max_strike: float, expiry: Optional[date] = None) -> List[Dict]:
        """Get options within strike range"""
        try:
            async with self.get_connection() as conn:
                if expiry:
                    query = """
                        SELECT * FROM options_chain 
                        WHERE symbol = $1 AND expiry = $2 
                        AND strike BETWEEN $3 AND $4
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain 
                            WHERE symbol = $1 AND expiry = $2
                        )
                        ORDER BY strike, option_type
                    """
                    rows = await conn.fetch(query, symbol, expiry, Decimal(str(min_strike)), Decimal(str(max_strike)))
                else:
                    query = """
                        SELECT * FROM options_chain 
                        WHERE symbol = $1 AND strike BETWEEN $2 AND $3
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain WHERE symbol = $1
                        )
                        ORDER BY expiry, strike, option_type
                    """
                    rows = await conn.fetch(query, symbol, Decimal(str(min_strike)), Decimal(str(max_strike)))
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting options by strike range: {e}")
            return []
    
    async def get_high_oi_strikes(self, symbol: str, limit: int = 10, expiry: Optional[date] = None) -> List[Dict]:
        """Get strikes with highest Open Interest"""
        try:
            async with self.get_connection() as conn:
                if expiry:
                    query = """
                        SELECT strike, option_type, oi, ltp, iv
                        FROM options_chain 
                        WHERE symbol = $1 AND expiry = $2 AND oi > 0
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain 
                            WHERE symbol = $1 AND expiry = $2
                        )
                        ORDER BY oi DESC
                        LIMIT $3
                    """
                    rows = await conn.fetch(query, symbol, expiry, limit)
                else:
                    query = """
                        SELECT strike, option_type, oi, ltp, iv, expiry
                        FROM options_chain 
                        WHERE symbol = $1 AND oi > 0
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain WHERE symbol = $1
                        )
                        ORDER BY oi DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query, symbol, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting high OI strikes: {e}")
            return []
    
    async def get_max_pain(self, symbol: str, expiry: Optional[date] = None) -> Optional[Dict]:
        """Calculate Max Pain from stored OI data"""
        try:
            async with self.get_connection() as conn:
                if expiry:
                    expiry_filter = "AND expiry = $2"
                    params = [symbol, expiry]
                else:
                    expiry_filter = "AND expiry = (SELECT MIN(expiry) FROM options_chain WHERE expiry > CURRENT_DATE AND symbol = $1)"
                    params = [symbol]
                
                # Get current price for calculation
                current_price = await self.get_current_price(symbol)
                if not current_price:
                    current_price = Decimal('24833.6')  # Fallback to your live price
                
                query = f"""
                    WITH pain_calculation AS (
                        SELECT 
                            strike as test_price,
                            SUM(CASE 
                                WHEN option_type = 'CE' AND $${len(params)+1} > strike THEN ($${len(params)+1} - strike) * oi
                                WHEN option_type = 'PE' AND $${len(params)+1} < strike THEN (strike - $${len(params)+1}) * oi
                                ELSE 0 
                            END) as total_pain
                        FROM options_chain 
                        WHERE symbol = $1 {expiry_filter}
                            AND timestamp = (
                                SELECT MAX(timestamp) FROM options_chain 
                                WHERE symbol = $1 {expiry_filter}
                            )
                        GROUP BY strike
                    )
                    SELECT 
                        test_price as max_pain_strike,
                        total_pain,
                        $${len(params)+1} as current_price
                    FROM pain_calculation 
                    ORDER BY total_pain ASC 
                    LIMIT 1
                """
                params.append(current_price)
                
                result = await conn.fetchrow(query, *params)
                
                if result:
                    return {
                        'max_pain_strike': float(result['max_pain_strike']),
                        'current_price': float(result['current_price']),
                        'total_pain': float(result['total_pain']),
                        'distance_from_max_pain': float(result['current_price'] - result['max_pain_strike'])
                    }
                return None
        except Exception as e:
            logger.error(f"Error calculating max pain: {e}")
            return None
    
    async def get_pcr_ratio(self, symbol: str, expiry: Optional[date] = None) -> Optional[Dict]:
        """Calculate Put-Call Ratio from OI data"""
        try:
            async with self.get_connection() as conn:
                if expiry:
                    query = """
                        SELECT 
                            option_type,
                            SUM(oi) as total_oi,
                            SUM(volume) as total_volume
                        FROM options_chain 
                        WHERE symbol = $1 AND expiry = $2
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain 
                            WHERE symbol = $1 AND expiry = $2
                        )
                        GROUP BY option_type
                    """
                    rows = await conn.fetch(query, symbol, expiry)
                else:
                    query = """
                        SELECT 
                            option_type,
                            SUM(oi) as total_oi,
                            SUM(volume) as total_volume
                        FROM options_chain 
                        WHERE symbol = $1
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM options_chain WHERE symbol = $1
                        )
                        GROUP BY option_type
                    """
                    rows = await conn.fetch(query, symbol)
                
                data = {row['option_type']: {'oi': row['total_oi'], 'volume': row['total_volume']} for row in rows}
                
                if 'CE' in data and 'PE' in data:
                    pcr_oi = data['PE']['oi'] / data['CE']['oi'] if data['CE']['oi'] > 0 else 0
                    pcr_volume = data['PE']['volume'] / data['CE']['volume'] if data['CE']['volume'] > 0 else 0
                    
                    return {
                        'pcr_oi': round(pcr_oi, 4),
                        'pcr_volume': round(pcr_volume, 4),
                        'ce_oi': data['CE']['oi'],
                        'pe_oi': data['PE']['oi'],
                        'ce_volume': data['CE']['volume'],
                        'pe_volume': data['PE']['volume'],
                        'total_oi': data['CE']['oi'] + data['PE']['oi']
                    }
                return None
        except Exception as e:
            logger.error(f"Error calculating PCR: {e}")
            return None
    
    # VIX Data Methods
    async def store_vix_data(self, vix_data: Dict) -> bool:
        """Store VIX data"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO vix_data 
                    (timestamp, open, high, low, close, volume) 
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (timestamp) 
                    DO UPDATE SET 
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """, 
                vix_data['timestamp'], 
                Decimal(str(vix_data['open'])), Decimal(str(vix_data['high'])),
                Decimal(str(vix_data['low'])), Decimal(str(vix_data['close'])),
                vix_data.get('volume', 0)
                )
            logger.info(f"Stored VIX data: {vix_data['close']}")
            return True
        except Exception as e:
            logger.error(f"Error storing VIX data: {e}")
            return False
    
    async def get_vix_data(self, limit: int = 100) -> List[Dict]:
        """Get VIX historical data"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM vix_data 
                    ORDER BY timestamp DESC 
                    LIMIT $1
                """, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting VIX data: {e}")
            return []
    
    async def get_current_vix(self) -> Optional[Decimal]:
        """Get current VIX level"""
        try:
            async with self.get_connection() as conn:
                vix = await conn.fetchval("""
                    SELECT close FROM vix_data 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                return vix
        except Exception as e:
            logger.error(f"Error getting current VIX: {e}")
            return None
    
    # Trading Signals Methods
    async def store_trading_signal(self, signal_data: Dict) -> int:
        """Store generated trading signal"""
        try:
            async with self.get_connection() as conn:
                signal_id = await conn.fetchval("""
                    INSERT INTO trading_signals 
                    (symbol, signal_type, direction, entry_price, stop_loss, target_price,
                     confidence_score, reasoning, timeframe, market_conditions) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """, 
                signal_data['symbol'], signal_data['signal_type'], signal_data['direction'],
                Decimal(str(signal_data.get('entry_price', 0))), 
                Decimal(str(signal_data.get('stop_loss', 0))),
                Decimal(str(signal_data.get('target_price', 0))),
                Decimal(str(signal_data.get('confidence_score', 0))),
                signal_data.get('reasoning', ''), signal_data.get('timeframe', ''),
                json.dumps(signal_data.get('market_conditions', {}))
                )
                
                logger.info(f"Stored trading signal {signal_id}: {signal_data['signal_type']}")
                return signal_id
        except Exception as e:
            logger.error(f"Error storing trading signal: {e}")
            return None
    
    async def get_active_signals(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get active trading signals"""
        try:
            async with self.get_connection() as conn:
                if symbol:
                    query = """
                        SELECT * FROM trading_signals 
                        WHERE symbol = $1 AND status = 'ACTIVE'
                        ORDER BY created_at DESC
                    """
                    rows = await conn.fetch(query, symbol)
                else:
                    query = """
                        SELECT * FROM trading_signals 
                        WHERE status = 'ACTIVE'
                        ORDER BY created_at DESC
                    """
                    rows = await conn.fetch(query)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting active signals: {e}")
            return []
    
    async def update_signal_status(self, signal_id: int, status: str, notes: Optional[str] = None) -> bool:
        """Update trading signal status"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    UPDATE trading_signals 
                    SET status = $2, updated_at = NOW()
                    WHERE id = $1
                """, signal_id, status)
                
                logger.info(f"Updated signal {signal_id} status to {status}")
                return True
        except Exception as e:
            logger.error(f"Error updating signal status: {e}")
            return False
    
    # Technical Indicators Storage
    async def store_technical_indicator(self, symbol: str, timeframe: str, timestamp: datetime, 
                                      indicator_name: str, indicator_value: Optional[float] = None, 
                                      indicator_data: Optional[Dict] = None) -> bool:
        """Store calculated technical indicators for caching"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO technical_indicators 
                    (symbol, timeframe, timestamp, indicator_name, indicator_value, indicator_data) 
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (symbol, timeframe, timestamp, indicator_name) 
                    DO UPDATE SET 
                        indicator_value = EXCLUDED.indicator_value,
                        indicator_data = EXCLUDED.indicator_data
                """, 
                symbol, timeframe, timestamp, indicator_name,
                Decimal(str(indicator_value)) if indicator_value else None,
                json.dumps(indicator_data) if indicator_data else None
                )
            return True
        except Exception as e:
            logger.error(f"Error storing technical indicator: {e}")
            return False
    
    async def get_technical_indicator(self, symbol: str, timeframe: str, indicator_name: str, limit: int = 100) -> List[Dict]:
        """Get stored technical indicators"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT timestamp, indicator_value, indicator_data
                    FROM technical_indicators 
                    WHERE symbol = $1 AND timeframe = $2 AND indicator_name = $3
                    ORDER BY timestamp DESC 
                    LIMIT $4
                """, symbol, timeframe, indicator_name, limit)
                
                result = []
                for row in rows:
                    data = dict(row)
                    if data['indicator_data']:
                        data['indicator_data'] = json.loads(data['indicator_data'])
                    result.append(data)
                
                return result
        except Exception as e:
            logger.error(f"Error getting technical indicator: {e}")
            return []
    
    # System Configuration Methods
    async def get_config(self, config_key: str) -> Optional[Any]:
        """Get system configuration value"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT config_value, config_type FROM system_config 
                    WHERE config_key = $1
                """, config_key)
                
                if row:
                    value = row['config_value']
                    config_type = row['config_type']
                    
                    if config_type == 'NUMBER':
                        return float(value)
                    elif config_type == 'BOOLEAN':
                        return value.lower() == 'true'
                    elif config_type == 'JSON':
                        return json.loads(value)
                    else:
                        return value
                return None
        except Exception as e:
            logger.error(f"Error getting config {config_key}: {e}")
            return None
    
    async def set_config(self, config_key: str, config_value: Any, config_type: str = 'STRING', description: str = '') -> bool:
        """Set system configuration value"""
        try:
            async with self.get_connection() as conn:
                if config_type == 'JSON':
                    value_str = json.dumps(config_value)
                else:
                    value_str = str(config_value)
                
                await conn.execute("""
                    INSERT INTO system_config (config_key, config_value, config_type, description)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (config_key)
                    DO UPDATE SET 
                        config_value = EXCLUDED.config_value,
                        config_type = EXCLUDED.config_type,
                        description = EXCLUDED.description,
                        updated_at = NOW()
                """, config_key, value_str, config_type, description)
                
                logger.info(f"Updated config {config_key}: {config_value}")
                return True
        except Exception as e:
            logger.error(f"Error setting config {config_key}: {e}")
            return False
    
    async def get_all_configs(self) -> Dict[str, Any]:
        """Get all system configurations"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT config_key, config_value, config_type FROM system_config 
                    ORDER BY config_key
                """)
                
                configs = {}
                for row in rows:
                    key = row['config_key']
                    value = row['config_value']
                    config_type = row['config_type']
                    
                    if config_type == 'NUMBER':
                        configs[key] = float(value)
                    elif config_type == 'BOOLEAN':
                        configs[key] = value.lower() == 'true'
                    elif config_type == 'JSON':
                        configs[key] = json.loads(value)
                    else:
                        configs[key] = value
                
                return configs
        except Exception as e:
            logger.error(f"Error getting all configs: {e}")
            return {}
    
    # Performance Tracking Methods
    async def store_daily_performance(self, performance_data: Dict) -> bool:
        """Store daily performance metrics"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO performance_metrics 
                    (date, total_pnl, realized_pnl, unrealized_pnl, number_of_trades,
                     win_rate, avg_win, avg_loss, max_drawdown, sharpe_ratio, portfolio_value)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (date)
                    DO UPDATE SET 
                        total_pnl = EXCLUDED.total_pnl,
                        realized_pnl = EXCLUDED.realized_pnl,
                        unrealized_pnl = EXCLUDED.unrealized_pnl,
                        number_of_trades = EXCLUDED.number_of_trades,
                        win_rate = EXCLUDED.win_rate,
                        avg_win = EXCLUDED.avg_win,
                        avg_loss = EXCLUDED.avg_loss,
                        max_drawdown = EXCLUDED.max_drawdown,
                        sharpe_ratio = EXCLUDED.sharpe_ratio,
                        portfolio_value = EXCLUDED.portfolio_value
                """,
                performance_data['date'], Decimal(str(performance_data['total_pnl'])),
                Decimal(str(performance_data['realized_pnl'])), 
                Decimal(str(performance_data['unrealized_pnl'])),
                performance_data['number_of_trades'], 
                Decimal(str(performance_data.get('win_rate', 0))),
                Decimal(str(performance_data.get('avg_win', 0))),
                Decimal(str(performance_data.get('avg_loss', 0))),
                Decimal(str(performance_data.get('max_drawdown', 0))),
                Decimal(str(performance_data.get('sharpe_ratio', 0))),
                Decimal(str(performance_data['portfolio_value']))
                )
                
                logger.info(f"Stored performance for {performance_data['date']}")
                return True
        except Exception as e:
            logger.error(f"Error storing performance: {e}")
            return False
    
    async def get_performance_history(self, days: int = 30) -> List[Dict]:
        """Get performance history"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM performance_metrics 
                    ORDER BY date DESC 
                    LIMIT $1
                """, days)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            return []
    
    # Active Positions Methods
    async def store_active_position(self, position_data: Dict) -> int:
        """Store active position"""
        try:
            async with self.get_connection() as conn:
                position_id = await conn.fetchval("""
                    INSERT INTO active_positions 
                    (symbol, strategy_type, entry_date, entry_price, quantity, 
                     current_price, unrealized_pnl, delta, gamma, theta, vega, option_details)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id
                """,
                position_data['symbol'], position_data['strategy_type'], position_data['entry_date'],
                Decimal(str(position_data['entry_price'])), position_data['quantity'],
                Decimal(str(position_data.get('current_price', 0))),
                Decimal(str(position_data.get('unrealized_pnl', 0))),
                Decimal(str(position_data.get('delta', 0))), Decimal(str(position_data.get('gamma', 0))),
                Decimal(str(position_data.get('theta', 0))), Decimal(str(position_data.get('vega', 0))),
                json.dumps(position_data.get('option_details', {}))
                )
                
                logger.info(f"Stored active position {position_id}: {position_data['strategy_type']}")
                return position_id
        except Exception as e:
            logger.error(f"Error storing active position: {e}")
            return None
    
    async def get_active_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get active positions"""
        try:
            async with self.get_connection() as conn:
                if symbol:
                    query = """
                        SELECT * FROM active_positions 
                        WHERE symbol = $1 AND status = 'OPEN'
                        ORDER BY entry_date DESC
                    """
                    rows = await conn.fetch(query, symbol)
                else:
                    query = """
                        SELECT * FROM active_positions 
                        WHERE status = 'OPEN'
                        ORDER BY entry_date DESC
                    """
                    rows = await conn.fetch(query)
                
                result = []
                for row in rows:
                    position = dict(row)
                    if position['option_details']:
                        position['option_details'] = json.loads(position['option_details'])
                    result.append(position)
                
                return result
        except Exception as e:
            logger.error(f"Error getting active positions: {e}")
            return []
    
    async def update_position_pnl(self, position_id: int, current_price: float, unrealized_pnl: float, 
                                 delta: float = None, gamma: float = None, theta: float = None, vega: float = None) -> bool:
        """Update position P&L and Greeks"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    UPDATE active_positions 
                    SET current_price = $2, unrealized_pnl = $3, 
                        delta = COALESCE($4, delta),
                        gamma = COALESCE($5, gamma),
                        theta = COALESCE($6, theta),
                        vega = COALESCE($7, vega),
                        updated_at = NOW()
                    WHERE id = $1
                """, 
                position_id, Decimal(str(current_price)), Decimal(str(unrealized_pnl)),
                Decimal(str(delta)) if delta is not None else None,
                Decimal(str(gamma)) if gamma is not None else None,
                Decimal(str(theta)) if theta is not None else None,
                Decimal(str(vega)) if vega is not None else None
                )
                return True
        except Exception as e:
            logger.error(f"Error updating position P&L: {e}")
            return False
    
    async def close_position(self, position_id: int, exit_price: float, realized_pnl: float) -> bool:
        """Close active position and move to historical trades"""
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    # Get position details
                    position = await conn.fetchrow("""
                        SELECT * FROM active_positions WHERE id = $1
                    """, position_id)
                    
                    if not position:
                        return False
                    
                    # Move to historical trades
                    await conn.execute("""
                        INSERT INTO historical_trades
                        (symbol, strategy_type, entry_date, exit_date, entry_price, exit_price,
                         quantity, realized_pnl, hold_duration, win_loss, trade_details)
                        VALUES ($1, $2, $3, NOW(), $4, $5, $6, $7, 
                                NOW() - $3, $8, $9)
                    """,
                    position['symbol'], position['strategy_type'], position['entry_date'],
                    position['entry_price'], Decimal(str(exit_price)), position['quantity'],
                    Decimal(str(realized_pnl)), 'WIN' if realized_pnl > 0 else 'LOSS',
                    json.dumps({'option_details': json.loads(position['option_details']) if position['option_details'] else {}})
                    )
                    
                    # Update position status
                    await conn.execute("""
                        UPDATE active_positions 
                        SET status = 'CLOSED', updated_at = NOW()
                        WHERE id = $1
                    """, position_id)
                
                logger.info(f"Closed position {position_id} with P&L: ₹{realized_pnl}")
                return True
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    # Historical Trades Methods
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get historical trades"""
        try:
            async with self.get_connection() as conn:
                if symbol:
                    query = """
                        SELECT * FROM historical_trades 
                        WHERE symbol = $1 
                        ORDER BY exit_date DESC 
                        LIMIT $2
                    """
                    rows = await conn.fetch(query, symbol, limit)
                else:
                    query = """
                        SELECT * FROM historical_trades 
                        ORDER BY exit_date DESC 
                        LIMIT $1
                    """
                    rows = await conn.fetch(query, limit)
                
                result = []
                for row in rows:
                    trade = dict(row)
                    if trade['trade_details']:
                        trade['trade_details'] = json.loads(trade['trade_details'])
                    result.append(trade)
                
                return result
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    async def get_trade_statistics(self, symbol: Optional[str] = None, days: int = 30) -> Dict:
        """Get trading statistics"""
        try:
            async with self.get_connection() as conn:
                if symbol:
                    query = """
                        SELECT 
                            COUNT(*) as total_trades,
                            SUM(CASE WHEN win_loss = 'WIN' THEN 1 ELSE 0 END) as winning_trades,
                            SUM(realized_pnl) as total_pnl,
                            AVG(CASE WHEN win_loss = 'WIN' THEN realized_pnl END) as avg_win,
                            AVG(CASE WHEN win_loss = 'LOSS' THEN realized_pnl END) as avg_loss,
                            MAX(realized_pnl) as max_win,
                            MIN(realized_pnl) as max_loss,
                            AVG(EXTRACT(EPOCH FROM hold_duration)/3600) as avg_hold_hours
                        FROM historical_trades 
                        WHERE symbol = $1 AND exit_date >= NOW() - INTERVAL '$2 days'
                    """
                    result = await conn.fetchrow(query, symbol, days)
                else:
                    query = """
                        SELECT 
                            COUNT(*) as total_trades,
                            SUM(CASE WHEN win_loss = 'WIN' THEN 1 ELSE 0 END) as winning_trades,
                            SUM(realized_pnl) as total_pnl,
                            AVG(CASE WHEN win_loss = 'WIN' THEN realized_pnl END) as avg_win,
                            AVG(CASE WHEN win_loss = 'LOSS' THEN realized_pnl END) as avg_loss,
                            MAX(realized_pnl) as max_win,
                            MIN(realized_pnl) as max_loss,
                            AVG(EXTRACT(EPOCH FROM hold_duration)/3600) as avg_hold_hours
                        FROM historical_trades 
                        WHERE exit_date >= NOW() - INTERVAL '$1 days'
                    """
                    result = await conn.fetchrow(query, days)
                
                if result and result['total_trades'] > 0:
                    win_rate = (result['winning_trades'] / result['total_trades']) * 100
                    profit_factor = abs(result['avg_win'] * result['winning_trades'] / 
                                      (result['avg_loss'] * (result['total_trades'] - result['winning_trades']))) if result['avg_loss'] else 0
                    
                    return {
                        'total_trades': result['total_trades'],
                        'winning_trades': result['winning_trades'],
                        'losing_trades': result['total_trades'] - result['winning_trades'],
                        'win_rate': round(win_rate, 2),
                        'total_pnl': float(result['total_pnl']),
                        'avg_win': float(result['avg_win']) if result['avg_win'] else 0,
                        'avg_loss': float(result['avg_loss']) if result['avg_loss'] else 0,
                        'max_win': float(result['max_win']) if result['max_win'] else 0,
                        'max_loss': float(result['max_loss']) if result['max_loss'] else 0,
                        'avg_hold_hours': round(float(result['avg_hold_hours']), 2) if result['avg_hold_hours'] else 0,
                        'profit_factor': round(profit_factor, 2)
                    }
                
                return {'total_trades': 0}
        except Exception as e:
            logger.error(f"Error getting trade statistics: {e}")
            return {'total_trades': 0}
    
    # Health Check Methods
    async def health_check(self) -> Dict:
        """Database health check"""
        try:
            start_time = datetime.now()
            async with self.get_connection() as conn:
                # Test basic connectivity
                await conn.fetchval('SELECT 1')
                
                # Check table counts
                market_data_count = await conn.fetchval('SELECT COUNT(*) FROM market_data_candles')
                options_count = await conn.fetchval('SELECT COUNT(*) FROM options_chain')
                signals_count = await conn.fetchval('SELECT COUNT(*) FROM trading_signals WHERE status = \'ACTIVE\'')
                positions_count = await conn.fetchval('SELECT COUNT(*) FROM active_positions WHERE status = \'OPEN\'')
                
                # Check latest data timestamps
                latest_market_data = await conn.fetchval('''
                    SELECT MAX(timestamp) FROM market_data_candles WHERE symbol = 'NIFTY'
                ''')
                latest_options_data = await conn.fetchval('''
                    SELECT MAX(timestamp) FROM options_chain WHERE symbol = 'NIFTY'
                ''')
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    'status': 'HEALTHY',
                    'response_time_ms': round(response_time, 2),
                    'tables': {
                        'market_data_candles': market_data_count,
                        'options_chain': options_count,
                        'active_signals': signals_count,
                        'open_positions': positions_count
                    },
                    'latest_data': {
                        'market_data': latest_market_data.isoformat() if latest_market_data else None,
                        'options_data': latest_options_data.isoformat() if latest_options_data else None
                    },
                    'connection_pool': {
                        'size': self.pool.get_size(),
                        'max_size': self.pool.get_max_size(),
                        'min_size': self.pool.get_min_size()
                    }
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'response_time_ms': 0
            }
    
    # Utility Methods
    async def cleanup_old_data(self, days_to_keep: Dict[str, int] = None) -> Dict:
        """Clean up old data based on retention policy"""
        if not days_to_keep:
            days_to_keep = {
                'market_data_5min': 365,
                'market_data_other': 730,
                'options_chain': 180,
                'technical_indicators': 90,
                'vix_data': 730
            }
        
        try:
            async with self.get_connection() as conn:
                cleanup_results = {}
                
                # Clean 5min market data
                result = await conn.execute(f"""
                    DELETE FROM market_data_candles 
                    WHERE timeframe = '5min' AND timestamp < NOW() - INTERVAL '{days_to_keep['market_data_5min']} days'
                """)
                cleanup_results['market_data_5min'] = result.split()[-1] if result else '0'
                
                # Clean other timeframe market data
                result = await conn.execute(f"""
                    DELETE FROM market_data_candles 
                    WHERE timeframe != '5min' AND timestamp < NOW() - INTERVAL '{days_to_keep['market_data_other']} days'
                """)
                cleanup_results['market_data_other'] = result.split()[-1] if result else '0'
                
                # Clean options chain data
                result = await conn.execute(f"""
                    DELETE FROM options_chain 
                    WHERE timestamp < NOW() - INTERVAL '{days_to_keep['options_chain']} days'
                """)
                cleanup_results['options_chain'] = result.split()[-1] if result else '0'
                
                # Clean technical indicators
                result = await conn.execute(f"""
                    DELETE FROM technical_indicators 
                    WHERE timestamp < NOW() - INTERVAL '{days_to_keep['technical_indicators']} days'
                """)
                cleanup_results['technical_indicators'] = result.split()[-1] if result else '0'
                
                logger.info(f"Data cleanup completed: {cleanup_results}")
                return cleanup_results
                
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            return {'error': str(e)}
    
    async def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            async with self.get_connection() as conn:
                stats = {}
                
                # Table sizes
                table_stats = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, attname
                """)
                
                # Recent data counts
                recent_data = await conn.fetchrow("""
                    SELECT 
                        (SELECT COUNT(*) FROM market_data_candles WHERE timestamp > NOW() - INTERVAL '1 day') as market_data_24h,
                        (SELECT COUNT(*) FROM options_chain WHERE timestamp > NOW() - INTERVAL '1 day') as options_24h,
                        (SELECT COUNT(*) FROM trading_signals WHERE created_at > NOW() - INTERVAL '1 day') as signals_24h,
                        (SELECT SUM(oi) FROM options_chain WHERE symbol = 'NIFTY' AND timestamp = (SELECT MAX(timestamp) FROM options_chain WHERE symbol = 'NIFTY')) as current_total_oi
                """)
                
                stats['recent_activity'] = dict(recent_data) if recent_data else {}
                stats['table_stats'] = [dict(row) for row in table_stats]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}

# Global database service instance
db_service = None

async def get_database_service() -> DatabaseService:
    """Get global database service instance"""
    global db_service
    if db_service is None:
        db_service = DatabaseService()
        await db_service.initialize()
    return db_service

async def close_database_service():
    """Close global database service"""
    global db_service
    if db_service:
        await db_service.close()
        db_service = None

# Context manager for database operations
class DatabaseManager:
    def __init__(self):
        self.db_service = None
    
    async def __aenter__(self):
        self.db_service = await get_database_service()
        return self.db_service
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Don't close the global service, just return
        pass

# Utility function for quick database operations
async def with_database(operation):
    """Execute operation with database service"""
    async with DatabaseManager() as db:
        return await operation(db)