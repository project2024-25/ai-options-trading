'use client';

import type React from 'react';
import { Briefcase, ShieldAlert, Percent, BarChartHorizontalBig, TrendingDown } from 'lucide-react';
import CardWrapper from '@/components/shared/CardWrapper';
import { useDataFetching } from '@/hooks/useDataFetching';
import { SERVICE_ENDPOINTS } from '@/lib/config';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';

// Interface matching your risk API response
interface RiskApiResponse {
  timestamp: string;
  portfolio_summary: {
    total_value: number;
    available_margin: number;
    margin_utilization: number;
    number_of_positions: number;
  };
  risk_metrics: {
    portfolio_var_1d: {
      "95_confidence": number;
      "99_confidence": number;
      expected_shortfall: number;
    };
    max_drawdown: {
      current: number;
      historical_max: number;
      underwater_days: number;
    };
  };
  greeks_exposure: {
    portfolio_delta: number;
    portfolio_gamma: number;
    portfolio_theta: number;
    portfolio_vega: number;
  };
  risk_warnings: Array<{
    type: string;
    message: string;
    severity: string;
    recommendation: string;
  }>;
}

const ValueWithIcon: React.FC<{ icon: React.ElementType; label: string; value: string | number; unit?: string; className?: string }> = ({ icon: Icon, label, value, unit, className }) => (
  <div className={`flex items-center space-x-2 text-sm ${className}`}>
    <Icon className="h-4 w-4 text-accent" />
    <span className="text-muted-foreground">{label}:</span>
    <span className="font-semibold">{value}{unit}</span>
  </div>
);

const RiskManagementDashboardCard: React.FC = () => {
  const { data, isLoading, error, isOnline, lastUpdated } = useDataFetching<RiskApiResponse>(SERVICE_ENDPOINTS.PORTFOLIO_RISK);

  if (isLoading && !data) {
    return (
      <CardWrapper title="Risk Management" icon={Briefcase} isLoading={true} error={null} isOnline={true} lastUpdated={null} serviceName="Risk Service">
        <div className="space-y-4 p-4">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </CardWrapper>
    );
  }

  return (
    <CardWrapper
      title="Risk Management"
      icon={Briefcase}
      isLoading={isLoading}
      error={error}
      isOnline={isOnline}
      lastUpdated={lastUpdated}
      serviceName="Risk Service"
    >
      {data && data.portfolio_summary && (
        <div className="space-y-4">
          <ValueWithIcon 
            icon={Briefcase} 
            label="Portfolio Value" 
            value={`₹${data.portfolio_summary.total_value.toLocaleString()}`}
          />
          
          <ValueWithIcon 
            icon={ShieldAlert} 
            label="VaR (95%)" 
            value={`₹${Math.abs(data.risk_metrics.portfolio_var_1d["95_confidence"]).toLocaleString()}`}
          />
          
          <div>
            <ValueWithIcon 
              icon={Percent} 
              label="Margin Utilization" 
              value={`${(data.portfolio_summary.margin_utilization * 100).toFixed(1)}%`}
            />
            <Progress 
              value={data.portfolio_summary.margin_utilization * 100} 
              className="h-2 mt-1" 
            />
          </div>
          
          <ValueWithIcon 
            icon={BarChartHorizontalBig} 
            label="Active Positions" 
            value={data.portfolio_summary.number_of_positions}
          />
          
          <ValueWithIcon 
            icon={TrendingDown} 
            label="Max Drawdown" 
            value={`${data.risk_metrics.max_drawdown.current.toFixed(1)}% (${data.risk_metrics.max_drawdown.underwater_days} days)`}
          />

          {data.risk_warnings && data.risk_warnings.length > 0 && (
            <div className="pt-2 border-t border-border mt-3">
              <h4 className="text-sm font-medium mb-1 text-orange-500">Risk Warnings:</h4>
              {data.risk_warnings.slice(0, 2).map((warning, index) => (
                <p key={index} className="text-xs text-orange-400 mb-1">
                  {warning.message}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </CardWrapper>
  );
};

export default RiskManagementDashboardCard;