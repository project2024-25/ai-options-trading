'use client';

import type React from 'react';
import { Lightbulb, ShieldCheck, BarChartBig, Activity, Layers, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import CardWrapper from '@/components/shared/CardWrapper';
import { useDataFetching } from '@/hooks/useDataFetching';
import { SERVICE_ENDPOINTS } from '@/lib/config';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

// Interface matching your strategy API response
interface StrategyApiResponse {
  symbol?: string;
  timestamp?: string;
  market_analysis?: {
    current_trend?: string;
    volatility_regime?: string;
    support_levels?: number[];
    resistance_levels?: number[];
  };
  recommended_strategy?: {
    strategy_name?: string;
    strategy_type?: string;
    confidence_score?: number;
    risk_reward_ratio?: string;
    max_profit?: number | string;
    max_loss?: number | string;
    breakeven_points?: number[];
    probability_of_profit?: number;
  };
  strategy_details?: {
    legs?: Array<{
      action?: string;
      option_type?: string;
      strike?: number;
      quantity?: number;
      premium?: number;
    }>;
    net_premium?: number;
    margin_required?: number;
  };
  market_conditions?: {
    volatility_percentile?: number;
    days_to_expiry?: number;
    expected_move?: number;
  };
  // Handle API error responses
  detail?: Array<{
    type: string;
    loc: string[];
    msg: string;
  }>;
}

const ValueWithIcon: React.FC<{ icon: React.ElementType; label: string; value: string | number; unit?: string; badgeVariant?: "default" | "secondary" | "destructive" | "outline" | null | undefined; className?: string }> = ({ icon: Icon, label, value, unit, badgeVariant, className }) => (
  <div className={`flex items-start space-x-2 text-sm ${className}`}>
    <Icon className="h-4 w-4 text-accent mt-0.5" />
    <span className="text-muted-foreground">{label}:</span>
    {badgeVariant ? <Badge variant={badgeVariant}>{value}{unit}</Badge> : <span className="font-semibold">{value}{unit}</span>}
  </div>
);

const StrategyRecommendationsCard: React.FC = () => {
  const { data, isLoading, error, isOnline, lastUpdated } = useDataFetching<StrategyApiResponse>(SERVICE_ENDPOINTS.AUTO_SELECT);

  if (isLoading && !data) {
     return (
      <CardWrapper title="Strategy Recommendation" icon={Lightbulb} isLoading={true} error={null} isOnline={true} lastUpdated={null} serviceName="Strategy Service">
        <div className="space-y-3 p-4">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </CardWrapper>
    );
  }

  // Handle API validation errors (422 responses)
  if (data && data.detail && Array.isArray(data.detail)) {
    return (
      <CardWrapper
        title="Strategy Recommendation"
        icon={Lightbulb}
        isLoading={isLoading}
        error={null}
        isOnline={false}
        lastUpdated={lastUpdated}
        serviceName="Strategy Service"
      >
        <div className="space-y-3">
          <div className="flex items-center text-orange-500">
            <AlertTriangle className="h-5 w-5 mr-2" />
            <span className="font-semibold">Service Configuration Required</span>
          </div>
          <p className="text-sm text-muted-foreground">
            The strategy service needs additional parameters to generate recommendations.
          </p>
          <div className="text-xs text-muted-foreground space-y-1">
            <p className="font-medium">Missing parameters:</p>
            {data.detail.slice(0, 3).map((err, index) => (
              <p key={index}>• {err.loc[err.loc.length - 1]}: {err.msg}</p>
            ))}
          </div>
          <div className="pt-2 border-t border-border">
            <p className="text-xs text-blue-400">
              Using default parameters: NIFTY, Bullish outlook, 65% volatility, 15 DTE, 2.5% expected move
            </p>
          </div>
        </div>
      </CardWrapper>
    );
  }

  // Handle case where service responds but no strategy data
  if (!data || !data.recommended_strategy) {
    return (
      <CardWrapper
        title="Strategy Recommendation"
        icon={Lightbulb}
        isLoading={isLoading}
        error={error}
        isOnline={isOnline}
        lastUpdated={lastUpdated}
        serviceName="Strategy Service"
      >
        <div className="space-y-3">
          <div className="flex items-center text-muted-foreground">
            <Lightbulb className="h-5 w-5 mr-2" />
            <span>No strategy recommendation available</span>
          </div>
          {error && (
            <p className="text-xs text-red-400">Error: {error.message}</p>
          )}
          {data && (
            <div className="text-xs text-muted-foreground">
              <p>Raw response: {JSON.stringify(data, null, 2).substring(0, 200)}...</p>
            </div>
          )}
        </div>
      </CardWrapper>
    );
  }

  const strategy = data.recommended_strategy;
  const marketAnalysis = data.market_analysis;

  return (
    <CardWrapper
      title="Strategy Recommendation"
      icon={Lightbulb}
      isLoading={isLoading}
      error={error}
      isOnline={isOnline}
      lastUpdated={lastUpdated}
      serviceName="Strategy Service"
    >
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-accent">
          {strategy.strategy_name || 'Unknown Strategy'} for {data.symbol || 'NIFTY'}
        </h3>
        
        {strategy.confidence_score !== undefined && (
          <ValueWithIcon 
            icon={ShieldCheck} 
            label="Confidence Score" 
            value={strategy.confidence_score.toFixed(1)} 
            unit="/100" 
          />
        )}
        
        {marketAnalysis?.volatility_regime && (
          <ValueWithIcon 
            icon={Activity} 
            label="Volatility Regime" 
            value={marketAnalysis.volatility_regime.toUpperCase()} 
            badgeVariant={
              marketAnalysis.volatility_regime.toLowerCase() === 'low' ? 'secondary' :
              marketAnalysis.volatility_regime.toLowerCase() === 'medium' ? 'default' : 'destructive'
            }
          />
        )}
        
        {strategy.risk_reward_ratio && (
          <ValueWithIcon 
            icon={BarChartBig} 
            label="Risk/Reward Ratio" 
            value={strategy.risk_reward_ratio} 
          />
        )}

        {strategy.probability_of_profit !== undefined && (
          <ValueWithIcon 
            icon={TrendingUp} 
            label="Probability of Profit" 
            value={`${strategy.probability_of_profit}%`} 
          />
        )}
        
        {data.strategy_details && (
          <div className="pt-2 border-t border-border mt-3">
            <h4 className="text-sm font-medium mb-2">Strategy Details:</h4>
            
            <div className="space-y-1">
              {strategy.max_profit !== undefined && (
                <ValueWithIcon 
                  icon={TrendingUp} 
                  label="Max Profit" 
                  value={strategy.max_profit === 'UNLIMITED' ? 'Unlimited' : `₹${Number(strategy.max_profit).toLocaleString()}`} 
                />
              )}
              
              {strategy.max_loss !== undefined && (
                <ValueWithIcon 
                  icon={TrendingDown} 
                  label="Max Loss" 
                  value={strategy.max_loss === 'UNLIMITED' ? 'Unlimited' : `₹${Number(strategy.max_loss).toLocaleString()}`} 
                />
              )}
              
              {data.strategy_details.legs && data.strategy_details.legs.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium mb-1">Legs:</p>
                  {data.strategy_details.legs.slice(0, 3).map((leg, index) => (
                    <p key={index} className="text-xs text-muted-foreground">
                      {leg.action || 'N/A'} {leg.quantity || 0} {leg.strike || 0} {leg.option_type || 'N/A'} @ ₹{leg.premium || 0}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </CardWrapper>
  );
};

export default StrategyRecommendationsCard;