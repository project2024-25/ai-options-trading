"""
AI Options Trading Agent - Order Execution Service
Handles automated order placement for approved signals
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import os

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Kite Connect for order execution
from kiteconnect import KiteConnect
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
class Settings:
    ORDER_EXECUTION_PORT = 8007
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"
    
    # Zerodha API Configuration
    KITE_API_KEY = os.getenv("KITE_API_KEY", "")
    KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "")
    
    # Safety settings
    PAPER_TRADING_MODE = os.getenv("PAPER_TRADING_MODE", "true").lower() == "true"
    MAX_ORDER_AMOUNT = 50000  # Maximum order value in INR
    
settings = Settings()

# Global Kite client
kite_client: Optional[KiteConnect] = None

# Pydantic models for request/response
class OrderRequest(BaseModel):
    signal_id: str
    symbol: str
    underlying: str  # NIFTY or BANKNIFTY
    strategy_type: str
    action: str  # BUY or SELL
    quantity: int
    price: Optional[float] = None
    order_type: str = "LIMIT"  # MARKET, LIMIT, SL, SL-M
    product: str = "MIS"  # MIS, CNC, NRML
    validity: str = "DAY"
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    
class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    message: str
    order_details: Optional[Dict[str, Any]] = None
    timestamp: str

class PositionInfo(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    pnl_percent: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with Kite Connect integration"""
    logger.info("Starting Order Execution Service...")
    
    global kite_client
    
    try:
        if settings.KITE_API_KEY and settings.KITE_ACCESS_TOKEN:
            logger.info("Initializing Kite Connect for order execution...")
            
            # Initialize Kite client
            kite_client = KiteConnect(api_key=settings.KITE_API_KEY)
            kite_client.set_access_token(settings.KITE_ACCESS_TOKEN)
            
            # Test connection
            try:
                profile = kite_client.profile()
                logger.info(f"✅ Connected to Kite as: {profile['user_name']}")
                
                if settings.PAPER_TRADING_MODE:
                    logger.warning("🔶 PAPER TRADING MODE ENABLED - Orders will be simulated")
                else:
                    logger.info("🟢 LIVE TRADING MODE - Orders will be executed")
                
            except Exception as e:
                logger.error(f"❌ Kite connection test failed: {e}")
                kite_client = None
        else:
            logger.warning("⚠️ Kite API credentials not provided - order execution disabled")
            kite_client = None
            
        logger.info("✅ Order Execution Service started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize service: {e}")
        kite_client = None
    
    yield
    
    # Cleanup
    logger.info("Shutting down Order Execution Service...")
    logger.info("Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="AI Options Trading - Order Execution Service",
    description="Automated order execution service with Zerodha Kite integration",
    version="1.0.0",
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
        "service": "Order Execution Service",
        "status": "running",
        "version": "1.0.0",
        "features": [
            "Automated order execution",
            "Position monitoring",
            "Risk validation",
            "Paper trading mode"
        ],
        "kite_enabled": kite_client is not None,
        "paper_trading": settings.PAPER_TRADING_MODE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = {
            "service": "order-execution",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "checks": {}
        }
        
        # Kite connection check
        if kite_client:
            try:
                profile = kite_client.profile()
                health_status["checks"]["kite"] = {
                    "status": "connected",
                    "user": profile.get("user_name", "Unknown"),
                    "user_id": profile.get("user_id", "Unknown"),
                    "mode": "paper_trading" if settings.PAPER_TRADING_MODE else "live_trading"
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
            "service": "order-execution",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "error": str(e)
        }

@app.post("/api/orders/execute", response_model=OrderResponse)
async def execute_order(order_request: OrderRequest, background_tasks: BackgroundTasks):
    """Execute an approved trading signal"""
    try:
        logger.info(f"Executing order for signal: {order_request.signal_id}")
        
        # Validate order request
        validation_result = await validate_order_request(order_request)
        if not validation_result["valid"]:
            return OrderResponse(
                success=False,
                message=f"Order validation failed: {validation_result['reason']}",
                timestamp=datetime.now().isoformat()
            )
        
        if settings.PAPER_TRADING_MODE:
            # Paper trading - simulate order
            return await simulate_order(order_request)
        else:
            # Live trading - execute real order
            return await execute_live_order(order_request, background_tasks)
            
    except Exception as e:
        logger.error(f"Error executing order: {e}")
        return OrderResponse(
            success=False,
            message=f"Order execution failed: {str(e)}",
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/orders/status/{order_id}")
async def get_order_status(order_id: str):
    """Get status of a specific order"""
    try:
        if not kite_client:
            raise HTTPException(status_code=503, detail="Kite client not available")
        
        if settings.PAPER_TRADING_MODE:
            # Return simulated status for paper trading
            return {
                "success": True,
                "data": {
                    "order_id": order_id,
                    "status": "COMPLETE",
                    "filled_quantity": 50,  # Simulated
                    "pending_quantity": 0,
                    "average_price": 100.0,  # Simulated
                    "order_type": "LIMIT",
                    "product": "MIS",
                    "mode": "paper_trading"
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Get live order status
            orders = kite_client.orders()
            order = next((o for o in orders if o["order_id"] == order_id), None)
            
            if order:
                return {
                    "success": True,
                    "data": order,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=404, detail="Order not found")
                
    except Exception as e:
        logger.error(f"Error getting order status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders/cancel/{order_id}")
async def cancel_order(order_id: str):
    """Cancel a pending order"""
    try:
        if not kite_client:
            raise HTTPException(status_code=503, detail="Kite client not available")
        
        if settings.PAPER_TRADING_MODE:
            logger.info(f"Paper trading: Simulating cancellation of order {order_id}")
            return {
                "success": True,
                "message": "Order cancelled (simulated)",
                "order_id": order_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Cancel live order
            result = kite_client.cancel_order(variety="regular", order_id=order_id)
            logger.info(f"Order cancelled: {order_id}")
            
            return {
                "success": True,
                "message": "Order cancelled successfully",
                "order_id": order_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/positions")
async def get_current_positions():
    """Get current trading positions"""
    try:
        if not kite_client:
            raise HTTPException(status_code=503, detail="Kite client not available")
        
        if settings.PAPER_TRADING_MODE:
            # Return simulated positions for paper trading
            return {
                "success": True,
                "data": [],  # Empty positions for paper trading
                "mode": "paper_trading",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Get live positions
            positions = kite_client.positions()
            
            # Process positions data
            processed_positions = []
            for position in positions.get("net", []):
                if position["quantity"] != 0:  # Only active positions
                    processed_positions.append({
                        "symbol": position["tradingsymbol"],
                        "instrument_token": position["instrument_token"],
                        "quantity": position["quantity"],
                        "average_price": position["average_price"],
                        "last_price": position["last_price"],
                        "pnl": position["pnl"],
                        "unrealised": position["unrealised"],
                        "realised": position["realised"],
                        "product": position["product"],
                        "exchange": position["exchange"]
                    })
            
            return {
                "success": True,
                "data": processed_positions,
                "count": len(processed_positions),
                "mode": "live_trading",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders/close-position")
async def close_position(symbol: str, quantity: int):
    """Close a specific position"""
    try:
        if not kite_client:
            raise HTTPException(status_code=503, detail="Kite client not available")
        
        if settings.PAPER_TRADING_MODE:
            logger.info(f"Paper trading: Simulating position closure for {symbol}")
            return {
                "success": True,
                "message": f"Position closed (simulated): {symbol}",
                "symbol": symbol,
                "quantity": quantity,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Close live position by placing opposite order
            action = "SELL" if quantity > 0 else "BUY"
            abs_quantity = abs(quantity)
            
            order_id = kite_client.place_order(
                variety="regular",
                exchange="NFO",  # Assuming options trading
                tradingsymbol=symbol,
                transaction_type=action,
                quantity=abs_quantity,
                product="MIS",
                order_type="MARKET"
            )
            
            logger.info(f"Position closure order placed: {order_id}")
            
            return {
                "success": True,
                "message": f"Position closure order placed: {symbol}",
                "order_id": order_id,
                "symbol": symbol,
                "quantity": abs_quantity,
                "action": action,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def validate_order_request(order_request: OrderRequest) -> Dict[str, Any]:
    """Validate order request before execution"""
    try:
        # Basic validations
        if order_request.quantity <= 0:
            return {"valid": False, "reason": "Quantity must be positive"}
        
        if order_request.underlying not in ["NIFTY", "BANKNIFTY"]:
            return {"valid": False, "reason": "Only NIFTY and BANKNIFTY supported"}
        
        if order_request.action not in ["BUY", "SELL"]:
            return {"valid": False, "reason": "Action must be BUY or SELL"}
        
        # Price validations
        if order_request.order_type == "LIMIT" and not order_request.price:
            return {"valid": False, "reason": "Price required for LIMIT orders"}
        
        if order_request.price and order_request.price <= 0:
            return {"valid": False, "reason": "Price must be positive"}
        
        # Risk validations
        estimated_value = (order_request.price or 100) * order_request.quantity
        if estimated_value > settings.MAX_ORDER_AMOUNT:
            return {"valid": False, "reason": f"Order value exceeds maximum limit: ₹{settings.MAX_ORDER_AMOUNT}"}
        
        # Market hours validation
        if not settings.PAPER_TRADING_MODE and not is_market_hours():
            return {"valid": False, "reason": "Market is closed"}
        
        return {"valid": True, "reason": "Order validated successfully"}
        
    except Exception as e:
        logger.error(f"Error validating order: {e}")
        return {"valid": False, "reason": f"Validation error: {str(e)}"}

async def simulate_order(order_request: OrderRequest) -> OrderResponse:
    """Simulate order execution for paper trading"""
    try:
        # Generate simulated order ID
        order_id = f"PAPER_{int(datetime.now().timestamp())}"
        
        # Simulate some processing time
        await asyncio.sleep(1)
        
        # Calculate simulated execution price
        base_price = order_request.price or 100.0
        simulated_price = base_price * (1 + (hash(order_id) % 100 - 50) / 10000)  # ±0.5% variation
        
        order_details = {
            "order_id": order_id,
            "symbol": order_request.symbol,
            "quantity": order_request.quantity,
            "price": round(simulated_price, 2),
            "action": order_request.action,
            "status": "COMPLETE",
            "product": order_request.product,
            "order_type": order_request.order_type,
            "mode": "paper_trading",
            "execution_time": datetime.now().isoformat()
        }
        
        logger.info(f"Paper trade executed: {order_details}")
        
        return OrderResponse(
            success=True,
            order_id=order_id,
            message="Order executed successfully (paper trading)",
            order_details=order_details,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in paper trading simulation: {e}")
        return OrderResponse(
            success=False,
            message=f"Paper trading simulation failed: {str(e)}",
            timestamp=datetime.now().isoformat()
        )

async def execute_live_order(order_request: OrderRequest, background_tasks: BackgroundTasks) -> OrderResponse:
    """Execute live order via Kite Connect"""
    try:
        if not kite_client:
            raise Exception("Kite client not available")
        
        # Place order via Kite Connect
        order_params = {
            "variety": "regular",
            "exchange": "NFO",  # Options trading
            "tradingsymbol": order_request.symbol,
            "transaction_type": order_request.action,
            "quantity": order_request.quantity,
            "product": order_request.product,
            "order_type": order_request.order_type,
            "validity": order_request.validity
        }
        
        # Add price for limit orders
        if order_request.order_type == "LIMIT" and order_request.price:
            order_params["price"] = order_request.price
        
        # Add stop loss for SL orders
        if order_request.order_type in ["SL", "SL-M"] and order_request.stop_loss:
            order_params["trigger_price"] = order_request.stop_loss
        
        # Place the order
        order_id = kite_client.place_order(**order_params)
        
        logger.info(f"Live order placed: {order_id}")
        
        # Schedule background task to monitor order
        background_tasks.add_task(monitor_order, order_id)
        
        return OrderResponse(
            success=True,
            order_id=order_id,
            message="Order placed successfully",
            order_details={
                "order_id": order_id,
                "symbol": order_request.symbol,
                "quantity": order_request.quantity,
                "action": order_request.action,
                "order_type": order_request.order_type,
                "mode": "live_trading",
                "placed_at": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error executing live order: {e}")
        return OrderResponse(
            success=False,
            message=f"Live order execution failed: {str(e)}",
            timestamp=datetime.now().isoformat()
        )

async def monitor_order(order_id: str):
    """Background task to monitor order status"""
    try:
        logger.info(f"Monitoring order: {order_id}")
        
        for _ in range(30):  # Monitor for 5 minutes (30 * 10 seconds)
            await asyncio.sleep(10)
            
            try:
                orders = kite_client.orders()
                order = next((o for o in orders if o["order_id"] == order_id), None)
                
                if order:
                    status = order.get("status", "UNKNOWN")
                    
                    if status in ["COMPLETE", "CANCELLED", "REJECTED"]:
                        logger.info(f"Order {order_id} final status: {status}")
                        break
                        
                    logger.info(f"Order {order_id} status: {status}")
                else:
                    logger.warning(f"Order {order_id} not found in order list")
                    break
                    
            except Exception as e:
                logger.error(f"Error monitoring order {order_id}: {e}")
                
        logger.info(f"Finished monitoring order: {order_id}")
        
    except Exception as e:
        logger.error(f"Error in order monitoring task: {e}")

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
        port=settings.ORDER_EXECUTION_PORT,
        reload=settings.DEBUG_MODE,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )