'use client';

import type React from 'react';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';
import CardWrapper from '@/components/shared/CardWrapper';
import { useDataFetching } from '@/hooks/useDataFetching';
import { SERVICE_ENDPOINTS } from '@/lib/config';
import { Skeleton } from '@/components/ui/skeleton';

// Simple interface that matches exactly what we see in the API
interface ApiResponse {
  success: boolean;
  data: {
    symbol: string;
    ltp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    change: number;
    volume: number;
    oi: number;
    timestamp: string;
    instrument_token: number;
  };
  source: string;
  timestamp: string;
}

const MarketDataDisplay: React.FC<{
  data: ApiResponse | null;
  isLoading: boolean;
  error: any;
  title: string;
}> = ({ data, isLoading, error, title }) => {
  
  if (isLoading && !data) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-1/3" />
      </div>
    );
  }

  // Debug logging
  console.log(`${title} received data:`, data);

  if (!data || !data.success || !data.data) {
    return (
      <div className="space-y-2">
        <h3 className="text-lg sm:text-xl font-semibold">{title}</h3>
        <p className="text-muted-foreground">No data available</p>
        {error && (
          <p className="text-xs text-red-500">Error: {error.message}</p>
        )}
        {data && (
          <p className="text-xs text-muted-foreground">
            Debug: {JSON.stringify(data, null, 2).substring(0, 200)}...
          </p>
        )}
      </div>
    );
  }

  const marketData = data.data;
  const price = marketData.ltp;
  const change = marketData.change;
  const changePercent = marketData.close !== 0 ? (change / marketData.close) * 100 : 0;
  const trend = change > 0 ? 'BULLISH' : change < 0 ? 'BEARISH' : 'NEUTRAL';

  const TrendIcon = trend === 'BULLISH' ? TrendingUp : trend === 'BEARISH' ? TrendingDown : Minus;
  const trendColor = trend === 'BULLISH' ? 'text-green-500' : trend === 'BEARISH' ? 'text-red-500' : 'text-muted-foreground';

  return (
    <div className="space-y-2">
      <h3 className="text-lg sm:text-xl font-semibold">{marketData.symbol}</h3>
      <p className={`text-2xl sm:text-3xl font-bold ${trendColor}`}>
        ₹{price.toLocaleString()}
      </p>
      <div className={`flex items-center text-sm ${trendColor}`}>
        <TrendIcon className="h-4 w-4 mr-1" />
        <span>
          {change > 0 ? '+' : ''}{change.toFixed(2)} ({changePercent > 0 ? '+' : ''}{changePercent.toFixed(2)}%)
        </span>
      </div>
      <p className="text-xs text-muted-foreground">Trend: {trend}</p>
      <div className="text-xs text-muted-foreground grid grid-cols-2 gap-1">
        <div>Open: ₹{marketData.open.toFixed(2)}</div>
        <div>High: ₹{marketData.high.toFixed(2)}</div>
        <div>Low: ₹{marketData.low.toFixed(2)}</div>
        <div>Close: ₹{marketData.close.toFixed(2)}</div>
      </div>
    </div>
  );
};

const MarketOverviewCard: React.FC = () => {
  const nifty = useDataFetching<ApiResponse>(SERVICE_ENDPOINTS.NIFTY_SNAPSHOT);
  const bankNifty = useDataFetching<ApiResponse>(SERVICE_ENDPOINTS.BANKNIFTY_SNAPSHOT);

  const isLoading = nifty.isLoading || bankNifty.isLoading;
  const isOnline = nifty.isOnline && bankNifty.isOnline;
  const error = nifty.error || bankNifty.error; 
  const lastUpdated = Math.max(nifty.lastUpdated || 0, bankNifty.lastUpdated || 0) || null;

  return (
    <CardWrapper
      title="Market Overview"
      icon={Activity}
      isLoading={isLoading}
      error={error}
      isOnline={isOnline}
      lastUpdated={lastUpdated}
      serviceName="Market Data Service"
      contentClassName="grid grid-cols-1 md:grid-cols-2 gap-6"
    >
      <MarketDataDisplay data={nifty.data} isLoading={nifty.isLoading} error={nifty.error} title="NIFTY" />
      <MarketDataDisplay data={bankNifty.data} isLoading={bankNifty.isLoading} error={bankNifty.error} title="BANKNIFTY" />
    </CardWrapper>
  );
};

export default MarketOverviewCard;