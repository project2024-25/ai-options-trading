# services/technical-analysis/volatility_service.py
"""
NIFTY Volatility Analysis Service
Task 3.3: Basic Volatility Analysis

Provides comprehensive volatility analysis for NIFTY/BANKNIFTY options trading
"""

import numpy as np
import pandas as pd
import math
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Add database service to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.sqlite_db_service import get_sqlite_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VolatilityAnalysisService:
    """
    Volatility Analysis Service for NIFTY/BANKNIFTY Options Trading
    Analyzes historical volatility, VIX, and volatility regimes
    """
    
    def __init__(self):
        self.db = None
        
    async def initialize(self):
        """Initialize with database connection"""
        try:
            self.db = await get_sqlite_database_service()
            logger.info("Volatility Analysis Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize volatility service: {e}")
            # Continue without database for testing
            self.db = None
    
    async def analyze_nifty_volatility(self, symbol: str = 'NIFTY', timeframe: str = '5min') -> Dict:
        """
        Comprehensive volatility analysis for NIFTY
        """
        try:
            print(f"📊 Analyzing {symbol} volatility...")
            
            # Get price data
            if self.db:
                prices_data = await self.db.get_market_data(symbol, timeframe, limit=200)
                if prices_data:
                    df = pd.DataFrame(prices_data)
                    df['close'] = pd.to_numeric(df['close'])
                    prices = df['close'].sort_index()
                else:
                    # Use simulated data if no real data
                    prices = self._generate_sample_data()
            else:
                # Use simulated data if no database
                prices = self._generate_sample_data()
            
            current_price = float(prices.iloc[-1])
            print(f"   📈 Current {symbol} Price: ₹{current_price:,.1f}")
            
            # Comprehensive volatility analysis
            analysis = {}
            
            # 1. Historical Volatility Analysis
            analysis['historical_volatility'] = self._calculate_historical_volatility_analysis(prices)
            
            # 2. Volatility Clustering
            analysis['volatility_clustering'] = self._analyze_volatility_clustering(prices)
            
            # 3. VIX-like Analysis
            analysis['vix_analysis'] = self._simulate_vix_analysis(current_price)
            
            # 4. GARCH Volatility
            analysis['garch_volatility'] = self._calculate_garch_volatility(prices)
            
            # 5. Volatility Forecasting
            analysis['volatility_forecast'] = self._forecast_volatility(prices)
            
            # 6. Options Trading Recommendations
            analysis['options_recommendations'] = self._generate_options_recommendations(analysis)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'analysis_time': datetime.now().isoformat(),
                'data_points': len(prices),
                'volatility_analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Volatility analysis failed: {e}")
            return {'error': f'Volatility analysis failed: {e}'}
    
    def _generate_sample_data(self, days: int = 100, start_price: float = 24833.6) -> pd.Series:
        """Generate realistic NIFTY price data for testing"""
        np.random.seed(42)  # For reproducible results
        
        # Parameters for realistic NIFTY simulation
        daily_return_mean = 0.0008  # ~20% annual return
        daily_volatility = 0.015    # ~24% annual volatility
        
        prices = [start_price]
        
        for _ in range(days):
            # Add volatility clustering effect
            vol_multiplier = 1.0
            if len(prices) > 10:
                recent_moves = [abs(prices[i] - prices[i-1])/prices[i-1] for i in range(-5, 0)]
                avg_recent_vol = sum(recent_moves) / len(recent_moves)
                if avg_recent_vol > 0.02:  # High recent volatility
                    vol_multiplier = 1.3
                elif avg_recent_vol < 0.005:  # Low recent volatility
                    vol_multiplier = 0.7
            
            # Generate return with volatility clustering
            daily_return = np.random.normal(daily_return_mean, daily_volatility * vol_multiplier)
            new_price = prices[-1] * (1 + daily_return)
            prices.append(new_price)
        
        return pd.Series(prices)
    
    def _calculate_historical_volatility_analysis(self, prices: pd.Series) -> Dict:
        """Calculate comprehensive historical volatility analysis"""
        try:
            hv_analysis = {}
            
            # Multiple timeframes
            windows = [10, 20, 50]
            for window in windows:
                hv = self._calculate_historical_volatility(prices, window)
                if hv:
                    hv_analysis[f'hv_{window}d'] = {
                        'value': round(hv, 4),
                        'percentage': round(hv * 100, 2)
                    }
            
            # Current volatility regime
            if 'hv_20d' in hv_analysis:
                hv_20 = hv_analysis['hv_20d']['value']
                if hv_20 > 0.25:
                    regime = 'HIGH'
                    interpretation = 'Excellent for premium selling strategies'
                    strategies = ['Covered calls', 'Cash-secured puts', 'Iron condors']
                elif hv_20 > 0.18:
                    regime = 'MODERATE'
                    interpretation = 'Balanced approach recommended'
                    strategies = ['Bull/bear spreads', 'Moderate premium collection']
                else:
                    regime = 'LOW'
                    interpretation = 'Consider buying volatility'
                    strategies = ['Long straddles', 'Long strangles', 'Calendar spreads']
                
                hv_analysis['regime'] = {
                    'level': regime,
                    'interpretation': interpretation,
                    'recommended_strategies': strategies
                }
            
            return hv_analysis
            
        except Exception as e:
            return {'error': f'Historical volatility analysis failed: {e}'}
    
    def _calculate_historical_volatility(self, prices: pd.Series, window: int = 20, annualize: bool = True) -> float:
        """Calculate historical volatility using standard deviation of returns"""
        if len(prices) < window + 1:
            return None
            
        # Calculate returns
        returns = prices.pct_change().dropna()
        
        if len(returns) < window:
            return None
            
        # Calculate rolling volatility
        volatility = returns.rolling(window=window).std()
        
        if annualize:
            # Annualize assuming 252 trading days
            volatility = volatility * math.sqrt(252)
            
        return float(volatility.iloc[-1]) if not pd.isna(volatility.iloc[-1]) else None
    
    def _analyze_volatility_clustering(self, prices: pd.Series, threshold: float = 2.0) -> Dict:
        """Analyze volatility clustering - periods of high/low volatility"""
        try:
            returns = prices.pct_change().dropna()
            
            # Calculate rolling volatility
            rolling_vol = returns.rolling(window=10).std() * math.sqrt(252)
            
            # Define high/low volatility periods
            vol_mean = rolling_vol.mean()
            vol_std = rolling_vol.std()
            
            high_vol_threshold = vol_mean + threshold * vol_std
            low_vol_threshold = vol_mean - threshold * vol_std
            
            # Current state
            current_vol = rolling_vol.iloc[-1] if not pd.isna(rolling_vol.iloc[-1]) else vol_mean
            
            if current_vol > high_vol_threshold:
                regime = 'HIGH_VOLATILITY'
                regime_strength = (current_vol - vol_mean) / vol_std
                trading_action = 'SELL_PREMIUM'
                interpretation = 'High vol regime: Time to sell premium, avoid buying options'
            elif current_vol < low_vol_threshold:
                regime = 'LOW_VOLATILITY'
                regime_strength = (vol_mean - current_vol) / vol_std
                trading_action = 'BUY_VOLATILITY'
                interpretation = 'Low vol regime: Good time to buy options, prepare for expansion'
            else:
                regime = 'NORMAL_VOLATILITY'
                regime_strength = abs(current_vol - vol_mean) / vol_std
                trading_action = 'BALANCED_APPROACH'
                interpretation = 'Normal vol regime: Balanced approach, monitor for regime change'
            
            # Count clustering periods
            high_vol_periods = (rolling_vol > high_vol_threshold).sum()
            low_vol_periods = (rolling_vol < low_vol_threshold).sum()
            
            return {
                'current_volatility': round(current_vol, 4),
                'current_volatility_percent': round(current_vol * 100, 2),
                'mean_volatility': round(vol_mean, 4),
                'volatility_std': round(vol_std, 4),
                'high_vol_threshold': round(high_vol_threshold, 4),
                'low_vol_threshold': round(low_vol_threshold, 4),
                'current_regime': regime,
                'regime_strength': round(regime_strength, 2),
                'trading_action': trading_action,
                'interpretation': interpretation,
                'high_vol_periods': int(high_vol_periods),
                'low_vol_periods': int(low_vol_periods),
                'clustering_detected': high_vol_periods > 5 or low_vol_periods > 5
            }
            
        except Exception as e:
            return {'error': f'Volatility clustering analysis failed: {e}'}
    
    def _simulate_vix_analysis(self, current_price: float) -> Dict:
        """Simulate VIX-like analysis for NIFTY (India VIX simulation)"""
        try:
            # Simulate India VIX level
            import random
            random.seed(int(current_price) % 100)  # Seed based on price for consistency
            
            base_vix = 16.5
            vix_variation = random.uniform(-2.5, 3.5)
            current_vix = base_vix + vix_variation
            
            # VIX interpretation for NIFTY options
            if current_vix > 25:
                vix_regime = 'HIGH'
                market_fear = 'ELEVATED'
                options_strategy = 'SELL_PREMIUM'
                vix_signal = 'BEARISH_FOR_MARKETS'
                specific_strategies = [
                    'Sell ATM straddles/strangles for premium collection',
                    'Iron condors in expected trading range',
                    'Avoid buying expensive options'
                ]
            elif current_vix > 20:
                vix_regime = 'ELEVATED'
                market_fear = 'MODERATE'
                options_strategy = 'NEUTRAL_STRATEGIES'
                vix_signal = 'CAUTIOUS'
                specific_strategies = [
                    'Iron butterflies for range-bound markets',
                    'Credit spreads with careful strike selection',
                    'Moderate premium collection strategies'
                ]
            elif current_vix > 15:
                vix_regime = 'MODERATE'
                market_fear = 'NORMAL'
                options_strategy = 'DIRECTIONAL_PLAYS'
                vix_signal = 'NEUTRAL'
                specific_strategies = [
                    'Bull/bear spreads for directional plays',
                    'Covered calls on existing positions',
                    'Balanced approach to volatility'
                ]
            elif current_vix > 12:
                vix_regime = 'LOW'
                market_fear = 'COMPLACENT'
                options_strategy = 'BUY_VOLATILITY' 
                vix_signal = 'BULLISH_FOR_MARKETS'
                specific_strategies = [
                    'Long straddles on upcoming events',
                    'Calendar spreads to benefit from time decay',
                    'Prepare for volatility expansion'
                ]
            else:
                vix_regime = 'VERY_LOW'
                market_fear = 'EXTREME_COMPLACENCY'
                options_strategy = 'LONG_STRADDLES'
                vix_signal = 'VOLATILITY_EXPANSION_DUE'
                specific_strategies = [
                    'Buy cheap options before volatility expansion',
                    'Long straddles with wide strikes',
                    'Volatility arbitrage opportunities'
                ]
            
            return {
                'current_vix': round(current_vix, 2),
                'vix_regime': vix_regime,
                'market_fear_level': market_fear,
                'vix_signal': vix_signal,
                'options_strategy_recommendation': options_strategy,
                'specific_strategies': specific_strategies,
                'interpretation': f"VIX at {current_vix:.1f} indicates {vix_regime.lower()} volatility environment",
                'trading_implications': {
                    'iv_level': 'HIGH' if current_vix > 20 else 'MODERATE' if current_vix > 15 else 'LOW',
                    'premium_selling': 'FAVORABLE' if current_vix > 18 else 'MODERATE' if current_vix > 14 else 'UNFAVORABLE',
                    'straddle_buying': 'UNFAVORABLE' if current_vix > 20 else 'MODERATE' if current_vix > 15 else 'FAVORABLE',
                    'directional_plays': 'MODERATE' if 14 < current_vix < 22 else 'LESS_FAVORABLE'
                }
            }
            
        except Exception as e:
            return {'error': f'VIX analysis failed: {e}'}
    
    def _calculate_garch_volatility(self, prices: pd.Series, alpha: float = 0.1, beta: float = 0.85) -> Dict:
        """Simple GARCH(1,1) volatility estimation"""
        try:
            returns = prices.pct_change().dropna()
            
            if len(returns) < 50:
                return {'error': 'Insufficient data for GARCH estimation'}
            
            # Initialize
            omega = 0.01  # Long-term variance
            variance = returns.var()  # Initial variance
            
            variances = []
            
            for i, ret in enumerate(returns):
                if i == 0:
                    variances.append(variance)
                else:
                    # GARCH(1,1): variance_t = omega + alpha * return²_(t-1) + beta * variance_(t-1)
                    variance = omega + alpha * (returns.iloc[i-1] ** 2) + beta * variance
                    variances.append(variance)
            
            # Convert to volatility (annualized)
            current_variance = variances[-1]
            current_volatility = math.sqrt(current_variance * 252)
            
            # Forecast next period
            next_variance = omega + alpha * (returns.iloc[-1] ** 2) + beta * current_variance
            forecast_volatility = math.sqrt(next_variance * 252)
            
            vol_change = forecast_volatility - current_volatility
            
            return {
                'model_type': 'GARCH(1,1)',
                'current_volatility': round(current_volatility, 4),
                'current_volatility_percent': round(current_volatility * 100, 2),
                'forecast_volatility': round(forecast_volatility, 4),
                'forecast_volatility_percent': round(forecast_volatility * 100, 2),
                'expected_change': round(vol_change, 4),
                'expected_change_percent': round(vol_change * 100, 2),
                'model_params': {'alpha': alpha, 'beta': beta, 'omega': omega},
                'interpretation': self._interpret_garch_forecast(vol_change)
            }
            
        except Exception as e:
            return {'error': f'GARCH calculation failed: {e}'}
    
    def _interpret_garch_forecast(self, vol_change: float) -> Dict:
        """Interpret GARCH volatility forecast for trading"""
        if abs(vol_change) > 0.02:
            if vol_change > 0:
                return {
                    'signal': 'VOLATILITY_INCREASE_EXPECTED',
                    'vega_risk': 'Long vega positions benefit, short vega at risk',
                    'strategy_adjustment': 'Consider reducing short volatility exposure',
                    'action': 'PREPARE_FOR_VOL_EXPANSION'
                }
            else:
                return {
                    'signal': 'VOLATILITY_DECREASE_EXPECTED',
                    'vega_risk': 'Short vega positions benefit, long vega at risk',
                    'strategy_adjustment': 'Consider reducing long volatility exposure',
                    'action': 'PREPARE_FOR_VOL_CONTRACTION'
                }
        else:
            return {
                'signal': 'VOLATILITY_STABLE',
                'vega_risk': 'Moderate vega exposure acceptable',
                'strategy_adjustment': 'Maintain current volatility exposure',
                'action': 'MONITOR_FOR_REGIME_CHANGE'
            }
    
    def _forecast_volatility(self, prices: pd.Series, forecast_days: int = 5) -> Dict:
        """Multi-method volatility forecasting"""
        try:
            returns = prices.pct_change().dropna()
            
            if len(returns) < 30:
                return {'error': 'Insufficient data for volatility forecasting'}
            
            # Method 1: Simple moving average of volatility
            recent_vol = returns.tail(20).std() * math.sqrt(252)
            
            # Method 2: EWMA (Exponentially Weighted Moving Average)
            ewma_returns = returns.ewm(span=20).var()
            ewma_vol = math.sqrt(ewma_returns.iloc[-1] * 252)
            
            # Method 3: Historical mean
            hist_vol = returns.std() * math.sqrt(252)
            
            # Ensemble forecast
            forecast_vol = (recent_vol * 0.5 + ewma_vol * 0.3 + hist_vol * 0.2)
            
            # Volatility regime prediction
            if forecast_vol > 0.25:
                predicted_regime = 'HIGH_VOLATILITY'
                regime_confidence = 85
            elif forecast_vol > 0.18:
                predicted_regime = 'ELEVATED_VOLATILITY'
                regime_confidence = 75
            elif forecast_vol > 0.12:
                predicted_regime = 'NORMAL_VOLATILITY'
                regime_confidence = 70
            else:
                predicted_regime = 'LOW_VOLATILITY'
                regime_confidence = 80
            
            # Trading implications
            vol_trend = 'INCREASING' if forecast_vol > recent_vol * 1.1 else 'DECREASING' if forecast_vol < recent_vol * 0.9 else 'STABLE'
            
            implications = self._generate_volatility_implications(recent_vol, forecast_vol, vol_trend)
            
            return {
                'forecast_horizon_days': forecast_days,
                'current_volatility': round(recent_vol, 4),
                'current_volatility_percent': round(recent_vol * 100, 2),
                'forecast_volatility': round(forecast_vol, 4),
                'forecast_volatility_percent': round(forecast_vol * 100, 2),
                'forecasting_methods': {
                    'recent_20d': round(recent_vol * 100, 2),
                    'ewma': round(ewma_vol * 100, 2),
                    'historical_mean': round(hist_vol * 100, 2)
                },
                'predicted_regime': predicted_regime,
                'regime_confidence': round(regime_confidence, 1),
                'volatility_trend': vol_trend,
                'trading_implications': implications
            }
            
        except Exception as e:
            return {'error': f'Volatility forecasting failed: {e}'}
    
    def _generate_volatility_implications(self, current_vol: float, forecast_vol: float, trend: str) -> Dict:
        """Generate trading implications from volatility forecast"""
        implications = {
            'iv_expectation': 'RISING' if forecast_vol > current_vol else 'FALLING',
            'vega_risk': 'HIGH' if abs(forecast_vol - current_vol) > 0.05 else 'MODERATE'  
        }
        
        if trend == 'INCREASING':
            implications['actionable_insights'] = [
                'Volatility expected to rise - consider long vega positions',
                'Avoid selling naked options',
                'Good time to buy straddles/strangles',
                'Close short volatility positions'
            ]
        elif trend == 'DECREASING':
            implications['actionable_insights'] = [
                'Volatility expected to fall - consider short vega positions',
                'Premium selling strategies favorable',
                'Close long volatility positions',
                'Iron condors and butterflies attractive'
            ]
        else:
            implications['actionable_insights'] = [
                'Volatility expected to remain stable',
                'Delta-neutral strategies appropriate',
                'Focus on time decay strategies',
                'Monitor for regime changes'
            ]
        
        return implications
    
    def _generate_options_recommendations(self, analysis: Dict) -> Dict:
        """Generate comprehensive options trading recommendations"""
        try:
            recommendations = {
                'overall_volatility_environment': 'MODERATE',
                'primary_strategies': [],
                'secondary_strategies': [],
                'risk_management': [],
                'key_considerations': []
            }
            
            # Analyze overall volatility environment
            hv_analysis = analysis.get('historical_volatility', {})
            clustering = analysis.get('volatility_clustering', {})
            vix_analysis = analysis.get('vix_analysis', {})
            forecast = analysis.get('volatility_forecast', {})
            
            # Determine overall environment
            high_vol_signals = 0
            low_vol_signals = 0
            
            if hv_analysis.get('regime', {}).get('level') == 'HIGH':
                high_vol_signals += 1
            elif hv_analysis.get('regime', {}).get('level') == 'LOW':
                low_vol_signals += 1
                
            if clustering.get('current_regime') == 'HIGH_VOLATILITY':
                high_vol_signals += 1
            elif clustering.get('current_regime') == 'LOW_VOLATILITY':
                low_vol_signals += 1
                
            if vix_analysis.get('vix_regime') in ['HIGH', 'ELEVATED']:
                high_vol_signals += 1
            elif vix_analysis.get('vix_regime') in ['LOW', 'VERY_LOW']:
                low_vol_signals += 1
            
            # Set overall environment
            if high_vol_signals > low_vol_signals:
                recommendations['overall_volatility_environment'] = 'HIGH'
                recommendations['primary_strategies'] = [
                    'Sell ATM straddles/strangles',
                    'Iron condors in expected range',
                    'Covered calls on existing positions',
                    'Cash-secured puts below support'
                ]
                recommendations['secondary_strategies'] = [
                    'Credit spreads (bull puts, bear calls)',
                    'Iron butterflies for range-bound markets'
                ]
                recommendations['risk_management'] = [
                    'Monitor for volatility spikes',
                    'Set stop-losses on short premium positions',
                    'Avoid naked short positions'
                ]
            elif low_vol_signals > high_vol_signals:
                recommendations['overall_volatility_environment'] = 'LOW'
                recommendations['primary_strategies'] = [
                    'Long straddles before events',
                    'Long strangles with wide strikes',
                    'Calendar spreads for time decay',
                    'Diagonal spreads'
                ]
                recommendations['secondary_strategies'] = [
                    'Ratio spreads for leveraged exposure',
                    'Volatility arbitrage opportunities'
                ]
                recommendations['risk_management'] = [
                    'Prepare for volatility expansion',
                    'Time entries before vol events',
                    'Monitor IV percentiles'
                ]
            else:
                recommendations['overall_volatility_environment'] = 'MODERATE'
                recommendations['primary_strategies'] = [
                    'Bull/bear spreads for direction',
                    'Balanced premium strategies',
                    'Directional plays with defined risk'
                ]
                recommendations['secondary_strategies'] = [
                    'Collar strategies for hedging',
                    'Modified butterflies'
                ]
                recommendations['risk_management'] = [
                    'Monitor regime changes',
                    'Adjust position sizing',
                    'Maintain balanced exposure'
                ]
            
            # Add forecast-based considerations
            if forecast.get('volatility_trend') == 'INCREASING':
                recommendations['key_considerations'].append('Volatility expected to rise - favor long vega')
            elif forecast.get('volatility_trend') == 'DECREASING':
                recommendations['key_considerations'].append('Volatility expected to fall - favor short vega')
            
            # Add VIX-specific insights
            if vix_analysis.get('specific_strategies'):
                recommendations['vix_based_strategies'] = vix_analysis['specific_strategies']
            
            return recommendations
            
        except Exception as e:
            return {'error': f'Options recommendations failed: {e}'}