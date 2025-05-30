# test_oi_standalone.py
"""
Standalone Open Interest Analysis Test
Task 3.4: Open Interest Analysis - No Directory Dependencies
"""

import numpy as np
import pandas as pd
import math
from datetime import datetime
from typing import Dict, List, Optional

class OpenInterestAnalysisService:
    """Standalone Open Interest Analysis for NIFTY Options Trading"""
    
    def __init__(self):
        pass
    
    def generate_realistic_options_chain(self, spot_price: float = 24833.6, expiry_days: int = 15) -> pd.DataFrame:
        """Generate realistic NIFTY options chain with OI patterns"""
        np.random.seed(42)  # For reproducible results
        
        # Generate strikes around current spot
        atm_strike = round(spot_price / 50) * 50  # Round to nearest 50
        strikes = []
        
        # NIFTY strikes in 50-point intervals
        for i in range(-20, 21):  # From deep ITM to deep OTM
            strike = atm_strike + (i * 50)
            if strike > 0:
                strikes.append(strike)
        
        options_data = []
        
        for strike in strikes:
            # Generate Call and Put options for each strike
            for option_type in ['CE', 'PE']:
                option_data = self._generate_option_data(
                    strike, option_type, spot_price, expiry_days
                )
                options_data.append(option_data)
        
        df = pd.DataFrame(options_data)
        return df.sort_values(['strike', 'option_type']).reset_index(drop=True)
    
    def _generate_option_data(self, strike: float, option_type: str, spot_price: float, expiry_days: int) -> Dict:
        """Generate realistic individual option data with proper OI patterns"""
        
        # Base OI calculation with realistic patterns
        base_oi = 1000
        distance_from_atm = abs(strike - spot_price)
        
        # ATM and near ATM get higher OI (realistic pattern)
        if distance_from_atm < 50:
            oi_multiplier = 4.0  # Very high OI at ATM
        elif distance_from_atm < 150:
            oi_multiplier = 2.5  # High OI near ATM
        elif distance_from_atm < 300:
            oi_multiplier = 1.5  # Moderate OI
        else:
            oi_multiplier = 0.5  # Lower OI for far OTM
        
        # Round number strikes (psychological levels) get higher OI
        if strike % 500 == 0:
            oi_multiplier *= 2.0  # Very round numbers
        elif strike % 100 == 0:
            oi_multiplier *= 1.5  # Round numbers
        
        # Add realistic randomness
        oi_multiplier *= np.random.uniform(0.7, 1.3)
        
        # Different patterns for calls vs puts
        if option_type == 'CE':  # Calls
            # Calls typically have higher OI at resistance levels
            if strike > spot_price:  # OTM calls
                oi_multiplier *= 1.2
        else:  # Puts
            # Puts typically have higher OI at support levels
            if strike < spot_price:  # OTM puts
                oi_multiplier *= 1.2
        
        # Calculate final OI
        oi = max(100, int(base_oi * oi_multiplier))
        
        # Volume is typically 10-30% of OI for active options
        volume = int(oi * np.random.uniform(0.1, 0.3))
        
        # Realistic pricing based on moneyness
        time_factor = max(0.1, expiry_days / 30)
        
        if option_type == 'CE':  # Call
            intrinsic = max(0, spot_price - strike)
            time_value = (spot_price * 0.01 * time_factor * np.random.uniform(0.5, 1.5))
            ltp = intrinsic + time_value
        else:  # Put
            intrinsic = max(0, strike - spot_price)
            time_value = (spot_price * 0.01 * time_factor * np.random.uniform(0.5, 1.5))
            ltp = intrinsic + time_value
        
        # Bid-Ask spread
        spread = max(0.05, ltp * 0.02)  # 2% spread
        bid = max(0.05, ltp - spread/2)
        ask = ltp + spread/2
        
        return {
            'strike': strike,
            'option_type': option_type,
            'ltp': round(ltp, 2),
            'volume': volume,
            'oi': oi,
            'bid': round(bid, 2),
            'ask': round(ask, 2)
        }
    
    def calculate_put_call_ratio(self, options_df: pd.DataFrame, spot_price: float) -> Dict:
        """Calculate comprehensive Put-Call Ratio analysis"""
        try:
            # Separate calls and puts
            calls = options_df[options_df['option_type'] == 'CE'].copy()
            puts = options_df[options_df['option_type'] == 'PE'].copy()
            
            if len(calls) == 0 or len(puts) == 0:
                return {'error': 'Insufficient options data for PCR calculation'}
            
            # Total PCR calculations
            total_put_volume = puts['volume'].sum()
            total_call_volume = calls['volume'].sum()
            total_put_oi = puts['oi'].sum()
            total_call_oi = calls['oi'].sum()
            
            pcr_volume = total_put_volume / total_call_volume if total_call_volume > 0 else 0
            pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # ATM PCR (most sensitive indicator)
            atm_range = 100  # Within 100 points of spot
            atm_calls = calls[abs(calls['strike'] - spot_price) <= atm_range]
            atm_puts = puts[abs(puts['strike'] - spot_price) <= atm_range]
            
            atm_put_oi = atm_puts['oi'].sum()
            atm_call_oi = atm_calls['oi'].sum()
            atm_pcr = atm_put_oi / atm_call_oi if atm_call_oi > 0 else 0
            
            # PCR interpretation for NIFTY options
            if pcr_oi > 1.5:
                sentiment = 'EXTREMELY_BEARISH'
                signal = 'OVERSOLD_BOUNCE_EXPECTED'
                action = 'CONTRARIAN_BULLISH_OPPORTUNITY'
                confidence = 'HIGH'
            elif pcr_oi > 1.2:
                sentiment = 'BEARISH'
                signal = 'PUT_HEAVY_ACTIVITY'
                action = 'CAUTIOUS_BULLISH_BIAS'
                confidence = 'MODERATE'
            elif pcr_oi > 0.8:
                sentiment = 'NEUTRAL'
                signal = 'BALANCED_SENTIMENT'
                action = 'FOLLOW_UNDERLYING_TREND'
                confidence = 'MODERATE'
            elif pcr_oi > 0.6:
                sentiment = 'BULLISH'
                signal = 'CALL_HEAVY_ACTIVITY'
                action = 'CAUTIOUS_BEARISH_BIAS'
                confidence = 'MODERATE'
            else:
                sentiment = 'EXTREMELY_BULLISH'
                signal = 'OVERBOUGHT_CORRECTION_EXPECTED'
                action = 'CONTRARIAN_BEARISH_OPPORTUNITY'
                confidence = 'HIGH'
            
            return {
                'pcr_volume': round(pcr_volume, 3),
                'pcr_oi': round(pcr_oi, 3),
                'atm_pcr': round(atm_pcr, 3),
                'total_call_oi': int(total_call_oi),
                'total_put_oi': int(total_put_oi),
                'total_call_volume': int(total_call_volume),
                'total_put_volume': int(total_put_volume),
                'sentiment': sentiment,
                'signal': signal,
                'action': action,
                'confidence': confidence,
                'interpretation': f"PCR of {pcr_oi:.2f} indicates {sentiment.lower().replace('_', ' ')} market sentiment",
                'trading_strategies': self._get_pcr_strategies(pcr_oi, sentiment)
            }
            
        except Exception as e:
            return {'error': f'PCR calculation failed: {e}'}
    
    def _get_pcr_strategies(self, pcr: float, sentiment: str) -> List[str]:
        """Get specific trading strategies based on PCR"""
        if pcr > 1.3:  # Very high PCR - Oversold
            return [
                'Buy calls on any dip or support bounce',
                'Sell cash-secured puts below key support levels',
                'Bull call spreads for limited risk bullish plays',
                'Avoid buying puts due to high premium'
            ]
        elif pcr < 0.7:  # Very low PCR - Overbought
            return [
                'Buy puts on any rally or resistance rejection',
                'Sell covered calls above key resistance levels',
                'Bear put spreads for limited risk bearish plays',
                'Avoid buying calls due to high premium'
            ]
        else:  # Balanced PCR
            return [
                'Follow the underlying trend direction',
                'Use spreads to reduce premium costs',
                'Iron condors if expecting range-bound movement',
                'Straddles/strangles if expecting volatility expansion'
            ]
    
    def calculate_max_pain(self, options_df: pd.DataFrame, spot_price: float) -> Dict:
        """Calculate Max Pain analysis for expiry bias"""
        try:
            # Get all unique strikes
            strikes = sorted(options_df['strike'].unique())
            
            max_pain_data = []
            
            # Calculate total pain at each strike level
            for test_strike in strikes:
                total_pain = 0
                
                # Calculate pain for all options if expiry at this strike
                for _, option in options_df.iterrows():
                    strike = option['strike']
                    oi = option['oi']
                    option_type = option['option_type']
                    
                    if option_type == 'CE':  # Call options
                        if test_strike > strike:  # Call becomes ITM
                            pain = (test_strike - strike) * oi
                            total_pain += pain
                    else:  # Put options
                        if test_strike < strike:  # Put becomes ITM
                            pain = (strike - test_strike) * oi
                            total_pain += pain
                
                max_pain_data.append({
                    'strike': test_strike,
                    'total_pain': total_pain
                })
            
            # Find Max Pain (minimum pain point)
            max_pain_df = pd.DataFrame(max_pain_data)
            max_pain_strike = max_pain_df.loc[max_pain_df['total_pain'].idxmin(), 'strike']
            min_pain_value = max_pain_df['total_pain'].min()
            
            # Analysis relative to current spot
            distance_to_max_pain = max_pain_strike - spot_price
            distance_percent = (distance_to_max_pain / spot_price) * 100
            
            # Max Pain interpretation
            if abs(distance_percent) < 1:
                interpretation = f"Max Pain very close to current price - expect sideways movement"
                signal = 'NEUTRAL_EXPIRY'
                bias = 'RANGE_BOUND'
                probability = 'HIGH'
            elif distance_percent > 2:
                interpretation = f"Max Pain above current price - bullish expiry bias"
                signal = 'BULLISH_EXPIRY_BIAS'
                bias = 'UPWARD_PRESSURE'
                probability = 'MODERATE'
            elif distance_percent < -2:
                interpretation = f"Max Pain below current price - bearish expiry bias"
                signal = 'BEARISH_EXPIRY_BIAS'
                bias = 'DOWNWARD_PRESSURE'
                probability = 'MODERATE'
            else:
                interpretation = f"Max Pain shows mild directional bias"
                signal = 'MILD_DIRECTIONAL_BIAS'
                bias = 'WEAK_BIAS'
                probability = 'LOW'
            
            # Get top 5 most likely expiry zones
            likely_zones = max_pain_df.nsmallest(5, 'total_pain')['strike'].tolist()
            
            return {
                'max_pain_strike': max_pain_strike,
                'current_spot': spot_price,
                'distance_points': round(distance_to_max_pain, 1),
                'distance_percent': round(distance_percent, 2),
                'signal': signal,
                'bias': bias,
                'probability': probability,
                'interpretation': interpretation,
                'likely_expiry_zones': likely_zones,
                'min_pain_value': int(min_pain_value),
                'trading_strategies': self._get_max_pain_strategies(distance_percent, signal)
            }
            
        except Exception as e:
            return {'error': f'Max Pain calculation failed: {e}'}
    
    def _get_max_pain_strategies(self, distance_percent: float, signal: str) -> List[str]:
        """Get trading strategies based on Max Pain analysis"""
        if signal == 'NEUTRAL_EXPIRY':
            return [
                'Short straddles/strangles around current levels',
                'Iron condors with strikes around max pain',
                'Time decay strategies work well',
                'Avoid directional bets near expiry'
            ]
        elif signal == 'BULLISH_EXPIRY_BIAS':
            return [
                'Bull call spreads targeting max pain level',
                'Cash-secured puts below current levels',
                'Covered calls above max pain strike',
                'Expect gradual upward drift towards expiry'
            ]
        elif signal == 'BEARISH_EXPIRY_BIAS':
            return [
                'Bear put spreads targeting max pain level',
                'Covered calls at current levels',
                'Protective puts for long equity positions',
                'Expect gradual downward drift towards expiry'
            ]
        else:
            return [
                'Neutral strategies with slight directional hedge',
                'Quick profit taking on any directional moves',
                'Remain flexible as bias is weak',
                'Monitor for changes in OI buildup'
            ]
    
    def analyze_oi_buildup(self, options_df: pd.DataFrame, spot_price: float) -> Dict:
        """Analyze Open Interest buildup patterns"""
        try:
            # Separate calls and puts
            calls = options_df[options_df['option_type'] == 'CE'].copy()
            puts = options_df[options_df['option_type'] == 'PE'].copy()
            
            # Find highest OI strikes (key levels)
            top_call_strikes = calls.nlargest(5, 'oi')[['strike', 'oi']].to_dict('records')
            top_put_strikes = puts.nlargest(5, 'oi')[['strike', 'oi']].to_dict('records')
            
            # Key resistance/support from highest OI
            call_resistance = top_call_strikes[0]['strike'] if top_call_strikes else spot_price
            put_support = top_put_strikes[0]['strike'] if top_put_strikes else spot_price
            
            # Total OI analysis
            total_call_oi = calls['oi'].sum()
            total_put_oi = puts['oi'].sum()
            oi_ratio = total_call_oi / total_put_oi if total_put_oi > 0 else 1
            
            # Buildup pattern interpretation
            if total_call_oi > total_put_oi * 1.3:
                buildup_signal = 'CALL_HEAVY_BUILDUP'
                interpretation = 'Strong bullish sentiment with call accumulation'
                market_expectation = 'UPWARD_BREAKOUT_LIKELY'
                action = 'WATCH_FOR_BREAKOUT_ABOVE_RESISTANCE'
            elif total_put_oi > total_call_oi * 1.3:
                buildup_signal = 'PUT_HEAVY_BUILDUP'
                interpretation = 'Strong bearish sentiment with put accumulation'
                market_expectation = 'DOWNWARD_BREAKDOWN_LIKELY'
                action = 'WATCH_FOR_BREAKDOWN_BELOW_SUPPORT'
            else:
                buildup_signal = 'BALANCED_BUILDUP'
                interpretation = 'Balanced OI suggests range-bound movement'
                market_expectation = 'SIDEWAYS_MOVEMENT_EXPECTED'
                action = 'RANGE_TRADING_STRATEGIES'
            
            return {
                'current_spot': spot_price,
                'buildup_signal': buildup_signal,
                'interpretation': interpretation,
                'market_expectation': market_expectation,
                'recommended_action': action,
                'call_resistance': call_resistance,
                'put_support': put_support,
                'total_call_oi': int(total_call_oi),
                'total_put_oi': int(total_put_oi),
                'oi_ratio': round(oi_ratio, 2),
                'top_call_strikes': top_call_strikes,
                'top_put_strikes': top_put_strikes,
                'key_levels': {
                    'immediate_resistance': call_resistance,
                    'immediate_support': put_support,
                    'resistance_strength': top_call_strikes[0]['oi'] if top_call_strikes else 0,
                    'support_strength': top_put_strikes[0]['oi'] if top_put_strikes else 0
                }
            }
            
        except Exception as e:
            return {'error': f'OI buildup analysis failed: {e}'}
    
    def derive_overall_sentiment(self, pcr_analysis: Dict, max_pain_analysis: Dict, oi_buildup_analysis: Dict) -> Dict:
        """Derive overall market sentiment from all OI analyses"""
        try:
            sentiment_signals = []
            confidence_weights = []
            
            # PCR Analysis contribution (highest weight)
            if 'sentiment' in pcr_analysis:
                pcr_sentiment = pcr_analysis['sentiment']
                if 'BULLISH' in pcr_sentiment:
                    sentiment_signals.append('BULLISH')
                    confidence_weights.append(3)  # High weight for PCR
                elif 'BEARISH' in pcr_sentiment:
                    sentiment_signals.append('BEARISH')
                    confidence_weights.append(3)
                else:
                    sentiment_signals.append('NEUTRAL')
                    confidence_weights.append(1)
            
            # Max Pain contribution (moderate weight)
            if 'signal' in max_pain_analysis:
                max_pain_signal = max_pain_analysis['signal']
                if 'BULLISH' in max_pain_signal:
                    sentiment_signals.append('BULLISH')
                    confidence_weights.append(2)
                elif 'BEARISH' in max_pain_signal:
                    sentiment_signals.append('BEARISH')
                    confidence_weights.append(2)
                else:
                    sentiment_signals.append('NEUTRAL')
                    confidence_weights.append(1)
            
            # OI Buildup contribution (moderate weight)
            if 'buildup_signal' in oi_buildup_analysis:
                buildup_signal = oi_buildup_analysis['buildup_signal']
                if 'CALL_HEAVY' in buildup_signal:
                    sentiment_signals.append('BULLISH')
                    confidence_weights.append(2)
                elif 'PUT_HEAVY' in buildup_signal:
                    sentiment_signals.append('BEARISH')
                    confidence_weights.append(2)
                else:
                    sentiment_signals.append('NEUTRAL')
                    confidence_weights.append(1)
            
            # Calculate weighted sentiment
            bullish_weight = sum(w for s, w in zip(sentiment_signals, confidence_weights) if s == 'BULLISH')
            bearish_weight = sum(w for s, w in zip(sentiment_signals, confidence_weights) if s == 'BEARISH')
            neutral_weight = sum(w for s, w in zip(sentiment_signals, confidence_weights) if s == 'NEUTRAL')
            
            total_weight = sum(confidence_weights)
            
            # Determine overall sentiment
            if bullish_weight > bearish_weight and bullish_weight > neutral_weight:
                overall_sentiment = 'BULLISH'
                confidence = min(95, (bullish_weight / total_weight) * 100)
            elif bearish_weight > bullish_weight and bearish_weight > neutral_weight:
                overall_sentiment = 'BEARISH'
                confidence = min(95, (bearish_weight / total_weight) * 100)
            else:
                overall_sentiment = 'NEUTRAL'
                confidence = 50
            
            # Generate trading recommendations
            if overall_sentiment == 'BULLISH' and confidence > 70:
                recommendations = [
                    'Primary: Long calls or bull call spreads',
                    'Secondary: Sell puts for premium collection',
                    'Watch for breakout above key resistance levels',
                    'Consider covered calls on existing positions'
                ]
                risk_factors = [
                    'Monitor for reversal signals if PCR becomes extreme',
                    'Set stop losses below key support levels'
                ]
            elif overall_sentiment == 'BEARISH' and confidence > 70:
                recommendations = [
                    'Primary: Long puts or bear put spreads',
                    'Secondary: Sell calls for premium collection',
                    'Watch for breakdown below key support levels',
                    'Consider protective puts for long positions'
                ]
                risk_factors = [
                    'Monitor for reversal signals if PCR becomes extreme',
                    'Set stop losses above key resistance levels'
                ]
            else:
                recommendations = [
                    'Range-bound strategies: Iron condors, butterflies',
                    'Straddles/strangles if expecting volatility',
                    'Time decay strategies in low volatility environment',
                    'Wait for clearer directional signals'
                ]
                risk_factors = [
                    'Sideways movement can erode long premium positions',
                    'Monitor for breakout signals from the range'
                ]
            
            return {
                'overall_sentiment': overall_sentiment,
                'confidence_percent': round(confidence, 1),
                'signal_breakdown': {
                    'bullish_weight': bullish_weight,
                    'bearish_weight': bearish_weight,
                    'neutral_weight': neutral_weight,
                    'total_signals': len(sentiment_signals)
                },
                'primary_recommendations': recommendations,
                'risk_factors': risk_factors,
                'key_message': f"{overall_sentiment} sentiment with {confidence:.0f}% confidence",
                'action_plan': f"Focus on {overall_sentiment.lower()} strategies with proper risk management"
            }
            
        except Exception as e:
            return {'error': f'Overall sentiment analysis failed: {e}'}

def test_standalone_oi_analysis():
    """Test the standalone Open Interest analysis"""
    print("📊 Testing NIFTY Open Interest Analysis (Standalone)")
    print("=" * 70)
    
    # Initialize service
    oi_service = OpenInterestAnalysisService()
    
    # Generate realistic options chain data
    print("📈 Generating realistic NIFTY options chain data...")
    current_spot = 24833.6
    options_df = oi_service.generate_realistic_options_chain(current_spot, expiry_days=15)
    
    print(f"   ✅ Generated {len(options_df)} options contracts")
    print(f"📊 Current NIFTY Spot: ₹{current_spot:,.1f}")
    print(f"📈 Strikes Range: ₹{options_df['strike'].min():,} - ₹{options_df['strike'].max():,}")
    print(f"🔢 Calls/Puts: {len(options_df[options_df['option_type']=='CE'])} calls, {len(options_df[options_df['option_type']=='PE'])} puts")
    print()
    
    # Test 1: Put-Call Ratio Analysis
    print("1️⃣  Put-Call Ratio (PCR) Analysis")
    print("-" * 40)
    
    pcr_analysis = oi_service.calculate_put_call_ratio(options_df, current_spot)
    
    if 'error' not in pcr_analysis:
        print(f"   PCR (OI Based): {pcr_analysis['pcr_oi']}")
        print(f"   PCR (Volume Based): {pcr_analysis['pcr_volume']}")
        print(f"   ATM PCR: {pcr_analysis['atm_pcr']}")
        print(f"   Total Call OI: {pcr_analysis['total_call_oi']:,}")
        print(f"   Total Put OI: {pcr_analysis['total_put_oi']:,}")
        print(f"   Market Sentiment: {pcr_analysis['sentiment']}")
        print(f"   Signal: {pcr_analysis['signal']}")
        print(f"   Confidence: {pcr_analysis['confidence']}")
        print(f"   💡 {pcr_analysis['interpretation']}")
        print(f"   🎯 Action: {pcr_analysis['action']}")
        
        print(f"\n   📊 Trading Strategies:")
        for strategy in pcr_analysis['trading_strategies']:
            print(f"      • {strategy}")
    else:
        print(f"   ❌ {pcr_analysis['error']}")
    
    print()
    
    # Test 2: Max Pain Analysis
    print("2️⃣  Max Pain Analysis")
    print("-" * 40)
    
    max_pain_analysis = oi_service.calculate_max_pain(options_df, current_spot)
    
    if 'error' not in max_pain_analysis:
        print(f"   Max Pain Strike: ₹{max_pain_analysis['max_pain_strike']:,}")
        print(f"   Current Spot: ₹{max_pain_analysis['current_spot']:,}")
        print(f"   Distance: {max_pain_analysis['distance_points']:+.1f} points ({max_pain_analysis['distance_percent']:+.1f}%)")
        print(f"   Signal: {max_pain_analysis['signal']}")
        print(f"   Bias: {max_pain_analysis['bias']}")
        print(f"   Probability: {max_pain_analysis['probability']}")
        print(f"   💡 {max_pain_analysis['interpretation']}")
        
        print(f"\n   🎯 Top 3 Likely Expiry Zones:")
        for i, strike in enumerate(max_pain_analysis['likely_expiry_zones'][:3], 1):
            print(f"      {i}. ₹{strike:,}")
        
        print(f"\n   📊 Trading Strategies:")
        for strategy in max_pain_analysis['trading_strategies']:
            print(f"      • {strategy}")
    else:
        print(f"   ❌ {max_pain_analysis['error']}")
    
    print()
    
    # Test 3: OI Buildup Analysis
    print("3️⃣  Open Interest Buildup Analysis")
    print("-" * 40)
    
    oi_buildup_analysis = oi_service.analyze_oi_buildup(options_df, current_spot)
    
    if 'error' not in oi_buildup_analysis:
        print(f"   Buildup Signal: {oi_buildup_analysis['buildup_signal']}")
        print(f"   Total Call OI: {oi_buildup_analysis['total_call_oi']:,}")
        print(f"   Total Put OI: {oi_buildup_analysis['total_put_oi']:,}")
        print(f"   OI Ratio (C/P): {oi_buildup_analysis['oi_ratio']}")
        print(f"   💡 {oi_buildup_analysis['interpretation']}")
        print(f"   📈 Market Expectation: {oi_buildup_analysis['market_expectation']}")
        print(f"   🎯 {oi_buildup_analysis['recommended_action']}")
        
        print(f"\n   🔥 Key Levels from OI:")
        print(f"      Resistance (Call OI): ₹{oi_buildup_analysis['call_resistance']:,}")
        print(f"      Support (Put OI): ₹{oi_buildup_analysis['put_support']:,}")
        
        print(f"\n   📈 Top Call Strikes by OI:")
        for i, strike_data in enumerate(oi_buildup_analysis['top_call_strikes'][:3], 1):
            print(f"      {i}. ₹{strike_data['strike']:,} - OI: {strike_data['oi']:,}")
        
        print(f"\n   📉 Top Put Strikes by OI:")
        for i, strike_data in enumerate(oi_buildup_analysis['top_put_strikes'][:3], 1):
            print(f"      {i}. ₹{strike_data['strike']:,} - OI: {strike_data['oi']:,}")
    else:
        print(f"   ❌ {oi_buildup_analysis['error']}")
    
    print()
    
    # Test 4: Overall Market Sentiment
    print("4️⃣  Overall Market Sentiment (OI Based)")
    print("-" * 40)
    
    overall_sentiment = oi_service.derive_overall_sentiment(
        pcr_analysis, max_pain_analysis, oi_buildup_analysis
    )
    
    if 'error' not in overall_sentiment:
        print(f"   Overall Sentiment: {overall_sentiment['overall_sentiment']}")
        print(f"   Confidence: {overall_sentiment['confidence_percent']:.1f}%")
        
        breakdown = overall_sentiment['signal_breakdown']
        print(f"\n   📊 Signal Breakdown:")
        print(f"      Bullish Weight: {breakdown['bullish_weight']}")
        print(f"      Bearish Weight: {breakdown['bearish_weight']}")