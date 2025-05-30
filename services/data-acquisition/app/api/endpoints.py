"""
API endpoints for Data Acquisition Service
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import insert_market_data, insert_options_data, get_latest_candle_data, get_latest_options_chain
from app.core.redis_client import (
    cache_market_data, get_cached_market_data,
    cache_options_chain, get_cached_options_chain,
    cache_index_snapshot, get_cached_index_snapshot
)
from app.services.kite_client import KiteClientService
from app.models.market_data import (
    IndexSnapshot, CandleData, OptionData,
    CandleDataRequest, CandleDataResponse,
    OptionsChainRequest, OptionsChainResponse,
    IndexSnapshotResponse, ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Global Kite service instance (will be injected)
kite_service: Optional[KiteClientService] = None


def get_kite_service() -> KiteClientService:
    """Dependency to get Kite service instance"""
    from app.main import kite_service as global_kite_service
    if not global_kite_service:
        raise HTTPException(status_code=503, detail="Kite service not available")
    return global_kite_service


@router.get("/data/nifty-snapshot", response_model=IndexSnapshotResponse)
async def get_nifty_snapshot(
    use_cache: bool = Query(True, description="Use cached data if available"),
    kite: KiteClientService = Depends(get_kite_service)
):
    """Get current NIFTY index snapshot"""
    try:
        # Check cache first if requested
        if use_cache:
            cached_data = await get_cached_index_snapshot("NIFTY")
            if cached_data:
                return IndexSnapshotResponse(
                    success=True,
                    data=IndexSnapshot(**cached_data),
                    from_cache=True
                )
        
        # Get fresh data from Kite API
        snapshot_data = await kite.get_index_snapshot("NIFTY")
        if not snapshot_data:
            raise HTTPException(status_code=503, detail="Failed to fetch NIFTY data")
        
        # Cache the data
        await cache_index_snapshot("NIFTY", snapshot_data)
        
        return IndexSnapshotResponse(
            success=True,
            data=IndexSnapshot(**snapshot_data),
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting NIFTY snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/banknifty-snapshot", response_model=IndexSnapshotResponse)
async def get_banknifty_snapshot(
    use_cache: bool = Query(True, description="Use cached data if available"),
    kite: KiteClientService = Depends(get_kite_service)
):
    """Get current BANKNIFTY index snapshot"""
    try:
        # Check cache first if requested
        if use_cache:
            cached_data = await get_cached_index_snapshot("BANKNIFTY")
            if cached_data:
                return IndexSnapshotResponse(
                    success=True,
                    data=IndexSnapshot(**cached_data),
                    from_cache=True
                )
        
        # Get fresh data from Kite API
        snapshot_data = await kite.get_index_snapshot("BANKNIFTY")
        if not snapshot_data:
            raise HTTPException(status_code=503, detail="Failed to fetch BANKNIFTY data")
        
        # Cache the data
        await cache_index_snapshot("BANKNIFTY", snapshot_data)
        
        return IndexSnapshotResponse(
            success=True,
            data=IndexSnapshot(**snapshot_data),
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BANKNIFTY snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/vix-data", response_model=IndexSnapshotResponse)
async def get_vix_data(
    use_cache: bool = Query(True, description="Use cached data if available"),
    kite: KiteClientService = Depends(get_kite_service)
):
    """Get current VIX data"""
    try:
        # Check cache first if requested
        if use_cache:
            cached_data = await get_cached_index_snapshot("VIX")
            if cached_data:
                return IndexSnapshotResponse(
                    success=True,
                    data=IndexSnapshot(**cached_data),
                    from_cache=True
                )
        
        # Get fresh data from Kite API
        vix_data = await kite.get_index_snapshot("VIX")
        if not vix_data:
            raise HTTPException(status_code=503, detail="Failed to fetch VIX data")
        
        # Cache the data
        await cache_index_snapshot("VIX", vix_data)
        
        return IndexSnapshotResponse(
            success=True,
            data=IndexSnapshot(**vix_data),
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting VIX data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/{symbol}-candles/{timeframe}", response_model=CandleDataResponse)
async def get_candle_data(
    symbol: str,
    timeframe: str,
    from_date: Optional[str] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="To date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Maximum number of candles", ge=1, le=1000),
    use_cache: bool = Query(True, description="Use cached data if available"),
    store_in_db: bool = Query(True, description="Store data in database"),
    kite: KiteClientService = Depends(get_kite_service)
):
    """Get candle data for NIFTY/BANKNIFTY"""
    try:
        # Validate symbol
        symbol = symbol.upper()
        if symbol not in ['NIFTY', 'BANKNIFTY']:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # Validate timeframe
        valid_timeframes = ['5min', '15min', '1hr', '1day', '1week', '1month']
        if timeframe not in valid_timeframes:
            raise HTTPException(status_code=400, detail=f"Timeframe must be one of {valid_timeframes}")
        
        # Check cache first if requested and no specific date range
        if use_cache and not from_date and not to_date:
            cached_data = await get_cached_market_data(symbol, timeframe)
            if cached_data:
                return CandleDataResponse(
                    success=True,
                    data=[CandleData(**candle) for candle in cached_data],
                    count=len(cached_data),
                    symbol=symbol,
                    timeframe=timeframe,
                    from_cache=True
                )
        
        # Parse dates if provided
        from_dt = None
        to_dt = None
        if from_date:
            from_dt = datetime.strptime(from_date, '%Y-%m-%d')
        if to_date:
            to_dt = datetime.strptime(to_date, '%Y-%m-%d')
        
        # Get fresh data from Kite API
        candle_data = await kite.get_candle_data(symbol, timeframe, from_dt, to_dt, limit)
        if not candle_data:
            raise HTTPException(status_code=503, detail=f"Failed to fetch candle data for {symbol}")
        
        # Store in database if requested
        if store_in_db:
            background_tasks = BackgroundTasks()
            for candle in candle_data:
                background_tasks.add_task(insert_market_data, candle)
        
        # Cache the data if it's current data (no specific date range)
        if not from_date and not to_date:
            await cache_market_data(symbol, timeframe, candle_data)
        
        return CandleDataResponse(
            success=True,
            data=[CandleData(**candle) for candle in candle_data],
            count=len(candle_data),
            symbol=symbol,
            timeframe=timeframe,
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candle data for {symbol} {timeframe}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/options-chain/{symbol}", response_model=OptionsChainResponse)
async def get_options_chain(
    symbol: str,
    expiry: Optional[str] = Query(None, description="Expiry date (YYYY-MM-DD)"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    store_in_db: bool = Query(True, description="Store data in database"),
    kite: KiteClientService = Depends(get_kite_service)
):
    """Get options chain data for NIFTY/BANKNIFTY"""
    try:
        # Validate symbol
        symbol = symbol.upper()
        if symbol not in ['NIFTY', 'BANKNIFTY']:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # Check cache first if requested and no specific expiry
        cache_key = f"{symbol}_{expiry}" if expiry else symbol
        if use_cache:
            cached_data = await get_cached_options_chain(cache_key)
            if cached_data:
                return OptionsChainResponse(
                    success=True,
                    data=[OptionData(**option) for option in cached_data],
                    count=len(cached_data),
                    symbol=symbol,
                    expiry=expiry,
                    from_cache=True
                )
        
        # Get fresh data from Kite API
        options_data = await kite.get_options_chain(symbol, expiry)
        if not options_data:
            raise HTTPException(status_code=503, detail=f"Failed to fetch options chain for {symbol}")
        
        # Store in database if requested
        if store_in_db:
            background_tasks = BackgroundTasks()
            for option in options_data:
                background_tasks.add_task(insert_options_data, option)
        
        # Cache the data
        await cache_options_chain(cache_key, options_data)
        
        return OptionsChainResponse(
            success=True,
            data=[OptionData(**option) for option in options_data],
            count=len(options_data),
            symbol=symbol,
            expiry=expiry,
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting options chain for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/historical/candles", response_model=CandleDataResponse)
async def get_historical_candles(
    symbol: str = Query(..., description="Symbol (NIFTY/BANKNIFTY)"),
    timeframe: str = Query(..., description="Timeframe"),
    days: int = Query(30, description="Number of days to fetch", ge=1, le=365)
):
    """Get historical candle data from database"""
    try:
        # Validate symbol
        symbol = symbol.upper()
        if symbol not in ['NIFTY', 'BANKNIFTY']:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # Get data from database
        candle_data = await get_latest_candle_data(symbol, timeframe, limit=days * 78)  # Approx candles per day
        
        if not candle_data:
            return CandleDataResponse(
                success=True,
                data=[],
                count=0,
                symbol=symbol,
                timeframe=timeframe,
                from_cache=False
            )
        
        # Convert to response format
        formatted_data = [CandleData(**candle) for candle in candle_data]
        
        return CandleDataResponse(
            success=True,
            data=formatted_data,
            count=len(formatted_data),
            symbol=symbol,
            timeframe=timeframe,
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical candles: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/historical/options", response_model=OptionsChainResponse)
async def get_historical_options(
    symbol: str = Query(..., description="Symbol (NIFTY/BANKNIFTY)"),
    expiry: Optional[str] = Query(None, description="Expiry date (YYYY-MM-DD)"),
    days: int = Query(7, description="Number of days to fetch", ge=1, le=30)
):
    """Get historical options data from database"""
    try:
        # Validate symbol
        symbol = symbol.upper()
        if symbol not in ['NIFTY', 'BANKNIFTY']:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # Get data from database
        options_data = await get_latest_options_chain(symbol, expiry, limit=1000)
        
        if not options_data:
            return OptionsChainResponse(
                success=True,
                data=[],
                count=0,
                symbol=symbol,
                expiry=expiry,
                from_cache=False
            )
        
        # Convert to response format
        formatted_data = [OptionData(**option) for option in options_data]
        
        return OptionsChainResponse(
            success=True,
            data=formatted_data,
            count=len(formatted_data),
            symbol=symbol,
            expiry=expiry,
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical options: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/data/collect/candles")
async def trigger_candle_collection(
    symbol: str = Query(..., description="Symbol (NIFTY/BANKNIFTY)"),
    timeframe: str = Query(..., description="Timeframe"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    kite: KiteClientService = Depends(get_kite_service)
):
    """Manually trigger candle data collection"""
    try:
        # Validate inputs
        symbol = symbol.upper()
        if symbol not in ['NIFTY', 'BANKNIFTY']:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # Add background task for data collection
        background_tasks.add_task(collect_and_store_candles, symbol, timeframe, kite)
        
        return {
            "success": True,
            "message": f"Candle data collection triggered for {symbol} {timeframe}",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering candle collection: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/data/collect/options")
async def trigger_options_collection(
    symbol: str = Query(..., description="Symbol (NIFTY/BANKNIFTY)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    kite: KiteClientService = Depends(get_kite_service)
):
    """Manually trigger options chain data collection"""
    try:
        # Validate inputs
        symbol = symbol.upper()
        if symbol not in ['NIFTY', 'BANKNIFTY']:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # Add background task for data collection
        background_tasks.add_task(collect_and_store_options, symbol, kite)
        
        return {
            "success": True,
            "message": f"Options chain collection triggered for {symbol}",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering options collection: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/market-status")
async def get_market_status():
    """Get current market status"""
    try:
        from app.main import is_market_hours
        
        market_open = is_market_hours()
        current_time = datetime.now()
        
        # Market session info
        session_info = {
            "is_open": market_open,
            "current_time": current_time.isoformat(),
            "timezone": "Asia/Kolkata",
            "next_session": None,
            "session_type": None
        }
        
        if market_open:
            session_info["session_type"] = "regular"
            # Calculate market close time
            market_close = current_time.replace(hour=15, minute=30, second=0, microsecond=0)
            session_info["time_to_close"] = str(market_close - current_time)
        else:
            # Calculate next market open
            next_open = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
            if current_time.time() > next_open.time():
                next_open += timedelta(days=1)
            
            # Skip weekends
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)
            
            session_info["next_session"] = next_open.isoformat()
            session_info["time_to_open"] = str(next_open - current_time)
        
        return {
            "success": True,
            "data": session_info,
            "timestamp": current_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/cache-stats")
async def get_cache_statistics():
    """Get cache performance statistics"""
    try:
        from app.core.redis_client import cache_manager
        
        stats = await cache_manager.get_cache_stats()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/data/cache/clear")
async def clear_cache(
    pattern: str = Query("*", description="Cache key pattern to clear")
):
    """Clear cache data"""
    try:
        from app.core.redis_client import cache_manager
        
        cleared_count = await cache_manager.clear_pattern(pattern)
        
        return {
            "success": True,
            "message": f"Cleared {cleared_count} cache keys matching pattern: {pattern}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Background task functions
async def collect_and_store_candles(symbol: str, timeframe: str, kite: KiteClientService):
    """Background task to collect and store candle data"""
    try:
        logger.info(f"Starting candle collection for {symbol} {timeframe}")
        
        # Get candle data
        candle_data = await kite.get_candle_data(symbol, timeframe, limit=100)
        
        if candle_data:
            # Store in database
            for candle in candle_data:
                await insert_market_data(candle)
            
            # Cache the data
            await cache_market_data(symbol, timeframe, candle_data)
            
            logger.info(f"Successfully collected and stored {len(candle_data)} candles for {symbol} {timeframe}")
        else:
            logger.warning(f"No candle data received for {symbol} {timeframe}")
            
    except Exception as e:
        logger.error(f"Error in background candle collection: {e}")


async def collect_and_store_options(symbol: str, kite: KiteClientService):
    """Background task to collect and store options data"""
    try:
        logger.info(f"Starting options collection for {symbol}")
        
        # Get options data
        options_data = await kite.get_options_chain(symbol)
        
        if options_data:
            # Store in database
            for option in options_data:
                await insert_options_data(option)
            
            # Cache the data
            await cache_options_chain(symbol, options_data)
            
            logger.info(f"Successfully collected and stored {len(options_data)} options for {symbol}")
        else:
            logger.warning(f"No options data received for {symbol}")
            
    except Exception as e:
        logger.error(f"Error in background options collection: {e}")


# Utility endpoints
@router.get("/data/instruments/{symbol}")
async def get_available_instruments(
    symbol: str,
    kite: KiteClientService = Depends(get_kite_service)
):
    """Get available instruments for a symbol"""
    try:
        # This would be useful for getting available expiries, strikes etc.
        # Implementation depends on Kite API structure
        
        return {
            "success": True,
            "message": f"Available instruments for {symbol}",
            "data": {},  # Placeholder
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting instruments: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data/expiries/{symbol}")
async def get_available_expiries(symbol: str):
    """Get available option expiries for a symbol"""
    try:
        # Get from database or cache
        # This is a placeholder - implement based on your data structure
        
        expiries = [
            (datetime.now().date() + timedelta(days=7)).isoformat(),
            (datetime.now().date() + timedelta(days=14)).isoformat(),
            (datetime.now().date() + timedelta(days=28)).isoformat(),
        ]
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "expiries": expiries
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting expiries: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            status_code=exc.status_code
        ).dict()
    )