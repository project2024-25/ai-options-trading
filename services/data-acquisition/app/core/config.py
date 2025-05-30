"""
Configuration management for Data Acquisition Service
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "data-acquisition"
    DATA_ACQUISITION_PORT: int = 8001
    DEBUG_MODE: bool = True
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://trading_user:trading_password@localhost:5432/options_trading"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "options_trading"
    DATABASE_USER: str = "trading_user"
    DATABASE_PASSWORD: str = "trading_password"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # Zerodha Kite API Configuration
    KITE_API_KEY: str = ""
    KITE_API_SECRET: str = ""
    KITE_ACCESS_TOKEN: str = ""
    KITE_SANDBOX_MODE: bool = True
    KITE_DEBUG_MODE: bool = True
    KITE_TIMEOUT: int = 7000
    
    # Market Data Configuration
    MARKET_START_TIME: str = "09:15"
    MARKET_END_TIME: str = "15:30"
    PRE_MARKET_START_TIME: str = "08:30"
    POST_MARKET_END_TIME: str = "16:00"
    
    # Data Collection Intervals (in seconds)
    CANDLE_DATA_INTERVAL: int = 300  # 5 minutes
    OPTIONS_CHAIN_INTERVAL: int = 300  # 5 minutes
    VIX_DATA_INTERVAL: int = 900  # 15 minutes
    MARKET_DATA_INTERVAL: int = 15  # 15 seconds
    
    # Cache Configuration (TTL in seconds)
    INDEX_DATA_CACHE_TTL: int = 15
    OPTIONS_CHAIN_CACHE_TTL: int = 300
    CANDLE_DATA_CACHE_TTL: int = 300
    INDICATORS_CACHE_TTL: int = 900
    HISTORICAL_DATA_CACHE_TTL: int = 3600
    
    # Trading Configuration
    ENABLE_NIFTY_TRADING: bool = True
    ENABLE_BANKNIFTY_TRADING: bool = True
    MIN_DAYS_TO_EXPIRY: int = 7
    MAX_DAYS_TO_EXPIRY: int = 45
    MIN_OPTION_VOLUME: int = 1000
    MAX_BID_ASK_SPREAD_NIFTY: float = 0.05
    MAX_BID_ASK_SPREAD_BANKNIFTY: float = 0.10
    
    # External APIs Configuration
    NSE_API_ENABLED: bool = False
    NSE_API_URL: str = "https://www.nseindia.com/api"
    NSE_API_TIMEOUT: int = 5000
    
    YAHOO_FINANCE_ENABLED: bool = True
    YAHOO_FINANCE_TIMEOUT: int = 10000
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # CORS Configuration
    CORS_ENABLED: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Monitoring and Health Checks
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 5000
    ENABLE_PERFORMANCE_MONITORING: bool = True
    PERFORMANCE_MONITORING_INTERVAL: int = 60
    
    # Data Storage Paths
    DATA_EXPORT_PATH: str = "exports/"
    BACKUP_PATH: str = "backups/"
    LOG_FILE_PATH: str = "logs/"
    
    # Paper Trading Configuration
    PAPER_TRADING_MODE: bool = True
    PAPER_TRADING_INITIAL_BALANCE: int = 1000000
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("DATABASE_URL", pre=True)
    def build_database_url(cls, v, values):
        """Build database URL if not provided"""
        if v and v != "postgresql://trading_user:trading_password@localhost:5432/options_trading":
            return v
        
        user = values.get("DATABASE_USER", "trading_user")
        password = values.get("DATABASE_PASSWORD", "trading_password")
        host = values.get("DATABASE_HOST", "localhost")
        port = values.get("DATABASE_PORT", 5432)
        db_name = values.get("DATABASE_NAME", "options_trading")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    @validator("REDIS_URL", pre=True)
    def build_redis_url(cls, v, values):
        """Build Redis URL if not provided"""
        if v and v != "redis://localhost:6379":
            return v
        
        host = values.get("REDIS_HOST", "localhost")
        port = values.get("REDIS_PORT", 6379)
        password = values.get("REDIS_PASSWORD")
        
        if password:
            return f"redis://:{password}@{host}:{port}"
        return f"redis://{host}:{port}"
    
    @validator("KITE_API_KEY")
    def validate_kite_api_key(cls, v):
        """Validate Kite API key is provided"""
        if not v and not os.getenv("PAPER_TRADING_MODE", "true").lower() == "true":
            raise ValueError("KITE_API_KEY is required for live trading")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Market symbols configuration
NIFTY_SYMBOLS = {
    "index": "NIFTY 50",
    "instrument_token": 256265,  # Zerodha instrument token for NIFTY
    "tick_size": 0.05,
    "lot_size": 50
}

BANKNIFTY_SYMBOLS = {
    "index": "NIFTY BANK",
    "instrument_token": 260105,  # Zerodha instrument token for BANK NIFTY
    "tick_size": 0.05,
    "lot_size": 25
}

VIX_SYMBOLS = {
    "index": "INDIA VIX",
    "instrument_token": 264969,  # Zerodha instrument token for VIX
    "tick_size": 0.0025
}

# Timeframe mappings for Kite API
TIMEFRAME_MAPPING = {
    "1min": "minute",
    "5min": "5minute", 
    "15min": "15minute",
    "1hr": "60minute",
    "1day": "day",
    "1week": "week",
    "1month": "month"
}

# Cache key prefixes
CACHE_KEYS = {
    "NIFTY_SNAPSHOT": "nifty:snapshot",
    "BANKNIFTY_SNAPSHOT": "banknifty:snapshot",
    "VIX_DATA": "vix:data",
    "NIFTY_CANDLES": "nifty:candles",
    "BANKNIFTY_CANDLES": "banknifty:candles",
    "NIFTY_OPTIONS_CHAIN": "nifty:options_chain",
    "BANKNIFTY_OPTIONS_CHAIN": "banknifty:options_chain",
    "MARKET_STATUS": "market:status"
}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_database_url() -> str:
    """Get database URL"""
    settings = get_settings()
    return settings.DATABASE_URL


def get_redis_url() -> str:
    """Get Redis URL"""
    settings = get_settings()
    return settings.REDIS_URL


def is_development() -> bool:
    """Check if running in development mode"""
    settings = get_settings()
    return settings.ENVIRONMENT.lower() in ["development", "dev", "local"]


def is_production() -> bool:
    """Check if running in production mode"""
    settings = get_settings()
    return settings.ENVIRONMENT.lower() in ["production", "prod"]


def get_market_symbols() -> dict:
    """Get all market symbols configuration"""
    return {
        "nifty": NIFTY_SYMBOLS,
        "banknifty": BANKNIFTY_SYMBOLS,
        "vix": VIX_SYMBOLS
    }


def get_cache_key(key_type: str, **kwargs) -> str:
    """Generate cache key with optional parameters"""
    base_key = CACHE_KEYS.get(key_type.upper())
    if not base_key:
        raise ValueError(f"Unknown cache key type: {key_type}")
    
    if kwargs:
        suffix = ":".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return f"{base_key}:{suffix}"
    
    return base_key