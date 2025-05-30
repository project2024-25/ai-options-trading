#!/usr/bin/env python3
"""
ML Service - Main Entry Point
Machine learning predictions for direction, volatility, and pattern recognition
"""

import uvicorn
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    ML_SERVICE_PORT = 8003
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting ML Service...")
    
    try:
        # Initialize ML models here
        logger.info("Loading ML models...")
        # TODO: Load your trained models
        # model_loader.load_direction_model()
        # model_loader.load_volatility_model()
        # model_loader.load_pattern_model()
        logger.info("✅ ML Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize ML service: {e}")
        raise
    finally:
        logger.info("Shutting down ML Service...")

# Create FastAPI application
app = FastAPI(
    title="ML Service",
    description="Machine learning predictions for options trading",
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
        "service": "ML Service",
        "status": "running",
        "version": "1.0.0",
        "description": "Machine learning predictions for NIFTY/BANKNIFTY options trading",
        "endpoints": [
            "/health",
            "/api/ml/direction-prediction/{symbol}",
            "/api/ml/volatility-forecast/{symbol}",
            "/api/ml/regime-detection",
            "/api/ml/pattern-recognition/{symbol}",
            "/api/ml/model-performance"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ml-service",
        "port": settings.ML_SERVICE_PORT,
        "models": {
            "direction_model": "loaded",
            "volatility_model": "loaded",
            "pattern_model": "loaded",
            "regime_model": "loaded"
        }
    }

@app.get("/api/ml/direction-prediction/{symbol}")
async def predict_direction(symbol: str, timeframe: Optional[str] = "1hr"):
    """Predict price direction using ML models"""
    try:
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        if timeframe not in ["5min", "15min", "1hr", "daily"]:
            raise HTTPException(status_code=400, detail="Invalid timeframe")
        
        # TODO: Implement actual ML prediction
        # prediction = direction_model.predict(symbol, timeframe)
        
        sample_prediction = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "timestamp": "2025-05-30T10:30:00Z",
            "prediction": {
                "direction": "bullish",
                "confidence": 0.72,
                "probability_up": 0.72,
                "probability_down": 0.28,
                "expected_move": {
                    "1hr": 0.85,
                    "4hr": 1.45,
                    "daily": 2.1
                },
                "target_levels": {
                    "resistance": [24850, 24920, 25000],
                    "support": [24680, 24620, 24550]
                }
            },
            "model_features": {
                "technical_score": 7.2,
                "momentum_score": 8.1,
                "volume_score": 6.8,
                "sentiment_score": 7.5
            },
            "risk_assessment": {
                "model_uncertainty": 0.28,
                "feature_importance": {
                    "rsi_divergence": 0.25,
                    "volume_profile": 0.22,
                    "macd_signal": 0.18,
                    "support_resistance": 0.15,
                    "vix_level": 0.20
                }
            }
        }
        
        return sample_prediction
        
    except Exception as e:
        logger.error(f"Error predicting direction: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict direction")

@app.get("/api/ml/volatility-forecast/{symbol}")
async def forecast_volatility(symbol: str, horizon: Optional[int] = 5):
    """Forecast volatility using ML models"""
    try:
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        if horizon not in [1, 3, 5, 10, 20]:
            raise HTTPException(status_code=400, detail="Horizon must be 1, 3, 5, 10, or 20 days")
        
        # TODO: Implement actual volatility forecasting
        # forecast = volatility_model.predict(symbol, horizon)
        
        sample_forecast = {
            "symbol": symbol.upper(),
            "forecast_horizon_days": horizon,
            "timestamp": "2025-05-30T10:30:00Z",
            "current_iv": 19.2,
            "current_hv": 16.8,
            "forecast": {
                "predicted_volatility": 18.5,
                "confidence_interval": {
                    "lower": 15.2,
                    "upper": 21.8,
                    "confidence_level": 0.95
                },
                "volatility_regime": "normal",
                "regime_probability": 0.78
            },
            "scenarios": [
                {
                    "scenario": "low_volatility",
                    "probability": 0.25,
                    "volatility_range": [12.0, 16.0],
                    "market_conditions": "stable_trending"
                },
                {
                    "scenario": "normal_volatility",
                    "probability": 0.50,
                    "volatility_range": [16.0, 22.0],
                    "market_conditions": "normal_oscillation"
                },
                {
                    "scenario": "high_volatility",
                    "probability": 0.25,
                    "volatility_range": [22.0, 30.0],
                    "market_conditions": "stress_events"
                }
            ],
            "trading_implications": {
                "optimal_strategies": ["iron_condor", "butterfly"],
                "avoid_strategies": ["long_straddle"],
                "vega_exposure": "neutral_to_short"
            }
        }
        
        return sample_forecast
        
    except Exception as e:
        logger.error(f"Error forecasting volatility: {e}")
        raise HTTPException(status_code=500, detail="Failed to forecast volatility")

@app.get("/api/ml/regime-detection")
async def detect_market_regime():
    """Detect current market regime"""
    try:
        # TODO: Implement actual regime detection
        # regime = regime_model.detect_current_regime()
        
        sample_regime = {
            "timestamp": "2025-05-30T10:30:00Z",
            "current_regime": {
                "primary": "bull_market",
                "secondary": "low_volatility",
                "confidence": 0.78,
                "duration_days": 15
            },
            "regime_probabilities": {
                "bull_market": 0.78,
                "bear_market": 0.12,
                "sideways_market": 0.10
            },
            "volatility_regime": {
                "current": "low_volatility",
                "probabilities": {
                    "low_vol": 0.65,
                    "normal_vol": 0.30,
                    "high_vol": 0.05
                }
            },
            "regime_characteristics": {
                "trend_strength": 7.5,
                "volatility_clustering": False,
                "mean_reversion_tendency": 0.35,
                "momentum_persistence": 0.72
            },
            "expected_duration": {
                "current_regime_days": 25,
                "transition_probability": 0.15
            },
            "trading_recommendations": {
                "preferred_strategies": [
                    "trend_following",
                    "momentum_strategies",
                    "covered_calls"
                ],
                "avoid_strategies": [
                    "contrarian_strategies",
                    "volatility_plays"
                ],
                "risk_level": "moderate"
            }
        }
        
        return sample_regime
        
    except Exception as e:
        logger.error(f"Error detecting market regime: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect market regime")

@app.get("/api/ml/pattern-recognition/{symbol}")
async def recognize_patterns(symbol: str, timeframe: Optional[str] = "1hr"):
    """Recognize chart patterns using ML"""
    try:
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Symbol must be NIFTY or BANKNIFTY")
        
        # TODO: Implement actual pattern recognition
        # patterns = pattern_model.recognize(symbol, timeframe)
        
        sample_patterns = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "timestamp": "2025-05-30T10:30:00Z",
            "detected_patterns": [
                {
                    "pattern_name": "ascending_triangle",
                    "confidence": 0.85,
                    "completion": 0.78,
                    "breakout_target": 25100,
                    "stop_loss": 24650,
                    "pattern_duration": 12,
                    "reliability_score": 7.8
                },
                {
                    "pattern_name": "bullish_flag",
                    "confidence": 0.72,
                    "completion": 0.65,
                    "breakout_target": 24950,
                    "stop_loss": 24700,
                    "pattern_duration": 8,
                    "reliability_score": 7.2
                }
            ],
            "pattern_analytics": {
                "overall_sentiment": "bullish",
                "pattern_strength": 8.1,
                "breakout_probability": 0.74,
                "false_breakout_risk": 0.26
            },
            "historical_performance": {
                "similar_patterns_found": 45,
                "success_rate": 0.73,
                "avg_gain_on_success": 2.8,
                "avg_loss_on_failure": -1.2
            },
            "options_implications": {
                "recommended_strategies": [
                    "long_calls",
                    "bull_call_spread"
                ],
                "optimal_expiry": "2025-06-26",
                "strike_selection": {
                    "aggressive": 24900,
                    "moderate": 24850,
                    "conservative": 24800
                }
            }
        }
        
        return sample_patterns
        
    except Exception as e:
        logger.error(f"Error recognizing patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to recognize patterns")

@app.get("/api/ml/model-performance")
async def get_model_performance():
    """Get ML model performance metrics"""
    try:
        # TODO: Implement actual model performance tracking
        
        performance_metrics = {
            "timestamp": "2025-05-30T10:30:00Z",
            "models": {
                "direction_prediction": {
                    "accuracy": 0.72,
                    "precision": 0.75,
                    "recall": 0.68,
                    "f1_score": 0.71,
                    "sharpe_ratio": 1.45,
                    "last_updated": "2025-05-29T00:00:00Z",
                    "training_samples": 15680,
                    "validation_accuracy": 0.69
                },
                "volatility_forecast": {
                    "mae": 2.15,
                    "rmse": 3.42,
                    "mape": 12.8,
                    "r_squared": 0.68,
                    "direction_accuracy": 0.71,
                    "last_updated": "2025-05-29T00:00:00Z"
                },
                "pattern_recognition": {
                    "pattern_accuracy": 0.78,
                    "false_positive_rate": 0.15,
                    "pattern_completion_rate": 0.73,
                    "profit_factor": 1.85,
                    "last_updated": "2025-05-28T00:00:00Z"
                },
                "regime_detection": {
                    "regime_accuracy": 0.81,
                    "transition_accuracy": 0.65,
                    "stability_score": 8.2,
                    "false_signals": 0.12,
                    "last_updated": "2025-05-29T00:00:00Z"
                }
            },
            "overall_performance": {
                "combined_accuracy": 0.74,
                "model_confidence": 0.78,
                "prediction_reliability": 8.1,
                "last_retraining": "2025-05-28T00:00:00Z",
                "next_retraining": "2025-06-28T00:00:00Z"
            },
            "feature_importance": {
                "technical_indicators": 0.35,
                "volume_profile": 0.25,
                "options_flow": 0.20,
                "market_sentiment": 0.15,
                "macro_factors": 0.05
            }
        }
        
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model performance")

if __name__ == "__main__":
    logger.info(f"Starting ML Service on port {settings.ML_SERVICE_PORT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.ML_SERVICE_PORT,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )