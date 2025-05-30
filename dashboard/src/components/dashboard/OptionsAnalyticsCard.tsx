'use client';

import type React from 'react';
import { Sigma, ArrowRightLeft, Hourglass, Wind, TrendingUp } from 'lucide-react';
import CardWrapper from '@/components/shared/CardWrapper';
import { useDataFetching } from '@/hooks/useDataFetching';
import { SERVICE_ENDPOINTS } from '@/lib/config';
import { Skeleton } from '@/components/ui/skeleton';

// Interface matching your options API response
interface OptionsApiResponse {
  symbol: string;
  expiry: string;
  timestamp: string;
  spot_price: number;
  options_chain: Array<{
    strike: number;
    call: {
      ltp: number;
      greeks: {
        delta: number;
        gamma: number;
        theta: number;
        vega: number;
      };
    };
    put: {
      ltp: number;
      greeks: {
        delta: number;
        gamma: number;
        theta: number;
        vega: number;
      };
    };
  }>;
  portfolio_greeks: {
    net_delta: number;
    net_gamma: number;
    net_theta: number;
    net_vega: number;
  };
}

// Using available icons that are somewhat relevant
const GreekIcon = ({ greekName }: { greekName: string }) => {
  switch (greekName.toLowerCase()) {
    case 'delta': return <ArrowRightLeft className="h-4 w-4 text-accent" />; // Movement
    case 'gamma': return <TrendingUp className="h-4 w-4 text-accent" />; // Rate of change
    case 'theta': return <Hourglass className="h-4 w-4 text-accent" />; // Time decay
    case 'vega': return <Wind className="h-4 w-4 text-accent" />; // Volatility
    default: return <Sigma className="h-4 w-4 text-accent" />; // Generic
  }
};

const ValueWithGreekIcon: React.FC<{ greekName: string; label: string; value: string | number; unit?: string; className?: string }> = ({ greekName, label, value, unit, className }) => (
  <div className={`flex items-center space-x-2 text-sm ${className}`}>
    <GreekIcon greekName={greekName} />
    <span className="text-muted-foreground">{label}:</span>
    <span className="font-semibold">{value}{unit}</span>
  </div>
);

const OptionsAnalyticsCard: React.FC = () => {
  const { data, isLoading, error, isOnline, lastUpdated } = useDataFetching<OptionsApiResponse>(SERVICE_ENDPOINTS.OPTIONS_GREEKS('NIFTY'));

  if (isLoading && !data) {
    return (
      <CardWrapper title="Portfolio Greeks (NIFTY)" icon={Sigma} isLoading={true} error={null} isOnline={true} lastUpdated={null} serviceName="Options Analytics Service">
        <div className="space-y-3 p-4">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </CardWrapper>
    );
  }

  return (
    <CardWrapper
      title="Portfolio Greeks (NIFTY)"
      icon={Sigma}
      isLoading={isLoading}
      error={error}
      isOnline={isOnline}
      lastUpdated={lastUpdated}
      serviceName="Options Analytics Service"
    >
      {data && data.portfolio_greeks && (
        <div className="space-y-3">
          <ValueWithGreekIcon 
            greekName="Delta" 
            label="Portfolio Delta" 
            value={data.portfolio_greeks.net_delta.toFixed(2)} 
          />
          <ValueWithGreekIcon 
            greekName="Gamma" 
            label="Portfolio Gamma" 
            value={data.portfolio_greeks.net_gamma.toFixed(2)} 
          />
          <ValueWithGreekIcon 
            greekName="Theta" 
            label="Portfolio Theta" 
            value={data.portfolio_greeks.net_theta.toFixed(2)} 
          />
          <ValueWithGreekIcon 
            greekName="Vega" 
            label="Portfolio Vega" 
            value={data.portfolio_greeks.net_vega.toFixed(2)} 
          />

          <div className="pt-2 border-t border-border mt-3">
            <p className="text-xs text-muted-foreground">
              Spot Price: ₹{data.spot_price.toLocaleString()} | Expiry: {data.expiry}
            </p>
          </div>
        </div>
      )}
    </CardWrapper>
  );
};

export default OptionsAnalyticsCard;