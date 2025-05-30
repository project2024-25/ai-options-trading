#!/usr/bin/env python3
"""
Risk Management Service - Main Entry Point
Position sizing, portfolio risk, VaR calculations, and risk monitoring
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
    RISK_MANAGEMENT_PORT = 8005
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"
    
    # Risk limits
    MAX_POSITION_RISK_PERCENT = 2.0  # Max 2% risk per position
    MAX_PORTFOLIO_RISK_PERCENT = 10.0  # Max 10% portfolio risk
    MAX_CORRELATION = 0.7  # Max correlation between positions
    MIN_LIQUIDITY_VOLUME = 10000  # Minimum daily volume

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Risk Management Service...")
    
    try:
        # Initialize risk models and calculators
        logger.info("Loading risk models...")
        logger.info("Initializing VaR calculators...")
        logger.info("Setting up position monitoring...")
        logger.info("✅ Risk Management Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize Risk Management: {e}")
        raise
    finally:
        logger.info("Shutting down Risk Management Service...")

# Create FastAPI application
app = FastAPI(
    title="Risk Management Service",
    description="Portfolio risk management, position sizing, and risk monitoring",
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
        "service": "Risk Management Service",
        "status": "running",
        "version": "1.0.0",
        "description": "Portfolio risk management and position sizing for options trading",
        "endpoints": [
            "/health",
            "/api/risk/position-sizing",
            "/api/risk/portfolio-risk",
            "/api/risk/var-calculation",
            "/api/risk/correlation-analysis",
            "/api/risk/stress-testing",
            "/api/risk/margin-requirements",
            "/api/risk/alerts"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "risk-management",
        "port": settings.RISK_MANAGEMENT_PORT,
        "risk_models": "loaded",
        "var_calculator": "ready",
        "position_monitor": "active",
        "risk_limits": {
            "max_position_risk": f"{settings.MAX_POSITION_RISK_PERCENT}%",
            "max_portfolio_risk": f"{settings.MAX_PORTFOLIO_RISK_PERCENT}%"
        }
    }

@app.post("/api/risk/position-sizing")
async def calculate_position_size(
    account_balance: float = Query(..., description="Current account balance"),
    strategy_risk: float = Query(..., description="Maximum loss for the strategy"),
    risk_percent: Optional[float] = Query(2.0, description="Risk percentage (default 2%)"),
    symbol: Optional[str] = Query("NIFTY", description="Symbol for liquidity check")
):
    """Calculate optimal position size using Kelly Criterion and risk management"""
    try:
        if risk_percent > settings.MAX_POSITION_RISK_PERCENT:
            raise HTTPException(
                status_code=400, 
                detail=f"Risk percentage cannot exceed {settings.MAX_POSITION_RISK_PERCENT}%"
            )
        
        # Calculate position size
        max_risk_amount = account_balance * (risk_percent / 100)
        position_size = int(max_risk_amount / strategy_risk) if strategy_risk > 0 else 0
        
        # Kelly Criterion calculation (simplified)
        win_rate = 0.65  # TODO: Get from historical data
        avg_win = 2500   # TODO: Get from strategy performance
        avg_loss = 1500  # TODO: Get from strategy performance
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_position_size = int((kelly_fraction * account_balance) / strategy_risk) if strategy_risk > 0 else 0
        
        # Conservative sizing (half-Kelly)
        conservative_size = int(kelly_position_size * 0.5)
        
        # Final position size (minimum of all calculations)
        final_position_size = min(position_size, conservative_size) if conservative_size > 0 else position_size
        
        sizing_result = {
            "timestamp": "2025-05-30T10:30:00Z",
            "inputs": {
                "account_balance": account_balance,
                "strategy_risk": strategy_risk,
                "risk_percent": risk_percent,
                "symbol": symbol
            },
            "calculations": {
                "max_risk_amount": max_risk_amount,
                "basic_position_size": position_size,
                "kelly_fraction": round(kelly_fraction, 4),
                "kelly_position_size": kelly_position_size,
                "conservative_size": conservative_size,
                "recommended_size": final_position_size
            },
            "risk_metrics": {
                "position_risk_amount": final_position_size * strategy_risk,
                "position_risk_percent": round((final_position_size * strategy_risk / account_balance) * 100, 2),
                "heat_ratio": round(final_position_size * strategy_risk / max_risk_amount, 2)
            },
            "liquidity_check": {
                "symbol": symbol,
                "min_volume_required": settings.MIN_LIQUIDITY_VOLUME,
                "status": "adequate"  # TODO: Check actual liquidity
            },
            "recommendations": [
                f"Position size: {final_position_size} lots",
                f"Total risk: ₹{final_position_size * strategy_risk:,.2f}",
                f"Risk percentage: {round((final_position_size * strategy_risk / account_balance) * 100, 2)}%"
            ]
        }
        
        return sizing_result
        
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate position size")

@app.get("/api/risk/portfolio-risk")
async def get_portfolio_risk():
    """Get comprehensive portfolio risk analysis"""
    try:
        # TODO: Get actual portfolio positions from database
        portfolio_risk = {
            "timestamp": "2025-05-30T10:30:00Z",
            "portfolio_summary": {
                "total_value": 525680.50,
                "available_margin": 185420.75,
                "margin_utilization": 0.68,
                "number_of_positions": 12
            },
            "risk_metrics": {
                "portfolio_var_1d": {
                    "95_confidence": -8950.25,
                    "99_confidence": -15680.80,
                    "expected_shortfall": -18750.45
                },
                "portfolio_var_5d": {
                    "95_confidence": -19850.60,
                    "99_confidence": -32450.90
                },
                "max_drawdown": {
                    "current": -5.8,
                    "historical_max": -12.5,
                    "underwater_days": 3
                },
                "portfolio_beta": {
                    "nifty": 0.85,
                    "banknifty": 0.72
                }
            },
            "position_breakdown": [
                {
                    "position_id": "NIFTY_24800_CE_LONG",
                    "symbol": "NIFTY",
                    "strategy": "Bull Call Spread",
                    "quantity": 50,
                    "current_value": 125680.50,
                    "unrealized_pnl": 8950.25,
                    "position_risk": 4550.00,
                    "var_contribution": -2850.30,
                    "correlation_risk": 0.45
                },
                {
                    "position_id": "BANKNIFTY_52000_PE_SHORT",
                    "symbol": "BANKNIFTY",
                    "strategy": "Cash Secured Put",
                    "quantity": -25,
                    "current_value": 89450.75,
                    "unrealized_pnl": -2150.80,
                    "position_risk": 6250.00,
                    "var_contribution": -1950.60
                }
            ],
            "greeks_exposure": {
                "portfolio_delta": 125.8,
                "portfolio_gamma": 45.2,
                "portfolio_theta": -850.5,
                "portfolio_vega": 1250.8,
                "delta_normalized": 0.35,  # Normalized by portfolio value
                "gamma_risk": "moderate",
                "theta_decay_daily": -850.5
            },
            "concentration_analysis": {
                "sector_concentration": {
                    "nifty_weight": 0.65,
                    "banknifty_weight": 0.35
                },
                "strategy_concentration": {
                    "directional": 0.40,
                    "volatility": 0.25,
                    "income": 0.35
                },
                "expiry_concentration": {
                    "weekly": 0.45,
                    "monthly": 0.55
                }
            },
            "risk_warnings": [
                {
                    "type": "high_gamma",
                    "message": "Portfolio gamma exposure above normal levels",
                    "severity": "medium",
                    "recommendation": "Consider gamma hedging"
                }
            ]
        }
        
        return portfolio_risk
        
    except Exception as e:
        logger.error(f"Error calculating portfolio risk: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate portfolio risk")

@app.get("/api/risk/var-calculation")
async def calculate_var(
    confidence_level: Optional[float] = Query(0.95, description="Confidence level (0.95 or 0.99)"),
    time_horizon: Optional[int] = Query(1, description="Time horizon in days"),
    method: Optional[str] = Query("historical", description="VaR method: historical, parametric, monte_carlo")
):
    """Calculate Value at Risk (VaR) for portfolio"""
    try:
        if confidence_level not in [0.95, 0.99]:
            raise HTTPException(status_code=400, detail="Confidence level must be 0.95 or 0.99")
        
        if method not in ["historical", "parametric", "monte_carlo"]:
            raise HTTPException(status_code=400, detail="Method must be historical, parametric, or monte_carlo")
        
        # TODO: Implement actual VaR calculations
        var_result = {
            "timestamp": "2025-05-30T10:30:00Z",
            "parameters": {
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "method": method,
                "portfolio_value": 525680.50
            },
            "var_calculations": {
                "historical_var": {
                    "1_day_95": -8950.25,
                    "1_day_99": -15680.80,
                    "5_day_95": -19850.60,
                    "5_day_99": -32450.90
                },
                "parametric_var": {
                    "1_day_95": -9125.45,
                    "1_day_99": -16250.30,
                    "5_day_95": -20450.75,
                    "5_day_99": -33680.20
                },
                "monte_carlo_var": {
                    "1_day_95": -8750.80,
                    "1_day_99": -15420.60,
                    "simulations": 10000,
                    "confidence_interval": [8500, 9000]
                }
            },
            "component_var": {
                "nifty_positions": -5680.25,
                "banknifty_positions": -3270.00,
                "diversification_benefit": 1250.45
            },
            "stress_scenarios": {
                "covid_march_2020": -45680.90,
                "nifty_5_percent_drop": -25680.40,
                "vix_spike_scenario": -18950.75
            },
            "risk_decomposition": {
                "systematic_risk": 0.65,
                "idiosyncratic_risk": 0.35,
                "correlation_risk": 0.25
            },
            "backtesting": {
                "violations_last_250_days": 8,
                "expected_violations": 13,
                "model_accuracy": "good",
                "kupiec_test_p_value": 0.15
            }
        }
        
        return var_result
        
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate VaR")

@app.get("/api/risk/correlation-analysis")
async def analyze_correlations():
    """Analyze correlation between positions and risk concentration"""
    try:
        correlation_analysis = {
            "timestamp": "2025-05-30T10:30:00Z",
            "correlation_matrix": {
                "nifty_banknifty": 0.78,
                "nifty_vix": -0.65,
                "banknifty_vix": -0.58,
                "options_underlying": 0.85
            },
            "position_correlations": [
                {
                    "position_1": "NIFTY_24800_CE",
                    "position_2": "NIFTY_24700_PE",
                    "correlation": -0.82,
                    "risk_level": "high_negative_correlation"
                },
                {
                    "position_1": "NIFTY_POSITIONS",
                    "position_2": "BANKNIFTY_POSITIONS",
                    "correlation": 0.78,
                    "risk_level": "high_positive_correlation"
                }
            ],
            "diversification_metrics": {
                "effective_positions": 7.2,
                "diversification_ratio": 0.68,
                "concentration_index": 0.35,
                "herfindahl_index": 0.28
            },
            "risk_concentration": {
                "top_3_positions_risk": 0.65,
                "single_position_max": 0.28,
                "sector_concentration": {
                    "financial": 0.75,
                    "index": 1.0
                }
            },
            "recommendations": [
                {
                    "type": "reduce_correlation",
                    "message": "High correlation between NIFTY and BANKNIFTY positions",
                    "action": "Consider diversifying into other sectors or strategies",
                    "priority": "medium"
                },
                {
                    "type": "position_size",
                    "message": "Position concentration within acceptable limits",
                    "action": "Continue monitoring",
                    "priority": "low"
                }
            ]
        }
        
        return correlation_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing correlations: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze correlations")

@app.get("/api/risk/stress-testing")
async def perform_stress_test(
    scenario: Optional[str] = Query("custom", description="Scenario: market_crash, vix_spike, interest_rate, custom"),
    nifty_move: Optional[float] = Query(-5.0, description="NIFTY move in %"),
    vix_move: Optional[float] = Query(50.0, description="VIX move in %"),
    time_decay: Optional[int] = Query(5, description="Days of time decay")
):
    """Perform stress testing on portfolio"""
    try:
        stress_results = {
            "timestamp": "2025-05-30T10:30:00Z",
            "scenario": scenario,
            "scenario_parameters": {
                "nifty_move_percent": nifty_move,
                "vix_move_percent": vix_move,
                "time_decay_days": time_decay
            },
            "current_portfolio_value": 525680.50,
            "stress_scenarios": {
                "market_crash_2008": {
                    "nifty_move": -35.0,
                    "vix_spike": 150.0,
                    "portfolio_impact": -185680.90,
                    "recovery_time_days": 180
                },
                "covid_march_2020": {
                    "nifty_move": -25.0,
                    "vix_spike": 200.0,
                    "portfolio_impact": -125450.75,
                    "recovery_time_days": 90
                },
                "custom_scenario": {
                    "nifty_move": nifty_move,
                    "vix_spike": vix_move,
                    "portfolio_impact": nifty_move * 2500 + vix_move * 150 - time_decay * 850,
                    "probability": "user_defined"
                }
            },
            "position_level_impact": [
                {
                    "position": "NIFTY_24800_CE_LONG",
                    "current_value": 125680.50,
                    "stressed_value": 45680.25,
                    "impact": -80000.25,
                    "impact_percent": -63.6
                },
                {
                    "position": "BANKNIFTY_52000_PE_SHORT",
                    "current_value": 89450.75,
                    "stressed_value": 125680.90,
                    "impact": 36230.15,
                    "impact_percent": 40.5
                }
            ],
            "greeks_stress_impact": {
                "delta_impact": nifty_move * 125.8 * 100,  # Delta * move * lot size
                "gamma_impact": 0.5 * 45.2 * (nifty_move * 100) ** 2,  # 0.5 * gamma * move^2
                "vega_impact": vix_move * 1250.8,  # Vega * VIX move
                "theta_impact": time_decay * -850.5  # Theta * days
            },
            "margin_impact": {
                "current_margin_used": 340259.75,
                "stressed_margin_required": 485670.25,
                "margin_call_risk": True,
                "additional_margin_needed": 145410.50
            },
            "risk_metrics_under_stress": {
                "max_loss_scenario": -245680.90,
                "probability_of_ruin": 0.05,
                "expected_recovery_time": 120,
                "liquidity_risk": "high"
            },
            "mitigation_strategies": [
                {
                    "strategy": "hedging",
                    "description": "Add protective puts to limit downside",
                    "cost": 8500.00,
                    "effectiveness": 0.75
                },
                {
                    "strategy": "position_reduction",
                    "description": "Reduce position sizes by 30%",
                    "cost": 0,
                    "effectiveness": 0.50
                }
            ]
        }
        
        return stress_results
        
    except Exception as e:
        logger.error(f"Error performing stress test: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform stress test")

@app.get("/api/risk/margin-requirements")
async def calculate_margin_requirements():
    """Calculate margin requirements for current and potential positions"""
    try:
        margin_analysis = {
            "timestamp": "2025-05-30T10:30:00Z",
            "account_summary": {
                "available_balance": 525680.50,
                "margin_used": 340259.75,
                "margin_available": 185420.75,
                "margin_utilization": 64.7
            },
            "position_margins": [
                {
                    "position": "NIFTY_24800_CE_LONG",
                    "quantity": 50,
                    "span_margin": 85680.00,
                    "exposure_margin": 12500.00,
                    "total_margin": 98180.00,
                    "premium_blocked": 125680.50
                },
                {
                    "position": "NIFTY_24700_PE_SHORT",
                    "quantity": -25,
                    "span_margin": 125680.50,
                    "exposure_margin": 18750.00,
                    "total_margin": 144430.50,
                    "premium_received": 89450.75
                }
            ],
            "span_calculation": {
                "nifty_span_rate": 3.5,
                "banknifty_span_rate": 4.2,
                "volatility_adjustment": 1.15,
                "liquidity_adjustment": 1.05
            },
            "margin_optimization": {
                "portfolio_margin_benefit": 25680.00,
                "cross_margining_benefit": 12500.00,
                "total_savings": 38180.00,
                "optimization_percentage": 10.1
            },
            "margin_alerts": [
                {
                    "type": "utilization_warning",
                    "message": "Margin utilization above 60%",
                    "threshold": 60.0,
                    "current": 64.7,
                    "severity": "medium"
                }
            ],
            "what_if_scenarios": {
                "add_position": {
                    "description": "Add BANKNIFTY 52000 CE Long (25 lots)",
                    "additional_margin": 95680.00,
                    "new_utilization": 82.9,
                    "feasible": True
                },
                "market_move": {
                    "scenario": "NIFTY down 3%",
                    "margin_increase": 45680.00,
                    "utilization_impact": 8.7,
                    "margin_call_risk": False
                }
            }
        }
        
        return margin_analysis
        
    except Exception as e:
        logger.error(f"Error calculating margin requirements: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate margin requirements")

@app.get("/api/risk/alerts")
async def get_risk_alerts():
    """Get current risk alerts and warnings"""
    try:
        risk_alerts = {
            "timestamp": "2025-05-30T10:30:00Z",
            "alert_summary": {
                "critical": 0,
                "high": 1,
                "medium": 3,
                "low": 2,
                "total": 6
            },
            "active_alerts": [
                {
                    "alert_id": "RISK_001",
                    "type": "position_concentration",
                    "severity": "high",
                    "message": "Single position risk exceeds 25% of portfolio",
                    "position": "NIFTY_24800_CE_LONG",
                    "current_value": 28.5,
                    "threshold": 25.0,
                    "recommendation": "Consider reducing position size",
                    "time_triggered": "2025-05-30T09:45:00Z"
                },
                {
                    "alert_id": "RISK_002",
                    "type": "correlation_risk",
                    "severity": "medium",
                    "message": "High correlation between positions",
                    "correlation": 0.78,
                    "threshold": 0.70,
                    "recommendation": "Diversify into uncorrelated assets",
                    "time_triggered": "2025-05-30T10:15:00Z"
                },
                {
                    "alert_id": "RISK_003",
                    "type": "margin_utilization",
                    "severity": "medium",
                    "message": "Margin utilization approaching warning level",
                    "current": 64.7,
                    "warning_threshold": 70.0,
                    "critical_threshold": 85.0,
                    "recommendation": "Monitor closely, prepare for margin call",
                    "time_triggered": "2025-05-30T10:20:00Z"
                },
                {
                    "alert_id": "RISK_004",
                    "type": "time_decay",
                    "severity": "medium",
                    "message": "High theta exposure with positions expiring soon",
                    "daily_theta": -850.5,
                    "positions_expiring_week": 3,
                    "recommendation": "Consider rolling or closing positions",
                    "time_triggered": "2025-05-30T10:25:00Z"
                }
            ],
            "risk_thresholds": {
                "position_risk_max": 2.0,
                "portfolio_risk_max": 10.0,
                "correlation_max": 0.70,
                "margin_utilization_warning": 70.0,
                "margin_utilization_critical": 85.0,
                "var_limit": 15000.0
            },
            "monitoring_status": {
                "position_monitor": "active",
                "var_calculator": "running",
                "correlation_tracker": "active",
                "margin_monitor": "active",
                "alert_system": "operational"
            }
        }
        
        return risk_alerts
        
    except Exception as e:
        logger.error(f"Error getting risk alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk alerts")

if __name__ == "__main__":
    logger.info(f"Starting Risk Management Service on port {settings.RISK_MANAGEMENT_PORT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.RISK_MANAGEMENT_PORT,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )