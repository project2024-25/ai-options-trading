"""
Enhanced Zerodha MCP Client with Options Chain Support
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import pytz

logger = logging.getLogger(__name__)


class MCPMode(Enum):
    """MCP Data Modes"""
    LTP = "ltp"           # Last Traded Price only
    QUOTE = "quote"       # LTP + OHLC + Volume
    FULL = "full"         # Complete market depth + all data


@dataclass
class OptionsChainRequest:
    """Options chain subscription request"""
    underlying: str       # "NIFTY" or "BANKNIFTY"
    expiry: str          # "2023-11-30" format
    strike_range: tuple  # (from_strike, to_strike) or None for all
    option_types: List[str] = None  # ["CE", "PE"] or None for both


@dataclass
class OptionsInstrument:
    """Options instrument details"""
    instrument_token: int
    tradingsymbol: str
    name: str
    expiry: date
    strike: float
    instrument_type: str  # "CE" or "PE"
    lot_size: int
    tick_size: float


class ZerodhaMCPClient:
    """Enhanced MCP Client with Options Chain Support"""
    
    def __init__(
        self,
        api_key: str,
        access_token: str,
        mcp_url: str = "wss://api.kite.trade/ws",
        reconnect_attempts: int = 5,
        heartbeat_interval: int = 30
    ):
        self.api_key = api_key
        self.access_token = access_token
        self.mcp_url = mcp_url
        self.reconnect_attempts = reconnect_attempts
        self.heartbeat_interval = heartbeat_interval
        
        # Connection state
        self.websocket = None
        self.is_connected = False
        self.is_authenticated = False
        self.sequence_id = 0
        
        # Subscriptions and data storage
        self.subscriptions: Dict[int, Any] = {}
        self.options_instruments: Dict[str, List[OptionsInstrument]] = {}
        self.live_options_data: Dict[int, Dict[str, Any]] = {}
        self.live_index_data: Dict[str, Dict[str, Any]] = {}
        
        # Data callbacks
        self.data_callbacks: Dict[str, List[Callable]] = {}
        
        # Background tasks
        self.heartbeat_task = None
        self.message_task = None
        
        # IST timezone
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # Standard instrument tokens (Zerodha specific)
        self.standard_tokens = {
            "NIFTY": 256265,
            "BANKNIFTY": 260105,
            "VIX": 264969
        }
    
    async def connect(self) -> bool:
        """Enhanced connection with proper Kite WebSocket protocol"""
        try:
            logger.info("Connecting to Zerodha WebSocket...")
            
            # Connect to Kite WebSocket
            self.websocket = await websockets.connect(
                self.mcp_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            # Kite WebSocket expects binary authentication
            auth_message = self._create_auth_message()
            await self.websocket.send(auth_message)
            
            # Wait for authentication response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            
            if self._verify_auth_response(response):
                self.is_connected = True
                self.is_authenticated = True
                logger.info("Successfully connected to Zerodha WebSocket")
                
                # Start background tasks
                await self._start_background_tasks()
                
                # Load instruments list
                await self._load_options_instruments()
                
                return True
            else:
                logger.error("WebSocket authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Zerodha WebSocket: {e}")
            return False
    
    def _create_auth_message(self) -> bytes:
        """Create Kite WebSocket authentication message"""
        # Kite WebSocket protocol: send access token as binary
        return self.access_token.encode('utf-8')
    
    def _verify_auth_response(self, response: bytes) -> bool:
        """Verify authentication response from Kite WebSocket"""
        try:
            # Kite sends binary response, successful auth usually returns specific bytes
            return len(response) > 0  # Simplified verification
        except Exception as e:
            logger.error(f"Error verifying auth response: {e}")
            return False
    
    async def subscribe_indices(self, indices: List[str], mode: MCPMode = MCPMode.FULL) -> bool:
        """Subscribe to index data (NIFTY, BANKNIFTY, VIX)"""
        try:
            tokens = []
            for index in indices:
                if index.upper() in self.standard_tokens:
                    token = self.standard_tokens[index.upper()]
                    tokens.append(token)
                    
                    # Store subscription
                    self.subscriptions[token] = {
                        "type": "index",
                        "symbol": index.upper(),
                        "mode": mode.value
                    }
            
            if tokens:
                success = await self._subscribe_tokens(tokens, mode)
                if success:
                    logger.info(f"Subscribed to {len(tokens)} indices: {indices}")
                return success
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to subscribe to indices: {e}")
            return False
    
    async def subscribe_options_chain(
        self, 
        request: OptionsChainRequest, 
        mode: MCPMode = MCPMode.QUOTE
    ) -> bool:
        """Subscribe to complete options chain for an underlying"""
        try:
            underlying = request.underlying.upper()
            
            # Get options instruments for the underlying and expiry
            instruments = await self._get_options_instruments(
                underlying, 
                request.expiry,
                request.strike_range,
                request.option_types
            )
            
            if not instruments:
                logger.error(f"No options instruments found for {underlying} {request.expiry}")
                return False
            
            # Extract tokens
            tokens = [inst.instrument_token for inst in instruments]
            
            # Subscribe to all tokens
            success = await self._subscribe_tokens(tokens, mode)
            
            if success:
                # Store subscription details
                for inst in instruments:
                    self.subscriptions[inst.instrument_token] = {
                        "type": "option",
                        "underlying": underlying,
                        "expiry": request.expiry,
                        "strike": inst.strike,
                        "option_type": inst.instrument_type,
                        "symbol": inst.tradingsymbol,
                        "mode": mode.value
                    }
                
                logger.info(f"Subscribed to {len(tokens)} options for {underlying} {request.expiry}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to subscribe to options chain: {e}")
            return False
    
    async def _subscribe_tokens(self, tokens: List[int], mode: MCPMode) -> bool:
        """Subscribe to specific instrument tokens"""
        try:
            if not self.is_connected or not tokens:
                return False
            
            # Kite WebSocket subscription message format
            # Mode mapping: ltp=1, quote=2, full=3
            mode_map = {"ltp": 1, "quote": 2, "full": 3}
            mode_value = mode_map.get(mode.value, 2)
            
            # Create subscription message (binary format for Kite)
            message = self._create_subscription_message(tokens, mode_value)
            await self.websocket.send(message)
            
            logger.debug(f"Sent subscription for {len(tokens)} tokens with mode {mode.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to tokens: {e}")
            return False
    
    def _create_subscription_message(self, tokens: List[int], mode: int) -> bytes:
        """Create binary subscription message for Kite WebSocket"""
        # Kite WebSocket binary format for subscription
        # This is a simplified version - actual format may vary
        
        message = bytearray()
        
        # Message type (subscribe = 1)
        message.append(1)
        
        # Mode
        message.append(mode)
        
        # Number of tokens
        message.extend(len(tokens).to_bytes(2, 'big'))
        
        # Tokens (4 bytes each)
        for token in tokens:
            message.extend(token.to_bytes(4, 'big'))
        
        return bytes(message)
    
    async def _load_options_instruments(self):
        """Load options instruments from Kite API"""
        try:
            # This would typically use Kite REST API to get instruments
            # For now, we'll create mock instruments for testing
            await self._create_mock_options_instruments()
            
        except Exception as e:
            logger.error(f"Failed to load options instruments: {e}")
    
    async def _create_mock_options_instruments(self):
        """Create mock options instruments for testing"""
        # Mock NIFTY options for current month expiry
        current_date = datetime.now().date()
        # Find next Thursday (typical options expiry)
        days_ahead = 3 - current_date.weekday()  # Thursday = 3
        if days_ahead <= 0:
            days_ahead += 7
        next_expiry = current_date + timedelta(days=days_ahead)
        
        nifty_base = 19850
        banknifty_base = 45200
        
        # Generate mock NIFTY options
        nifty_options = []
        for i in range(-10, 11):  # 21 strikes around ATM
            strike = nifty_base + (i * 50)
            
            for option_type in ["CE", "PE"]:
                token = 1000000 + (i + 10) * 100 + (1 if option_type == "CE" else 2)
                
                instrument = OptionsInstrument(
                    instrument_token=token,
                    tradingsymbol=f"NIFTY{next_expiry.strftime('%y%m%d')}{strike}{option_type}",
                    name="NIFTY",
                    expiry=next_expiry,
                    strike=float(strike),
                    instrument_type=option_type,
                    lot_size=50,
                    tick_size=0.05
                )
                nifty_options.append(instrument)
        
        # Generate mock BANKNIFTY options
        banknifty_options = []
        for i in range(-10, 11):  # 21 strikes around ATM
            strike = banknifty_base + (i * 100)
            
            for option_type in ["CE", "PE"]:
                token = 2000000 + (i + 10) * 100 + (1 if option_type == "CE" else 2)
                
                instrument = OptionsInstrument(
                    instrument_token=token,
                    tradingsymbol=f"BANKNIFTY{next_expiry.strftime('%y%m%d')}{strike}{option_type}",
                    name="BANKNIFTY",
                    expiry=next_expiry,
                    strike=float(strike),
                    instrument_type=option_type,
                    lot_size=25,
                    tick_size=0.05
                )
                banknifty_options.append(instrument)
        
        # Store instruments
        expiry_str = next_expiry.strftime('%Y-%m-%d')
        self.options_instruments[f"NIFTY_{expiry_str}"] = nifty_options
        self.options_instruments[f"BANKNIFTY_{expiry_str}"] = banknifty_options
        
        logger.info(f"Created mock options instruments for {expiry_str}")
    
    async def _get_options_instruments(
        self, 
        underlying: str, 
        expiry: str,
        strike_range: tuple = None,
        option_types: List[str] = None
    ) -> List[OptionsInstrument]:
        """Get options instruments for given criteria"""
        try:
            key = f"{underlying}_{expiry}"
            instruments = self.options_instruments.get(key, [])
            
            # Filter by strike range
            if strike_range:
                from_strike, to_strike = strike_range
                instruments = [
                    inst for inst in instruments 
                    if from_strike <= inst.strike <= to_strike
                ]
            
            # Filter by option types
            if option_types:
                instruments = [
                    inst for inst in instruments 
                    if inst.instrument_type in option_types
                ]
            
            return instruments
            
        except Exception as e:
            logger.error(f"Error getting options instruments: {e}")
            return []
    
    async def _start_background_tasks(self):
        """Start background tasks for message processing"""
        self.message_task = asyncio.create_task(self._message_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _message_loop(self):
        """Process incoming WebSocket messages"""
        while self.is_connected:
            try:
                # Receive binary message from Kite WebSocket
                message = await self.websocket.recv()
                await self._process_message(message)
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.is_connected = False
                break
                
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, message: bytes):
        """Process binary message from Kite WebSocket"""
        try:
            # Parse Kite WebSocket binary format
            parsed_data = self._parse_kite_message(message)
            
            if parsed_data:
                await self._handle_market_data(parsed_data)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _parse_kite_message(self, message: bytes) -> Optional[Dict[str, Any]]:
        """Parse Kite WebSocket binary message format"""
        try:
            # Simplified parser - actual Kite format is more complex
            if len(message) < 8:
                return None
            
            # Extract instrument token (first 4 bytes)
            instrument_token = int.from_bytes(message[0:4], 'big')
            
            # Check if we have subscription for this token
            if instrument_token not in self.subscriptions:
                return None
            
            subscription = self.subscriptions[instrument_token]
            
            # Mock parsing - in real implementation, parse actual binary format
            import random
            
            if subscription["type"] == "index":
                # Mock index data
                base_price = 19850 if subscription["symbol"] == "NIFTY" else 45200
                change = random.uniform(-2, 2)
                current_price = base_price * (1 + change / 100)
                
                return {
                    "instrument_token": instrument_token,
                    "type": "index",
                    "symbol": subscription["symbol"],
                    "ltp": round(current_price, 2),
                    "volume": random.randint(100000, 1000000),
                    "change": round(change, 2),
                    "timestamp": datetime.now(self.ist).isoformat()
                }
            
            elif subscription["type"] == "option":
                # Mock options data
                strike = subscription["strike"]
                option_type = subscription["option_type"]
                
                # Simple option pricing mock
                spot = 19850 if subscription["underlying"] == "NIFTY" else 45200
                if option_type == "CE":
                    intrinsic = max(0, spot - strike)
                else:
                    intrinsic = max(0, strike - spot)
                
                time_value = random.uniform(5, 50)
                ltp = intrinsic + time_value
                
                return {
                    "instrument_token": instrument_token,
                    "type": "option",
                    "underlying": subscription["underlying"],
                    "strike": strike,
                    "option_type": option_type,
                    "symbol": subscription["symbol"],
                    "ltp": round(ltp, 2),
                    "volume": random.randint(1000, 50000),
                    "oi": random.randint(10000, 100000),
                    "timestamp": datetime.now(self.ist).isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing Kite message: {e}")
            return None
    
    async def _handle_market_data(self, data: Dict[str, Any]):
        """Handle parsed market data"""
        try:
            data_type = data.get("type")
            
            if data_type == "index":
                # Store index data
                symbol = data["symbol"]
                self.live_index_data[symbol] = data
                
                # Trigger callbacks
                await self._trigger_callbacks("index_data", data)
                
            elif data_type == "option":
                # Store options data
                token = data["instrument_token"]
                self.live_options_data[token] = data
                
                # Trigger callbacks
                await self._trigger_callbacks("options_data", data)
                
        except Exception as e:
            logger.error(f"Error handling market data: {e}")
    
    async def _trigger_callbacks(self, callback_type: str, data: Dict[str, Any]):
        """Trigger registered callbacks"""
        callbacks = self.data_callbacks.get(callback_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat (if required by Kite)"""
        while self.is_connected:
            try:
                # Kite WebSocket may not require explicit heartbeat
                # Ping/Pong is handled by websockets library
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                break
    
    def register_callback(self, callback_type: str, callback: Callable):
        """Register callback for specific data type"""
        if callback_type not in self.data_callbacks:
            self.data_callbacks[callback_type] = []
        self.data_callbacks[callback_type].append(callback)
    
    async def get_live_index_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest index data"""
        return self.live_index_data.get(symbol.upper())
    
    async def get_live_options_chain(self, underlying: str, expiry: str) -> List[Dict[str, Any]]:
        """Get latest options chain data"""
        options_data = []
        
        for token, data in self.live_options_data.items():
            if (data.get("underlying", "").upper() == underlying.upper() and 
                data.get("expiry") == expiry):
                options_data.append(data)
        
        # Sort by strike and option type
        options_data.sort(key=lambda x: (x.get("strike", 0), x.get("option_type", "")))
        return options_data
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        try:
            self.is_connected = False
            
            # Cancel background tasks
            if self.message_task:
                self.message_task.cancel()
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            
            # Close WebSocket
            if self.websocket:
                await self.websocket.close()
            
            logger.info("Disconnected from Zerodha WebSocket")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.is_connected,
            "authenticated": self.is_authenticated,
            "total_subscriptions": len(self.subscriptions),
            "index_subscriptions": len([s for s in self.subscriptions.values() if s["type"] == "index"]),
            "options_subscriptions": len([s for s in self.subscriptions.values() if s["type"] == "option"]),
            "live_index_symbols": len(self.live_index_data),
            "live_options_count": len(self.live_options_data),
            "server_url": self.mcp_url
        }