"""
Zerodha Kite API client service for market data collection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json

import pandas as pd
from kiteconnect import KiteConnect
import httpx
import pytz

from app.core.config import get_settings, NIFTY_SYMBOLS, BANKNIFTY_SYMBOLS, VIX_SYMBOLS, TIMEFRAME_MAPPING

logger = logging.getLogger(__name__)


class KiteClientService:
    """Zerodha Kite API client service"""
    
    def __init__(self, api_key: str, api_secret: str, access_token: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.settings = get_settings()
        
        # Initialize Kite client
        self.kite = None
        self.is_initialized = False
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 0.34  # ~3 requests per second
        
        # Session management
        self.session_expires = None
        
        # IST timezone
        self.ist = pytz.timezone('Asia/Kolkata')
    
    async def initialize(self) -> bool:
        """Initialize Kite client and authenticate"""
        try:
            if not self.api_key:
                logger.warning("Kite API key not provided - running in mock mode")
                self.is_initialized = True
                return True
            
            # Initialize KiteConnect
            self.kite = KiteConnect(api_key=self.api_key)
            
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                
                # Verify session
                try:
                    profile = self.kite.profile()
                    logger.info(f"Kite client initialized for user: {profile.get('user_name', 'Unknown')}")
                    self.is_initialized = True
                    return True
                except Exception as e:
                    logger.error(f"Access token validation failed: {e}")
                    return False
            else:
                logger.warning("No access token provided - manual authentication required")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Kite client: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """Check if Kite client is connected and authenticated"""
        try:
            if not self.kite or not self.is_initialized:
                return False
            
            # Test with a simple API call
            await self._rate_limit_request("profile")
            profile = self.kite.profile()
            return profile is not None
            
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    async def _rate_limit_request(self, endpoint: str):
        """Apply rate limiting for API requests"""
        current_time = datetime.now().timestamp()
        last_time = self.last_request_time.get(endpoint, 0)
        
        time_diff = current_time - last_time
        if time_diff < self.min_request_interval:
            wait_time = self.min_request_interval - time_diff
            await asyncio.sleep(wait_time)
        
        self.last_request_time[endpoint] = datetime.now().timestamp()
    
    async def get_index_snapshot(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current snapshot of NIFTY/BANKNIFTY/VIX
        
        Args:
            symbol: 'NIFTY', 'BANKNIFTY', or 'VIX'
        
        Returns:
            Dictionary with current price, change, volume etc.
        """
        try:
            if not self.is_initialized:
                return self._get_mock_index_data(symbol)
            
            await self._rate_limit_request("quote")
            
            # Get instrument token
            if symbol.upper() == 'NIFTY':
                instrument_token = NIFTY_SYMBOLS['instrument_token']
            elif symbol.upper() == 'BANKNIFTY':
                instrument_token = BANKNIFTY_SYMBOLS['instrument_token']
            elif symbol.upper() == 'VIX':
                instrument_token = VIX_SYMBOLS['instrument_token']
            else:
                raise ValueError(f"Unsupported symbol: {symbol}")
            
            # Get quote
            quote = self.kite.quote([instrument_token])
            data = quote.get(str(instrument_token), {})
            
            if not data:
                logger.error(f"No data received for {symbol}")
                return None
            
            # Format response
            return {
                'symbol': symbol.upper(),
                'ltp': data.get('last_price', 0),
                'open': data.get('ohlc', {}).get('open', 0),
                'high': data.get('ohlc', {}).get('high', 0),
                'low': data.get('ohlc', {}).get('low', 0),
                'close': data.get('ohlc', {}).get('close', 0),
                'change': data.get('net_change', 0),
                'change_percent': data.get('oi_day_change_percentage', 0),
                'volume': data.get('volume', 0),
                'oi': data.get('oi', 0),
                'timestamp': datetime.now(self.ist).isoformat(),
                'instrument_token': instrument_token
            }
            
        except Exception as e:
            logger.error(f"Error getting {symbol} snapshot: {e}")
            return self._get_mock_index_data(symbol)
    
    async def get_candle_data(
        self, 
        symbol: str, 
        timeframe: str, 
        from_date: datetime = None, 
        to_date: datetime = None,
        limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical candle data for NIFTY/BANKNIFTY
        
        Args:
            symbol: 'NIFTY' or 'BANKNIFTY'
            timeframe: '5min', '15min', '1hr', '1day' etc.
            from_date: Start date
            to_date: End date
            limit: Maximum number of candles
        
        Returns:
            List of candle dictionaries
        """
        try:
            if not self.is_initialized:
                return self._get_mock_candle_data(symbol, timeframe, limit)
            
            await self._rate_limit_request("historical_data")
            
            # Get instrument token
            if symbol.upper() == 'NIFTY':
                instrument_token = NIFTY_SYMBOLS['instrument_token']
            elif symbol.upper() == 'BANKNIFTY':
                instrument_token = BANKNIFTY_SYMBOLS['instrument_token']
            else:
                raise ValueError(f"Unsupported symbol: {symbol}")
            
            # Map timeframe
            kite_timeframe = TIMEFRAME_MAPPING.get(timeframe, timeframe)
            
            # Set default dates if not provided
            if not to_date:
                to_date = datetime.now(self.ist)
            if not from_date:
                if timeframe in ['5min', '15min']:
                    from_date = to_date - timedelta(days=7)  # 1 week for intraday
                elif timeframe in ['1hr']:
                    from_date = to_date - timedelta(days=30)  # 1 month for hourly
                else:
                    from_date = to_date - timedelta(days=365)  # 1 year for daily+
            
            # Get historical data
            candles = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=kite_timeframe
            )
            
            if not candles:
                logger.warning(f"No candle data received for {symbol} {timeframe}")
                return []
            
            # Format candles
            formatted_candles = []
            for candle in candles[-limit:]:  # Get last 'limit' candles
                formatted_candles.append({
                    'symbol': symbol.upper(),
                    'timeframe': timeframe,
                    'timestamp': candle['date'].isoformat() if isinstance(candle['date'], datetime) else candle['date'],
                    'open': float(candle['open']),
                    'high': float(candle['high']),
                    'low': float(candle['low']),
                    'close': float(candle['close']),
                    'volume': int(candle.get('volume', 0)),
                    'oi': int(candle.get('oi', 0))
                })
            
            return formatted_candles
            
        except Exception as e:
            logger.error(f"Error getting candle data for {symbol} {timeframe}: {e}")
            return self._get_mock_candle_data(symbol, timeframe, limit)
    
    async def get_options_chain(self, symbol: str, expiry: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get options chain data for NIFTY/BANKNIFTY
        
        Args:
            symbol: 'NIFTY' or 'BANKNIFTY'
            expiry: Expiry date in 'YYYY-MM-DD' format (optional)
        
        Returns:
            List of options data dictionaries
        """
        try:
            if not self.is_initialized:
                return self._get_mock_options_chain(symbol)
            
            await self._rate_limit_request("instruments")
            
            # Get all instruments
            instruments = self.kite.instruments("NFO")  # NSE F&O segment
            
            # Filter for the symbol
            symbol_filter = "NIFTY" if symbol.upper() == "NIFTY" else "BANKNIFTY"
            options_instruments = [
                inst for inst in instruments 
                if inst['name'] == symbol_filter and inst['instrument_type'] in ['CE', 'PE']
            ]
            
            if expiry:
                # Filter by expiry if provided
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                options_instruments = [
                    inst for inst in options_instruments 
                    if inst['expiry'].date() == expiry_date
                ]
            else:
                # Get next expiry
                next_expiry = self._get_next_expiry(options_instruments)
                options_instruments = [
                    inst for inst in options_instruments 
                    if inst['expiry'].date() == next_expiry
                ]
            
            if not options_instruments:
                logger.warning(f"No options instruments found for {symbol}")
                return []
            
            # Get quotes for all options (in batches due to API limits)
            batch_size = 200  # Kite API limit
            all_options_data = []
            
            for i in range(0, len(options_instruments), batch_size):
                batch = options_instruments[i:i + batch_size]
                instrument_tokens = [inst['instrument_token'] for inst in batch]
                
                try:
                    await self._rate_limit_request("quote_batch")
                    quotes = self.kite.quote(instrument_tokens)
                    
                    for inst in batch:
                        token = str(inst['instrument_token'])
                        quote_data = quotes.get(token, {})
                        
                        if quote_data:
                            option_data = self._format_option_data(inst, quote_data)
                            all_options_data.append(option_data)
                            
                except Exception as e:
                    logger.error(f"Error getting quotes for batch: {e}")
                    continue
            
            return sorted(all_options_data, key=lambda x: (x['strike'], x['option_type']))
            
        except Exception as e:
            logger.error(f"Error getting options chain for {symbol}: {e}")
            return self._get_mock_options_chain(symbol)
    
    def _format_option_data(self, instrument: Dict, quote_data: Dict) -> Dict[str, Any]:
        """Format option data from Kite API response"""
        try:
            # Calculate Greeks (simplified - you might want to use a proper options pricing library)
            spot_price = quote_data.get('last_price', 0)
            strike = instrument['strike']
            
            # Basic Greeks calculation (placeholder - implement proper Black-Scholes)
            delta = self._calculate_delta(spot_price, strike, instrument['instrument_type'])
            gamma = self._calculate_gamma(spot_price, strike)
            theta = self._calculate_theta(spot_price, strike)
            vega = self._calculate_vega(spot_price, strike)
            
            # Calculate intrinsic and time value
            if instrument['instrument_type'] == 'CE':
                intrinsic_value = max(0, spot_price - strike)
            else:  # PE
                intrinsic_value = max(0, strike - spot_price)
            
            ltp = quote_data.get('last_price', 0)
            time_value = max(0, ltp - intrinsic_value)
            
            return {
                'symbol': instrument['name'],
                'expiry': instrument['expiry'].date().isoformat(),
                'strike': float(strike),
                'option_type': instrument['instrument_type'],
                'timestamp': datetime.now(self.ist).isoformat(),
                'ltp': float(ltp),
                'bid': float(quote_data.get('depth', {}).get('buy', [{}])[0].get('price', 0)),
                'ask': float(quote_data.get('depth', {}).get('sell', [{}])[0].get('price', 0)),
                'volume': int(quote_data.get('volume', 0)),
                'oi': int(quote_data.get('oi', 0)),
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'vega': round(vega, 4),
                'rho': 0.0,  # Placeholder
                'iv': self._calculate_implied_volatility(ltp, spot_price, strike, instrument['instrument_type']),
                'intrinsic_value': round(intrinsic_value, 2),
                'time_value': round(time_value, 2),
                'instrument_token': instrument['instrument_token']
            }
            
        except Exception as e:
            logger.error(f"Error formatting option data: {e}")
            return {}
    
    def _get_next_expiry(self, instruments: List[Dict]) -> datetime.date:
        """Get the next expiry date from instruments list"""
        expiries = [inst['expiry'].date() for inst in instruments]
        expiries = sorted(set(expiries))
        
        today = datetime.now(self.ist).date()
        next_expiry = None
        
        for expiry in expiries:
            if expiry >= today:
                next_expiry = expiry
                break
        
        return next_expiry or expiries[0] if expiries else today
    
    # Simplified Greeks calculations (implement proper Black-Scholes later)
    def _calculate_delta(self, spot: float, strike: float, option_type: str) -> float:
        """Calculate approximate delta"""
        if option_type == 'CE':
            return 0.5 if spot == strike else (0.8 if spot > strike else 0.2)
        else:  # PE
            return -0.5 if spot == strike else (-0.2 if spot > strike else -0.8)
    
    def _calculate_gamma(self, spot: float, strike: float) -> float:
        """Calculate approximate gamma"""
        return 0.01 if abs(spot - strike) < 100 else 0.005
    
    def _calculate_theta(self, spot: float, strike: float) -> float:
        """Calculate approximate theta"""
        return -10.0 if abs(spot - strike) < 100 else -5.0
    
    def _calculate_vega(self, spot: float, strike: float) -> float:
        """Calculate approximate vega"""
        return 15.0 if abs(spot - strike) < 100 else 8.0
    
    def _calculate_implied_volatility(self, option_price: float, spot: float, strike: float, option_type: str) -> float:
        """Calculate approximate implied volatility"""
        # Simplified IV calculation - implement proper numerical methods later
        if option_price <= 0:
            return 0.0
        
        # Basic approximation based on option price relative to intrinsic value
        if option_type == 'CE':
            intrinsic = max(0, spot - strike)
        else:
            intrinsic = max(0, strike - spot)
        
        time_value = option_price - intrinsic
        if time_value <= 0:
            return 0.0
        
        # Very rough approximation - replace with proper Black-Scholes inversion
        return min(100.0, max(5.0, (time_value / spot) * 100))
    
    # Mock data methods for testing without API
    def _get_mock_index_data(self, symbol: str) -> Dict[str, Any]:
        """Generate mock index data for testing"""
        base_prices = {'NIFTY': 19850, 'BANKNIFTY': 45200, 'VIX': 15.5}
        base_price = base_prices.get(symbol.upper(), 20000)
        
        import random
        change = random.uniform(-2, 2)
        current_price = base_price + (base_price * change / 100)
        
        return {
            'symbol': symbol.upper(),
            'ltp': round(current_price, 2),
            'open': round(base_price, 2),
            'high': round(current_price + abs(change) * 10, 2),
            'low': round(current_price - abs(change) * 10, 2),
            'close': round(base_price, 2),
            'change': round(change * base_price / 100, 2),
            'change_percent': round(change, 2),
            'volume': random.randint(1000000, 5000000),
            'oi': random.randint(100000, 500000),
            'timestamp': datetime.now(self.ist).isoformat(),
            'instrument_token': 0
        }
    
    def _get_mock_candle_data(self, symbol: str, timeframe: str, limit: int) -> List[Dict[str, Any]]:
        """Generate mock candle data for testing"""
        import random
        base_prices = {'NIFTY': 19850, 'BANKNIFTY': 45200}
        base_price = base_prices.get(symbol.upper(), 20000)
        
        candles = []
        current_price = base_price
        
        # Generate time intervals based on timeframe
        if '5min' in timeframe:
            time_delta = timedelta(minutes=5)
        elif '15min' in timeframe:
            time_delta = timedelta(minutes=15)
        elif '1hr' in timeframe:
            time_delta = timedelta(hours=1)
        else:
            time_delta = timedelta(days=1)
        
        start_time = datetime.now(self.ist) - (time_delta * limit)
        
        for i in range(limit):
            timestamp = start_time + (time_delta * i)
            
            # Generate OHLC with some randomness
            change_percent = random.uniform(-1, 1)
            open_price = current_price
            close_price = open_price * (1 + change_percent / 100)
            high_price = max(open_price, close_price) * (1 + abs(change_percent) / 200)
            low_price = min(open_price, close_price) * (1 - abs(change_percent) / 200)
            
            candles.append({
                'symbol': symbol.upper(),
                'timeframe': timeframe,
                'timestamp': timestamp.isoformat(),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': random.randint(10000, 100000),
                'oi': random.randint(1000, 10000)
            })
            
            current_price = close_price
        
        return candles
    
    def _get_mock_options_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """Generate mock options chain data for testing"""
        import random
        base_prices = {'NIFTY': 19850, 'BANKNIFTY': 45200}
        spot_price = base_prices.get(symbol.upper(), 20000)
        
        options_data = []
        
        # Generate strikes around current price
        strike_interval = 50 if symbol.upper() == 'NIFTY' else 100
        num_strikes = 20
        
        center_strike = round(spot_price / strike_interval) * strike_interval
        
        for i in range(-num_strikes//2, num_strikes//2 + 1):
            strike = center_strike + (i * strike_interval)
            
            for option_type in ['CE', 'PE']:
                # Calculate basic option pricing
                if option_type == 'CE':
                    intrinsic = max(0, spot_price - strike)
                    delta = 0.5 if spot_price == strike else (0.8 if spot_price > strike else 0.2)
                else:
                    intrinsic = max(0, strike - spot_price)
                    delta = -0.5 if spot_price == strike else (-0.2 if spot_price > strike else -0.8)
                
                time_value = random.uniform(5, 50)
                ltp = intrinsic + time_value
                
                options_data.append({
                    'symbol': symbol.upper(),
                    'expiry': (datetime.now().date() + timedelta(days=7)).isoformat(),
                    'strike': float(strike),
                    'option_type': option_type,
                    'timestamp': datetime.now(self.ist).isoformat(),
                    'ltp': round(ltp, 2),
                    'bid': round(ltp * 0.98, 2),
                    'ask': round(ltp * 1.02, 2),
                    'volume': random.randint(1000, 50000),
                    'oi': random.randint(5000, 100000),
                    'delta': round(delta, 4),
                    'gamma': round(random.uniform(0.005, 0.02), 4),
                    'theta': round(random.uniform(-15, -5), 4),
                    'vega': round(random.uniform(8, 20), 4),
                    'rho': round(random.uniform(-2, 2), 4),
                    'iv': round(random.uniform(10, 30), 2),
                    'intrinsic_value': round(intrinsic, 2),
                    'time_value': round(time_value, 2),
                    'instrument_token': random.randint(100000, 999999)
                })
        
        return options_data
    
    async def close(self):
        """Close Kite client connections"""
        try:
            # No specific close method for KiteConnect, just reset state
            self.is_initialized = False
            self.kite = None
            logger.info("Kite client closed successfully")
        except Exception as e:
            logger.error(f"Error closing Kite client: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Kite service"""
        try:
            if not self.is_initialized:
                return {"status": "not_initialized", "authenticated": False}
            
            if await self.is_connected():
                return {"status": "healthy", "authenticated": True}
            else:
                return {"status": "unhealthy", "authenticated": False, "error": "Connection failed"}
                
        except Exception as e:
            return {"status": "unhealthy", "authenticated": False, "error": str(e)}