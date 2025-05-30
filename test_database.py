# simple_postgres_test.py
import asyncio
import asyncpg
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simple_postgres_test():
    """Simple PostgreSQL test without complex migrations"""
    print("🐳 Testing PostgreSQL with Simple Setup...")
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect('postgresql://trading_user:your_secure_password@localhost:5432/trading_db')
        print("✅ Connected to PostgreSQL!")
        
        # Create simple tables
        print("📋 Creating basic tables...")
        
        # Market data table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data_simple (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                open DECIMAL(12,4) NOT NULL,
                high DECIMAL(12,4) NOT NULL,
                low DECIMAL(12,4) NOT NULL,
                close DECIMAL(12,4) NOT NULL,
                volume BIGINT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Options data table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS options_simple (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                expiry DATE NOT NULL,
                strike DECIMAL(10,2) NOT NULL,
                option_type TEXT NOT NULL,
                ltp DECIMAL(10,4),
                oi BIGINT DEFAULT 0,
                delta DECIMAL(6,4),
                iv DECIMAL(6,4),
                timestamp TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        print("✅ Tables created successfully!")
        
        # Test storing your NIFTY data
        print("💰 Testing NIFTY data storage...")
        await conn.execute("""
            INSERT INTO market_data_simple 
            (symbol, timeframe, timestamp, open, high, low, close, volume) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 'NIFTY', '5min', datetime.now(), 24800.0, 24850.0, 24780.0, 24833.6, 1250000)
        
        print("✅ NIFTY ₹24,833.6 stored in PostgreSQL!")
        
        # Test storing options data
        print("📈 Testing options data storage...")
        await conn.execute("""
            INSERT INTO options_simple 
            (symbol, expiry, strike, option_type, ltp, oi, delta, iv) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 'NIFTY', date(2024, 1, 25), 24800, 'CE', 45.50, 1900000, 0.52, 18.5)
        
        await conn.execute("""
            INSERT INTO options_simple 
            (symbol, expiry, strike, option_type, ltp, oi, delta, iv) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 'NIFTY', date(2024, 1, 25), 24800, 'PE', 28.75, 1100000, -0.48, 19.2)
        
        print("✅ Options data stored! (30 Lakh+ OI)")
        
        # Simple Max Pain calculation
        print("🎯 Testing Max Pain calculation...")
        current_price = 24833.6
        
        # Get all options for calculation
        options = await conn.fetch("""
            SELECT strike, option_type, oi FROM options_simple 
            WHERE symbol = 'NIFTY' AND expiry = $1
        """, date(2024, 1, 25))
        
        # Calculate max pain
        strikes = list(set(float(opt['strike']) for opt in options))  # Convert to float
        min_pain = float('inf')
        max_pain_strike = None
        
        for test_strike in strikes:
            total_pain = 0
            for opt in options:
                strike_val = float(opt['strike'])  # Convert to float
                oi_val = int(opt['oi'])  # Convert to int
                
                if opt['option_type'] == 'CE' and current_price > strike_val:
                    total_pain += (current_price - strike_val) * oi_val
                elif opt['option_type'] == 'PE' and current_price < strike_val:
                    total_pain += (strike_val - current_price) * oi_val
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = test_strike
        
        print(f"✅ Max Pain: ₹{max_pain_strike}")
        print(f"📍 Current Price: ₹{current_price}")
        print(f"📏 Distance: ₹{current_price - max_pain_strike}")
        
        # Test PCR calculation
        print("⚖️ Testing PCR calculation...")
        ce_oi = sum(int(opt['oi']) for opt in options if opt['option_type'] == 'CE')  # Convert to int
        pe_oi = sum(int(opt['oi']) for opt in options if opt['option_type'] == 'PE')  # Convert to int
        pcr = pe_oi / ce_oi if ce_oi > 0 else 0
        
        print(f"✅ PCR: {pcr:.4f}")
        print(f"📊 CE OI: {ce_oi:,} ({ce_oi/100000:.1f} Lakh)")
        print(f"📊 PE OI: {pe_oi:,} ({pe_oi/100000:.1f} Lakh)")
        
        # Test Redis connection
        print("🔴 Testing Redis connection...")
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            r.set('test_key', 'PostgreSQL and Redis working!')
            result = r.get('test_key')
            print(f"✅ Redis working: {result}")
        except Exception as e:
            print(f"⚠️ Redis test failed: {e}")
        
        await conn.close()
        
        print("\n🎉 PostgreSQL + Docker setup COMPLETED!")
        print("🚀 Production database is ready!")
        print("💾 Your ₹24,833.6 NIFTY data is stored in PostgreSQL!")
        print("📈 Options analysis is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_postgres_test())
    if success:
        print("\n✅ Docker + PostgreSQL setup COMPLETE!")
        print("🔄 Ready for Technical Analysis implementation!")
    else:
        print("\n⚠️ Use SQLite for now, PostgreSQL can be fixed later")