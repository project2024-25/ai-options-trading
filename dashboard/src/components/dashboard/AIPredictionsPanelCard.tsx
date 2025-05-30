'use client';

import React from 'react';
import { Cpu, TrendingUp, TrendingDown, Activity, Percent, Target, Zap, BarChart3 } from 'lucide-react';
import CardWrapper from '@/components/shared/CardWrapper';
import { useDataFetching } from '@/hooks/useDataFetching';
import { SERVICE_ENDPOINTS } from '@/lib/config';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

// Interface matching your ML API response
interface MLApiResponse {
  symbol: string;
  timeframe: string;
  timestamp: string;
  prediction: {
    direction: string;
    confidence: number;
    probability_up: number;
    probability_down: number;
    expected_move: {
      "1hr": number;
      "4hr": number;
      daily: number;
    };
    target_levels: {
      resistance: number[];
      support: number[];
    };
  };
  model_features: {
    technical_score: number;
    momentum_score: number;
    volume_score: number;
    sentiment_score: number;
  };
  risk_assessment: {
    model_uncertainty: number;
    feature_importance: {
      rsi_divergence: number;
      volume_profile: number;
      macd_signal: number;
      support_resistance: number;
      vix_level: number;
    };
  };
}

const ValueWithIcon: React.FC<{ icon: React.ElementType; label: string; value: string | number; unit?: string; className?: string; badgeVariant?: "default" | "secondary" | "destructive" | "outline" | null | undefined }> = ({ icon: Icon, label, value, unit, className, badgeVariant }) => (
  <div className={`flex items-center space-x-2 text-sm ${className}`}>
    <Icon className="h-4 w-4 text-accent" />
    <span className="text-muted-foreground">{label}:</span>
    {badgeVariant ? (
      <Badge variant={badgeVariant} className="text-xs">
        {value}{unit}
      </Badge>
    ) : (
      <span className="font-semibold">{value}{unit}</span>
    )}
  </div>
);

const AIPredictionsPanelCard: React.FC = () => {
  const { data, isLoading, error, isOnline, lastUpdated } = useDataFetching<MLApiResponse>(SERVICE_ENDPOINTS.DIRECTION_PREDICTION('NIFTY'));

  if (isLoading && !data) {
    return (
      <CardWrapper title="AI Predictions (NIFTY)" icon={Cpu} isLoading={true} error={null} isOnline={true} lastUpdated={null} serviceName="AI Prediction Service">
        <div className="space-y-3 p-4">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </CardWrapper>
    );
  }
  
  if (!data || !data.prediction) {
    return (
      <CardWrapper title="AI Predictions (NIFTY)" icon={Cpu} isLoading={isLoading} error={error} isOnline={isOnline} lastUpdated={lastUpdated} serviceName="AI Prediction Service">
        <div className="space-y-3">
          <p className="text-muted-foreground">No prediction data available</p>
          {error && <p className="text-xs text-red-400">Error: {error.message}</p>}
        </div>
      </CardWrapper>
    );
  }

  const prediction = data.prediction;
  const predictionDirection = prediction.direction.toUpperCase();
  const predictionColor = predictionDirection === 'BULLISH' ? 'text-green-500' : predictionDirection === 'BEARISH' ? 'text-red-500' : 'text-muted-foreground';
  const PredictionIcon = predictionDirection === 'BULLISH' ? TrendingUp : predictionDirection === 'BEARISH' ? TrendingDown : Activity;

  // Determine market regime based on confidence and scores
  const averageScore = (data.model_features.technical_score + data.model_features.momentum_score + data.model_features.sentiment_score) / 3;
  const marketRegime = averageScore > 7.5 ? 'Strong Trend' : averageScore > 6.5 ? 'Moderate Trend' : 'Consolidation';

  return (
    <CardWrapper
      title="AI Predictions (NIFTY)"
      icon={Cpu}
      isLoading={isLoading}
      error={error}
      isOnline={isOnline}
      lastUpdated={lastUpdated}
      serviceName="AI Prediction Service"
    >
      <div className="space-y-3">
        <div className={`flex items-center text-lg font-semibold ${predictionColor}`}>
          <PredictionIcon className="h-6 w-6 mr-2" />
          Direction: {predictionDirection}
        </div>
        
        <ValueWithIcon 
          icon={Percent} 
          label="Confidence" 
          value={(prediction.confidence * 100).toFixed(1)} 
          unit="%" 
          badgeVariant={prediction.confidence > 0.7 ? 'default' : prediction.confidence > 0.6 ? 'secondary' : 'outline'}
        />
        
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-muted-foreground">Prob Up: </span>
            <span className="font-semibold text-green-400">{(prediction.probability_up * 100).toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-muted-foreground">Prob Down: </span>
            <span className="font-semibold text-red-400">{(prediction.probability_down * 100).toFixed(1)}%</span>
          </div>
        </div>

        <ValueWithIcon 
          icon={Target} 
          label="Expected Move (1hr)" 
          value={`${prediction.expected_move["1hr"]}%`}
        />

        <ValueWithIcon 
          icon={Zap} 
          label="Market Regime" 
          value={marketRegime}
          badgeVariant={marketRegime.includes('Strong') ? 'default' : marketRegime.includes('Moderate') ? 'secondary' : 'outline'}
        />

        {/* Model Scores */}
        <div className="pt-2 border-t border-border">
          <h4 className="text-sm font-medium mb-2">Model Scores:</h4>
          <div className="grid grid-cols-2 gap-1 text-xs">
            <div>
              <span className="text-muted-foreground">Technical: </span>
              <span className="font-semibold">{data.model_features.technical_score.toFixed(1)}/10</span>
            </div>
            <div>
              <span className="text-muted-foreground">Momentum: </span>
              <span className="font-semibold">{data.model_features.momentum_score.toFixed(1)}/10</span>
            </div>
            <div>
              <span className="text-muted-foreground">Volume: </span>
              <span className="font-semibold">{data.model_features.volume_score.toFixed(1)}/10</span>
            </div>
            <div>
              <span className="text-muted-foreground">Sentiment: </span>
              <span className="font-semibold">{data.model_features.sentiment_score.toFixed(1)}/10</span>
            </div>
          </div>
        </div>

        {/* Key Levels */}
        {prediction.target_levels && (
          <div className="pt-2 border-t border-border">
            <h4 className="text-sm font-medium mb-2">Key Levels:</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-muted-foreground">Resistance: </span>
                <span className="font-semibold text-red-400">
                  {prediction.target_levels.resistance.slice(0, 2).join(', ')}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Support: </span>
                <span className="font-semibold text-green-400">
                  {prediction.target_levels.support.slice(0, 2).join(', ')}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </CardWrapper>
  );
};

export default AIPredictionsPanelCard;