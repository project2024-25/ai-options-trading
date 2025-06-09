"""
AI Options Trading Agent - Data Acquisition Service with Live Data
Simple version using KiteConnect directly - Complete Implementation
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Simple import - using KiteConnect directly
from kiteconnect import KiteConnect

import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    DATA_ACQUISITION_PORT = 8001
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"
    
    # Zerodha API Configuration
    KITE_API_KEY = ""
    KITE_ACCESS_TOKEN = ""

settings = Settings()

class LiveDataCache:
    """Cache for storing last live market data"""
    
    def __init__(self):
        self.cache_dir = Path("data_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "last_live_data.json"
        
    def save_live_data(self, symbol: str, data: dict):
        """Save live data to cache"""
        try:
            # Load existing cache
            cache_data = {}
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
            
            # Update with new data
            cache_data[symbol] = {
                **data,
                "cached_at": datetime.now().isoformat(),
                "market_time": "15:30" if not is_market_hours() else datetime.now().strftime("%H:%M")
            }
            
            # Save back to file
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"✅ Cached live data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error saving cache for {symbol}: {e}")
    
    def get_cached_data(self, symbol: str):
        """Get last live data from cache"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                if symbol in cache_data:
                    cached_entry = cache_data[symbol]
                    # Update timestamp but keep original data
                    cached_entry["timestamp"] = datetime.now().isoformat()
                    cached_entry["source"] = "last_live_data"
                    cached_entry["note"] = f"Last live data from market close (3:30 PM)"
                    
                    logger.info(f"✅ Retrieved cached live data for {symbol}")
                    return cached_entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading cache for {symbol}: {e}")
            return None
        
live_cache = LiveDataCache()


# Global Kite client
kite_client: Optional[KiteConnect] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with Kite Connect integration"""
    logger.info("Starting Data Acquisition Service with Live Kite Data...")
    
    global kite_client
    
    try:
        # Load environment variables
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        settings.KITE_API_KEY = os.getenv("KITE_API_KEY", "")
        settings.KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "")
        
        if settings.KITE_API_KEY and settings.KITE_ACCESS_TOKEN:
            logger.info("✅ Found API credentials - initializing Kite client")
            
            # Initialize Kite client
            kite_client = KiteConnect(api_key=settings.KITE_API_KEY)
            kite_client.set_access_token(settings.KITE_ACCESS_TOKEN)
            
            # Test connection
            try:
                profile = kite_client.profile()
                logger.info(f"✅ Connected to Kite as: {profile['user_name']}")
                
                # Test market data
                quote = kite_client.quote(["NSE:NIFTY 50"])
                nifty_price = quote["NSE:NIFTY 50"]["last_price"]
                logger.info(f"✅ Live NIFTY price: ₹{nifty_price}")
                
            except Exception as e:
                logger.error(f"❌ Kite connection test failed: {e}")
                kite_client = None
                
        else:
            logger.warning("⚠️  Kite API credentials not provided - using mock data")
            kite_client = None
        
        logger.info("✅ Data Acquisition Service started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize service: {e}")
        kite_client = None
    
    yield
    
    # Cleanup
    logger.info("Shutting down Data Acquisition Service...")
    logger.info("Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AI Options Trading - Data Acquisition Service (Live)",
    description="Market data service with live Zerodha Kite integration",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Data Acquisition Service (Live Kite)",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Live market data via Kite Connect",
            "Real-time NIFTY/BANKNIFTY prices",
            "Options chain data",
            "Market data analytics"
        ],
        "kite_enabled": kite_client is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check with Kite status"""
    try:
        health_status = {
            "service": "data-acquisition-live",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "checks": {}
        }
        
        # Kite connection check
        if kite_client:
            try:
                # Test connection
                profile = kite_client.profile()
                health_status["checks"]["kite"] = {
                    "status": "connected",
                    "user": profile.get("user_name", "Unknown"),
                    "user_id": profile.get("user_id", "Unknown")
                }
            except Exception as e:
                health_status["checks"]["kite"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["kite"] = "not_configured"
            health_status["status"] = "degraded"
        
        # Market hours check
        health_status["checks"]["market_hours"] = "open" if is_market_hours() else "closed"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "service": "data-acquisition-live",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "error": str(e)
        }


@app.get("/api/data/nifty-snapshot")
async def get_nifty_snapshot():
    """Get live NIFTY snapshot or last live data outside market hours"""
    try:
        if kite_client and is_market_hours():
            try:
                # Get live NIFTY data during market hours
                quote = kite_client.quote(["NSE:NIFTY 50"])
                nifty_data = quote["NSE:NIFTY 50"]
                
                live_data = {
                    "success": True,
                    "data": {
                        "symbol": "NIFTY",
                        "ltp": nifty_data["last_price"],
                        "open": nifty_data.get("ohlc", {}).get("open", 0),
                        "high": nifty_data.get("ohlc", {}).get("high", 0),
                        "low": nifty_data.get("ohlc", {}).get("low", 0),
                        "close": nifty_data.get("ohlc", {}).get("close", 0),
                        "change": nifty_data.get("net_change", 0),
                        "volume": nifty_data.get("volume", 0),
                        "oi": nifty_data.get("oi", 0),
                        "timestamp": datetime.now().isoformat(),
                        "instrument_token": nifty_data.get("instrument_token", 256265)
                    },
                    "source": "kite_live",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache this live data for later use
                live_cache.save_live_data("NIFTY", live_data["data"])
                
                return live_data
                
            except Exception as e:
                logger.error(f"Error getting live NIFTY data: {e}")
                # Fall back to cached data
                cached = live_cache.get_cached_data("NIFTY")
                if cached:
                    return {
                        "success": True,
                        "data": cached,
                        "source": "last_live_data",
                        "timestamp": datetime.now().isoformat()
                    }
                return await get_mock_index_data("NIFTY")
        
        else:
            # Outside market hours - try to get cached live data first
            cached_data = live_cache.get_cached_data("NIFTY")
            if cached_data:
                return {
                    "success": True,
                    "data": cached_data,
                    "source": "last_live_data",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # No cached data available, fall back to mock
                return await get_mock_index_data("NIFTY")
        
    except Exception as e:
        logger.error(f"Error in NIFTY snapshot endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/banknifty-snapshot")
async def get_banknifty_snapshot():
    """Get live BANKNIFTY snapshot or last live data outside market hours"""
    try:
        if kite_client and is_market_hours():
            try:
                # Get live BANKNIFTY data during market hours
                quote = kite_client.quote(["NSE:NIFTY BANK"])
                banknifty_data = quote["NSE:NIFTY BANK"]
                
                live_data = {
                    "success": True,
                    "data": {
                        "symbol": "BANKNIFTY",
                        "ltp": banknifty_data["last_price"],
                        "open": banknifty_data.get("ohlc", {}).get("open", 0),
                        "high": banknifty_data.get("ohlc", {}).get("high", 0),
                        "low": banknifty_data.get("ohlc", {}).get("low", 0),
                        "close": banknifty_data.get("ohlc", {}).get("close", 0),
                        "change": banknifty_data.get("net_change", 0),
                        "volume": banknifty_data.get("volume", 0),
                        "oi": banknifty_data.get("oi", 0),
                        "timestamp": datetime.now().isoformat(),
                        "instrument_token": banknifty_data.get("instrument_token", 260105)
                    },
                    "source": "kite_live",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache this live data for later use
                live_cache.save_live_data("BANKNIFTY", live_data["data"])
                
                return live_data
                
            except Exception as e:
                logger.error(f"Error getting live BANKNIFTY data: {e}")
                # Fall back to cached data
                cached = live_cache.get_cached_data("BANKNIFTY")
                if cached:
                    return {
                        "success": True,
                        "data": cached,
                        "source": "last_live_data",
                        "timestamp": datetime.now().isoformat()
                    }
                return await get_mock_index_data("BANKNIFTY")
        
        else:
            # Outside market hours - try to get cached live data first
            cached_data = live_cache.get_cached_data("BANKNIFTY")
            if cached_data:
                return {
                    "success": True,
                    "data": cached_data,
                    "source": "last_live_data",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # No cached data available, fall back to mock
                return await get_mock_index_data("BANKNIFTY")
        
    except Exception as e:
        logger.error(f"Error in BANKNIFTY snapshot endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/vix-data")
async def get_vix_data():
    """Get live VIX data or last live data outside market hours"""
    try:
        if kite_client and is_market_hours():
            try:
                # Get live VIX data during market hours
                quote = kite_client.quote(["NSE:INDIA VIX"])
                vix_data = quote["NSE:INDIA VIX"]
                
                live_data = {
                    "success": True,
                    "data": {
                        "symbol": "VIX",
                        "ltp": vix_data["last_price"],
                        "open": vix_data.get("ohlc", {}).get("open", 0),
                        "high": vix_data.get("ohlc", {}).get("high", 0),
                        "low": vix_data.get("ohlc", {}).get("low", 0),
                        "close": vix_data.get("ohlc", {}).get("close", 0),
                        "change": vix_data.get("net_change", 0),
                        "timestamp": datetime.now().isoformat(),
                        "instrument_token": vix_data.get("instrument_token", 264969)
                    },
                    "source": "kite_live",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache this live data for later use
                live_cache.save_live_data("VIX", live_data["data"])
                
                return live_data
                
            except Exception as e:
                logger.error(f"Error getting live VIX data: {e}")
                # Fall back to cached data
                cached = live_cache.get_cached_data("VIX")
                if cached:
                    return {
                        "success": True,
                        "data": cached,
                        "source": "last_live_data",
                        "timestamp": datetime.now().isoformat()
                    }
                return await get_mock_index_data("VIX")
        
        else:
            # Outside market hours - try to get cached live data first
            cached_data = live_cache.get_cached_data("VIX")
            if cached_data:
                return {
                    "success": True,
                    "data": cached_data,
                    "source": "last_live_data",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # No cached data available, fall back to mock
                return await get_mock_index_data("VIX")
        
    except Exception as e:
        logger.error(f"Error in VIX data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/options-chain/{underlying}")
async def get_options_chain(
    underlying: str,
    expiry: Optional[str] = Query(None, description="Expiry date (YYYY-MM-DD)"),
    limit: int = Query(20, description="Maximum options to return", ge=1, le=100)
):
    """Get live options chain data"""
    try:
        underlying = underlying.upper()
        if underlying not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Only NIFTY and BANKNIFTY supported")
        
        if kite_client:
            try:
                # Get instruments
                instruments = kite_client.instruments("NFO")
                
                # Filter options for the underlying
                underlying_name = "NIFTY" if underlying == "NIFTY" else "BANKNIFTY"
                options = [
                    inst for inst in instruments 
                    if inst['name'] == underlying_name and inst['instrument_type'] in ['CE', 'PE']
                ]
                
                # Filter by expiry if provided
                if expiry:
                    try:
                        expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                        options = [
                            opt for opt in options
                            if datetime.strptime(opt['expiry'], '%Y-%m-%d').date() == expiry_date
                        ]
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid expiry date format. Use YYYY-MM-DD")
                else:
                    # Get nearest active expiry
                    current_date = datetime.now().date()
                    active_expiries = []
                    
                    for opt in options:
                        try:
                            exp_date = datetime.strptime(opt['expiry'], '%Y-%m-%d').date()
                            if exp_date >= current_date:
                                active_expiries.append(exp_date)
                        except:
                            continue
                    
                    if active_expiries:
                        nearest_expiry = min(set(active_expiries))
                        options = [
                            opt for opt in options
                            if datetime.strptime(opt['expiry'], '%Y-%m-%d').date() == nearest_expiry
                        ]
                        expiry = nearest_expiry.strftime('%Y-%m-%d')
                
                # Limit options and get quotes
                limited_options = options[:limit]
                
                if limited_options:
                    # Get quotes for options
                    option_tokens = [f"NFO:{opt['tradingsymbol']}" for opt in limited_options]
                    
                    try:
                        quotes = kite_client.quote(option_tokens)
                        
                        options_data = []
                        for opt in limited_options:
                            token = f"NFO:{opt['tradingsymbol']}"
                            if token in quotes:
                                quote_data = quotes[token]
                                
                                # Calculate basic Greeks (simplified)
                                spot_price = 24834 if underlying == "NIFTY" else 50500  # Approximate current prices
                                strike = opt["strike"]
                                option_type = opt["instrument_type"]
                                
                                if option_type == "CE":
                                    intrinsic_value = max(0, spot_price - strike)
                                else:
                                    intrinsic_value = max(0, strike - spot_price)
                                
                                ltp = quote_data["last_price"]
                                time_value = max(0, ltp - intrinsic_value)
                                
                                options_data.append({
                                    "underlying": underlying,
                                    "strike": opt["strike"],
                                    "option_type": opt["instrument_type"],
                                    "symbol": opt["tradingsymbol"],
                                    "ltp": ltp,
                                    "bid": quote_data.get("depth", {}).get("buy", [{}])[0].get("price", 0) if quote_data.get("depth") else 0,
                                    "ask": quote_data.get("depth", {}).get("sell", [{}])[0].get("price", 0) if quote_data.get("depth") else 0,
                                    "volume": quote_data.get("volume", 0),
                                    "oi": quote_data.get("oi", 0),
                                    "change": quote_data.get("net_change", 0),
                                    "expiry": opt["expiry"],
                                    "lot_size": opt["lot_size"],
                                    "tick_size": opt["tick_size"],
                                    "intrinsic_value": round(intrinsic_value, 2),
                                    "time_value": round(time_value, 2),
                                    "timestamp": datetime.now().isoformat(),
                                    "instrument_token": opt["instrument_token"]
                                })
                        
                        # Sort by strike price and option type
                        options_data.sort(key=lambda x: (x["strike"], x["option_type"]))
                        
                        return {
                            "success": True,
                            "data": options_data,
                            "count": len(options_data),
                            "underlying": underlying,
                            "expiry": expiry,
                            "source": "kite_live",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                    except Exception as e:
                        logger.error(f"Error getting options quotes: {e}")
                        return await get_mock_options_chain(underlying, expiry, limit)
                
                else:
                    return {
                        "success": True,
                        "data": [],
                        "count": 0,
                        "underlying": underlying,
                        "expiry": expiry,
                        "message": "No options found for the specified criteria",
                        "source": "kite_live"
                    }
                
            except Exception as e:
                logger.error(f"Error getting live options data: {e}")
                return await get_mock_options_chain(underlying, expiry, limit)
        else:
            return await get_mock_options_chain(underlying, expiry, limit)
        
    except Exception as e:
        logger.error(f"Error in options chain endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/options-summary/{underlying}")
async def get_options_summary(underlying: str):
    """Get options chain summary with key metrics"""
    try:
        underlying = underlying.upper()
        if underlying not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Only NIFTY and BANKNIFTY supported")
        
        if kite_client:
            try:
                # Get options chain data
                options_response = await get_options_chain(underlying, limit=50)
                
                if options_response["success"] and options_response["data"]:
                    options_data = options_response["data"]
                    
                    # Separate CE and PE options
                    ce_options = [opt for opt in options_data if opt["option_type"] == "CE"]
                    pe_options = [opt for opt in options_data if opt["option_type"] == "PE"]
                    
                    # Calculate key metrics
                    total_ce_volume = sum(opt["volume"] for opt in ce_options)
                    total_pe_volume = sum(opt["volume"] for opt in pe_options)
                    total_ce_oi = sum(opt["oi"] for opt in ce_options)
                    total_pe_oi = sum(opt["oi"] for opt in pe_options)
                    
                    pcr_volume = total_pe_volume / total_ce_volume if total_ce_volume > 0 else 0
                    pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
                    
                    # Find max pain (simplified calculation)
                    strikes = list(set(opt["strike"] for opt in options_data))
                    strikes.sort()
                    
                    max_pain_strike = 0
                    if strikes and len(strikes) > 5:
                        # Simplified max pain - strike with minimum total pain
                        pain_values = []
                        for strike in strikes:
                            ce_pain = sum(
                                max(0, strike - opt["strike"]) * opt["oi"]
                                for opt in ce_options if opt["strike"] < strike
                            )
                            pe_pain = sum(
                                max(0, opt["strike"] - strike) * opt["oi"]
                                for opt in pe_options if opt["strike"] > strike
                            )
                            pain_values.append((strike, ce_pain + pe_pain))
                        
                        if pain_values:
                            max_pain_strike = min(pain_values, key=lambda x: x[1])[0]
                    
                    return {
                        "success": True,
                        "data": {
                            "underlying": underlying,
                            "total_options": len(options_data),
                            "ce_count": len(ce_options),
                            "pe_count": len(pe_options),
                            "expiry": options_response.get("expiry"),
                            "volume_metrics": {
                                "total_ce_volume": total_ce_volume,
                                "total_pe_volume": total_pe_volume,
                                "pcr_volume": round(pcr_volume, 4)
                            },
                            "oi_metrics": {
                                "total_ce_oi": total_ce_oi,
                                "total_pe_oi": total_pe_oi,
                                "pcr_oi": round(pcr_oi, 4)
                            },
                            "max_pain_strike": max_pain_strike,
                            "strike_range": {
                                "min_strike": min(strikes) if strikes else 0,
                                "max_strike": max(strikes) if strikes else 0
                            }
                        },
                        "source": "kite_live",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return await get_mock_options_summary(underlying)
                    
            except Exception as e:
                logger.error(f"Error calculating options summary: {e}")
                return await get_mock_options_summary(underlying)
        else:
            return await get_mock_options_summary(underlying)
        
    except Exception as e:
        logger.error(f"Error in options summary endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/candles/{symbol}")
async def get_candle_data(
    symbol: str,
    timeframe: str = Query("day", description="Timeframe: minute, 5minute, 15minute, 60minute, day"),
    days: int = Query(30, description="Number of days", ge=1, le=365)
):
    """Get historical candle data"""
    try:
        symbol = symbol.upper()
        if symbol not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Only NIFTY and BANKNIFTY supported")
        
        if kite_client:
            try:
                # Map symbol to instrument token
                instrument_token = 256265 if symbol == "NIFTY" else 260105
                
                # Calculate date range
                to_date = datetime.now()
                from_date = to_date - timedelta(days=days)
                
                # Get historical data
                candles = kite_client.historical_data(
                    instrument_token=instrument_token,
                    from_date=from_date,
                    to_date=to_date,
                    interval=timeframe
                )
                
                if candles:
                    formatted_candles = []
                    for candle in candles:
                        formatted_candles.append({
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "timestamp": candle["date"].isoformat() if hasattr(candle["date"], 'isoformat') else str(candle["date"]),
                            "open": float(candle["open"]),
                            "high": float(candle["high"]),
                            "low": float(candle["low"]),
                            "close": float(candle["close"]),
                            "volume": int(candle.get("volume", 0)),
                            "oi": int(candle.get("oi", 0))
                        })
                    
                    return {
                        "success": True,
                        "data": formatted_candles,
                        "count": len(formatted_candles),
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "days": days,
                        "source": "kite_live",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": True,
                        "data": [],
                        "count": 0,
                        "message": "No candle data available",
                        "source": "kite_live"
                    }
                    
            except Exception as e:
                logger.error(f"Error getting candle data: {e}")
                return await get_mock_candle_data(symbol, timeframe, days)
        else:
            return await get_mock_candle_data(symbol, timeframe, days)
        
    except Exception as e:
        logger.error(f"Error in candle data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/market-status")
async def get_market_status():
    """Get comprehensive market status"""
    try:
        market_open = is_market_hours()
        current_time = datetime.now()
        
        status_data = {
            "is_open": market_open,
            "current_time": current_time.isoformat(),
            "timezone": "Asia/Kolkata",
            "session_type": "regular" if market_open else "closed",
            "kite_connected": kite_client is not None
        }
        
        if kite_client:
            try:
                # Add live market data
                nifty_quote = kite_client.quote(["NSE:NIFTY 50"])
                banknifty_quote = kite_client.quote(["NSE:NIFTY BANK"])
                
                status_data["live_data"] = {
                    "nifty_ltp": nifty_quote["NSE:NIFTY 50"]["last_price"],
                    "banknifty_ltp": banknifty_quote["NSE:NIFTY BANK"]["last_price"],
                    "data_source": "kite_live"
                }
            except Exception as e:
                status_data["live_data"] = {"error": str(e)}
        
        return {
            "success": True,
            "data": status_data,
            "timestamp": current_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mock data functions for fallback
async def get_mock_index_data(symbol: str):
    """Generate mock index data when live data unavailable"""
    import random
    
    # Use current market prices as base
    base_prices = {"NIFTY": 24834, "BANKNIFTY": 50500, "VIX": 15.5}
    base_price = base_prices.get(symbol, 20000)
    
    change = random.uniform(-2, 2)
    current_price = base_price + (base_price * change / 100)
    
    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "ltp": round(current_price, 2),
            "open": round(base_price, 2),
            "high": round(current_price + abs(change) * 10, 2),
            "low": round(current_price - abs(change) * 10, 2),
            "close": round(base_price, 2),
            "change": round(change * base_price / 100, 2),
            "volume": random.randint(100000, 1000000),
            "oi": random.randint(10000, 100000),
            "timestamp": datetime.now().isoformat(),
            "instrument_token": {"NIFTY": 256265, "BANKNIFTY": 260105, "VIX": 264969}.get(symbol, 0)
        },
        "source": "mock_data",
        "timestamp": datetime.now().isoformat()
    }


async def get_mock_options_chain(underlying: str, expiry: str = None, limit: int = 20):
    """Generate mock options chain"""
    import random
    
    if not expiry:
        expiry = (datetime.now().date() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    base_prices = {"NIFTY": 24834, "BANKNIFTY": 50500}
    spot_price = base_prices.get(underlying, 20000)
    strike_interval = 50 if underlying == "NIFTY" else 100
    
    options_data = []
    center_strike = round(spot_price / strike_interval) * strike_interval
    
    for i in range(-limit//4, limit//4 + 1):
        strike = center_strike + (i * strike_interval)
        
        for option_type in ["CE", "PE"]:
            if option_type == "CE":
                intrinsic = max(0, spot_price - strike)
            else:
                intrinsic = max(0, strike - spot_price)
            
            time_value = random.uniform(5, 50)
            ltp = intrinsic + time_value
            
            options_data.append({
                "underlying": underlying,
                "strike": strike,
                "option_type": option_type,
                "symbol": f"{underlying}{expiry.replace('-', '')}{strike}{option_type}",
                "ltp": round(ltp, 2),
                "bid": round(ltp * 0.98, 2),
                "ask": round(ltp * 1.02, 2),
                "volume": random.randint(1000, 50000),
                "oi": random.randint(10000, 100000),
                "change": round(random.uniform(-20, 20), 2),
                "expiry": expiry,
                "lot_size": 50 if underlying == "NIFTY" else 25,
                "tick_size": 0.05,
                "intrinsic_value": round(intrinsic, 2),
                "time_value": round(time_value, 2),
                "timestamp": datetime.now().isoformat(),
                "instrument_token": random.randint(100000, 999999)
            })
    
    return {
        "success": True,
        "data": options_data[:limit],
        "count": min(len(options_data), limit),
        "underlying": underlying,
        "expiry": expiry,
        "source": "mock_data",
        "timestamp": datetime.now().isoformat()
    }


async def get_mock_options_summary(underlying: str):
    """Generate mock options summary"""
    import random
    
    return {
        "success": True,
        "data": {
            "underlying": underlying,
            "total_options": 40,
            "ce_count": 20,
            "pe_count": 20,
            "expiry": (datetime.now().date() + timedelta(days=7)).strftime('%Y-%m-%d'),
            "volume_metrics": {
                "total_ce_volume": random.randint(100000, 500000),
                "total_pe_volume": random.randint(100000, 500000),
                "pcr_volume": round(random.uniform(0.7, 1.3), 4)
            },
            "oi_metrics": {
                "total_ce_oi": random.randint(500000, 2000000),
                "total_pe_oi": random.randint(500000, 2000000),
                "pcr_oi": round(random.uniform(0.8, 1.2), 4)
            },
            "max_pain_strike": round(24834 if underlying == "NIFTY" else 50500, -2),
            "strike_range": {
                "min_strike": 24600 if underlying == "NIFTY" else 50000,
                "max_strike": 25000 if underlying == "NIFTY" else 51000
            }
        },
        "source": "mock_data",
        "timestamp": datetime.now().isoformat()
    }


async def get_mock_candle_data(symbol: str, timeframe: str, days: int):
    """Generate mock candle data"""
    import random
    
    base_prices = {"NIFTY": 24834, "BANKNIFTY": 50500}
    base_price = base_prices.get(symbol, 20000)
    
    # Calculate number of candles based on timeframe
    if timeframe == "minute":
        total_minutes = days * 24 * 60
        candle_count = min(total_minutes, 1000)  # Limit to 1000 candles
        time_delta = timedelta(minutes=1)
    elif timeframe == "5minute":
        total_candles = days * 24 * 12  # 12 five-minute candles per hour
        candle_count = min(total_candles, 500)
        time_delta = timedelta(minutes=5)
    elif timeframe == "15minute":
        total_candles = days * 24 * 4  # 4 fifteen-minute candles per hour
        candle_count = min(total_candles, 200)
        time_delta = timedelta(minutes=15)
    elif timeframe == "60minute":
        candle_count = min(days * 24, 100)  # 24 hourly candles per day
        time_delta = timedelta(hours=1)
    else:  # day
        candle_count = days
        time_delta = timedelta(days=1)
    
    candles = []
    current_price = base_price
    start_time = datetime.now() - timedelta(days=days)
    
    for i in range(candle_count):
        timestamp = start_time + (time_delta * i)
        
        # Generate realistic OHLC data
        change_percent = random.uniform(-2, 2)
        open_price = current_price
        close_price = open_price * (1 + change_percent / 100)
        
        high_price = max(open_price, close_price) * (1 + abs(change_percent) / 200)
        low_price = min(open_price, close_price) * (1 - abs(change_percent) / 200)
        
        candles.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": timestamp.isoformat(),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": random.randint(10000, 100000),
            "oi": random.randint(1000, 10000)
        })
        
        current_price = close_price
    
    return {
        "success": True,
        "data": candles,
        "count": len(candles),
        "symbol": symbol,
        "timeframe": timeframe,
        "days": days,
        "source": "mock_data",
        "timestamp": datetime.now().isoformat()
    }


def is_market_hours() -> bool:
    """Check if current time is within market hours"""
    try:
        from datetime import time
        import pytz
        
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_start = time(9, 15)
        market_end = time(15, 30)
        current_time = now.time()
        
        return market_start <= current_time <= market_end
        
    except Exception as e:
        logger.error(f"Error checking market hours: {e}")
        return False


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.DATA_ACQUISITION_PORT,
        reload=settings.DEBUG_MODE,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )