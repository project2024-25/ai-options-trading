# services/database/sqlite_db_service.py
import sqlite3
import json
import os
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging
import asyncio
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteDatabaseService:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'trading.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.connection = None
        
    async def initialize(self):
        """Initialize SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            await self.create_tables()
            await self.insert_default_config()
            logger.info("SQLite database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_tables(self):
        """Create all required tables"""
        cursor = self.connection.cursor()
        
        # Market Data Candles Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data_candles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """)
        
        # Options Chain Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS options_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                expiry TEXT NOT NULL,
                strike REAL NOT NULL,
                option_type TEXT NOT NULL,
                ltp REAL,
                bid REAL,
                ask REAL,
                volume INTEGER DEFAULT 0,
                oi INTEGER DEFAULT 0,
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                rho REAL,
                iv REAL,
                intrinsic_value REAL,
                time_value REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, expiry, strike, option_type, timestamp)
            )
        """)
        
        # Trading Signals Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL,
                stop_loss REAL,
                target_price REAL,
                confidence_score REAL,
                reasoning TEXT,
                status TEXT DEFAULT 'ACTIVE',
                timeframe TEXT,
                market_conditions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System Configuration Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                config_type TEXT NOT NULL,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance Metrics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_pnl REAL NOT NULL,
                realized_pnl REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                number_of_trades INTEGER DEFAULT 0,
                win_rate REAL,
                avg_win REAL,
                avg_loss REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                portfolio_value REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timeframe ON market_data_candles(symbol, timeframe)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_options_chain_symbol_expiry ON options_chain(symbol, expiry)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trading_signals_status ON trading_signals(status)")
        
        self.connection.commit()
    
    async def insert_default_config(self):
        """Insert default system configuration"""
        cursor = self.connection.cursor()
        
        configs = [
            ('max_risk_per_trade', '2.0', 'NUMBER', 'Maximum risk percentage per trade'),
            ('max_portfolio_risk', '10.0', 'NUMBER', 'Maximum portfolio risk percentage'),
            ('min_days_to_expiry', '7', 'NUMBER', 'Minimum days to expiry for options'),
            ('max_days_to_expiry', '45', 'NUMBER', 'Maximum days to expiry for options'),
            ('trading_enabled', 'false', 'BOOLEAN', 'Enable/disable live trading'),
            ('data_collection_enabled', 'true', 'BOOLEAN', 'Enable/disable data collection'),
        ]
        
        for config in configs:
            cursor.execute("""
                INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description)
                VALUES (?, ?, ?, ?)
            """, config)
        
        self.connection.commit()
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    # Market Data Methods
    async def store_market_data(self, symbol: str, timeframe: str, candle_data: Dict) -> bool:
        """Store your live NIFTY ₹24,833.6 data"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO market_data_candles 
                (symbol, timeframe, timestamp, open, high, low, close, volume) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, timeframe, candle_data['timestamp'].isoformat(),
                float(candle_data['open']), float(candle_data['high']),
                float(candle_data['low']), float(candle_data['close']),
                candle_data['volume']
            ))
            self.connection.commit()
            logger.info(f"Stored {symbol} {timeframe} data: ₹{candle_data['close']}")
            return True
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
            return False
    
    async def get_market_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict]:
        """Get historical market data"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT timestamp, open, high, low, close, volume
                FROM market_data_candles 
                WHERE symbol = ? AND timeframe = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (symbol, timeframe, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from latest 5min data"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT close FROM market_data_candles 
                WHERE symbol = ? AND timeframe = '5min'
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            return result['close'] if result else None
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    # Options Chain Methods
    async def store_options_chain(self, options_data: List[Dict]) -> bool:
        """Store your 30+ Lakh OI options data"""
        try:
            cursor = self.connection.cursor()
            for option in options_data:
                cursor.execute("""
                    INSERT OR REPLACE INTO options_chain 
                    (symbol, expiry, strike, option_type, ltp, bid, ask, volume, oi,
                     delta, gamma, theta, vega, rho, iv, intrinsic_value, time_value, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    option['symbol'], option['expiry'].isoformat(), float(option['strike']),
                    option['option_type'], float(option.get('ltp', 0)),
                    float(option.get('bid', 0)), float(option.get('ask', 0)),
                    option.get('volume', 0), option.get('oi', 0),
                    float(option.get('delta', 0)), float(option.get('gamma', 0)),
                    float(option.get('theta', 0)), float(option.get('vega', 0)),
                    float(option.get('rho', 0)), float(option.get('iv', 0)),
                    float(option.get('intrinsic_value', 0)), 
                    float(option.get('time_value', 0)),
                    option.get('timestamp', datetime.now()).isoformat()
                ))
            
            self.connection.commit()
            total_oi = sum(opt.get('oi', 0) for opt in options_data)
            logger.info(f"Stored options chain data. Total OI: {total_oi:,}")
            return True
        except Exception as e:
            logger.error(f"Error storing options data: {e}")
            return False
    
    async def get_options_chain(self, symbol: str, expiry: Optional[date] = None) -> List[Dict]:
        """Get current options chain data"""
        try:
            cursor = self.connection.cursor()
            if expiry:
                cursor.execute("""
                    SELECT * FROM options_chain 
                    WHERE symbol = ? AND expiry = ?
                    ORDER BY strike, option_type
                """, (symbol, expiry.isoformat()))
            else:
                cursor.execute("""
                    SELECT * FROM options_chain 
                    WHERE symbol = ?
                    ORDER BY expiry, strike, option_type
                """, (symbol,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting options chain: {e}")
            return []
    
    async def get_max_pain(self, symbol: str, expiry: Optional[date] = None) -> Optional[Dict]:
        """Calculate Max Pain from stored OI data"""
        try:
            cursor = self.connection.cursor()
            
            # Get current price
            current_price = await self.get_current_price(symbol)
            if not current_price:
                current_price = 24833.6  # Fallback to your live price
            
            # Get options data
            if expiry:
                cursor.execute("""
                    SELECT strike, option_type, oi FROM options_chain 
                    WHERE symbol = ? AND expiry = ?
                """, (symbol, expiry.isoformat()))
            else:
                cursor.execute("""
                    SELECT strike, option_type, oi FROM options_chain 
                    WHERE symbol = ?
                """, (symbol,))
            
            options = cursor.fetchall()
            if not options:
                return None
            
            # Calculate max pain
            strikes = list(set(opt['strike'] for opt in options))
            min_pain = float('inf')
            max_pain_strike = None
            
            for test_strike in strikes:
                total_pain = 0
                for opt in options:
                    if opt['option_type'] == 'CE' and current_price > opt['strike']:
                        total_pain += (current_price - opt['strike']) * opt['oi']
                    elif opt['option_type'] == 'PE' and current_price < opt['strike']:
                        total_pain += (opt['strike'] - current_price) * opt['oi']
                
                if total_pain < min_pain:
                    min_pain = total_pain
                    max_pain_strike = test_strike
            
            return {
                'max_pain_strike': max_pain_strike,
                'current_price': current_price,
                'total_pain': min_pain,
                'distance_from_max_pain': current_price - max_pain_strike
            }
        except Exception as e:
            logger.error(f"Error calculating max pain: {e}")
            return None
    
    async def get_pcr_ratio(self, symbol: str, expiry: Optional[date] = None) -> Optional[Dict]:
        """Calculate Put-Call Ratio from OI data"""
        try:
            cursor = self.connection.cursor()
            if expiry:
                cursor.execute("""
                    SELECT option_type, SUM(oi) as total_oi, SUM(volume) as total_volume
                    FROM options_chain 
                    WHERE symbol = ? AND expiry = ?
                    GROUP BY option_type
                """, (symbol, expiry.isoformat()))
            else:
                cursor.execute("""
                    SELECT option_type, SUM(oi) as total_oi, SUM(volume) as total_volume
                    FROM options_chain 
                    WHERE symbol = ?
                    GROUP BY option_type
                """, (symbol,))
            
            data = {row['option_type']: {'oi': row['total_oi'], 'volume': row['total_volume']} 
                   for row in cursor.fetchall()}
            
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
    
    # Trading Signals Methods
    async def store_trading_signal(self, signal_data: Dict) -> int:
        """Store generated trading signal"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO trading_signals 
                (symbol, signal_type, direction, entry_price, stop_loss, target_price,
                 confidence_score, reasoning, timeframe, market_conditions) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data['symbol'], signal_data['signal_type'], signal_data['direction'],
                float(signal_data.get('entry_price', 0)), 
                float(signal_data.get('stop_loss', 0)),
                float(signal_data.get('target_price', 0)),
                float(signal_data.get('confidence_score', 0)),
                signal_data.get('reasoning', ''), signal_data.get('timeframe', ''),
                json.dumps(signal_data.get('market_conditions', {}))
            ))
            
            self.connection.commit()
            signal_id = cursor.lastrowid
            logger.info(f"Stored trading signal {signal_id}: {signal_data['signal_type']}")
            return signal_id
        except Exception as e:
            logger.error(f"Error storing trading signal: {e}")
            return None
    
    async def get_active_signals(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get active trading signals"""
        try:
            cursor = self.connection.cursor()
            if symbol:
                cursor.execute("""
                    SELECT * FROM trading_signals 
                    WHERE symbol = ? AND status = 'ACTIVE'
                    ORDER BY created_at DESC
                """, (symbol,))
            else:
                cursor.execute("""
                    SELECT * FROM trading_signals 
                    WHERE status = 'ACTIVE'
                    ORDER BY created_at DESC
                """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting active signals: {e}")
            return []
    
    # Configuration Methods
    async def get_config(self, config_key: str) -> Optional[Any]:
        """Get system configuration value"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT config_value, config_type FROM system_config 
                WHERE config_key = ?
            """, (config_key,))
            
            result = cursor.fetchone()
            if result:
                value = result['config_value']
                config_type = result['config_type']
                
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
            cursor = self.connection.cursor()
            if config_type == 'JSON':
                value_str = json.dumps(config_value)
            else:
                value_str = str(config_value)
            
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (config_key, config_value, config_type, description)
                VALUES (?, ?, ?, ?)
            """, (config_key, value_str, config_type, description))
            
            self.connection.commit()
            logger.info(f"Updated config {config_key}: {config_value}")
            return True
        except Exception as e:
            logger.error(f"Error setting config {config_key}: {e}")
            return False
    
    # Health Check Methods
    async def health_check(self) -> Dict:
        """Database health check"""
        try:
            start_time = datetime.now()
            cursor = self.connection.cursor()
            
            # Test basic connectivity
            cursor.execute('SELECT 1')
            
            # Check table counts
            cursor.execute('SELECT COUNT(*) FROM market_data_candles')
            market_data_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM options_chain')
            options_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trading_signals WHERE status = 'ACTIVE'")
            signals_count = cursor.fetchone()[0]
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'HEALTHY',
                'response_time_ms': round(response_time, 2),
                'database_path': self.db_path,
                'tables': {
                    'market_data_candles': market_data_count,
                    'options_chain': options_count,
                    'active_signals': signals_count
                }
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'response_time_ms': 0
            }

# Global database service instance
sqlite_db_service = None

async def get_sqlite_database_service() -> SQLiteDatabaseService:
    """Get global SQLite database service instance"""
    global sqlite_db_service
    if sqlite_db_service is None:
        sqlite_db_service = SQLiteDatabaseService()
        await sqlite_db_service.initialize()
    return sqlite_db_service