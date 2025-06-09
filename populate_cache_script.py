#!/usr/bin/env python3
"""
Populate Cache with Live Data Script
Get current live market data and save to cache for after-hours use
"""

import json
import os
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect
from dotenv import load_dotenv

def populate_cache_with_live_data():
    """Get live data and populate cache"""
    print("📊 POPULATING CACHE WITH LIVE MARKET DATA")
    print("=" * 50)
    
    # Load credentials
    load_dotenv()
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    if not api_key or not access_token:
        print("❌ Missing Kite API credentials")
        return False
    
    try:
        # Initialize Kite
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test connection
        profile = kite.profile()
        print(f"✅ Connected as: {profile['user_name']}")
        
        # Get live quotes
        print("\n📈 Fetching live market data...")
        quotes = kite.quote(["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:INDIA VIX"])
        
        # Prepare cache directory
        cache_dir = Path("services/data-acquisition/app/data_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare cache data
        cache_data = {}
        current_time = datetime.now()
        
        # NIFTY data
        if "NSE:NIFTY 50" in quotes:
            nifty = quotes["NSE:NIFTY 50"]
            cache_data["NIFTY"] = {
                "symbol": "NIFTY",
                "ltp": nifty["last_price"],
                "open": nifty.get("ohlc", {}).get("open", 0),
                "high": nifty.get("ohlc", {}).get("high", 0),
                "low": nifty.get("ohlc", {}).get("low", 0),
                "close": nifty.get("ohlc", {}).get("close", 0),
                "change": nifty.get("net_change", 0),
                "volume": nifty.get("volume", 0),
                "oi": nifty.get("oi", 0),
                "instrument_token": 256265,
                "timestamp": current_time.isoformat(),
                "cached_at": current_time.isoformat(),
                "market_time": "15:30" if current_time.hour >= 15 else current_time.strftime("%H:%M")
            }
            print(f"✅ NIFTY: ₹{nifty['last_price']} (Change: {nifty.get('net_change', 0):+.2f})")
        
        # BANKNIFTY data
        if "NSE:NIFTY BANK" in quotes:
            banknifty = quotes["NSE:NIFTY BANK"]
            cache_data["BANKNIFTY"] = {
                "symbol": "BANKNIFTY",
                "ltp": banknifty["last_price"],
                "open": banknifty.get("ohlc", {}).get("open", 0),
                "high": banknifty.get("ohlc", {}).get("high", 0),
                "low": banknifty.get("ohlc", {}).get("low", 0),
                "close": banknifty.get("ohlc", {}).get("close", 0),
                "change": banknifty.get("net_change", 0),
                "volume": banknifty.get("volume", 0),
                "oi": banknifty.get("oi", 0),
                "instrument_token": 260105,
                "timestamp": current_time.isoformat(),
                "cached_at": current_time.isoformat(),
                "market_time": "15:30" if current_time.hour >= 15 else current_time.strftime("%H:%M")
            }
            print(f"✅ BANKNIFTY: ₹{banknifty['last_price']} (Change: {banknifty.get('net_change', 0):+.2f})")
        
        # VIX data
        if "NSE:INDIA VIX" in quotes:
            vix = quotes["NSE:INDIA VIX"]
            cache_data["VIX"] = {
                "symbol": "VIX",
                "ltp": vix["last_price"],
                "open": vix.get("ohlc", {}).get("open", 0),
                "high": vix.get("ohlc", {}).get("high", 0),
                "low": vix.get("ohlc", {}).get("low", 0),
                "close": vix.get("ohlc", {}).get("close", 0),
                "change": vix.get("net_change", 0),
                "instrument_token": 264969,
                "timestamp": current_time.isoformat(),
                "cached_at": current_time.isoformat(),
                "market_time": "15:30" if current_time.hour >= 15 else current_time.strftime("%H:%M")
            }
            print(f"✅ VIX: {vix['last_price']} (Change: {vix.get('net_change', 0):+.2f})")
        
        # Save to cache file
        cache_file = cache_dir / "last_live_data.json"
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"\n🎉 CACHE POPULATED SUCCESSFULLY!")
        print(f"   Cache file: {cache_file}")
        print(f"   Symbols cached: {list(cache_data.keys())}")
        print(f"   Cache time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test cache retrieval
        print(f"\n🧪 TESTING CACHE RETRIEVAL:")
        with open(cache_file, 'r') as f:
            test_data = json.load(f)
        
        for symbol in ["NIFTY", "BANKNIFTY", "VIX"]:
            if symbol in test_data:
                data = test_data[symbol]
                print(f"   {symbol}: ₹{data['ltp']} (cached at {data['cached_at'][:19]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating cache: {e}")
        return False

def test_enhanced_service():
    """Test if the enhanced service is working"""
    print(f"\n🧪 TESTING ENHANCED SERVICE")
    print("=" * 35)
    
    try:
        import requests
        
        # Test NIFTY endpoint
        response = requests.get("http://localhost:8001/api/data/nifty-snapshot", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            source = data.get('source', 'unknown')
            ltp = data.get('data', {}).get('ltp', 'N/A')
            
            print(f"✅ NIFTY Endpoint: Working")
            print(f"   Source: {source}")
            print(f"   LTP: ₹{ltp}")
            
            if source == "last_live_data":
                note = data.get('data', {}).get('note', '')
                print(f"   Note: {note}")
                print(f"🎉 SUCCESS: Service is using cached live data!")
                return True
            elif source == "kite_live":
                print(f"🎉 SUCCESS: Service is using live data!")
                return True
            else:
                print(f"⚠️ Service is using {source} data")
                return False
        else:
            print(f"❌ Service test failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Service test error: {e}")
        print(f"   Make sure Data Acquisition service is running on port 8001")
        return False

if __name__ == "__main__":
    print("🔧 LIVE DATA CACHE POPULATION TOOL")
    print("=" * 45)
    print("This will fetch current live market data and save it to cache")
    print("for use outside market hours.\n")
    
    # Populate cache
    success = populate_cache_with_live_data()
    
    if success:
        # Test the enhanced service
        test_enhanced_service()
        
        print(f"\n🎯 WHAT'S NEXT:")
        print(f"1. ✅ Cache is populated with live data")
        print(f"2. ✅ Your service will now show real market prices outside hours")
        print(f"3. 🔄 Restart your Data Acquisition service to pick up changes")
        print(f"4. 🧪 Test: curl http://localhost:8001/api/data/nifty-snapshot")
        print(f"\nInstead of 'mock_data', you should now see 'last_live_data'!")
        
    else:
        print(f"\n❌ CACHE POPULATION FAILED")
        print(f"1. Check your Kite API credentials")
        print(f"2. Ensure you have internet connectivity")
        print(f"3. Verify Kite API token is not expired")
        print(f"4. Try running setup_zerodha.py to refresh token")
    
    print(f"\nScript completed.")