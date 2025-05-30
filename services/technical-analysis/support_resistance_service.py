# services/technical-analysis/support_resistance_service.py
import pandas as pd
import numpy as np
import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Add database service to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.sqlite_db_service import get_sqlite_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupportResistanceService:
    def __init__(self):
        self.db = None
        
    async def initialize(self):
        """Initialize with database connection"""
        self.db = await get_sqlite_database_service()
        logger.info("Support/Resistance Service initialized")
    
    async def detect_nifty_key_levels(self) -> Dict:
        """Detect support/resistance levels for your NIFTY ₹24,833.6 data"""
        
        if not self.db:
            await self.initialize()
        
        print("🎯 Detecting Support/Resistance levels for NIFTY...")
        
        # Get NIFTY data (more data for better level detection)
        candles = await self.db.get_market_data('NIFTY', '5min', limit=100)
        
        if not candles:
            return {'error': 'No NIFTY data found'}
        
        # Get options data for OI-based levels
        options_data = await self.db.get_options_chain('NIFTY')
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        
        # Fix timestamp parsing
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        except:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
            except:
                df['timestamp'] = pd.to_datetime(df['timestamp'], infer_datetime_format=True)
        
        df = df.sort_values('timestamp')
        
        # Ensure numeric columns
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        current_price = float(df['close'].iloc[-1])
        
        print(f"   💰 Current NIFTY Price: ₹{current_price}")
        print(f"   📊 Analyzing {len(df)} candles for key levels...")
        
        # Multiple methods for level detection
        levels = {}
        
        # 1. Pivot Points (Traditional)
        levels['pivot_points'] = self.calculate_pivot_points(df)
        
        # 2. Swing Highs/Lows
        levels['swing_levels'] = self.detect_swing_levels(df)
        
        # 3. Volume Profile Levels
        levels['volume_levels'] = self.calculate_volume_profile_levels(df)
        
        # 4. Options-based levels (using your OI data)
        levels['options_levels'] = self.calculate_options_based_levels(options_data, current_price)
        
        # 5. Psychological Levels (round numbers)
        levels['psychological_levels'] = self.identify_psychological_levels(current_price)
        
        # 6. Moving Average Levels
        levels['ma_levels'] = self.calculate_ma_levels(df)
        
        # 7. Recent High/Low Levels
        levels['recent_levels'] = self.calculate_recent_highs_lows(df)
        
        # Consolidate all levels
        consolidated_levels = self.consolidate_all_levels(levels, current_price)
        
        # Get immediate support/resistance
        key_levels = self.get_immediate_levels(consolidated_levels, current_price)
        
        return {
            'symbol': 'NIFTY',
            'current_price': current_price,
            'analysis_time': datetime.now().isoformat(),
            'data_points': len(df),
            'level_detection_methods': levels,
            'consolidated_levels': consolidated_levels,
            'key_levels': key_levels,
            'trading_plan': self.generate_trading_plan(key_levels, current_price)
        }
    
    def calculate_pivot_points(self, df: pd.DataFrame) -> Dict:
        """Calculate traditional pivot points from yesterday's data"""
        try:
            if len(df) < 2:
                return {'error': 'Insufficient data for pivot points'}
            
            # Use yesterday's data (or latest complete session)
            yesterday = df.iloc[-2]  # Previous candle
            
            high = float(yesterday['high'])
            low = float(yesterday['low'])
            close = float(yesterday['close'])
            
            # Calculate pivot point
            pivot = (high + low + close) / 3
            
            # Calculate support and resistance levels
            r1 = 2 * pivot - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)
            
            s1 = 2 * pivot - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)
            
            return {
                'pivot': round(pivot, 2),
                'resistance_levels': {
                    'r1': round(r1, 2),
                    'r2': round(r2, 2),
                    'r3': round(r3, 2)
                },
                'support_levels': {
                    's1': round(s1, 2),
                    's2': round(s2, 2),
                    's3': round(s3, 2)
                },
                'method': 'TRADITIONAL_PIVOTS'
            }
            
        except Exception as e:
            return {'error': f'Pivot points calculation failed: {e}'}
    
    def detect_swing_levels(self, df: pd.DataFrame, window: int = 5) -> Dict:
        """Detect swing highs and lows"""
        try:
            if len(df) < window * 2 + 1:
                return {'error': f'Need at least {window * 2 + 1} data points for swing detection'}
            
            highs = df['high'].values
            lows = df['low'].values
            
            swing_highs = []
            swing_lows = []
            
            # Find swing highs and lows
            for i in range(window, len(df) - window):
                # Check for swing high
                is_swing_high = True
                for j in range(1, window + 1):
                    if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    swing_highs.append({
                        'price': round(float(highs[i]), 2),
                        'index': i,
                        'timestamp': df.iloc[i]['timestamp'],
                        'strength': self.calculate_level_strength(highs, i, 'high')
                    })
                
                # Check for swing low
                is_swing_low = True
                for j in range(1, window + 1):
                    if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                        is_swing_low = False
                        break
                
                if is_swing_low:
                    swing_lows.append({
                        'price': round(float(lows[i]), 2),
                        'index': i,
                        'timestamp': df.iloc[i]['timestamp'],
                        'strength': self.calculate_level_strength(lows, i, 'low')
                    })
            
            # Sort by strength and get top levels
            swing_highs = sorted(swing_highs, key=lambda x: x['strength'], reverse=True)[:10]
            swing_lows = sorted(swing_lows, key=lambda x: x['strength'], reverse=True)[:10]
            
            return {
                'swing_highs': swing_highs,
                'swing_lows': swing_lows,
                'method': 'SWING_DETECTION'
            }
            
        except Exception as e:
            return {'error': f'Swing level detection failed: {e}'}
    
    def calculate_level_strength(self, prices: np.array, index: int, level_type: str) -> float:
        """Calculate the strength of a support/resistance level"""
        try:
            price = prices[index]
            touches = 0
            
            # Count how many times price has touched this level
            tolerance = price * 0.001  # 0.1% tolerance
            
            for i, p in enumerate(prices):
                if abs(p - price) <= tolerance and i != index:
                    touches += 1
            
            # Consider volume if available (simplified strength calculation)
            base_strength = touches * 2
            
            # Age factor (more recent levels are stronger)
            age_factor = max(0.5, 1 - (len(prices) - index) / len(prices))
            
            return base_strength * age_factor
            
        except Exception as e:
            return 1.0  # Default strength
    
    def calculate_volume_profile_levels(self, df: pd.DataFrame) -> Dict:
        """Calculate volume-weighted price levels"""
        try:
            if 'volume' not in df.columns or df['volume'].isna().all():
                return {'error': 'No volume data available'}
            
            # Create price bins
            price_min = df['low'].min()
            price_max = df['high'].max()
            num_bins = 20
            
            price_bins = np.linspace(price_min, price_max, num_bins)
            volume_profile = {}
            
            for _, row in df.iterrows():
                # Distribute volume across the candle's price range
                candle_prices = np.linspace(row['low'], row['high'], 5)
                volume_per_price = row['volume'] / 5
                
                for price in candle_prices:
                    # Find the appropriate bin
                    bin_index = np.digitize(price, price_bins) - 1
                    bin_index = max(0, min(bin_index, len(price_bins) - 2))
                    
                    bin_price = price_bins[bin_index]
                    
                    if bin_price not in volume_profile:
                        volume_profile[bin_price] = 0
                    volume_profile[bin_price] += volume_per_price
            
            # Find high volume areas (potential support/resistance)
            sorted_volume = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
            high_volume_levels = []
            
            for price, volume in sorted_volume[:5]:  # Top 5 volume levels
                high_volume_levels.append({
                    'price': round(float(price), 2),
                    'volume': int(volume),
                    'strength': volume / max(volume_profile.values()) * 10
                })
            
            # Point of Control (highest volume level)
            poc = sorted_volume[0] if sorted_volume else None
            
            return {
                'high_volume_levels': high_volume_levels,
                'point_of_control': {
                    'price': round(float(poc[0]), 2),
                    'volume': int(poc[1])
                } if poc else None,
                'method': 'VOLUME_PROFILE'
            }
            
        except Exception as e:
            return {'error': f'Volume profile calculation failed: {e}'}
    
    def calculate_options_based_levels(self, options_data: List[Dict], current_price: float) -> Dict:
        """Calculate support/resistance from your options OI data"""
        try:
            if not options_data:
                return {'error': 'No options data available'}
            
            # Group by strike price and sum OI
            strike_oi = {}
            total_oi = 0
            
            for option in options_data:
                strike = float(option['strike'])
                oi = int(option.get('oi', 0))
                option_type = option['option_type']
                
                if strike not in strike_oi:
                    strike_oi[strike] = {'total_oi': 0, 'ce_oi': 0, 'pe_oi': 0}
                
                strike_oi[strike]['total_oi'] += oi
                total_oi += oi
                
                if option_type == 'CE':
                    strike_oi[strike]['ce_oi'] += oi
                else:
                    strike_oi[strike]['pe_oi'] += oi
            
            # Find strikes with highest OI (potential S/R levels)
            high_oi_strikes = []
            for strike, data in strike_oi.items():
                if data['total_oi'] > 0:
                    strength = (data['total_oi'] / total_oi) * 100 if total_oi > 0 else 0
                    
                    high_oi_strikes.append({
                        'price': round(strike, 2),
                        'total_oi': data['total_oi'],
                        'ce_oi': data['ce_oi'],
                        'pe_oi': data['pe_oi'],
                        'strength': round(strength, 2),
                        'type': 'RESISTANCE' if strike > current_price else 'SUPPORT'
                    })
            
            # Sort by OI and get top levels
            high_oi_strikes = sorted(high_oi_strikes, key=lambda x: x['total_oi'], reverse=True)[:10]
            
            # Calculate Max Pain (simplified)
            max_pain_strike = self.calculate_simple_max_pain(strike_oi, current_price)
            
            return {
                'high_oi_strikes': high_oi_strikes,
                'max_pain': {
                    'price': round(max_pain_strike, 2),
                    'distance_from_current': round(abs(current_price - max_pain_strike), 2)
                },
                'method': 'OPTIONS_OI_ANALYSIS'
            }
            
        except Exception as e:
            return {'error': f'Options-based levels calculation failed: {e}'}
    
    def calculate_simple_max_pain(self, strike_oi: Dict, current_price: float) -> float:
        """Simplified Max Pain calculation"""
        try:
            min_pain = float('inf')
            max_pain_strike = current_price
            
            for test_strike in strike_oi.keys():
                total_pain = 0
                
                for strike, data in strike_oi.items():
                    # CE pain
                    if test_strike > strike:
                        total_pain += (test_strike - strike) * data['ce_oi']
                    
                    # PE pain
                    if test_strike < strike:
                        total_pain += (strike - test_strike) * data['pe_oi']
                
                if total_pain < min_pain:
                    min_pain = total_pain
                    max_pain_strike = test_strike
            
            return max_pain_strike
            
        except Exception as e:
            return current_price
    
    def identify_psychological_levels(self, current_price: float) -> Dict:
        """Identify round number psychological levels"""
        try:
            levels = []
            
            # Round to nearest 100
            base_100 = int(current_price // 100) * 100
            
            # Generate levels around current price
            for i in range(-3, 4):  # 3 levels above and below
                level_100 = base_100 + (i * 100)
                if level_100 > 0:
                    distance = abs(current_price - level_100)
                    levels.append({
                        'price': level_100,
                        'type': 'HUNDRED_LEVEL',
                        'distance': round(distance, 2),
                        'strength': max(1, 5 - distance / 100)  # Closer levels are stronger
                    })
            
            # Round to nearest 50
            base_50 = int(current_price // 50) * 50
            for i in range(-2, 3):  # 2 levels above and below
                level_50 = base_50 + (i * 50)
                if level_50 > 0 and level_50 % 100 != 0:  # Exclude 100-levels already added
                    distance = abs(current_price - level_50)
                    levels.append({
                        'price': level_50,
                        'type': 'FIFTY_LEVEL',
                        'distance': round(distance, 2),
                        'strength': max(1, 3 - distance / 50)
                    })
            
            # Sort by distance from current price
            levels = sorted(levels, key=lambda x: x['distance'])
            
            return {
                'psychological_levels': levels[:10],  # Top 10 closest levels
                'method': 'PSYCHOLOGICAL_LEVELS'
            }
            
        except Exception as e:
            return {'error': f'Psychological levels calculation failed: {e}'}
    
    def calculate_ma_levels(self, df: pd.DataFrame) -> Dict:
        """Calculate moving average levels as dynamic S/R"""
        try:
            close_prices = df['close']
            ma_levels = []
            
            periods = [9, 21, 50, 100, 200]
            
            for period in periods:
                if len(close_prices) >= period:
                    ma = close_prices.rolling(window=period).mean().iloc[-1]
                    
                    # Determine if MA is acting as support or resistance
                    current_price = close_prices.iloc[-1]
                    ma_type = 'RESISTANCE' if current_price < ma else 'SUPPORT'
                    
                    # Calculate MA slope (trend)
                    if len(close_prices) >= period + 5:
                        ma_prev = close_prices.rolling(window=period).mean().iloc[-6]
                        slope = 'RISING' if ma > ma_prev else 'FALLING'
                    else:
                        slope = 'NEUTRAL'
                    
                    ma_levels.append({
                        'price': round(float(ma), 2),
                        'period': period,
                        'type': ma_type,
                        'slope': slope,
                        'strength': period / 20,  # Longer periods have more strength
                        'distance': round(abs(current_price - ma), 2)
                    })
            
            return {
                'ma_levels': ma_levels,
                'method': 'MOVING_AVERAGES'
            }
            
        except Exception as e:
            return {'error': f'MA levels calculation failed: {e}'}
    
    def calculate_recent_highs_lows(self, df: pd.DataFrame) -> Dict:
        """Calculate recent highs and lows"""
        try:
            periods = [5, 10, 20, 50]
            recent_levels = []
            
            for period in periods:
                if len(df) >= period:
                    recent_data = df.tail(period)
                    
                    recent_high = recent_data['high'].max()
                    recent_low = recent_data['low'].min()
                    
                    recent_levels.append({
                        'high': {
                            'price': round(float(recent_high), 2),
                            'period': f'{period}_PERIOD',
                            'type': 'RESISTANCE',
                            'strength': period / 10
                        },
                        'low': {
                            'price': round(float(recent_low), 2),
                            'period': f'{period}_PERIOD',
                            'type': 'SUPPORT',
                            'strength': period / 10
                        }
                    })
            
            return {
                'recent_levels': recent_levels,
                'method': 'RECENT_HIGHS_LOWS'
            }
            
        except Exception as e:
            return {'error': f'Recent levels calculation failed: {e}'}
    
    def consolidate_all_levels(self, levels: Dict, current_price: float) -> List[Dict]:
        """Consolidate all detected levels and remove duplicates"""
        try:
            all_levels = []
            
            # Extract levels from all methods
            for method, method_data in levels.items():
                if 'error' in method_data:
                    continue
                
                if method == 'pivot_points':
                    # Add pivot levels
                    if 'pivot' in method_data:
                        all_levels.append({
                            'price': method_data['pivot'],
                            'type': 'PIVOT',
                            'strength': 5,
                            'method': method,
                            'distance': abs(current_price - method_data['pivot'])
                        })
                    
                    # Add resistance levels
                    for level_name, price in method_data.get('resistance_levels', {}).items():
                        all_levels.append({
                            'price': price,
                            'type': 'RESISTANCE',
                            'strength': 4,
                            'method': f"{method}_{level_name}",
                            'distance': abs(current_price - price)
                        })
                    
                    # Add support levels
                    for level_name, price in method_data.get('support_levels', {}).items():
                        all_levels.append({
                            'price': price,
                            'type': 'SUPPORT',
                            'strength': 4,
                            'method': f"{method}_{level_name}",
                            'distance': abs(current_price - price)
                        })
                
                elif method == 'swing_levels':
                    # Add swing highs
                    for swing in method_data.get('swing_highs', []):
                        all_levels.append({
                            'price': swing['price'],
                            'type': 'RESISTANCE',
                            'strength': swing['strength'],
                            'method': method,
                            'distance': abs(current_price - swing['price'])
                        })
                    
                    # Add swing lows
                    for swing in method_data.get('swing_lows', []):
                        all_levels.append({
                            'price': swing['price'],
                            'type': 'SUPPORT',
                            'strength': swing['strength'],
                            'method': method,
                            'distance': abs(current_price - swing['price'])
                        })
                
                elif method == 'volume_levels':
                    for vol_level in method_data.get('high_volume_levels', []):
                        level_type = 'RESISTANCE' if vol_level['price'] > current_price else 'SUPPORT'
                        all_levels.append({
                            'price': vol_level['price'],
                            'type': level_type,
                            'strength': vol_level['strength'],
                            'method': method,
                            'distance': abs(current_price - vol_level['price'])
                        })
                
                elif method == 'options_levels':
                    for oi_level in method_data.get('high_oi_strikes', []):
                        all_levels.append({
                            'price': oi_level['price'],
                            'type': oi_level['type'],
                            'strength': oi_level['strength'] / 2,  # Scale down OI strength
                            'method': f"{method}_OI",
                            'distance': abs(current_price - oi_level['price'])
                        })
                    
                    # Add Max Pain as a level
                    if 'max_pain' in method_data:
                        all_levels.append({
                            'price': method_data['max_pain']['price'],
                            'type': 'MAX_PAIN',
                            'strength': 6,  # High strength for max pain
                            'method': f"{method}_MAX_PAIN",
                            'distance': method_data['max_pain']['distance_from_current']
                        })
                
                elif method == 'psychological_levels':
                    for psych_level in method_data.get('psychological_levels', []):
                        level_type = 'RESISTANCE' if psych_level['price'] > current_price else 'SUPPORT'
                        all_levels.append({
                            'price': psych_level['price'],
                            'type': level_type,
                            'strength': psych_level['strength'],
                            'method': f"{method}_{psych_level['type']}",
                            'distance': psych_level['distance']
                        })
                
                elif method == 'ma_levels':
                    for ma_level in method_data.get('ma_levels', []):
                        all_levels.append({
                            'price': ma_level['price'],
                            'type': ma_level['type'],
                            'strength': ma_level['strength'],
                            'method': f"{method}_MA{ma_level['period']}",
                            'distance': ma_level['distance']
                        })
            
            # Remove duplicates (levels within 0.25% of each other)
            consolidated = []
            tolerance = current_price * 0.0025  # 0.25% tolerance
            
            # Sort by price
            all_levels = sorted(all_levels, key=lambda x: x['price'])
            
            for level in all_levels:
                # Check if this level is close to any existing consolidated level
                is_duplicate = False
                for existing in consolidated:
                    if abs(level['price'] - existing['price']) <= tolerance:
                        # Merge with existing level (keep stronger one)
                        if level['strength'] > existing['strength']:
                            existing.update(level)
                            existing['strength'] += level['strength'] * 0.5  # Bonus for confluence
                            existing['method'] += f" + {level['method']}"
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    consolidated.append(level)
            
            # Sort by strength and distance
            consolidated = sorted(consolidated, key=lambda x: (x['strength'], -x['distance']), reverse=True)
            
            return consolidated[:20]  # Return top 20 levels
            
        except Exception as e:
            return [{'error': f'Level consolidation failed: {e}'}]
    
    def get_immediate_levels(self, consolidated_levels: List[Dict], current_price: float) -> Dict:
        """Get immediate support and resistance levels"""
        try:
            resistance_levels = [l for l in consolidated_levels if l['price'] > current_price]
            support_levels = [l for l in consolidated_levels if l['price'] < current_price]
            
            # Sort resistance by proximity (closest first)
            resistance_levels = sorted(resistance_levels, key=lambda x: x['distance'])
            
            # Sort support by proximity (closest first)
            support_levels = sorted(support_levels, key=lambda x: x['distance'])
            
            immediate_resistance = resistance_levels[0] if resistance_levels else None
            immediate_support = support_levels[0] if support_levels else None
            
            return {
                'immediate_resistance': immediate_resistance,
                'immediate_support': immediate_support,
                'next_resistance_levels': resistance_levels[1:4] if len(resistance_levels) > 1 else [],
                'next_support_levels': support_levels[1:4] if len(support_levels) > 1 else [],
                'all_resistance_levels': resistance_levels[:10],
                'all_support_levels': support_levels[:10]
            }
            
        except Exception as e:
            return {'error': f'Immediate levels calculation failed: {e}'}
    
    def generate_trading_plan(self, key_levels: Dict, current_price: float) -> Dict:
        """Generate options trading plan based on S/R levels"""
        try:
            immediate_resistance = key_levels.get('immediate_resistance')
            immediate_support = key_levels.get('immediate_support')
            
            trading_plan = {
                'current_price': current_price,
                'market_structure': self.assess_market_structure(key_levels, current_price)
            }
            
            # Resistance-based strategies
            if immediate_resistance:
                resistance_price = immediate_resistance['price']
                resistance_distance = immediate_resistance['distance']
                resistance_strength = immediate_resistance['strength']
                
                if resistance_distance <= current_price * 0.005:  # Within 0.5%
                    resistance_action = 'SELL_CALLS_NEAR_RESISTANCE'
                    resistance_strategy = f"Consider selling {resistance_price} CE as price approaches strong resistance"
                elif resistance_distance <= current_price * 0.01:  # Within 1%
                    resistance_action = 'PREPARE_RESISTANCE_TRADE'
                    resistance_strategy = f"Prepare for resistance at ₹{resistance_price} - consider CE selling or PUT buying"
                else:
                    resistance_action = 'MONITOR_RESISTANCE'
                    resistance_strategy = f"Monitor price action near ₹{resistance_price} resistance"
                
                trading_plan['resistance_plan'] = {
                    'level': resistance_price,
                    'distance_percent': round((resistance_distance / current_price) * 100, 2),
                    'strength': resistance_strength,
                    'action': resistance_action,
                    'strategy': resistance_strategy
                }
            
            # Support-based strategies
            if immediate_support:
                support_price = immediate_support['price']
                support_distance = immediate_support['distance']
                support_strength = immediate_support['strength']
                
                if support_distance <= current_price * 0.005:  # Within 0.5%
                    support_action = 'BUY_CALLS_NEAR_SUPPORT'
                    support_strategy = f"Consider buying calls near ₹{support_price} support level"
                elif support_distance <= current_price * 0.01:  # Within 1%
                    support_action = 'PREPARE_SUPPORT_TRADE'
                    support_strategy = f"Prepare for support at ₹{support_price} - consider CE buying or PUT selling"
                else:
                    support_action = 'MONITOR_SUPPORT'
                    support_strategy = f"Monitor price action near ₹{support_price} support"
                
                trading_plan['support_plan'] = {
                    'level': support_price,
                    'distance_percent': round((support_distance / current_price) * 100, 2),
                    'strength': support_strength,
                    'action': support_action,
                    'strategy': support_strategy
                }
            
            # Range trading opportunities
            if immediate_resistance and immediate_support:
                range_size = immediate_resistance['price'] - immediate_support['price']
                range_percent = (range_size / current_price) * 100
                
                if range_percent > 2:  # Significant range
                    trading_plan['range_trading'] = {
                        'range_size': round(range_size, 2),
                        'range_percent': round(range_percent, 2),
                        'strategy': 'RANGE_TRADING_OPPORTUNITY',
                        'action': f"Range: ₹{immediate_support['price']} - ₹{immediate_resistance['price']} ({range_percent:.1f}%)",
                        'recommendation': 'Consider iron condor or range-bound strategies'
                    }
            
            return trading_plan
            
        except Exception as e:
            return {'error': f'Trading plan generation failed: {e}'}
    
    def assess_market_structure(self, key_levels: Dict, current_price: float) -> str:
        """Assess overall market structure based on S/R levels"""
        try:
            resistance_levels = key_levels.get('all_resistance_levels', [])
            support_levels = key_levels.get('all_support_levels', [])
            
            if not resistance_levels or not support_levels:
                return 'INSUFFICIENT_DATA'
            
            # Check if price is in upper, middle, or lower part of range
            nearest_resistance = resistance_levels[0]['price'] if resistance_levels else current_price + 100
            nearest_support = support_levels[0]['price'] if support_levels else current_price - 100
            
            range_size = nearest_resistance - nearest_support
            position_in_range = (current_price - nearest_support) / range_size
            
            if position_in_range > 0.7:
                return 'UPPER_RANGE_RESISTANCE_ZONE'
            elif position_in_range < 0.3:
                return 'LOWER_RANGE_SUPPORT_ZONE'
            else:
                return 'MIDDLE_RANGE_BALANCED'
                
        except Exception as e:
            return 'ANALYSIS_ERROR'