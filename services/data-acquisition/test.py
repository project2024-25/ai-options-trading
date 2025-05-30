"""
Quick test for Zerodha API permissions
"""

from kiteconnect import KiteConnect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('KITE_API_KEY')
access_token = os.getenv('KITE_ACCESS_TOKEN')

if not api_key or not access_token:
    print("❌ No credentials found in .env file")
    exit()

try:
    # Test connection
    kite = KiteConnect(api_key)
    kite.set_access_token(access_token)
    
    # Test profile (should always work)
    profile = kite.profile()
    print(f"✅ Connected as: {profile['user_name']}")
    
    # Test market data (requires permission)
    quote = kite.quote(['NSE:NIFTY 50'])
    nifty_price = quote['NSE:NIFTY 50']['last_price']
    print(f"✅ NIFTY: ₹{nifty_price}")
    
    print("🎉 All tests passed! Market data permission is working.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    
    if "Insufficient permission" in str(e):
        print("\n🔧 Solution:")
        print("1. Go to https://developers.kite.trade/apps")
        print("2. Click on your app")
        print("3. Enable 'Market Data' permission")
        print("4. Regenerate access token")
    else:
        print("This might be a different issue. Check your credentials.")