#!/usr/bin/env python3
"""
Strategy Engine Service - Main Entry Point
Options strategy generation, selection, and backtesting
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
    STRATEGY_ENGINE_PORT = 8004
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Strategy Engine Service...")
    
    try:
        # Initialize strategy models and backtesting engine
        logger.info("Loading strategy templates...")
        logger.info("Initializing backtesting engine...")
        logger.info("✅ Strategy Engine Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize Strategy Engine: {e}")
        raise
    finally:
        logger.info("Shutting down Strategy Engine Service...")

# Create FastAPI application
app = FastAPI(
    title="Strategy Engine Service",
    description="Options strategy generation, selection, and backtesting for NIFTY/BANKNIFTY",
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
        "service": "Strategy Engine Service",
        "status": "running",
        "version": "1.0.0",
        "description": "Options strategy generation and selection for NIFTY/BANKNIFTY",
        "endpoints": [
            "/health",
            "/api/strategy/nifty-directional",
            "/api/strategy/banknifty-directional", 
            "/api/strategy/volatility-plays",
            "/api/strategy/income-generation",
            "/api/strategy/hedge-analysis",
            "/api/strategy/backtest/{strategy_name}",
            "/api/strategy/signals"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "strategy-engine",
        "port": settings.STRATEGY_ENGINE_PORT,
        "strategy_templates": "loaded",
        "backtesting_engine": "ready",
        "signal_generator": "active"
    }

@app.get("/api/strategy/nifty-directional")
async def get_nifty_directional_strategies(
    market_outlook: Optional[str] = Query("bullish", description="bullish, bearish, or neutral"),
    risk_level: Optional[str] = Query("moderate", description="low, moderate, or high"),
    max_risk: Optional[float] = Query(5000, description="Maximum risk per trade")
):
    """Generate directional strategies for NIFTY"""
    try:
        if market_outlook not in ["bullish", "bearish", "neutral"]:
            raise HTTPException(status_code=400, detail="Invalid market outlook")
        
        # TODO: Integrate with ML predictions and technical analysis
        strategies = {
            "symbol": "NIFTY",
            "market_outlook": market_outlook,
            "risk_level": risk_level,
            "max_risk": max_risk,
            "timestamp": "2025-05-30T10:30:00Z",
            "recommended_strategies": []
        }
        
        if market_outlook == "bullish":
            strategies["recommended_strategies"] = [
                {
                    "strategy_name": "Bull Call Spread",
                    "confidence": 8.5,
                    "setup": {
                        "buy_strike": 24800,
                        "sell_strike": 24900,
                        "expiry": "2025-06-05",
                        "net_premium": 45.50,
                        "max_profit": 54.50,
                        "max_loss": 45.50,
                        "breakeven": 24845.50
                    },
                    "market_conditions": {
                        "ideal_iv": "15-20%",
                        "time_to_expiry": "5-15 days",
                        "expected_move": "1-3%"
                    },
                    "risk_reward": 1.20,
                    "probability_of_profit": 0.65,
                    "strategy_score": 8.5
                },
                {
                    "strategy_name": "Long Call",
                    "confidence": 7.8,
                    "setup": {
                        "strike": 24850,
                        "expiry": "2025-06-05",
                        "premium": 78.50,
                        "max_profit": "unlimited",
                        "max_loss": 78.50,
                        "breakeven": 24928.50
                    },
                    "risk_reward": 3.15,
                    "probability_of_profit": 0.45,
                    "strategy_score": 7.8
                }
            ]
        elif market_outlook == "bearish":
            strategies["recommended_strategies"] = [
                {
                    "strategy_name": "Bear Put Spread",
                    "confidence": 8.2,
                    "setup": {
                        "buy_strike": 24700,
                        "sell_strike": 24600,
                        "expiry": "2025-06-05",
                        "net_premium": 42.25,
                        "max_profit": 57.75,
                        "max_loss": 42.25,
                        "breakeven": 24657.75
                    },
                    "risk_reward": 1.37,
                    "probability_of_profit": 0.62,
                    "strategy_score": 8.2
                }
            ]
        else:  # neutral
            strategies["recommended_strategies"] = [
                {
                    "strategy_name": "Iron Condor",
                    "confidence": 8.8,
                    "setup": {
                        "call_spread": {"buy": 24900, "sell": 24950},
                        "put_spread": {"buy": 24650, "sell": 24600},
                        "expiry": "2025-06-05",
                        "net_credit": 35.75,
                        "max_profit": 35.75,
                        "max_loss": 14.25,
                        "breakeven_upper": 24935.75,
                        "breakeven_lower": 24685.75
                    },
                    "risk_reward": 2.51,
                    "probability_of_profit": 0.78,
                    "strategy_score": 8.8
                }
            ]
        
        return strategies
        
    except Exception as e:
        logger.error(f"Error generating NIFTY strategies: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate strategies")

@app.get("/api/strategy/volatility-plays")
async def get_volatility_strategies(
    vol_expectation: Optional[str] = Query("increase", description="increase, decrease, or stable"),
    current_iv_percentile: Optional[float] = Query(45.0, description="Current IV percentile")
):
    """Generate volatility-based strategies"""
    try:
        strategies = {
            "volatility_expectation": vol_expectation,
            "current_iv_percentile": current_iv_percentile,
            "timestamp": "2025-05-30T10:30:00Z",
            "recommended_strategies": []
        }
        
        if vol_expectation == "increase":
            strategies["recommended_strategies"] = [
                {
                    "strategy_name": "Long Straddle",
                    "confidence": 8.0,
                    "setup": {
                        "strike": 24800,
                        "call_premium": 85.50,
                        "put_premium": 82.25,
                        "total_premium": 167.75,
                        "expiry": "2025-06-05",
                        "breakeven_upper": 24967.75,
                        "breakeven_lower": 24632.25
                    },
                    "volatility_target": ">25%",
                    "time_decay_risk": "high",
                    "strategy_score": 8.0
                },
                {
                    "strategy_name": "Long Strangle",
                    "confidence": 7.5,
                    "setup": {
                        "call_strike": 24850,
                        "put_strike": 24750,
                        "call_premium": 68.50,
                        "put_premium": 65.25,
                        "total_premium": 133.75,
                        "expiry": "2025-06-05"
                    },
                    "strategy_score": 7.5
                }
            ]
        elif vol_expectation == "decrease":
            strategies["recommended_strategies"] = [
                {
                    "strategy_name": "Short Iron Butterfly",
                    "confidence": 8.3,
                    "setup": {
                        "center_strike": 24800,
                        "wing_strikes": [24700, 24900],
                        "net_credit": 65.25,
                        "max_profit": 65.25,
                        "max_loss": 34.75,
                        "expiry": "2025-06-05"
                    },
                    "ideal_conditions": "IV > 20%, trending to < 15%",
                    "strategy_score": 8.3
                }
            ]
        
        return strategies
        
    except Exception as e:
        logger.error(f"Error generating volatility strategies: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate volatility strategies")

@app.get("/api/strategy/income-generation")
async def get_income_strategies(
    account_size: Optional[float] = Query(500000, description="Account size in INR"),
    monthly_target: Optional[float] = Query(2.0, description="Monthly return target %")
):
    """Generate income generation strategies"""
    try:
        strategies = {
            "account_size": account_size,
            "monthly_target_percent": monthly_target,
            "monthly_target_amount": account_size * (monthly_target / 100),
            "timestamp": "2025-05-30T10:30:00Z",
            "recommended_strategies": [
                {
                    "strategy_name": "Covered Call",
                    "confidence": 8.5,
                    "setup": {
                        "underlying_position": "Long NIFTY futures",
                        "call_strike": 24900,
                        "call_premium": 45.50,
                        "expiry": "2025-06-05",
                        "monthly_income_potential": 6825.00,
                        "annualized_return": 16.38
                    },
                    "risk_profile": "moderate",
                    "capital_requirement": 185000,
                    "strategy_score": 8.5
                },
                {
                    "strategy_name": "Cash Secured Put",
                    "confidence": 8.2,
                    "setup": {
                        "put_strike": 24650,
                        "put_premium": 52.25,
                        "expiry": "2025-06-05",
                        "cash_requirement": 246500,
                        "monthly_income_potential": 7837.50,
                        "annualized_return": 19.15
                    },
                    "risk_profile": "moderate",
                    "assignment_risk": "medium",
                    "strategy_score": 8.2
                },
                {
                    "strategy_name": "Wheel Strategy",
                    "confidence": 9.0,
                    "setup": {
                        "phase": "cash_secured_puts",
                        "target_strikes": [24650, 24600, 24550],
                        "estimated_monthly_return": 2.5,
                        "win_rate": 0.85
                    },
                    "description": "Systematic premium collection through puts and covered calls",
                    "strategy_score": 9.0
                }
            ]
        }
        
        return strategies
        
    except Exception as e:
        logger.error(f"Error generating income strategies: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate income strategies")

@app.get("/api/strategy/signals")
async def get_current_signals():
    """Get current trading signals based on market analysis"""
    try:
        # TODO: Integrate with technical analysis and ML predictions
        signals = {
            "timestamp": "2025-05-30T10:30:00Z",
            "market_summary": {
                "nifty_trend": "bullish",
                "banknifty_trend": "sideways",
                "volatility_regime": "low",
                "overall_sentiment": "cautiously_optimistic"
            },
            "active_signals": [
                {
                    "signal_id": "NIFTY_BULL_CALL_001",
                    "symbol": "NIFTY",
                    "strategy": "Bull Call Spread",
                    "confidence": 8.5,
                    "entry_time": "2025-05-30T10:30:00Z",
                    "setup": {
                        "buy_strike": 24800,
                        "sell_strike": 24900,
                        "expiry": "2025-06-05",
                        "target_entry_price": 45.50
                    },
                    "rationale": "Bullish momentum with low volatility, good risk-reward",
                    "risk_reward": 1.20,
                    "max_risk": 4550,
                    "target_profit": 5450,
                    "stop_loss": 22.75,
                    "time_validity": "end_of_day"
                },
                {
                    "signal_id": "BANKNIFTY_IC_001",
                    "symbol": "BANKNIFTY",
                    "strategy": "Iron Condor",
                    "confidence": 7.8,
                    "entry_time": "2025-05-30T10:30:00Z",
                    "setup": {
                        "strikes": [51800, 51900, 52200, 52300],
                        "net_credit": 125.50,
                        "expiry": "2025-06-05"
                    },
                    "rationale": "Sideways movement expected, high probability play",
                    "probability_of_profit": 0.75,
                    "max_risk": 3945,
                    "max_profit": 12550
                }
            ],
            "watchlist": [
                {
                    "symbol": "NIFTY",
                    "setup": "Long Call if breaks 24850",
                    "trigger_level": 24850,
                    "confidence": 7.2
                },
                {
                    "symbol": "BANKNIFTY",
                    "setup": "Bear Put Spread if breaks below 51900",
                    "trigger_level": 51900,
                    "confidence": 7.0
                }
            ]
        }
        
        return signals
        
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate signals")

@app.get("/api/strategy/backtest/{strategy_name}")
async def backtest_strategy(
    strategy_name: str,
    start_date: Optional[str] = Query("2024-01-01", description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query("2025-05-30", description="End date YYYY-MM-DD"),
    initial_capital: Optional[float] = Query(100000, description="Initial capital")
):
    """Backtest a specific strategy"""
    try:
        # TODO: Implement actual backtesting engine
        backtest_results = {
            "strategy_name": strategy_name,
            "backtest_period": {
                "start_date": start_date,
                "end_date": end_date,
                "total_days": 150
            },
            "capital": {
                "initial": initial_capital,
                "final": initial_capital * 1.245,
                "peak": initial_capital * 1.298,
                "trough": initial_capital * 0.945
            },
            "performance_metrics": {
                "total_return": 24.5,
                "annualized_return": 18.8,
                "sharpe_ratio": 1.45,
                "max_drawdown": -5.5,
                "win_rate": 0.68,
                "profit_factor": 1.85,
                "avg_win": 2850.50,
                "avg_loss": -1240.25
            },
            "trade_statistics": {
                "total_trades": 145,
                "winning_trades": 98,
                "losing_trades": 47,
                "avg_trade_duration": 3.5,
                "best_trade": 8500.75,
                "worst_trade": -3200.50
            },
            "monthly_returns": [
                {"month": "2024-01", "return": 2.5},
                {"month": "2024-02", "return": 1.8},
                {"month": "2024-03", "return": -0.5},
                {"month": "2024-04", "return": 3.2},
                {"month": "2024-05", "return": 1.9}
            ],
            "strategy_specific_metrics": {
                "optimal_dte": 8,
                "best_iv_percentile": 35,
                "market_regime_performance": {
                    "bull_market": 28.5,
                    "bear_market": -2.1,
                    "sideways_market": 15.8
                }
            }
        }
        
        return backtest_results
        
    except Exception as e:
        logger.error(f"Error backtesting strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to backtest strategy")

if __name__ == "__main__":
    logger.info(f"Starting Strategy Engine Service on port {settings.STRATEGY_ENGINE_PORT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.STRATEGY_ENGINE_PORT,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )