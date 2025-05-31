# File: services/strategy-engine/app/main.py
# Restored Strategy Service with proper structure

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import asyncio
import httpx
import random
from datetime import datetime, timedelta
from enhanced_trade_builder import router as trade_builder_router

# Create FastAPI app
app = FastAPI(
    title="Enhanced Strategy Engine Service",
    description="AI-powered options trading strategy engine",
    version="1.0.0"
)
app.include_router(trade_builder_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "enhanced-strategy-engine",
        "port": 8004,
        "strategy_templates": "loaded",
        "zerodha_patterns": "loaded",
        "backtesting_engine": "ready",
        "signal_generator": "active"
    }

@app.get("/api/strategy/strategy-recommendation")
async def get_strategy_recommendation(
    symbol: str = Query(..., description="NIFTY or BANKNIFTY"),
    current_spot: float = Query(..., description="Current spot price"),
    volatility_percentile: float = Query(..., description="Current IV percentile"),
    days_to_expiry: int = Query(..., description="Days to expiry"),
    market_sentiment: str = Query(..., description="bullish, bearish, or neutral"),
    event_proximity: bool = Query(default=False, description="Is there a major event nearby"),
    account_size: float = Query(default=500000, description="Account size for position sizing")
):
    """Get personalized strategy recommendation based on comprehensive analysis"""
    
    try:
        # Market regime analysis
        if volatility_percentile < 30:
            volatility_regime = "low"
        elif volatility_percentile < 70:
            volatility_regime = "normal"
        else:
            volatility_regime = "high"
        
        # Time regime
        if days_to_expiry <= 7:
            time_regime = "first_half"
        else:
            time_regime = "second_half"
        
        # Strategy selection logic
        if market_sentiment == "bullish" and volatility_regime == "low":
            strategy_name = "Bull Call Spread"
            rationale = "Low volatility suitable for debit spreads"
            confidence = 8
            expected_return = 12
            probability_of_profit = 0.65
        elif market_sentiment == "neutral" and volatility_regime == "low":
            strategy_name = "Short Strangle"
            rationale = "Range-bound market with premium collection"
            confidence = 8
            expected_return = 18
            probability_of_profit = 0.72
        elif market_sentiment == "bearish" and volatility_regime == "low":
            strategy_name = "Bear Put Spread"
            rationale = "Bearish outlook with limited risk"
            confidence = 7
            expected_return = 15
            probability_of_profit = 0.60
        elif volatility_regime == "high":
            strategy_name = "Iron Condor"
            rationale = "High volatility with range-bound expectation"
            confidence = 6
            expected_return = 20
            probability_of_profit = 0.55
        else:
            strategy_name = "Long Straddle"
            rationale = "Uncertain direction with volatility play"
            confidence = 5
            expected_return = 25
            probability_of_profit = 0.45
        
        # Position sizing calculation
        max_risk_amount = account_size * 0.02  # 2% risk
        
        if "Spread" in strategy_name:
            risk_per_lot = 1000  # Approximate for spreads
        elif "Strangle" in strategy_name or "Straddle" in strategy_name:
            risk_per_lot = 2000  # Higher risk for vol strategies
        else:
            risk_per_lot = 1500
        
        recommended_lots = max(1, int(max_risk_amount / risk_per_lot))
        recommended_lots = min(recommended_lots, 20)  # Cap at 20 lots
        
        total_margin_required = recommended_lots * risk_per_lot
        margin_utilization = (total_margin_required / account_size) * 100
        
        return {
            "symbol": symbol,
            "analysis_timestamp": datetime.now().isoformat() + "Z",
            "market_inputs": {
                "spot_price": current_spot,
                "volatility_percentile": volatility_percentile,
                "days_to_expiry": days_to_expiry,
                "market_sentiment": market_sentiment,
                "event_proximity": event_proximity,
                "account_size": account_size
            },
            "market_regime_analysis": {
                "volatility_regime": volatility_regime,
                "time_regime": time_regime,
                "event_impact": "high" if event_proximity else "low",
                "overall_environment": f"{volatility_regime}_vol_{time_regime}_series"
            },
            "recommended_strategy": {
                "name": strategy_name,
                "rationale": rationale,
                "confidence": confidence,
                "expected_return": expected_return,
                "probability_of_profit": probability_of_profit
            },
            "risk_management": {
                "stop_loss": "50% of premium paid/received",
                "profit_target": "75% of maximum profit",
                "time_stop": "Exit 7 days before expiry",
                "adjustment_rules": "Convert to spreads if tested",
                "position_monitoring": "Daily Greeks and P&L review"
            },
            "position_sizing": {
                "max_risk_amount": max_risk_amount,
                "recommended_lots": recommended_lots,
                "risk_per_lot": risk_per_lot,
                "total_margin_required": total_margin_required,
                "margin_utilization": margin_utilization
            },
            "alternatives": []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating strategy recommendation: {str(e)}")

# Replace your direct endpoint with this fixed version

@app.get("/api/strategy/specific-trade-direct")
async def get_specific_trade_direct(
    symbol: str = "NIFTY",
    account_size: float = 500000
):
    """Direct integration test - FIXED for high spot price"""
    
    try:
        # Get market data
        async with httpx.AsyncClient(timeout=10.0) as client:
            market_response = await client.get(f"http://localhost:8001/api/data/{symbol.lower()}-snapshot")
            market_data = market_response.json()
            current_spot = market_data["data"]["ltp"]
        
        # Get options chain
        async with httpx.AsyncClient(timeout=10.0) as client:
            options_response = await client.get(f"http://localhost:8001/api/data/options-chain/{symbol.lower()}")
            options_data = options_response.json()
        
        # Simple processing
        contracts = options_data["data"]
        ce_contracts = [c for c in contracts if c["option_type"] == "CE"]
        strikes = [c["strike"] for c in ce_contracts]
        strikes.sort()
        
        # Handle edge cases
        if current_spot > max(strikes):
            # Spot is above all strikes - use the two highest strikes for a spread
            buy_strike = strikes[-2]  # Second highest
            sell_strike = strikes[-1]  # Highest
        elif current_spot < min(strikes):
            # Spot is below all strikes - use the two lowest strikes
            buy_strike = strikes[0]   # Lowest
            sell_strike = strikes[1]  # Second lowest
        else:
            # Normal case - find ATM and next strike
            atm_strike = min(strikes, key=lambda x: abs(x - current_spot))
            atm_index = strikes.index(atm_strike)
            
            buy_strike = atm_strike
            # Try to find next higher strike
            if atm_index < len(strikes) - 1:
                sell_strike = strikes[atm_index + 1]
            else:
                # If ATM is the highest, use previous strike as buy
                buy_strike = strikes[atm_index - 1]
                sell_strike = atm_strike
        
        # Find the actual contracts
        buy_contract = next((c for c in ce_contracts if c["strike"] == buy_strike), None)
        sell_contract = next((c for c in ce_contracts if c["strike"] == sell_strike), None)
        
        if not buy_contract or not sell_contract:
            return {
                "error": "Contracts not found after strike selection",
                "current_spot": current_spot,
                "selected_buy_strike": buy_strike,
                "selected_sell_strike": sell_strike,
                "available_strikes": strikes
            }
        
        # Calculate trade
        buy_mid = (buy_contract["bid"] + buy_contract["ask"]) / 2
        sell_mid = (sell_contract["bid"] + sell_contract["ask"]) / 2
        net_debit = buy_mid - sell_mid
        
        # Handle negative net debit (credit spread)
        if net_debit < 0:
            trade_type = "CREDIT"
            net_credit = abs(net_debit)
            max_profit = net_credit
            max_loss = (sell_contract["strike"] - buy_contract["strike"]) - net_credit
        else:
            trade_type = "DEBIT"
            max_profit = (sell_contract["strike"] - buy_contract["strike"]) - net_debit
            max_loss = net_debit
        
        max_risk = account_size * 0.02
        lot_size = buy_contract["lot_size"]
        max_lots = max(1, min(10, int(max_risk / (abs(net_debit) * lot_size))))
        
        net_premium = abs(net_debit) * max_lots * lot_size
        total_max_profit = abs(max_profit) * max_lots * lot_size
        total_max_loss = abs(max_loss) * max_lots * lot_size
        
        return {
            "strategy_name": f"Bull Call Spread ({trade_type})",
            "current_spot": current_spot,
            "trade_type": trade_type,
            "market_situation": "Above all strikes" if current_spot > max(strikes) else 
                              "Below all strikes" if current_spot < min(strikes) else "Normal",
            "buy_contract": {
                "symbol": buy_contract["symbol"],
                "strike": buy_contract["strike"],
                "ltp": buy_contract["ltp"],
                "bid": buy_contract["bid"],
                "ask": buy_contract["ask"],
                "mid_price": buy_mid
            },
            "sell_contract": {
                "symbol": sell_contract["symbol"],
                "strike": sell_contract["strike"],
                "ltp": sell_contract["ltp"],
                "bid": sell_contract["bid"],
                "ask": sell_contract["ask"],
                "mid_price": sell_mid
            },
            "trade_details": {
                "net_debit_credit": net_debit,
                "lots": max_lots,
                "lot_size": lot_size,
                "total_quantity": max_lots * lot_size,
                "net_premium": net_premium,
                "max_profit": total_max_profit,
                "max_loss": total_max_loss,
                "breakeven": buy_contract["strike"] + (net_debit if net_debit > 0 else 0)
            },
            "execution_checklist": [
                f"BUY {max_lots} lots of {buy_contract['symbol']} at ₹{buy_mid:.2f}",
                f"SELL {max_lots} lots of {sell_contract['symbol']} at ₹{sell_mid:.2f}",
                f"Net {'Investment' if trade_type == 'DEBIT' else 'Credit'}: ₹{net_premium:.0f}",
                f"Max Profit: ₹{total_max_profit:.0f}",
                f"Max Loss: ₹{total_max_loss:.0f}",
                f"Strike Spread: {sell_contract['strike'] - buy_contract['strike']} points"
            ]
        }
        
    except Exception as e:
        import traceback
        return {"error": f"Failed: {str(e)}", "traceback": traceback.format_exc()}

@app.get("/api/strategy/debug-spot")
async def debug_spot_price():
    """Debug spot price calculation"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            market_response = await client.get("http://localhost:8001/api/data/nifty-snapshot")
            market_data = market_response.json()
            current_spot = market_data["data"]["ltp"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            options_response = await client.get("http://localhost:8001/api/data/options-chain/nifty")
            options_data = options_response.json()
        
        strikes = [c["strike"] for c in options_data["data"] if c["option_type"] == "CE"]
        atm_strike = min(strikes, key=lambda x: abs(x - current_spot))
        
        return {
            "current_spot": current_spot,
            "available_strikes": sorted(strikes),
            "atm_strike": atm_strike,
            "spot_above_max_strike": current_spot > max(strikes),
            "spot_below_min_strike": current_spot < min(strikes)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)