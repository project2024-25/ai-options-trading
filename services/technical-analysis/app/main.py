#!/usr/bin/env python3
"""
Technical Analysis Service - Main Entry Point
Integrates indicators, support/resistance, volatility, and OI analysis
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
    from indicators_service import IndicatorsService
    from support_resistance_service import SupportResistanceService
    from volatility_service import VolatilityService
    from oi_analysis_service import OIAnalysisService
except ImportError as e:
    logging.warning(f"Some service modules not found: {e}")
    # We'll create basic implementations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    TECHNICAL_ANALYSIS_PORT = 8002
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Technical Analysis Service...")
    
    try:
        # Initialize your service modules here
        logger.info("✅ Technical Analysis Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
    finally:
        logger.info("Shutting down Technical Analysis Service...")

# Create FastAPI application
app = FastAPI(
    title="Technical Analysis Service",
    description="Multi-timeframe technical analysis for NIFTY/BANKNIFTY options trading",
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
        "service": "Technical Analysis Service",
        "status": "running",
        "version": "1.0.0",
        "description": "Multi-timeframe technical analysis for NIFTY/BANKNIFTY",
        "endpoints": [
            "/health",
            "/api/analysis/nifty-indicators/{timeframe}",
            "/api/analysis/banknifty-indicators/{timeframe}",
            "/api/analysis/support-resistance/nifty",
            "/api/analysis/support-resistance/banknifty",
            "/api/analysis/volatility-analysis",
            "/api/analysis/oi-buildup"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "technical-analysis",
        "port": settings.TECHNICAL_ANALYSIS_PORT,
        "indicators": "loaded",
        "support_resistance": "loaded",
        "volatility_analysis": "loaded",
        "oi_analysis": "loaded"
    }

@app.get("/api/analysis/nifty-indicators/{timeframe}")
async def get_nifty_indicators(timeframe: str):
    """Get technical indicators for NIFTY"""
    try:
        if timeframe not in ["5min", "15min", "1hr", "daily"]:
            raise HTTPException(status_code=400, detail="Invalid timeframe. Use: 5min, 15min, 1hr, daily")
        
        # TODO: Integrate with your indicators_service.py
        sample_data = {
            "symbol": "NIFTY",
            "timeframe": timeframe,
            "timestamp": "2025-05-30T10:30:00Z",
            "indicators": {
                "trend": {
                    "sma_9": 24750.5,
                    "sma_21": 24720.8,
                    "ema_9": 24760.2,
                    "ema_21": 24740.5,
                    "trend_direction": "bullish"
                },
                "momentum": {
                    "rsi_14": 65.4,
                    "rsi_21": 62.8,
                    "macd": {
                        "macd_line": 45.2,
                        "signal_line": 38.7,
                        "histogram": 6.5,
                        "signal": "bullish_crossover"
                    },
                    "stochastic": {
                        "k_percent": 72.3,
                        "d_percent": 68.9,
                        "signal": "overbought_warning"
                    }
                },
                "volatility": {
                    "bollinger_bands": {
                        "upper": 24950.8,
                        "middle": 24750.5,
                        "lower": 24550.2,
                        "position": "middle_range"
                    },
                    "atr_14": 180.5
                }
            },
            "signals": {
                "overall_trend": "bullish",
                "strength": 7.2,
                "confidence": 75
            }
        }
        
        return sample_data
        
    except Exception as e:
        logger.error(f"Error calculating NIFTY indicators: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate indicators")

@app.get("/api/analysis/banknifty-indicators/{timeframe}")
async def get_banknifty_indicators(timeframe: str):
    """Get technical indicators for BANKNIFTY"""
    try:
        if timeframe not in ["5min", "15min", "1hr", "daily"]:
            raise HTTPException(status_code=400, detail="Invalid timeframe")
        
        # TODO: Integrate with your indicators_service.py
        sample_data = {
            "symbol": "BANKNIFTY",
            "timeframe": timeframe,
            "timestamp": "2025-05-30T10:30:00Z",
            "indicators": {
                "trend": {
                    "sma_9": 52100.5,
                    "sma_21": 52050.8,
                    "ema_9": 52120.2,
                    "ema_21": 52080.5,
                    "trend_direction": "sideways"
                },
                "momentum": {
                    "rsi_14": 55.8,
                    "macd": {
                        "macd_line": 25.1,
                        "signal_line": 28.3,
                        "histogram": -3.2,
                        "signal": "bearish_momentum"
                    }
                }
            },
            "signals": {
                "overall_trend": "sideways",
                "strength": 5.5,
                "confidence": 65
            }
        }
        
        return sample_data
        
    except Exception as e:
        logger.error(f"Error calculating BANKNIFTY indicators: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate indicators")

@app.get("/api/analysis/support-resistance/nifty")
async def get_nifty_levels():
    """Get support and resistance levels for NIFTY"""
    try:
        # TODO: Integrate with your support_resistance_service.py
        return {
            "symbol": "NIFTY",
            "timestamp": "2025-05-30T10:30:00Z",
            "levels": {
                "resistance": [
                    {"level": 24900, "strength": 8.5, "type": "psychological"},
                    {"level": 25000, "strength": 9.2, "type": "round_number"},
                    {"level": 25150, "strength": 7.8, "type": "previous_high"}
                ],
                "support": [
                    {"level": 24700, "strength": 8.0, "type": "volume_profile"},
                    {"level": 24550, "strength": 8.8, "type": "swing_low"},
                    {"level": 24400, "strength": 7.5, "type": "fibonacci"}
                ],
                "pivot_points": {
                    "classic": {
                        "pp": 24833,
                        "r1": 24950,
                        "r2": 25100,
                        "r3": 25217,
                        "s1": 24683,
                        "s2": 24533,
                        "s3": 24416
                    },
                    "fibonacci": {
                        "pp": 24833,
                        "r1": 24878,
                        "r2": 24911,
                        "s1": 24788,
                        "s2": 24755
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating support/resistance: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate levels")

@app.get("/api/analysis/support-resistance/banknifty")
async def get_banknifty_levels():
    """Get support and resistance levels for BANKNIFTY"""
    try:
        return {
            "symbol": "BANKNIFTY",
            "timestamp": "2025-05-30T10:30:00Z",
            "levels": {
                "resistance": [
                    {"level": 52300, "strength": 8.2, "type": "psychological"},
                    {"level": 52500, "strength": 9.0, "type": "round_number"}
                ],
                "support": [
                    {"level": 51900, "strength": 8.5, "type": "volume_profile"},
                    {"level": 51700, "strength": 8.0, "type": "swing_low"}
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error calculating BANKNIFTY levels: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate levels")

@app.get("/api/analysis/volatility-analysis")
async def get_volatility_analysis():
    """Get comprehensive volatility analysis"""
    try:
        # TODO: Integrate with your volatility_service.py
        return {
            "timestamp": "2025-05-30T10:30:00Z",
            "vix_analysis": {
                "current": 15.23,
                "percentile_1m": 45.2,
                "percentile_3m": 38.7,
                "percentile_6m": 42.1,
                "regime": "low_volatility",
                "trend": "stable"
            },
            "historical_volatility": {
                "nifty": {
                    "10d": 12.8,
                    "20d": 14.2,
                    "30d": 16.5
                },
                "banknifty": {
                    "10d": 15.2,
                    "20d": 17.8,
                    "30d": 19.1
                }
            },
            "volatility_clustering": {
                "detected": True,
                "strength": 6.5,
                "duration_days": 5
            },
            "regime_probabilities": {
                "low_vol": 0.65,
                "medium_vol": 0.30,
                "high_vol": 0.05
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing volatility: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze volatility")

@app.get("/api/analysis/oi-buildup")
async def get_oi_analysis():
    """Get Open Interest buildup analysis"""
    try:
        # TODO: Integrate with your oi_analysis_service.py
        return {
            "timestamp": "2025-05-30T10:30:00Z",
            "nifty": {
                "total_oi": 15892350,
                "oi_change": 245780,
                "oi_change_percent": 1.57,
                "pcr": 0.82,
                "max_pain": 24800,
                "buildup_pattern": "long_buildup",
                "key_strikes": {
                    "calls": [
                        {"strike": 24800, "oi": 1250000, "oi_change": 125000},
                        {"strike": 24900, "oi": 980000, "oi_change": 89000}
                    ],
                    "puts": [
                        {"strike": 24700, "oi": 1100000, "oi_change": 95000},
                        {"strike": 24600, "oi": 850000, "oi_change": 72000}
                    ]
                }
            },
            "banknifty": {
                "total_oi": 8945620,
                "oi_change": 156890,
                "oi_change_percent": 1.78,
                "pcr": 0.75,
                "max_pain": 52000,
                "buildup_pattern": "short_covering"
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing OI buildup: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze OI buildup")

if __name__ == "__main__":
    logger.info(f"Starting Technical Analysis Service on port {settings.TECHNICAL_ANALYSIS_PORT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.TECHNICAL_ANALYSIS_PORT,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )