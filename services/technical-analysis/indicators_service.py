# services/technical-analysis/indicators_service.py
import pandas as pd
import numpy as np
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Add database service to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.sqlite_db_service import get_sqlite_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    def __init__(self):
        self.db = None
        
    async def initialize(self):
        """Initialize with database connection"""
        self.db = await get_sqlite_database_service()
        logger.info("Technical Analysis Service initialized (Pandas-only version)")
    
    async def analyze_nifty_live_data(self) -> Dict:
        """Analyze your live ₹24,833.6 NIFTY data with technical indicators"""
        
        if not self.db:
            await self.initialize()
        
        print("📊 Analyzing live NIFTY data with technical indicators...")
        
        # Get your stored NIFTY data
        candles = await self.db.get_market_data('NIFTY', '5min', limit=50)
        
        if not candles:
            return {'error': 'No NIFTY data found'}
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Ensure numeric columns
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        current_price = float(df['close'].iloc[-1])
        
        print(f"   📈 Current NIFTY Price: ₹{current_price}")
        print(f"   📊 Analyzing {len(df)} data points...")
        
        # Calculate technical indicators
        analysis = {}
        
        # 1. RSI (Relative Strength Index)
        analysis['rsi'] = self.calculate_rsi(df['close'])
        
        # 2. MACD
        analysis['macd'] = self.calculate_macd(df['close'])
        
        # 3. Bollinger Bands
        analysis['bollinger_bands'] = self.calculate_bollinger_bands(df['close'])
        
        # 4. Moving Averages
        analysis['moving_averages'] = self.calculate_moving_averages(df['close'])
        
        # 5. Volume Analysis
        analysis['volume_analysis'] = self.analyze_volume(df)
        
        # 6. Support/Resistance
        analysis['support_resistance'] = self.find_support_resistance(df)
        
        # 7. Overall Signal
        analysis['overall_signal'] = self.generate_overall_signal(analysis, current_price)
        
        return {
            'symbol': 'NIFTY',
            'current_price': current_price,
            'analysis_time': datetime.now().isoformat(),
            'data_points': len(df),
            'technical_analysis': analysis
        }
    
    def calculate_rsi(self, close_prices: pd.Series, period: int = 14) -> Dict:
        """Calculate RSI using pandas for your NIFTY data"""
        try:
            if len(close_prices) < period + 1:
                return {'error': f'Need at least {period + 1} data points for RSI'}
            
            # Calculate price changes
            delta = close_prices.diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses
            avg_gains = gains.rolling(window=period).mean()
            avg_losses = losses.rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = float(rsi.iloc[-1])
            
            # RSI interpretation for NIFTY trading
            if current_rsi > 70:
                signal = 'OVERBOUGHT'
                action = 'CONSIDER_SELLING_CALLS'
                strength = 'STRONG'
            elif current_rsi > 60:
                signal = 'STRONG_BULLISH'
                action = 'HOLD_LONG_POSITIONS'
                strength = 'MODERATE'
            elif current_rsi > 50:
                signal = 'BULLISH'
                action = 'CONSIDER_BUYING_CALLS'
                strength = 'WEAK'
            elif current_rsi > 40:
                signal = 'BEARISH'
                action = 'CONSIDER_BUYING_PUTS'
                strength = 'WEAK'
            elif current_rsi > 30:
                signal = 'STRONG_BEARISH'
                action = 'HOLD_SHORT_POSITIONS'
                strength = 'MODERATE'
            else:
                signal = 'OVERSOLD'
                action = 'CONSIDER_SELLING_PUTS'
                strength = 'STRONG'
            
            return {
                'current_rsi': round(current_rsi, 2),
                'signal': signal,
                'action': action,
                'strength': strength,
                'interpretation': f"RSI {current_rsi:.1f} indicates {signal.lower().replace('_', ' ')} conditions for NIFTY"
            }
            
        except Exception as e:
            return {'error': f'RSI calculation failed: {e}'}
    
    def calculate_macd(self, close_prices: pd.Series, fast=12, slow=26, signal_period=9) -> Dict:
        """Calculate MACD using pandas for trend analysis"""
        try:
            if len(close_prices) < slow:
                return {'error': f'Need at least {slow} data points for MACD'}
            
            # Calculate EMAs
            ema_fast = close_prices.ewm(span=fast).mean()
            ema_slow = close_prices.ewm(span=slow).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            current_hist = float(histogram.iloc[-1])
            
            # Detect crossovers
            prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0
            
            # MACD interpretation for NIFTY options trading
            if current_macd > current_signal:
                if prev_hist <= 0 and current_hist > 0:
                    signal = 'BULLISH_CROSSOVER'
                    action = 'STRONG_BUY_CALLS'
                    strength = 'VERY_STRONG'
                else:
                    signal = 'BULLISH'
                    action = 'CONSIDER_LONG_POSITIONS'
                    strength = 'MODERATE'
            else:
                if prev_hist >= 0 and current_hist < 0:
                    signal = 'BEARISH_CROSSOVER'
                    action = 'STRONG_BUY_PUTS'
                    strength = 'VERY_STRONG'
                else:
                    signal = 'BEARISH'
                    action = 'CONSIDER_SHORT_POSITIONS'
                    strength = 'MODERATE'
            
            return {
                'macd_line': round(current_macd, 4),
                'signal_line': round(current_signal, 4),
                'histogram': round(current_hist, 4),
                'signal': signal,
                'action': action,
                'strength': strength,
                'crossover_detected': 'CROSSOVER' in signal,
                'interpretation': f"MACD shows {signal.lower().replace('_', ' ')} momentum for NIFTY"
            }
            
        except Exception as e:
            return {'error': f'MACD calculation failed: {e}'}
    
    def calculate_bollinger_bands(self, close_prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict:
        """Calculate Bollinger Bands using pandas for volatility analysis"""
        try:
            if len(close_prices) < period:
                return {'error': f'Need at least {period} data points for Bollinger Bands'}
            
            # Calculate moving average (middle band)
            sma = close_prices.rolling(window=period).mean()
            
            # Calculate standard deviation
            std = close_prices.rolling(window=period).std()
            
            # Calculate bands
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            current_price = float(close_prices.iloc[-1])
            bb_upper = float(upper_band.iloc[-1])
            bb_middle = float(sma.iloc[-1])
            bb_lower = float(lower_band.iloc[-1])
            
            # Bollinger Band position analysis for NIFTY options
            price_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            
            if current_price > bb_upper:
                position = 'ABOVE_UPPER_BAND'
                signal = 'OVERBOUGHT'
                action = 'SELL_CALLS_OR_BUY_PUTS'
                strength = 'STRONG'
            elif current_price < bb_lower:
                position = 'BELOW_LOWER_BAND'
                signal = 'OVERSOLD'
                action = 'SELL_PUTS_OR_BUY_CALLS'
                strength = 'STRONG'
            elif price_position > 0.7:
                position = 'UPPER_BAND_APPROACH'
                signal = 'APPROACHING_RESISTANCE'
                action = 'PREPARE_FOR_REVERSAL'
                strength = 'MODERATE'
            elif price_position < 0.3:
                position = 'LOWER_BAND_APPROACH'
                signal = 'APPROACHING_SUPPORT'
                action = 'PREPARE_FOR_BOUNCE'
                strength = 'MODERATE'
            else:
                position = 'MIDDLE_RANGE'
                signal = 'NEUTRAL'
                action = 'WAIT_FOR_BREAKOUT'
                strength = 'WEAK'
            
            # Band width (volatility measure)
            band_width = ((bb_upper - bb_lower) / bb_middle) * 100
            
            if band_width > 4:
                volatility = 'HIGH'
                vol_action = 'GOOD_FOR_STRADDLES'
            elif band_width > 2:
                volatility = 'NORMAL'
                vol_action = 'MODERATE_VOLATILITY'
            else:
                volatility = 'LOW'
                vol_action = 'VOLATILITY_SQUEEZE'
            
            return {
                'upper_band': round(bb_upper, 2),
                'middle_band': round(bb_middle, 2),
                'lower_band': round(bb_lower, 2),
                'current_price': round(current_price, 2),
                'position': position,
                'signal': signal,
                'action': action,
                'strength': strength,
                'price_position_percent': round(price_position * 100, 1),
                'band_width_percent': round(band_width, 2),
                'volatility': volatility,
                'volatility_action': vol_action,
                'interpretation': f"NIFTY at {position.lower().replace('_', ' ')}, volatility is {volatility.lower()}"
            }
            
        except Exception as e:
            return {'error': f'Bollinger Bands calculation failed: {e}'}
    
    def calculate_moving_averages(self, close_prices: pd.Series) -> Dict:
        """Calculate various moving averages for trend analysis"""
        try:
            current_price = float(close_prices.iloc[-1])
            
            ma_data = {}
            periods = [5, 9, 21, 50]
            
            for period in periods:
                if len(close_prices) >= period:
                    # Simple Moving Average
                    sma = close_prices.rolling(window=period).mean()
                    sma_value = float(sma.iloc[-1])
                    
                    # Exponential Moving Average
                    ema = close_prices.ewm(span=period).mean()
                    ema_value = float(ema.iloc[-1])
                    
                    # Calculate position relative to MA
                    sma_distance = ((current_price - sma_value) / sma_value) * 100
                    ema_distance = ((current_price - ema_value) / ema_value) * 100
                    
                    ma_data[f'sma_{period}'] = {
                        'value': round(sma_value, 2),
                        'position': 'ABOVE' if current_price > sma_value else 'BELOW',
                        'distance_percent': round(sma_distance, 2),
                        'trend': 'RISING' if len(sma) > 1 and sma.iloc[-1] > sma.iloc[-2] else 'FALLING'
                    }
                    
                    ma_data[f'ema_{period}'] = {
                        'value': round(ema_value, 2),
                        'position': 'ABOVE' if current_price > ema_value else 'BELOW',
                        'distance_percent': round(ema_distance, 2),
                        'trend': 'RISING' if len(ema) > 1 and ema.iloc[-1] > ema.iloc[-2] else 'FALLING'
                    }
            
            # Moving average crossover analysis
            crossover_signals = []
            
            # Short-term trend (EMA 9 vs EMA 21)
            if 'ema_9' in ma_data and 'ema_21' in ma_data:
                if ma_data['ema_9']['value'] > ma_data['ema_21']['value']:
                    crossover_signals.append('SHORT_TERM_BULLISH')
                else:
                    crossover_signals.append('SHORT_TERM_BEARISH')
            
            # Medium-term trend (EMA 21 vs EMA 50)
            if 'ema_21' in ma_data and 'ema_50' in ma_data:
                if ma_data['ema_21']['value'] > ma_data['ema_50']['value']:
                    crossover_signals.append('MEDIUM_TERM_BULLISH')
                else:
                    crossover_signals.append('MEDIUM_TERM_BEARISH')
            
            # Overall trend assessment
            bullish_signals = len([s for s in crossover_signals if 'BULLISH' in s])
            bearish_signals = len([s for s in crossover_signals if 'BEARISH' in s])
            
            if bullish_signals > bearish_signals:
                overall_trend = 'BULLISH'
                trend_action = 'FAVOR_LONG_POSITIONS'
            elif bearish_signals > bullish_signals:
                overall_trend = 'BEARISH'
                trend_action = 'FAVOR_SHORT_POSITIONS'
            else:
                overall_trend = 'SIDEWAYS'
                trend_action = 'RANGE_TRADING'
            
            return {
                'current_price': current_price,
                'moving_averages': ma_data,
                'crossover_signals': crossover_signals,
                'overall_trend': overall_trend,
                'trend_action': trend_action,
                'interpretation': f"NIFTY trend is {overall_trend.lower()} - {trend_action.lower().replace('_', ' ')}"
            }
            
        except Exception as e:
            return {'error': f'Moving averages calculation failed: {e}'}
    
    def analyze_volume(self, df: pd.DataFrame) -> Dict:
        """Analyze volume patterns for NIFTY options insights"""
        try:
            if 'volume' not in df.columns or df['volume'].isna().all():
                return {'error': 'No volume data available'}
            
            current_volume = int(df['volume'].iloc[-1])
            
            # Volume moving averages
            volume_sma_10 = df['volume'].rolling(window=10).mean()
            volume_sma_20 = df['volume'].rolling(window=20).mean()
            
            avg_volume_10 = int(volume_sma_10.iloc[-1]) if not pd.isna(volume_sma_10.iloc[-1]) else current_volume
            avg_volume_20 = int(volume_sma_20.iloc[-1]) if not pd.isna(volume_sma_20.iloc[-1]) else current_volume
            
            # Volume ratio analysis
            volume_ratio_10 = current_volume / avg_volume_10 if avg_volume_10 > 0 else 1
            volume_ratio_20 = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
            
            # Volume signal interpretation
            if volume_ratio_20 > 2:
                volume_signal = 'VERY_HIGH'
                volume_action = 'STRONG_BREAKOUT_LIKELY'
                strength = 'VERY_STRONG'
            elif volume_ratio_20 > 1.5:
                volume_signal = 'HIGH'
                volume_action = 'INCREASED_INTEREST'
                strength = 'STRONG'
            elif volume_ratio_20 > 0.8:
                volume_signal = 'NORMAL'
                volume_action = 'TYPICAL_TRADING'
                strength = 'MODERATE'
            else:
                volume_signal = 'LOW'
                volume_action = 'WEAK_PARTICIPATION'
                strength = 'WEAK'
            
            # Volume trend
            recent_volumes = df['volume'].tail(5)
            volume_trend = 'INCREASING' if recent_volumes.iloc[-1] > recent_volumes.mean() else 'DECREASING'
            
            return {
                'current_volume': current_volume,
                'average_volume_10': avg_volume_10,
                'average_volume_20': avg_volume_20,
                'volume_ratio_10': round(volume_ratio_10, 2),
                'volume_ratio_20': round(volume_ratio_20, 2),
                'volume_signal': volume_signal,
                'volume_action': volume_action,
                'strength': strength,
                'volume_trend': volume_trend,
                'interpretation': f"Volume is {volume_signal.lower()} ({volume_ratio_20:.1f}x average) - {volume_action.lower().replace('_', ' ')}"
            }
            
        except Exception as e:
            return {'error': f'Volume analysis failed: {e}'}
    
    def find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Find support and resistance levels for NIFTY options trading"""
        try:
            highs = df['high'].values
            lows = df['low'].values
            closes = df['close'].values
            current_price = float(df['close'].iloc[-1])
            
            # Find pivot points (simplified)
            def find_peaks_troughs(data, window=3):
                peaks = []
                troughs = []
                
                for i in range(window, len(data) - window):
                    # Check for peak
                    if all(data[i] >= data[i-j] for j in range(1, window+1)) and \
                       all(data[i] >= data[i+j] for j in range(1, window+1)):
                        peaks.append(data[i])
                    
                    # Check for trough
                    if all(data[i] <= data[i-j] for j in range(1, window+1)) and \
                       all(data[i] <= data[i+j] for j in range(1, window+1)):
                        troughs.append(data[i])
                
                return peaks, troughs
            
            # Find recent peaks and troughs
            resistance_levels, support_levels = find_peaks_troughs(closes)
            
            # Add recent high/low
            recent_high = float(np.max(highs[-10:]))  # 10-period high
            recent_low = float(np.min(lows[-10:]))    # 10-period low
            
            if recent_high not in resistance_levels:
                resistance_levels.append(recent_high)
            if recent_low not in support_levels:
                support_levels.append(recent_low)
            
            # Sort and get closest levels
            resistance_levels = sorted(set(resistance_levels), reverse=True)
            support_levels = sorted(set(support_levels), reverse=True)
            
            # Find immediate support and resistance
            immediate_resistance = next((level for level in resistance_levels if level > current_price), None)
            immediate_support = next((level for level in reversed(support_levels) if level < current_price), None)
            
            # Calculate distances
            resistance_distance = ((immediate_resistance - current_price) / current_price) * 100 if immediate_resistance else None
            support_distance = ((current_price - immediate_support) / current_price) * 100 if immediate_support else None
            
            # Strength assessment
            if resistance_distance and resistance_distance < 1:
                resistance_strength = 'STRONG'
            elif resistance_distance and resistance_distance < 2:
                resistance_strength = 'MODERATE'
            else:
                resistance_strength = 'WEAK'
            
            if support_distance and support_distance < 1:
                support_strength = 'STRONG'
            elif support_distance and support_distance < 2:
                support_strength = 'MODERATE'
            else:
                support_strength = 'WEAK'
            
            return {
                'current_price': current_price,
                'immediate_resistance': round(immediate_resistance, 2) if immediate_resistance else None,
                'immediate_support': round(immediate_support, 2) if immediate_support else None,
                'resistance_distance_percent': round(resistance_distance, 2) if resistance_distance else None,
                'support_distance_percent': round(support_distance, 2) if support_distance else None,
                'resistance_strength': resistance_strength if immediate_resistance else None,
                'support_strength': support_strength if immediate_support else None,
                'all_resistance_levels': [round(level, 2) for level in resistance_levels[:5]],
                'all_support_levels': [round(level, 2) for level in support_levels[:5]],
                'interpretation': f"Next resistance at ₹{immediate_resistance:.2f} ({resistance_distance:.1f}% away), support at ₹{immediate_support:.2f} ({support_distance:.1f}% away)" if immediate_resistance and immediate_support else "Limited support/resistance data"
            }
            
        except Exception as e:
            return {'error': f'Support/Resistance calculation failed: {e}'}
    
    def generate_overall_signal(self, analysis: Dict, current_price: float) -> Dict:
        """Generate overall trading signal from all indicators for NIFTY options"""
        try:
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            signal_weights = 0
            
            signal_details = []
            
            # RSI signals (weight: 2)
            rsi_data = analysis.get('rsi', {})
            if 'signal' in rsi_data and 'strength' in rsi_data:
                weight = 3 if rsi_data['strength'] == 'STRONG' else 2 if rsi_data['strength'] == 'MODERATE' else 1
                total_signals += 1
                signal_weights += weight
                
                if rsi_data['signal'] in ['OVERSOLD', 'BULLISH', 'STRONG_BULLISH']:
                    bullish_signals += weight
                    signal_details.append(f"RSI: {rsi_data['signal']} (Weight: {weight})")
                elif rsi_data['signal'] in ['OVERBOUGHT', 'BEARISH', 'STRONG_BEARISH']:
                    bearish_signals += weight
                    signal_details.append(f"RSI: {rsi_data['signal']} (Weight: {weight})")
            
            # MACD signals (weight: 3 for crossovers, 2 for regular)
            macd_data = analysis.get('macd', {})
            if 'signal' in macd_data and 'strength' in macd_data:
                weight = 4 if macd_data['strength'] == 'VERY_STRONG' else 3 if macd_data['strength'] == 'STRONG' else 2
                total_signals += 1
                signal_weights += weight
                
                if 'BULLISH' in macd_data['signal']:
                    bullish_signals += weight
                    signal_details.append(f"MACD: {macd_data['signal']} (Weight: {weight})")
                elif 'BEARISH' in macd_data['signal']:
                    bearish_signals += weight
                    signal_details.append(f"MACD: {macd_data['signal']} (Weight: {weight})")
            
            # Bollinger Bands signals (weight: 2)
            bb_data = analysis.get('bollinger_bands', {})
            if 'signal' in bb_data and 'strength' in bb_data:
                weight = 3 if bb_data['strength'] == 'STRONG' else 2 if bb_data['strength'] == 'MODERATE' else 1
                total_signals += 1
                signal_weights += weight
                
                if bb_data['signal'] in ['OVERSOLD', 'APPROACHING_SUPPORT']:
                    bullish_signals += weight
                    signal_details.append(f"BB: {bb_data['signal']} (Weight: {weight})")
                elif bb_data['signal'] in ['OVERBOUGHT', 'APPROACHING_RESISTANCE']:
                    bearish_signals += weight
                    signal_details.append(f"BB: {bb_data['signal']} (Weight: {weight})")
            
            # Moving Average signals (weight: 2)
            ma_data = analysis.get('moving_averages', {})
            if 'overall_trend' in ma_data:
                weight = 2
                total_signals += 1
                signal_weights += weight
                
                if ma_data['overall_trend'] == 'BULLISH':
                    bullish_signals += weight
                    signal_details.append(f"MA: BULLISH TREND (Weight: {weight})")
                elif ma_data['overall_trend'] == 'BEARISH':
                    bearish_signals += weight
                    signal_details.append(f"MA: BEARISH TREND (Weight: {weight})")
            
            # Volume confirmation (weight: 1)
            volume_data = analysis.get('volume_analysis', {})
            if 'volume_signal' in volume_data and 'strength' in volume_data:
                if volume_data['volume_signal'] in ['HIGH', 'VERY_HIGH']:
                    weight = 1
                    total_signals += 1
                    signal_weights += weight
                    signal_details.append(f"Volume: {volume_data['volume_signal']} CONFIRMATION (Weight: {weight})")
                    # Volume confirms the direction, so add to stronger side
                    if bullish_signals > bearish_signals:
                        bullish_signals += weight
                    elif bearish_signals > bullish_signals:
                        bearish_signals += weight
            
            # Calculate overall signal
            if signal_weights == 0:
                overall_direction = 'NEUTRAL'
                confidence = 0
                action = 'WAIT'
                options_action = 'NO_ACTION'
            else:
                signal_strength = abs(bullish_signals - bearish_signals) / signal_weights
                confidence = round(signal_strength * 100, 1)
                
                if bullish_signals > bearish_signals:
                    overall_direction = 'BULLISH'
                    if confidence > 80:
                        action = 'STRONG_BUY'
                        options_action = 'BUY_CALLS_OR_SELL_PUTS'
                    elif confidence > 60:
                        action = 'BUY'
                        options_action = 'CONSIDER_CALLS'
                    elif confidence > 40:
                        action = 'WEAK_BUY'
                        options_action = 'SMALL_CALL_POSITION'
                    else:
                        action = 'HOLD'
                        options_action = 'WAIT_FOR_CONFIRMATION'
                        
                elif bearish_signals > bullish_signals:
                    overall_direction = 'BEARISH'
                    if confidence > 80:
                        action = 'STRONG_SELL'
                        options_action = 'BUY_PUTS_OR_SELL_CALLS'
                    elif confidence > 60:
                        action = 'SELL'
                        options_action = 'CONSIDER_PUTS'
                    elif confidence > 40:
                        action = 'WEAK_SELL'
                        options_action = 'SMALL_PUT_POSITION'
                    else:
                        action = 'HOLD'
                        options_action = 'WAIT_FOR_CONFIRMATION'
                else:
                    overall_direction = 'NEUTRAL'
                    action = 'HOLD'
                    options_action = 'RANGE_TRADING_OR_STRADDLES'
                    confidence = 0
            
            # Risk assessment
            if confidence > 70:
                risk_level = 'LOW'
            elif confidence > 50:
                risk_level = 'MODERATE'
            elif confidence > 30:
                risk_level = 'HIGH'
            else:
                risk_level = 'VERY_HIGH'
            
            return {
                'overall_direction': overall_direction,
                'confidence_percent': confidence,
                'action': action,
                'options_action': options_action,
                'risk_level': risk_level,
                'bullish_signals_weight': bullish_signals,
                'bearish_signals_weight': bearish_signals,
                'total_signals': total_signals,
                'signal_weights': signal_weights,
                'signal_details': signal_details,
                'summary': f"{overall_direction} signal with {confidence}% confidence - {action}",
                'options_recommendation': f"NIFTY Options: {options_action.replace('_', ' ').title()}",
                'current_price': current_price,
                'risk_management': f"Risk Level: {risk_level} - Position size accordingly"
            }
            
        except Exception as e:
            return {'error': f'Overall signal generation failed: {e}'}