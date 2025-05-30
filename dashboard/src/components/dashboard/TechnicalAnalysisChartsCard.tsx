'use client';

import type React from 'react';
import { LineChart as LucideLineChart, BarChart3, TrendingUp, TrendingDown, PercentSquare } from 'lucide-react';
import CardWrapper from '@/components/shared/CardWrapper';
import { useDataFetching } from '@/hooks/useDataFetching';
import { SERVICE_ENDPOINTS } from '@/lib/config';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

// Interface matching your technical analysis API response
interface TechnicalApiResponse {
  symbol: string;
  timeframe: string;
  timestamp: string;
  indicators: {
    trend: {
      sma_9: number;
      sma_21: number;
      ema_9: number;
      ema_21: number;
      trend_direction: string;
    };
    momentum: {
      rsi_14: number;
      rsi_21: number;
      macd: {
        macd_line: number;
        signal_line: number;
        histogram: number;
        signal: string;
      };
      stochastic: {
        k_percent: number;
        d_percent: number;
        signal: string;
      };
    };
    volatility: {
      bollinger_bands: {
        upper: number;
        middle: number;
        lower: number;
        position: string;
      };
      atr_14: number;
    };
  };
  signals: {
    overall_trend: string;
    strength: number;
    confidence: number;
  };
}

const ValueWithIcon: React.FC<{ icon: React.ElementType; label: string; value: string | number; unit?: string; className?: string; badgeVariant?: "default" | "secondary" | "destructive" | "outline" | null | undefined }> = ({ icon: Icon, label, value, unit, className, badgeVariant }) => (
  <div className={`flex items-center space-x-2 text-xs ${className}`}>
    <Icon className="h-3.5 w-3.5 text-accent" />
    <span className="text-muted-foreground">{label}:</span>
    {badgeVariant ? (
      <Badge variant={badgeVariant} className="text-xs px-1 py-0">
        {value}{unit}
      </Badge>
    ) : (
      <span className="font-semibold">{value}{unit}</span>
    )}
  </div>
);

const TechnicalAnalysisChartsCard: React.FC = () => {
  const { data, isLoading, error, isOnline, lastUpdated } = useDataFetching<TechnicalApiResponse>(SERVICE_ENDPOINTS.NIFTY_INDICATORS('1hr'));

  if (isLoading && !data) {
     return (
      <CardWrapper title="Technical Analysis (NIFTY 1hr)" icon={LucideLineChart} isLoading={true} error={null} isOnline={true} lastUpdated={null} serviceName="Technical Analysis Service">
        <div className="space-y-3 p-4">
          <Skeleton className="h-40 w-full" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
      </CardWrapper>
    );
  }

  return (
    <CardWrapper
      title={`Technical Analysis (${data?.symbol || 'NIFTY'} ${data?.timeframe || '1hr'})`}
      icon={LucideLineChart}
      isLoading={isLoading}
      error={error}
      isOnline={isOnline}
      lastUpdated={lastUpdated}
      serviceName="Technical Analysis Service"
    >
      {data && data.indicators && (
        <div className="space-y-4">
          {/* Overall Signal */}
          <div className="text-center p-3 bg-muted/30 rounded-md">
            <ValueWithIcon 
              icon={TrendingUp} 
              label="Overall Trend" 
              value={data.signals.overall_trend.toUpperCase()} 
              badgeVariant={
                data.signals.overall_trend.toLowerCase() === 'bullish' ? 'default' :
                data.signals.overall_trend.toLowerCase() === 'bearish' ? 'destructive' : 'secondary'
              }
              className="justify-center"
            />
            <div className="flex justify-center space-x-4 mt-2">
              <span className="text-xs">Strength: {data.signals.strength.toFixed(1)}/10</span>
              <span className="text-xs">Confidence: {data.signals.confidence}%</span>
            </div>
          </div>

          {/* Key Indicators */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2">
            <ValueWithIcon 
              icon={LucideLineChart} 
              label="EMA 21" 
              value={data.indicators.trend.ema_21.toFixed(2)} 
            />
            <ValueWithIcon 
              icon={PercentSquare} 
              label="RSI 14" 
              value={data.indicators.momentum.rsi_14.toFixed(1)} 
              badgeVariant={
                data.indicators.momentum.rsi_14 > 70 ? 'destructive' :
                data.indicators.momentum.rsi_14 < 30 ? 'default' : 'secondary'
              }
            />
            <ValueWithIcon 
              icon={BarChart3} 
              label="MACD Signal" 
              value={data.indicators.momentum.macd.signal.replace('_', ' ').toUpperCase()} 
              badgeVariant={
                data.indicators.momentum.macd.signal.includes('bullish') ? 'default' :
                data.indicators.momentum.macd.signal.includes('bearish') ? 'destructive' : 'secondary'
              }
            />
            <ValueWithIcon 
              icon={TrendingUp} 
              label="BB Position" 
              value={data.indicators.volatility.bollinger_bands.position.replace('_', ' ').toUpperCase()} 
              badgeVariant="outline"
            />
          </div>

          {/* Support & Resistance from Bollinger Bands */}
          <div className="pt-2 border-t border-border">
            <h4 className="text-sm font-medium mb-2">Key Levels:</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-muted-foreground">BB Upper: </span>
                <span className="font-semibold text-red-400">₹{data.indicators.volatility.bollinger_bands.upper.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">BB Lower: </span>
                <span className="font-semibold text-green-400">₹{data.indicators.volatility.bollinger_bands.lower.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </CardWrapper>
  );
};

export default TechnicalAnalysisChartsCard;