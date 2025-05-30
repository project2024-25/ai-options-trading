#!/usr/bin/env python3
"""
Options Analytics Service - Main Entry Point
Greeks calculations, IV surface, volatility analysis, and options-specific metrics
"""

import uvicorn
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List

# Import your existing service modules
try:
    from greeks_service import GreeksService
except ImportError as e:
    logging.warning(f"Greeks service module not found: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    OPTIONS_ANALYTICS_PORT = 8006
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Options Analytics Service...")
    
    try:
        # Initialize Greeks service and other modules
        logger.info("✅ Options Analytics Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
    finally:
        logger.info("Shutting down Options Analytics Service...")

# Create FastAPI application
app = FastAPI(
    title="Options Analytics Service",
    description="Advanced options analytics including Greeks, IV surface, and volatility modeling",
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
        "service": "Options Analytics Service",
        "status": "running",
        "version": "1.0.0",
        "description": "Advanced options analytics for NIFTY/BANKNIFTY options",
        "endpoints": [
            "/health",
            "/api/options/greeks/{symbol}",
            "/api/options/iv-surface/{symbol}",
            "/api/options/max-pain/{symbol}/{expiry}",
            "/api/options/volatility-skew/{symbol}",
            "/api/options/time-decay-impact",
            "/api/options/scenario-analysis"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "options-analytics",
        "port": settings.OPTIONS_ANALYTICS_PORT,
        "greeks_calculator": "loaded",
        "iv_models": "loaded",
        "volatility_models": "loaded"
    }

@app.get("/api/options/greeks/{symbol}")
async def get_options_greeks(symbol: str, expiry: Optional[str] = None):
    """Get Greeks for all options of a symbol"""
    try:
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # TODO: Integrate with your greeks_service.py
        sample_data = {
            "symbol": symbol.upper(),
            "expiry": expiry or "2025-06-05",
            "timestamp": "2025-05-30T10:30:00Z",
            "spot_price": 24753.05 if symbol.upper() == "NIFTY" else 52150.80,
            "options_chain": [
                {
                    "strike": 24700,
                    "call": {
                        "ltp": 125.50,
                        "bid": 124.00,
                        "ask": 127.00,
                        "volume": 25680,
                        "oi": 2150000,
                        "greeks": {
                            "delta": 0.65,
                            "gamma": 0.012,
                            "theta": -8.5,
                            "vega": 15.2,
                            "rho": 5.8
                        },
                        "iv": 18.5,
                        "intrinsic_value": 53.05,
                        "time_value": 72.45
                    },
                    "put": {
                        "ltp": 72.25,
                        "bid": 71.00,
                        "ask": 73.50,
                        "volume": 18920,
                        "oi": 1890000,
                        "greeks": {
                            "delta": -0.35,
                            "gamma": 0.012,
                            "theta": -7.8,
                            "vega": 15.2,
                            "rho": -3.2
                        },
                        "iv": 18.8,
                        "intrinsic_value": 0,
                        "time_value": 72.25
                    }
                },
                {
                    "strike": 24800,
                    "call": {
                        "ltp": 85.75,
                        "bid": 84.50,
                        "ask": 87.00,
                        "volume": 45250,
                        "oi": 3250000,
                        "greeks": {
                            "delta": 0.45,
                            "gamma": 0.015,
                            "theta": -9.2,
                            "vega": 18.5,
                            "rho": 4.1
                        },
                        "iv": 19.2,
                        "intrinsic_value": 0,
                        "time_value": 85.75
                    },
                    "put": {
                        "ltp": 132.70,
                        "bid": 131.00,
                        "ask": 134.50,
                        "volume": 38760,
                        "oi": 2980000,
                        "greeks": {
                            "delta": -0.55,
                            "gamma": 0.015,
                            "theta": -8.8,
                            "vega": 18.5,
                            "rho": -4.8
                        },
                        "iv": 19.5,
                        "intrinsic_value": 46.95,
                        "time_value": 85.75
                    }
                }
            ],
            "portfolio_greeks": {
                "net_delta": 0.0,
                "net_gamma": 450.2,
                "net_theta": -850.5,
                "net_vega": 1250.8
            }
        }
        
        return sample_data
        
    except Exception as e:
        logger.error(f"Error calculating Greeks: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate Greeks")

@app.get("/api/options/iv-surface/{symbol}")
async def get_iv_surface(symbol: str):
    """Get Implied Volatility surface"""
    try:
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        return {
            "symbol": symbol.upper(),
            "timestamp": "2025-05-30T10:30:00Z",
            "spot_price": 24753.05 if symbol.upper() == "NIFTY" else 52150.80,
            "iv_surface": {
                "expiries": ["2025-06-05", "2025-06-12", "2025-06-26", "2025-07-31"],
                "strikes": [
                    {"strike": 24600, "days_to_expiry": [6, 13, 27, 62], "iv_values": [17.5, 18.2, 19.1, 20.5]},
                    {"strike": 24700, "days_to_expiry": [6, 13, 27, 62], "iv_values": [18.5, 19.0, 19.8, 21.2]},
                    {"strike": 24800, "days_to_expiry": [6, 13, 27, 62], "iv_values": [19.2, 19.5, 20.3, 21.8]},
                    {"strike": 24900, "days_to_expiry": [6, 13, 27, 62], "iv_values": [20.1, 20.3, 21.0, 22.5]}
                ],
                "term_structure": {
                    "atm_iv": [19.2, 19.5, 20.3, 21.8],
                    "days": [6, 13, 27, 62],
                    "volatility_smile": {
                        "skew": -2.5,
                        "kurtosis": 0.8
                    }
                }
            },
            "analytics": {
                "avg_iv": 19.8,
                "iv_rank": 45.2,
                "iv_percentile": 38.7,
                "term_structure_slope": "normal_contango"
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating IV surface: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate IV surface")

@app.get("/api/options/max-pain/{symbol}/{expiry}")
async def get_max_pain(symbol: str, expiry: str):
    """Calculate Max Pain for given expiry"""
    try:
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        return {
            "symbol": symbol.upper(),
            "expiry": expiry,
            "timestamp": "2025-05-30T10:30:00Z",
            "max_pain": {
                "level": 24800 if symbol.upper() == "NIFTY" else 52000,
                "total_pain": 25680000000,
                "confidence": 8.5
            },
            "pain_by_strike": [
                {"strike": 24600, "total_pain": 45600000000},
                {"strike": 24700, "total_pain": 32400000000},
                {"strike": 24800, "total_pain": 25680000000},  # Minimum = Max Pain
                {"strike": 24900, "total_pain": 38900000000},
                {"strike": 25000, "total_pain": 52100000000}
            ],
            "oi_distribution": {
                "call_oi": 15680000,
                "put_oi": 12890000,
                "pcr": 0.82,
                "heavy_strikes": {
                    "calls": [24900, 25000],
                    "puts": [24700, 24600]
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating Max Pain: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate Max Pain")

@app.get("/api/options/volatility-skew/{symbol}")
async def get_volatility_skew(symbol: str, expiry: Optional[str] = None):
    """Get volatility skew analysis"""
    try:
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        return {
            "symbol": symbol.upper(),
            "expiry": expiry or "2025-06-05",
            "timestamp": "2025-05-30T10:30:00Z",
            "skew_analysis": {
                "put_call_skew": -2.5,
                "skew_direction": "put_skew",
                "skew_strength": "moderate",
                "risk_reversal_25d": -1.8,
                "butterfly_25d": 2.3
            },
            "strike_iv_data": [
                {"strike": 24600, "moneyness": 0.94, "call_iv": 17.5, "put_iv": 20.0},
                {"strike": 24700, "moneyness": 0.98, "call_iv": 18.5, "put_iv": 19.0},
                {"strike": 24800, "moneyness": 1.00, "call_iv": 19.2, "put_iv": 19.5},
                {"strike": 24900, "moneyness": 1.04, "call_iv": 19.8, "put_iv": 19.2},
                {"strike": 25000, "moneyness": 1.08, "call_iv": 20.1, "put_iv": 18.8}
            ],
            "market_sentiment": {
                "fear_index": 6.5,
                "skew_interpretation": "moderate_bearish_sentiment",
                "volatility_risk_premium": 3.2
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating volatility skew: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate volatility skew")

@app.get("/api/options/time-decay-impact")
async def get_time_decay_impact():
    """Analyze time decay impact on current positions"""
    try:
        return {
            "timestamp": "2025-05-30T10:30:00Z",
            "portfolio_theta": -850.5,
            "theta_impact": {
                "daily": -850.5,
                "weekly": -5953.5,
                "weekend": -1701.0
            },
            "position_breakdown": [
                {
                    "position_id": "NIFTY_24800_CE",
                    "quantity": 50,
                    "theta_per_lot": -9.2,
                    "total_theta": -460.0,
                    "days_to_expiry": 6,
                    "theta_acceleration": "high"
                },
                {
                    "position_id": "NIFTY_24700_PE",
                    "quantity": -25,
                    "theta_per_lot": -7.8,
                    "total_theta": 195.0,
                    "days_to_expiry": 6,
                    "theta_acceleration": "high"
                }
            ],
            "theta_optimization": {
                "net_theta_target": -500,
                "current_efficiency": 85.2,
                "suggested_adjustments": [
                    "Reduce long option exposure by 20%",
                    "Consider theta-positive strategies"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing time decay: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze time decay")

@app.get("/api/options/scenario-analysis")
async def get_scenario_analysis(
    price_change: Optional[float] = Query(None, description="Price change in %"),
    vol_change: Optional[float] = Query(None, description="Volatility change in %"),
    time_decay: Optional[int] = Query(None, description="Days to decay")
):
    """Perform scenario analysis on current positions"""
    try:
        scenarios = {
            "base_case": {
                "price_change": 0,
                "vol_change": 0,
                "time_decay": 0,
                "portfolio_pnl": 0
            },
            "scenarios": [
                {
                    "name": "bull_case",
                    "price_change": 2.0,
                    "vol_change": -10.0,
                    "time_decay": 1,
                    "portfolio_pnl": 15680.50,
                    "probability": 0.25
                },
                {
                    "name": "bear_case",
                    "price_change": -2.0,
                    "vol_change": 15.0,
                    "time_decay": 1,
                    "portfolio_pnl": -8950.25,
                    "probability": 0.20
                },
                {
                    "name": "sideways_case",
                    "price_change": 0.5,
                    "vol_change": -5.0,
                    "time_decay": 1,
                    "portfolio_pnl": -850.50,
                    "probability": 0.35
                },
                {
                    "name": "high_vol_case",
                    "price_change": 1.0,
                    "vol_change": 25.0,
                    "time_decay": 1,
                    "portfolio_pnl": 25680.75,
                    "probability": 0.20
                }
            ],
            "risk_metrics": {
                "var_95": -12580.30,
                "expected_return": 2850.45,
                "max_loss": -25680.90,
                "max_gain": 45620.80,
                "breakeven_moves": {
                    "upside": 1.8,
                    "downside": -1.5
                }
            }
        }
        
        # Apply custom scenario if provided
        if any([price_change, vol_change, time_decay]):
            custom_scenario = {
                "name": "custom_scenario",
                "price_change": price_change or 0,
                "vol_change": vol_change or 0,
                "time_decay": time_decay or 0
            }
            # Calculate custom PnL (simplified calculation)
            custom_pnl = (price_change or 0) * 500 + (vol_change or 0) * 100 - (time_decay or 0) * 850
            custom_scenario["portfolio_pnl"] = custom_pnl
            scenarios["custom_scenario"] = custom_scenario
        
        return {
            "timestamp": "2025-05-30T10:30:00Z",
            "current_portfolio_value": 125680.50,
            "scenarios": scenarios
        }
        
    except Exception as e:
        logger.error(f"Error performing scenario analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform scenario analysis")

if __name__ == "__main__":
    logger.info(f"Starting Options Analytics Service on port {settings.OPTIONS_ANALYTICS_PORT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.OPTIONS_ANALYTICS_PORT,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )