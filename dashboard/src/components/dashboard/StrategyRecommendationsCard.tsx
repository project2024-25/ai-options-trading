// File: dashboard/src/components/StrategyRecommendationsCard.tsx
// Enhanced version with specific trade details

"use client";

import React, { useState, useEffect } from 'react';

interface SpecificTrade {
  strategy_name: string;
  current_spot: number;
  trade_type: string;
  market_situation: string;
  buy_contract: {
    symbol: string;
    strike: number;
    ltp: number;
    mid_price: number;
  };
  sell_contract: {
    symbol: string;
    strike: number;
    ltp: number;
    mid_price: number;
  };
  trade_details: {
    net_debit_credit: number;
    lots: number;
    lot_size: number;
    total_quantity: number;
    net_premium: number;
    max_profit: number;
    max_loss: number;
    breakeven: number;
  };
  execution_checklist: string[];
}

const StrategyRecommendationsCard: React.FC = () => {
  const [specificTrade, setSpecificTrade] = useState<SpecificTrade | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchSpecificTrade = async (): Promise<void> => {
    try {
      setLoading(true);
      
      // Call your new specific trade endpoint
      const response = await fetch(
        'http://localhost:8004/api/strategy/specific-trade-direct?symbol=NIFTY&account_size=500000'
      );
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const tradeData: SpecificTrade = await response.json();
      
      if (tradeData.error) {
        throw new Error(tradeData.error);
      }
      
      setSpecificTrade(tradeData);
      setError(null);
      setLastUpdated(new Date());
      
    } catch (err) {
      console.error('Specific trade fetch error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpecificTrade();
    
    // Refresh every 2 minutes (since this is more expensive)
    const interval = setInterval(fetchSpecificTrade, 120000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (amount: number): string => {
    return `₹${Math.round(amount).toLocaleString()}`;
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getTradeTypeColor = (tradeType: string): string => {
    return tradeType === 'DEBIT' ? 'text-orange-400' : 'text-green-400';
  };

  const getRiskRewardRatio = (): number => {
    if (!specificTrade) return 0;
    const { max_profit, max_loss } = specificTrade.trade_details;
    return max_loss > 0 ? max_profit / max_loss : 0;
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <span className="text-blue-400">🎯</span>
            <h3 className="text-lg font-semibold text-white">Specific Trade Recommendation</h3>
          </div>
          <span className="text-yellow-400 text-sm">Loading...</span>
        </div>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !specificTrade) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <span className="text-blue-400">🎯</span>
            <h3 className="text-lg font-semibold text-white">Specific Trade Recommendation</h3>
          </div>
          <span className="text-red-400 text-sm">Error</span>
        </div>
        <div className="text-red-400 text-sm">
          {error || 'No trade data available'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-blue-400">🎯</span>
          <h3 className="text-lg font-semibold text-white">Specific Trade Recommendation</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${getTradeTypeColor(specificTrade.trade_type)}`}>
            {specificTrade.trade_type}
          </span>
          <span className="text-green-400 text-sm">
            Updated {formatTime(lastUpdated)}
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {/* Strategy Header */}
        <div>
          <h4 className="text-lg font-medium text-blue-400 mb-1">
            {specificTrade.strategy_name}
          </h4>
          <p className="text-gray-300 text-sm">
            NIFTY @ {formatCurrency(specificTrade.current_spot)} • {specificTrade.market_situation}
          </p>
        </div>

        {/* Trade Legs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="bg-gray-700 rounded p-3">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-green-400 text-sm font-medium">BUY</span>
              <span className="text-gray-300 text-sm">{specificTrade.trade_details.lots} lots</span>
            </div>
            <div className="text-white font-medium">{specificTrade.buy_contract.strike} CE</div>
            <div className="text-gray-300 text-sm">{formatCurrency(specificTrade.buy_contract.mid_price)}</div>
            <div className="text-xs text-gray-400">{specificTrade.buy_contract.symbol}</div>
          </div>
          
          <div className="bg-gray-700 rounded p-3">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-red-400 text-sm font-medium">SELL</span>
              <span className="text-gray-300 text-sm">{specificTrade.trade_details.lots} lots</span>
            </div>
            <div className="text-white font-medium">{specificTrade.sell_contract.strike} CE</div>
            <div className="text-gray-300 text-sm">{formatCurrency(specificTrade.sell_contract.mid_price)}</div>
            <div className="text-xs text-gray-400">{specificTrade.sell_contract.symbol}</div>
          </div>
        </div>

        {/* Trade Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-gray-400 text-xs">Investment</div>
            <div className="text-white font-medium">{formatCurrency(specificTrade.trade_details.net_premium)}</div>
          </div>
          
          <div className="text-center">
            <div className="text-gray-400 text-xs">Max Profit</div>
            <div className="text-green-400 font-medium">{formatCurrency(specificTrade.trade_details.max_profit)}</div>
          </div>
          
          <div className="text-center">
            <div className="text-gray-400 text-xs">Max Loss</div>
            <div className="text-red-400 font-medium">{formatCurrency(specificTrade.trade_details.max_loss)}</div>
          </div>
          
          <div className="text-center">
            <div className="text-gray-400 text-xs">Breakeven</div>
            <div className="text-blue-400 font-medium">{specificTrade.trade_details.breakeven.toFixed(0)}</div>
          </div>
        </div>

        {/* Risk-Reward Analysis */}
        <div className="bg-gray-700 rounded p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-300 text-sm">Risk-Reward Analysis</span>
            <span className="text-blue-400 text-sm font-medium">
              1:{getRiskRewardRatio().toFixed(2)}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-gray-400">
              Quantity: <span className="text-white">{specificTrade.trade_details.total_quantity}</span>
            </div>
            <div className="text-gray-400">
              Spread: <span className="text-white">{specificTrade.sell_contract.strike - specificTrade.buy_contract.strike}pts</span>
            </div>
            <div className="text-gray-400">
              Account Risk: <span className="text-white">{((specificTrade.trade_details.max_loss / 500000) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Quick Execution Checklist */}
        <div className="border-t border-gray-700 pt-3">
          <div className="flex items-center justify-between">
            <h5 className="text-sm font-medium text-gray-300">Quick Actions</h5>
            <button 
              onClick={fetchSpecificTrade}
              className="text-blue-400 hover:text-blue-300 text-xs"
            >
              Refresh
            </button>
          </div>
          <div className="mt-2 space-y-1">
            {specificTrade.execution_checklist.slice(0, 3).map((item, index) => (
              <div key={index} className="text-xs text-gray-400 flex items-start">
                <span className="text-blue-400 mr-1">•</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyRecommendationsCard;