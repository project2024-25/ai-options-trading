# File: enhanced_trade_builder.py - FIXED VERSION
# Enhanced trade builder with better error handling

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any
import httpx
import math
from datetime import datetime
from pydantic import BaseModel
import traceback

router = APIRouter()

class OptionContract(BaseModel):
    symbol: str
    strike: float
    option_type: str
    ltp: float
    bid: float
    ask: float
    volume: int
    oi: int
    lot_size: int
    mid_price: float = None

class TradeDetails(BaseModel):
    action: str  # BUY or SELL
    contract: OptionContract
    quantity: int
    lots: int
    premium: float
    total_cost: float

class SpecificTrade(BaseModel):
    strategy_name: str
    underlying: str
    current_spot: float
    legs: List[TradeDetails]
    net_premium: float
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    total_lots: int
    execution_checklist: List[str]

async def get_options_chain(symbol: str) -> List[OptionContract]:
    """Get live options chain data"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://localhost:8001/api/data/options-chain/{symbol.lower()}")
            data = response.json()
            
            if not data.get("success"):
                raise HTTPException(status_code=500, detail=f"Failed to get options data: {data}")
            
            contracts = []
            for option in data["data"]:
                contract = OptionContract(
                    symbol=option["symbol"],
                    strike=option["strike"],
                    option_type=option["option_type"],
                    ltp=option["ltp"],
                    bid=option["bid"],
                    ask=option["ask"],
                    volume=option["volume"],
                    oi=option["oi"],
                    lot_size=option["lot_size"]
                )
                contract.mid_price = (contract.bid + contract.ask) / 2
                contracts.append(contract)
            
            return contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching options data: {str(e)}")

def build_bull_call_spread(contracts: List[OptionContract], spot_price: float, account_size: float) -> SpecificTrade:
    """Build specific Bull Call Spread trade with relaxed filters"""
    
    try:
        # Filter CE options with relaxed criteria
        ce_contracts = [c for c in contracts if c.option_type == "CE"]
        
        if len(ce_contracts) < 2:
            raise HTTPException(status_code=400, detail=f"Insufficient CE options. Found {len(ce_contracts)} CE contracts")
        
        # Apply liquidity filters progressively
        liquid_ce = [c for c in ce_contracts if c.volume > 500 and c.oi > 1000]  # Relaxed from 1000/5000
        
        if len(liquid_ce) < 2:
            # Further relax criteria
            liquid_ce = [c for c in ce_contracts if c.volume > 100 and c.oi > 500]
            
        if len(liquid_ce) < 2:
            # Use all CE contracts if needed
            liquid_ce = ce_contracts
            
        # Sort by strike price
        liquid_ce.sort(key=lambda x: x.strike)
        
        # Find ATM strike (closest to spot price)
        atm_strike = min([c.strike for c in liquid_ce], key=lambda x: abs(x - spot_price))
        
        # Find buy and sell contracts
        buy_contract = None
        sell_contract = None
        
        # Find the ATM contract to buy
        for contract in liquid_ce:
            if contract.strike == atm_strike:
                buy_contract = contract
                break
        
        # Find a contract 50-100 points higher to sell
        for offset in [50, 100, 150]:
            sell_strike = atm_strike + offset
            for contract in liquid_ce:
                if contract.strike == sell_strike:
                    sell_contract = contract
                    break
            if sell_contract:
                break
        
        if not buy_contract:
            raise HTTPException(status_code=400, detail=f"ATM contract not found for strike {atm_strike}")
            
        if not sell_contract:
            # Use the next available higher strike
            higher_strikes = [c for c in liquid_ce if c.strike > atm_strike]
            if higher_strikes:
                sell_contract = min(higher_strikes, key=lambda x: x.strike)
            else:
                raise HTTPException(status_code=400, detail="No higher strike available for spread")
        
        # Calculate position sizing
        net_debit = buy_contract.mid_price - sell_contract.mid_price
        
        if net_debit <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid spread: net debit is {net_debit}")
        
        max_risk_amount = account_size * 0.02  # 2% risk
        max_lots = max(1, int(max_risk_amount / (net_debit * buy_contract.lot_size)))
        max_lots = min(max_lots, 10)  # Cap at 10 lots
        
        # Build trade legs
        buy_leg = TradeDetails(
            action="BUY",
            contract=buy_contract,
            quantity=max_lots * buy_contract.lot_size,
            lots=max_lots,
            premium=buy_contract.mid_price,
            total_cost=buy_contract.mid_price * max_lots * buy_contract.lot_size
        )
        
        sell_leg = TradeDetails(
            action="SELL",
            contract=sell_contract,
            quantity=max_lots * sell_contract.lot_size,
            lots=max_lots,
            premium=sell_contract.mid_price,
            total_cost=sell_contract.mid_price * max_lots * sell_contract.lot_size
        )
        
        # Calculate trade metrics
        net_premium = net_debit * max_lots * buy_contract.lot_size
        max_profit = ((sell_contract.strike - buy_contract.strike) - net_debit) * max_lots * buy_contract.lot_size
        max_loss = net_premium
        breakeven = buy_contract.strike + net_debit
        
        return SpecificTrade(
            strategy_name="Bull Call Spread",
            underlying="NIFTY",
            current_spot=spot_price,
            legs=[buy_leg, sell_leg],
            net_premium=net_premium,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven],
            total_lots=max_lots,
            execution_checklist=[
                f"Verify NIFTY spot between ₹{buy_contract.strike-25:.0f} - ₹{buy_contract.strike+25:.0f}",
                f"Check {buy_contract.symbol} bid-ask spread < 5%",
                f"Check {sell_contract.symbol} bid-ask spread < 5%",
                f"Execute both legs simultaneously",
                f"Set stop-loss at 50% of premium (₹{max_loss*0.5:.0f})",
                f"Set profit target at 75% of max profit (₹{max_profit*0.75:.0f})",
                f"Monitor position until {buy_contract.strike + net_debit:.0f} breakeven"
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building bull call spread: {str(e)}")

@router.get("/api/strategy/specific-trade", response_model=SpecificTrade)
async def get_specific_trade(
    symbol: str = "NIFTY",
    strategy_name: str = "Bull Call Spread",
    account_size: float = 500000,
    risk_percentage: float = 2.0
):
    """Generate specific executable trade details"""
    
    try:
        # Get current market data
        async with httpx.AsyncClient(timeout=10.0) as client:
            market_response = await client.get(f"http://localhost:8001/api/data/{symbol.lower()}-snapshot")
            market_data = market_response.json()
            
            if not market_data.get("success"):
                raise HTTPException(status_code=500, detail=f"Failed to get market data: {market_data}")
                
            current_spot = market_data["data"]["ltp"]
        
        # Get options chain
        contracts = await get_options_chain(symbol)
        
        if not contracts:
            raise HTTPException(status_code=400, detail="No options contracts available")
        
        # Build specific trade
        if strategy_name.lower() == "bull call spread":
            trade = build_bull_call_spread(contracts, current_spot, account_size)
        else:
            raise HTTPException(status_code=400, detail=f"Strategy '{strategy_name}' not implemented yet")
        
        return trade
        
    except HTTPException as he:
        raise he
    except Exception as e:
        # Better error reporting
        error_details = f"Unexpected error: {str(e)}\nTraceback: {traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_details)

@router.get("/api/strategy/available-strategies")
async def get_available_strategies():
    """Get list of available strategy implementations"""
    return {
        "strategies": [
            {
                "name": "Bull Call Spread",
                "description": "Bullish limited risk debit spread",
                "market_outlook": "Moderately bullish",
                "risk_profile": "Limited risk, limited reward"
            }
        ]
    }

@router.get("/api/strategy/debug-trade")
async def debug_trade_generation(symbol: str = "NIFTY"):
    """Debug trade generation step by step"""
    
    debug_info = {}
    
    try:
        # Step 1: Test market data
        async with httpx.AsyncClient(timeout=10.0) as client:
            market_response = await client.get(f"http://localhost:8001/api/data/{symbol.lower()}-snapshot")
            market_data = market_response.json()
            debug_info["market_data"] = {
                "status": "success" if market_data.get("success") else "failed",
                "spot_price": market_data.get("data", {}).get("ltp", "not_found"),
                "response_keys": list(market_data.keys())
            }
    except Exception as e:
        debug_info["market_data"] = {"status": "error", "error": str(e)}
    
    try:
        # Step 2: Test options chain
        contracts = await get_options_chain(symbol)
        ce_contracts = [c for c in contracts if c.option_type == "CE"]
        liquid_ce = [c for c in ce_contracts if c.volume > 500 and c.oi > 1000]
        
        debug_info["options_analysis"] = {
            "total_contracts": len(contracts),
            "ce_contracts": len(ce_contracts),
            "liquid_ce_contracts": len(liquid_ce),
            "sample_liquid": {
                "symbol": liquid_ce[0].symbol if liquid_ce else "none",
                "strike": liquid_ce[0].strike if liquid_ce else "none",
                "ltp": liquid_ce[0].ltp if liquid_ce else "none",
                "volume": liquid_ce[0].volume if liquid_ce else "none",
                "oi": liquid_ce[0].oi if liquid_ce else "none"
            } if liquid_ce else "no_liquid_options"
        }
    except Exception as e:
        debug_info["options_analysis"] = {"status": "error", "error": str(e)}
    
    return debug_info

# Add this simple test endpoint to your enhanced_trade_builder.py

@router.get("/api/strategy/simple-test")
async def simple_test():
    """Simple test to identify the exact issue"""
    
    try:
        # Step 1: Get market data
        async with httpx.AsyncClient(timeout=10.0) as client:
            market_response = await client.get("http://localhost:8001/api/data/nifty-snapshot")
            market_data = market_response.json()
            current_spot = market_data["data"]["ltp"]
        
        # Step 2: Get options chain
        contracts = await get_options_chain("NIFTY")
        ce_contracts = [c for c in contracts if c.option_type == "CE"]
        
        # Step 3: Find ATM strike
        atm_strike = min([c.strike for c in ce_contracts], key=lambda x: abs(x - current_spot))
        
        # Step 4: Find contracts
        buy_contract = None
        sell_contract = None
        
        for contract in ce_contracts:
            if contract.strike == atm_strike:
                buy_contract = contract
                break
        
        for contract in ce_contracts:
            if contract.strike == atm_strike + 50:  # 50 points higher
                sell_contract = contract
                break
        
        # Step 5: Check if we found both
        result = {
            "current_spot": current_spot,
            "atm_strike": atm_strike,
            "buy_contract_found": buy_contract is not None,
            "sell_contract_found": sell_contract is not None,
            "available_strikes": sorted([c.strike for c in ce_contracts])
        }
        
        if buy_contract:
            result["buy_contract"] = {
                "symbol": buy_contract.symbol,
                "strike": buy_contract.strike,
                "ltp": buy_contract.ltp,
                "bid": buy_contract.bid,
                "ask": buy_contract.ask,
                "mid_price": buy_contract.mid_price
            }
        
        if sell_contract:
            result["sell_contract"] = {
                "symbol": sell_contract.symbol,
                "strike": sell_contract.strike,
                "ltp": sell_contract.ltp,
                "bid": sell_contract.bid,
                "ask": sell_contract.ask,
                "mid_price": sell_contract.mid_price
            }
        
        # Step 6: Calculate net debit if both found
        if buy_contract and sell_contract:
            net_debit = buy_contract.mid_price - sell_contract.mid_price
            result["net_debit"] = net_debit
            result["net_debit_valid"] = net_debit > 0
        
        return result
        
    except Exception as e:
        return {"error": f"Test failed: {str(e)}", "traceback": traceback.format_exc()}
    
# Add this position sizing test to your enhanced_trade_builder.py

@router.get("/api/strategy/position-test")
async def position_sizing_test(account_size: float = 500000):
    """Test the position sizing calculation"""
    
    try:
        # Use the same logic as simple-test to get contracts
        async with httpx.AsyncClient(timeout=10.0) as client:
            market_response = await client.get("http://localhost:8001/api/data/nifty-snapshot")
            market_data = market_response.json()
            current_spot = market_data["data"]["ltp"]
        
        contracts = await get_options_chain("NIFTY")
        ce_contracts = [c for c in contracts if c.option_type == "CE"]
        atm_strike = min([c.strike for c in ce_contracts], key=lambda x: abs(x - current_spot))
        
        buy_contract = next((c for c in ce_contracts if c.strike == atm_strike), None)
        sell_contract = next((c for c in ce_contracts if c.strike == atm_strike + 50), None)
        
        if not buy_contract or not sell_contract:
            return {"error": "Contracts not found"}
        
        # Calculate position sizing step by step
        net_debit = buy_contract.mid_price - sell_contract.mid_price
        max_risk_amount = account_size * 0.02  # 2% risk
        lot_size = buy_contract.lot_size
        
        # Position sizing calculation
        max_lots = max(1, int(max_risk_amount / (net_debit * lot_size)))
        max_lots = min(max_lots, 10)  # Cap at 10 lots
        
        # Calculate final metrics
        net_premium = net_debit * max_lots * lot_size
        max_profit = ((sell_contract.strike - buy_contract.strike) - net_debit) * max_lots * lot_size
        max_loss = net_premium
        breakeven = buy_contract.strike + net_debit
        
        # Build trade legs
        buy_leg = {
            "action": "BUY",
            "symbol": buy_contract.symbol,
            "strike": buy_contract.strike,
            "quantity": max_lots * lot_size,
            "lots": max_lots,
            "premium": buy_contract.mid_price,
            "total_cost": buy_contract.mid_price * max_lots * lot_size
        }
        
        sell_leg = {
            "action": "SELL",
            "symbol": sell_contract.symbol,
            "strike": sell_contract.strike,
            "quantity": max_lots * lot_size,
            "lots": max_lots,
            "premium": sell_contract.mid_price,
            "total_cost": sell_contract.mid_price * max_lots * lot_size
        }
        
        return {
            "account_size": account_size,
            "net_debit": net_debit,
            "max_risk_amount": max_risk_amount,
            "lot_size": lot_size,
            "calculated_lots": int(max_risk_amount / (net_debit * lot_size)),
            "max_lots": max_lots,
            "net_premium": net_premium,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "breakeven": breakeven,
            "buy_leg": buy_leg,
            "sell_leg": sell_leg,
            "trade_construction_success": True
        }
        
    except Exception as e:
        return {
            "error": f"Position sizing failed: {str(e)}", 
            "traceback": traceback.format_exc()
        }