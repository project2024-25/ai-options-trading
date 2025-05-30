# add_sample_nifty_data.py
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from database.sqlite_db_service import get_sqlite_database_service

async def add_sample_data():
    """Add sample NIFTY data for technical analysis testing"""
    print("📊 Adding sample NIFTY data for technical analysis...")
    
    try:
        db = await get_sqlite_database_service()
        
        # Generate realistic NIFTY 5-minute candles around your current ₹24,833.6 price
        base_price = 24833.6
        base_time = datetime.now() - timedelta(hours=2)  # Start 2 hours ago
        
        sample_candles = []
        current_price = base_price - 50  # Start slightly lower
        
        # Generate 30 candles (enough for RSI calculation)
        for i in range(30):
            # Simulate realistic price movement
            volatility = 15  # NIFTY typical 5-min volatility
            price_change = (hash(str(i)) % 21 - 10) * volatility / 10  # Random movement
            
            open_price = current_price
            high_price = open_price + abs(price_change) + (hash(str(i*2)) % 10)
            low_price = open_price - abs(price_change) - (hash(str(i*3)) % 8)
            close_price = open_price + price_change
            
            # Ensure logical OHLC relationship
            high_price = max(open_price, close_price, high_price)
            low_price = min(open_price, close_price, low_price)
            
            # Generate volume
            base_volume = 1000000
            volume = base_volume + (hash(str(i*4)) % 500000)
            
            candle = {
                'timestamp': base_time + timedelta(minutes=i*5),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            }
            
            sample_candles.append(candle)
            current_price = close_price
        
        # Make the last candle your current ₹24,833.6 price
        sample_candles[-1]['close'] = 24833.6
        sample_candles[-1]['high'] = max(sample_candles[-1]['high'], 24833.6)
        sample_candles[-1]['low'] = min(sample_candles[-1]['low'], 24833.6)
        
        # Store all candles
        stored_count = 0
        for candle in sample_candles:
            success = await db.store_market_data('NIFTY', '5min', candle)
            if success:
                stored_count += 1
        
        print(f"✅ Added {stored_count} NIFTY 5-minute candles")
        print(f"💰 Latest price: ₹{sample_candles[-1]['close']}")
        print(f"📈 Price range: ₹{min(c['low'] for c in sample_candles):.2f} - ₹{max(c['high'] for c in sample_candles):.2f}")
        
        # Verify data
        all_candles = await db.get_market_data('NIFTY', '5min', limit=50)
        print(f"📊 Total NIFTY candles in database: {len(all_candles)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add sample data: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(add_sample_data())
    if success:
        print("\n🎉 Sample data added successfully!")
        print("📊 Now ready for full technical analysis testing!")
        print("💡 Run: python test_nifty_technical_analysis.py")
    else:
        print("\n❌ Failed to add sample data")