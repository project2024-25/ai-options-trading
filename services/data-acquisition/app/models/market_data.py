"""
Pydantic models for market data structures
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    service: str
    status: str = Field(..., description="Service status: healthy, unhealthy, degraded")
    timestamp: str
    version: str
    checks: Dict[str, Any] = Field(default_factory=dict)


class IndexSnapshot(BaseModel):
    """Index snapshot data model"""
    symbol: str = Field(..., description="Index symbol (NIFTY, BANKNIFTY, VIX)")
    ltp: float = Field(..., description="Last traded price")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Day's high price")
    low: float = Field(..., description="Day's low price")
    close: float = Field(..., description="Previous day's closing price")
    change: float = Field(..., description="Absolute change from previous close")
    change_percent: float = Field(..., description="Percentage change from previous close")
    volume: int = Field(default=0, description="Trading volume")
    oi: int = Field(default=0, description="Open interest")
    timestamp: str = Field(..., description="Data timestamp")
    instrument_token: Optional[int] = Field(default=None, description="Kite instrument token")

    @validator('symbol')
    def validate_symbol(cls, v):
        allowed_symbols = ['NIFTY', 'BANKNIFTY', 'VIX']
        if v.upper() not in allowed_symbols:
            raise ValueError(f'Symbol must be one of {allowed_symbols}')
        return v.upper()


class CandleData(BaseModel):
    """Candle/OHLCV data model"""
    symbol: str = Field(..., description="Index symbol")
    timeframe: str = Field(..., description="Timeframe (5min, 15min, 1hr, 1day)")
    timestamp: str = Field(..., description="Candle timestamp")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(default=0, description="Trading volume")
    oi: int = Field(default=0, description="Open interest")

    @validator('timeframe')
    def validate_timeframe(cls, v):
        allowed_timeframes = ['1min', '5min', '15min', '1hr', '1day', '1week', '1month']
        if v not in allowed_timeframes:
            raise ValueError(f'Timeframe must be one of {allowed_timeframes}')
        return v

    @validator('high')
    def validate_high(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('High price cannot be less than low price')
        return v

    @validator('low')
    def validate_low(cls, v, values):
        if 'high' in values and v > values['high']:
            raise ValueError('Low price cannot be greater than high price')
        return v


class OptionData(BaseModel):
    """Option data model"""
    symbol: str = Field(..., description="Underlying symbol (NIFTY, BANKNIFTY)")
    expiry: str = Field(..., description="Expiry date (YYYY-MM-DD)")
    strike: float = Field(..., description="Strike price")
    option_type: str = Field(..., description="Option type (CE/PE)")
    timestamp: str = Field(..., description="Data timestamp")
    ltp: Optional[float] = Field(default=None, description="Last traded price")
    bid: Optional[float] = Field(default=None, description="Bid price")
    ask: Optional[float] = Field(default=None, description="Ask price")
    volume: int = Field(default=0, description="Trading volume")
    oi: int = Field(default=0, description="Open interest")
    delta: Optional[float] = Field(default=None, description="Delta greek")
    gamma: Optional[float] = Field(default=None, description="Gamma greek")
    theta: Optional[float] = Field(default=None, description="Theta greek")
    vega: Optional[float] = Field(default=None, description="Vega greek")
    rho: Optional[float] = Field(default=None, description="Rho greek")
    iv: Optional[float] = Field(default=None, description="Implied volatility")
    intrinsic_value: Optional[float] = Field(default=None, description="Intrinsic value")
    time_value: Optional[float] = Field(default=None, description="Time value")
    instrument_token: Optional[int] = Field(default=None, description="Kite instrument token")

    @validator('option_type')
    def validate_option_type(cls, v):
        if v.upper() not in ['CE', 'PE']:
            raise ValueError('Option type must be CE or PE')
        return v.upper()

    @validator('strike')
    def validate_strike(cls, v):
        if v <= 0:
            raise ValueError('Strike price must be positive')
        return v

    @validator('iv')
    def validate_iv(cls, v):
        if v is not None and (v < 0 or v > 200):
            raise ValueError('Implied volatility must be between 0 and 200')
        return v


class TradingSignal(BaseModel):
    """Trading signal model"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    symbol: str = Field(..., description="Underlying symbol")
    strategy_type: str = Field(..., description="Strategy type")
    signal_strength: int = Field(..., description="Signal strength (1-10)", ge=1, le=10)
    recommended_trade: Dict[str, Any] = Field(..., description="Trade recommendation details")
    entry_price_range: Dict[str, float] = Field(..., description="Entry price range")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    target_price: Optional[float] = Field(default=None, description="Target price")
    expected_pnl: Dict[str, float] = Field(..., description="Expected P&L details")
    greeks_analysis: Dict[str, float] = Field(..., description="Greeks analysis")
    approval_status: str = Field(default="pending", description="Approval status")
    execution_status: str = Field(default="pending", description="Execution status")
    confidence_score: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    market_conditions: Dict[str, Any] = Field(..., description="Market conditions")

    @validator('approval_status')
    def validate_approval_status(cls, v):
        allowed_statuses = ['pending', 'approved', 'rejected', 'expired']
        if v not in allowed_statuses:
            raise ValueError(f'Approval status must be one of {allowed_statuses}')
        return v

    @validator('execution_status')
    def validate_execution_status(cls, v):
        allowed_statuses = ['pending', 'executed', 'failed', 'cancelled']
        if v not in allowed_statuses:
            raise ValueError(f'Execution status must be one of {allowed_statuses}')
        return v


class ActivePosition(BaseModel):
    """Active position model"""
    entry_datetime: str = Field(..., description="Position entry datetime")
    symbol: str = Field(..., description="Underlying symbol")
    strategy: str = Field(..., description="Strategy name")
    option_details: Dict[str, Any] = Field(..., description="Option details")
    quantity: int = Field(..., description="Position quantity")
    entry_price: float = Field(..., description="Entry price")
    current_price: Optional[float] = Field(default=None, description="Current market price")
    pnl_amount: Optional[float] = Field(default=None, description="P&L amount")
    pnl_percentage: Optional[float] = Field(default=None, description="P&L percentage")
    delta: Optional[float] = Field(default=None, description="Position delta")
    gamma: Optional[float] = Field(default=None, description="Position gamma")
    theta: Optional[float] = Field(default=None, description="Position theta")
    vega: Optional[float] = Field(default=None, description="Position vega")
    days_to_expiry: Optional[int] = Field(default=None, description="Days to expiry")
    exit_conditions: Dict[str, Any] = Field(..., description="Exit conditions")
    risk_status: str = Field(default="normal", description="Risk status")
    is_active: bool = Field(default=True, description="Position active status")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    @validator('quantity')
    def validate_quantity(cls, v):
        if v == 0:
            raise ValueError('Quantity cannot be zero')
        return v

    @validator('risk_status')
    def validate_risk_status(cls, v):
        allowed_statuses = ['normal', 'warning', 'critical']
        if v not in allowed_statuses:
            raise ValueError(f'Risk status must be one of {allowed_statuses}')
        return v


class HistoricalTrade(BaseModel):
    """Historical trade model"""
    trade_date: str = Field(..., description="Trade date")
    symbol: str = Field(..., description="Underlying symbol")
    strategy: str = Field(..., description="Strategy name")
    entry_price: float = Field(..., description="Entry price")
    exit_price: float = Field(..., description="Exit price")
    quantity: int = Field(..., description="Trade quantity")
    hold_duration: Optional[str] = Field(default=None, description="Hold duration")
    pnl_amount: float = Field(..., description="P&L amount")
    pnl_percentage: float = Field(..., description="P&L percentage")
    max_drawdown: Optional[float] = Field(default=None, description="Maximum drawdown")
    strategy_effectiveness_score: Optional[float] = Field(default=None, description="Strategy effectiveness")
    market_conditions: Dict[str, Any] = Field(..., description="Market conditions during trade")
    entry_datetime: str = Field(..., description="Entry datetime")
    exit_datetime: str = Field(..., description="Exit datetime")

    @validator('quantity')
    def validate_quantity(cls, v):
        if v == 0:
            raise ValueError('Quantity cannot be zero')
        return v


class SystemConfig(BaseModel):
    """System configuration model"""
    config_key: str = Field(..., description="Configuration key")
    config_value: Dict[str, Any] = Field(..., description="Configuration value")
    description: Optional[str] = Field(default=None, description="Configuration description")
    is_active: bool = Field(default=True, description="Configuration active status")
    updated_by: Optional[str] = Field(default=None, description="Last updated by")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# Request/Response models for API endpoints
class CandleDataRequest(BaseModel):
    """Request model for candle data"""
    symbol: str = Field(..., description="Symbol (NIFTY/BANKNIFTY)")
    timeframe: str = Field(..., description="Timeframe")
    from_date: Optional[str] = Field(default=None, description="From date (YYYY-MM-DD)")
    to_date: Optional[str] = Field(default=None, description="To date (YYYY-MM-DD)")
    limit: int = Field(default=100, description="Maximum number of candles", gt=0, le=1000)


class OptionsChainRequest(BaseModel):
    """Request model for options chain"""
    symbol: str = Field(..., description="Symbol (NIFTY/BANKNIFTY)")
    expiry: Optional[str] = Field(default=None, description="Expiry date (YYYY-MM-DD)")


class CandleDataResponse(BaseModel):
    """Response model for candle data"""
    success: bool = Field(..., description="Request success status")
    data: List[CandleData] = Field(..., description="Candle data list")
    count: int = Field(..., description="Number of candles returned")
    symbol: str = Field(..., description="Symbol")
    timeframe: str = Field(..., description="Timeframe")
    from_cache: bool = Field(default=False, description="Data retrieved from cache")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class OptionsChainResponse(BaseModel):
    """Response model for options chain"""
    success: bool = Field(..., description="Request success status")
    data: List[OptionData] = Field(..., description="Options data list")
    count: int = Field(..., description="Number of options returned")
    symbol: str = Field(..., description="Symbol")
    expiry: Optional[str] = Field(default=None, description="Expiry date")
    from_cache: bool = Field(default=False, description="Data retrieved from cache")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class IndexSnapshotResponse(BaseModel):
    """Response model for index snapshot"""
    success: bool = Field(..., description="Request success status")
    data: IndexSnapshot = Field(..., description="Index snapshot data")
    from_cache: bool = Field(default=False, description="Data retrieved from cache")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(default=False, description="Request success status")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Market data validation helpers
class MarketDataValidator:
    """Market data validation utilities"""
    
    @staticmethod
    def validate_market_hours(timestamp: datetime) -> bool:
        """Validate if timestamp is within market hours"""
        import pytz
        
        ist = pytz.timezone('Asia/Kolkata')
        if timestamp.tzinfo is None:
            timestamp = ist.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(ist)
        
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if timestamp.weekday() >= 5:
            return False
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_start = timestamp.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = timestamp.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_start <= timestamp <= market_end
    
    @staticmethod
    def validate_option_expiry(expiry_date: date) -> bool:
        """Validate if expiry date is valid"""
        today = datetime.now().date()
        
        # Expiry should be in the future
        if expiry_date <= today:
            return False
        
        # Check if it's a Thursday (typical options expiry day)
        # Allow some flexibility for weekly/monthly expiries
        return True  # Simplified validation
    
    @staticmethod
    def validate_strike_price(strike: float, symbol: str, current_price: float) -> bool:
        """Validate if strike price is reasonable"""
        if strike <= 0:
            return False
        
        # Strike should be within reasonable range of current price
        # Allow strikes from 50% below to 50% above current price
        min_strike = current_price * 0.5
        max_strike = current_price * 1.5
        
        return min_strike <= strike <= max_strike
    
    @staticmethod
    def validate_bid_ask_spread(bid: float, ask: float, ltp: float) -> bool:
        """Validate bid-ask spread reasonableness"""
        if bid <= 0 or ask <= 0 or ltp <= 0:
            return False
        
        if bid >= ask:
            return False
        
        # LTP should be between bid and ask
        if not (bid <= ltp <= ask):
            return False
        
        # Spread should not be too wide (max 10% of LTP)
        spread_percent = (ask - bid) / ltp
        return spread_percent <= 0.10