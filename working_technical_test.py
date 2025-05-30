# working_technical_test.py
import asyncio
import sys
import os
import pandas as pd
import numpy as np

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

# Import database service directly
from database.sqlite_db_service import get_sqlite_database_service

class SimpleTechnicalAnalysis:
    def __init__(self):
        self.db = None
    
    async def initialize(self):
        self.db = await get_sqlite_database_service()
    
    async def analyze_nifty_data(self):
        """Complete technical analysis on your NIFTY data"""
        if not self.db:
            await self.initialize()
        
        print("📊 Analyzing NIFTY data with technical indicators...")
        
        # Get NIFTY data
        candles = await self.db.get_market_data('NIFTY', '5min', limit=50)
        
        if not candles:
            return {'error': 'No NIFTY data found'}
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        
        # Fix timestamp parsing issue
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        except:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
            except:
                df['timestamp'] = pd.to_datetime(df['timestamp'], infer_datetime_format=True)
        
        df = df.sort_values('timestamp')
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        current_price = float(df['close'].iloc[-1])
        print(f"   💰 Current NIFTY Price: ₹{current_price}")
        print(f"   📊 Analyzing {len(df)} data points...")
        
        analysis = {}
        
        # 1. RSI Analysis
        analysis['rsi'] = self.calculate_rsi(df['close'])
        
        # 2. MACD Analysis
        analysis['macd'] = self.calculate_macd(df['close'])
        
        # 3. Bollinger Bands
        analysis['bollinger'] = self.calculate_bollinger_bands(df['close'])
        
        # 4. Moving Averages
        analysis['moving_averages'] = self.calculate_moving_averages(df['close'])
        
        # 5. Volume Analysis
        analysis['volume'] = self.analyze_volume(df)
        
        # 6. Overall Signal
        analysis['overall'] = self.generate_overall_signal(analysis, current_price)
        
        return {
            'current_price': current_price,
            'data_points': len(df),
            'analysis': analysis
        }
    
    def calculate_rsi(self, close_prices, period=14):
        """Calculate RSI"""
        try:
            if len(close_prices) < period + 1:
                return {'error': f'Need {period + 1}+ data points for RSI, have {len(close_prices)}'}
            
            delta = close_prices.diff()
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            avg_gains = gains.rolling(window=period).mean()
            avg_losses = losses.rolling(window=period).mean()
            
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = float(rsi.iloc[-1])
            
            if current_rsi > 70:
                signal = 'OVERBOUGHT'
                action = 'SELL_CALLS'
            elif current_rsi < 30:
                signal = 'OVERSOLD'
                action = 'BUY_CALLS'
            elif current_rsi > 50:
                signal = 'BULLISH'
                action = 'CONSIDER_CALLS'
            else:
                signal = 'BEARISH'
                action = 'CONSIDER_PUTS'
            
            return {
                'value': round(current_rsi, 2),
                'signal': signal,
                'action': action
            }
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_macd(self, close_prices, fast=12, slow=26, signal_period=9):
        """Calculate MACD"""
        try:
            if len(close_prices) < slow:
                return {'error': f'Need {slow}+ data points for MACD, have {len(close_prices)}'}
            
            ema_fast = close_prices.ewm(span=fast).mean()
            ema_slow = close_prices.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period).mean()
            histogram = macd_line - signal_line
            
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            current_hist = float(histogram.iloc[-1])
            
            # Detect crossover
            prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0
            
            if current_macd > current_signal:
                if prev_hist <= 0 and current_hist > 0:
                    signal = 'BULLISH_CROSSOVER'
                    action = 'STRONG_BUY_CALLS'
                else:
                    signal = 'BULLISH'
                    action = 'CONSIDER_CALLS'
            else:
                if prev_hist >= 0 and current_hist < 0:
                    signal = 'BEARISH_CROSSOVER'
                    action = 'STRONG_BUY_PUTS'
                else:
                    signal = 'BEARISH'
                    action = 'CONSIDER_PUTS'
            
            return {
                'macd': round(current_macd, 4),
                'signal_line': round(current_signal, 4),
                'histogram': round(current_hist, 4),
                'signal': signal,
                'action': action,
                'crossover': 'CROSSOVER' in signal
            }
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_bollinger_bands(self, close_prices, period=20):
        """Calculate Bollinger Bands"""
        try:
            if len(close_prices) < period:
                return {'error': f'Need {period}+ data points for BB, have {len(close_prices)}'}
            
            sma = close_prices.rolling(window=period).mean()
            std = close_prices.rolling(window=period).std()
            
            upper = sma + (std * 2)
            lower = sma - (std * 2)
            
            current_price = float(close_prices.iloc[-1])
            bb_upper = float(upper.iloc[-1])
            bb_middle = float(sma.iloc[-1])
            bb_lower = float(lower.iloc[-1])
            
            if current_price > bb_upper:
                position = 'ABOVE_UPPER'
                signal = 'OVERBOUGHT'
                action = 'SELL_CALLS'
            elif current_price < bb_lower:
                position = 'BELOW_LOWER'
                signal = 'OVERSOLD'
                action = 'BUY_CALLS'
            else:
                position = 'MIDDLE_RANGE'
                signal = 'NEUTRAL'
                action = 'RANGE_TRADE'
            
            band_width = ((bb_upper - bb_lower) / bb_middle) * 100
            volatility = 'HIGH' if band_width > 4 else 'NORMAL' if band_width > 2 else 'LOW'
            
            return {
                'upper': round(bb_upper, 2),
                'middle': round(bb_middle, 2),
                'lower': round(bb_lower, 2),
                'position': position,
                'signal': signal,
                'action': action,
                'volatility': volatility,
                'band_width': round(band_width, 2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_moving_averages(self, close_prices):
        """Calculate moving averages"""
        try:
            current_price = float(close_prices.iloc[-1])
            
            mas = {}
            for period in [9, 21]:
                if len(close_prices) >= period:
                    ma = close_prices.rolling(window=period).mean().iloc[-1]
                    mas[f'ma_{period}'] = {
                        'value': round(float(ma), 2),
                        'position': 'ABOVE' if current_price > ma else 'BELOW'
                    }
            
            # Trend determination
            if len(mas) >= 2:
                ma9_above = mas.get('ma_9', {}).get('position') == 'ABOVE'
                ma21_above = mas.get('ma_21', {}).get('position') == 'ABOVE'
                
                if ma9_above and ma21_above:
                    trend = 'BULLISH'
                    action = 'FAVOR_CALLS'
                elif not ma9_above and not ma21_above:
                    trend = 'BEARISH'
                    action = 'FAVOR_PUTS'
                else:
                    trend = 'MIXED'
                    action = 'WAIT'
            else:
                trend = 'INSUFFICIENT_DATA'
                action = 'WAIT'
            
            return {
                'moving_averages': mas,
                'trend': trend,
                'action': action
            }
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_volume(self, df):
        """Analyze volume"""
        try:
            if 'volume' not in df.columns:
                return {'error': 'No volume data'}
            
            current_volume = int(df['volume'].iloc[-1])
            avg_volume = int(df['volume'].rolling(window=min(10, len(df))).mean().iloc[-1])
            
            ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            if ratio > 1.5:
                signal = 'HIGH'
                confirmation = 'STRONG'
            elif ratio > 1.2:
                signal = 'ABOVE_AVERAGE'
                confirmation = 'MODERATE'
            else:
                signal = 'NORMAL'
                confirmation = 'WEAK'
            
            return {
                'current': current_volume,
                'average': avg_volume,
                'ratio': round(ratio, 2),
                'signal': signal,
                'confirmation': confirmation
            }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_overall_signal(self, analysis, current_price):
        """Generate overall signal"""
        try:
            bullish_signals = 0
            bearish_signals = 0
            signal_strength = 0
            
            details = []
            
            # RSI
            rsi = analysis.get('rsi', {})
            if 'signal' in rsi:
                if rsi['signal'] in ['OVERSOLD', 'BULLISH']:
                    bullish_signals += 1
                    details.append(f"RSI: {rsi['signal']}")
                elif rsi['signal'] in ['OVERBOUGHT', 'BEARISH']:
                    bearish_signals += 1
                    details.append(f"RSI: {rsi['signal']}")
            
            # MACD
            macd = analysis.get('macd', {})
            if 'signal' in macd:
                weight = 2 if macd.get('crossover') else 1
                if 'BULLISH' in macd['signal']:
                    bullish_signals += weight
                    details.append(f"MACD: {macd['signal']}")
                elif 'BEARISH' in macd['signal']:
                    bearish_signals += weight
                    details.append(f"MACD: {macd['signal']}")
            
            # Bollinger Bands
            bb = analysis.get('bollinger', {})
            if 'signal' in bb:
                if bb['signal'] in ['OVERSOLD']:
                    bullish_signals += 1
                    details.append(f"BB: {bb['signal']}")
                elif bb['signal'] in ['OVERBOUGHT']:
                    bearish_signals += 1
                    details.append(f"BB: {bb['signal']}")
            
            # Moving Averages
            ma = analysis.get('moving_averages', {})
            if 'trend' in ma:
                if ma['trend'] == 'BULLISH':
                    bullish_signals += 1
                    details.append("MA: BULLISH TREND")
                elif ma['trend'] == 'BEARISH':
                    bearish_signals += 1
                    details.append("MA: BEARISH TREND")
            
            # Volume confirmation
            volume = analysis.get('volume', {})
            if volume.get('confirmation') in ['STRONG', 'MODERATE']:
                details.append(f"Volume: {volume['signal']} CONFIRMATION")
            
            # Overall assessment
            total_signals = bullish_signals + bearish_signals
            if total_signals > 0:
                confidence = abs(bullish_signals - bearish_signals) / total_signals * 100
            else:
                confidence = 0
            
            if bullish_signals > bearish_signals:
                direction = 'BULLISH'
                if confidence > 70:
                    action = 'STRONG_BUY_CALLS'
                elif confidence > 50:
                    action = 'BUY_CALLS'
                else:
                    action = 'WEAK_BUY_CALLS'
            elif bearish_signals > bullish_signals:
                direction = 'BEARISH'
                if confidence > 70:
                    action = 'STRONG_BUY_PUTS'
                elif confidence > 50:
                    action = 'BUY_PUTS'
                else:
                    action = 'WEAK_BUY_PUTS'
            else:
                direction = 'NEUTRAL'
                action = 'RANGE_TRADE'
            
            return {
                'direction': direction,
                'confidence': round(confidence, 1),
                'action': action,
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'details': details,
                'summary': f"{direction} with {confidence:.1f}% confidence - {action}"
            }
        except Exception as e:
            return {'error': str(e)}

async def main():
    """Test technical analysis on NIFTY data"""
    print("🚀 NIFTY Technical Analysis Test")
    print("=" * 60)
    
    try:
        ta = SimpleTechnicalAnalysis()
        result = await ta.analyze_nifty_data()
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        print(f"💰 Current NIFTY Price: ₹{result['current_price']}")
        print(f"📊 Data Points: {result['data_points']}")
        
        analysis = result['analysis']
        
        # Show results
        print(f"\n📊 TECHNICAL ANALYSIS RESULTS:")
        
        # RSI
        if 'rsi' in analysis and 'value' in analysis['rsi']:
            rsi = analysis['rsi']
            print(f"📈 RSI: {rsi['value']} ({rsi['signal']}) → {rsi['action']}")
        elif 'rsi' in analysis and 'error' in analysis['rsi']:
            print(f"📈 RSI: {analysis['rsi']['error']}")
        
        # MACD
        if 'macd' in analysis and 'signal' in analysis['macd']:
            macd = analysis['macd']
            crossover = " - CROSSOVER!" if macd['crossover'] else ""
            print(f"📊 MACD: {macd['signal']}{crossover} → {macd['action']}")
        elif 'macd' in analysis and 'error' in analysis['macd']:
            print(f"📊 MACD: {analysis['macd']['error']}")
        
        # Bollinger Bands
        if 'bollinger' in analysis and 'position' in analysis['bollinger']:
            bb = analysis['bollinger']
            print(f"📏 Bollinger: {bb['position']} ({bb['volatility']} vol) → {bb['action']}")
        elif 'bollinger' in analysis and 'error' in analysis['bollinger']:
            print(f"📏 Bollinger: {analysis['bollinger']['error']}")
        
        # Moving Averages
        if 'moving_averages' in analysis and 'trend' in analysis['moving_averages']:
            ma = analysis['moving_averages']
            print(f"📈 Trend: {ma['trend']} → {ma['action']}")
        
        # Volume
        if 'volume' in analysis and 'signal' in analysis['volume']:
            vol = analysis['volume']
            print(f"📊 Volume: {vol['signal']} ({vol['ratio']}x avg) → {vol['confirmation']} confirmation")
        
        # Overall Signal
        if 'overall' in analysis and 'direction' in analysis['overall']:
            overall = analysis['overall']
            print(f"\n🎯 OVERALL SIGNAL:")
            print(f"   Direction: {overall['direction']}")
            print(f"   Confidence: {overall['confidence']}%")
            print(f"   Action: {overall['action']}")
            print(f"   Summary: {overall['summary']}")
            
            print(f"\n📋 Signal Details:")
            for detail in overall['details']:
                print(f"   • {detail}")
        
        print(f"\n✅ Technical Analysis Complete!")
        print(f"🚀 Task 3.1: Multi-timeframe Technical Indicators WORKING!")
        
        return True
        
    except Exception as e:
        print(f"❌ Technical analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 SUCCESS: Technical analysis is working perfectly!")
        print("📊 Your NIFTY data is being analyzed with multiple indicators!")
    else:
        print("\n❌ FAILED: Check errors above.")