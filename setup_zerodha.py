"""
Setup script for Zerodha API credentials and testing
"""

import os
import json
from datetime import datetime
from kiteconnect import KiteConnect


def setup_credentials():
    """Interactive setup for Zerodha credentials"""
    print("=== Zerodha API Credentials Setup ===\n")
    
    # Get API credentials
    api_key = input("Enter your Kite API Key: ").strip()
    if not api_key:
        print("API Key is required!")
        return False
    
    api_secret = input("Enter your Kite API Secret: ").strip()
    if not api_secret:
        print("API Secret is required!")
        return False
    
    # Generate login URL
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()
    
    print(f"\n1. Open this URL in your browser:")
    print(f"   {login_url}")
    print("\n2. Login with your Zerodha credentials")
    print("3. After login, you'll be redirected to a URL with 'request_token' parameter")
    print("4. Copy the 'request_token' value from the URL")
    
    request_token = input("\nEnter the request_token from URL: ").strip()
    if not request_token:
        print("Request token is required!")
        return False
    
    try:
        # Generate session
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        print(f"\n✅ Successfully generated access token!")
        print(f"Access Token: {access_token}")
        
        # Test the connection
        kite.set_access_token(access_token)
        profile = kite.profile()
        
        print(f"\n✅ Connection test successful!")
        print(f"Connected as: {profile['user_name']} ({profile['email']})")
        
        # Save to .env file
        save_to_env(api_key, access_token)
        
        # Test market data
        test_market_data(kite)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def save_to_env(api_key: str, access_token: str):
    """Save credentials to .env file"""
    env_content = f"""# Zerodha API Credentials
KITE_API_KEY={api_key}
KITE_ACCESS_TOKEN={access_token}

# Service Configuration
DATA_ACQUISITION_PORT=8001
DEBUG_MODE=true
LOG_LEVEL=INFO

# MCP Configuration
MCP_URL=wss://api.kite.trade/ws
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"\n✅ Credentials saved to .env file")
        
    except Exception as e:
        print(f"\n❌ Error saving .env file: {e}")


def test_market_data(kite: KiteConnect):
    """Test market data retrieval with better error handling"""
    print("\n=== Testing Market Data ===")
    
    try:
        # Test NIFTY data
        nifty_quote = kite.quote(["NSE:NIFTY 50"])
        nifty_data = nifty_quote["NSE:NIFTY 50"]
        
        print(f"NIFTY 50:")
        print(f"  LTP: ₹{nifty_data['last_price']}")
        
        # Handle different field names for change percentage
        change_pct = (nifty_data.get('oi_day_change_percentage') or 
                     nifty_data.get('change_percent') or 
                     nifty_data.get('net_change_percentage') or 0)
        
        print(f"  Change: {nifty_data.get('net_change', 0)} ({change_pct:.2f}%)")
        print(f"  Volume: {nifty_data.get('volume', 0):,}")
        print(f"  Open: ₹{nifty_data.get('ohlc', {}).get('open', 0)}")
        print(f"  High: ₹{nifty_data.get('ohlc', {}).get('high', 0)}")
        print(f"  Low: ₹{nifty_data.get('ohlc', {}).get('low', 0)}")
        
        # Test BANKNIFTY data
        banknifty_quote = kite.quote(["NSE:NIFTY BANK"])
        banknifty_data = banknifty_quote["NSE:NIFTY BANK"]
        
        change_pct_bn = (banknifty_data.get('oi_day_change_percentage') or 
                        banknifty_data.get('change_percent') or 
                        banknifty_data.get('net_change_percentage') or 0)
        
        print(f"\nBANKNIFTY:")
        print(f"  LTP: ₹{banknifty_data['last_price']}")
        print(f"  Change: {banknifty_data.get('net_change', 0)} ({change_pct_bn:.2f}%)")
        print(f"  Volume: {banknifty_data.get('volume', 0):,}")
        
        # Get instruments for options
        print(f"\n=== Testing Options Data ===")
        instruments = kite.instruments("NFO")
        
        # Find NIFTY options
        nifty_options = [
            inst for inst in instruments 
            if inst['name'] == 'NIFTY' and inst['instrument_type'] in ['CE', 'PE']
        ]
        
        print(f"Found {len(nifty_options)} NIFTY options instruments")
        
        # Find BANKNIFTY options
        banknifty_options = [
            inst for inst in instruments 
            if inst['name'] == 'BANKNIFTY' and inst['instrument_type'] in ['CE', 'PE']
        ]
        
        print(f"Found {len(banknifty_options)} BANKNIFTY options instruments")
        
        # Test options quote (get a few ATM options)
        if nifty_options:
            # Find ATM options for current expiry
            current_price = nifty_data['last_price']
            atm_strike = round(current_price / 50) * 50  # Round to nearest 50
            
            # Get current and next expiry options
            current_date = datetime.now().date()
            
            atm_options = []
            for inst in nifty_options:
                try:
                    if (inst['strike'] == atm_strike and 
                        datetime.strptime(inst['expiry'], '%Y-%m-%d').date() >= current_date):
                        atm_options.append(inst)
                        if len(atm_options) >= 4:  # Get first 4 ATM options
                            break
                except:
                    continue
            
            if atm_options:
                option_tokens = [f"NFO:{opt['tradingsymbol']}" for opt in atm_options]
                
                try:
                    option_quotes = kite.quote(option_tokens)
                    
                    print(f"\nSample NIFTY {atm_strike} Options:")
                    for token in option_tokens:
                        if token in option_quotes:
                            opt_data = option_quotes[token]
                            symbol = token.replace("NFO:", "")
                            volume = opt_data.get('volume', 0)
                            oi = opt_data.get('oi', 0)
                            print(f"  {symbol}: ₹{opt_data['last_price']} (Vol: {volume:,}, OI: {oi:,})")
                            
                except Exception as opt_error:
                    print(f"  Could not fetch options quotes: {opt_error}")
        
        # Test VIX data
        try:
            vix_quote = kite.quote(["NSE:INDIA VIX"])
            vix_data = vix_quote["NSE:INDIA VIX"]
            
            vix_change_pct = (vix_data.get('oi_day_change_percentage') or 
                             vix_data.get('change_percent') or 
                             vix_data.get('net_change_percentage') or 0)
            
            print(f"\nINDIA VIX:")
            print(f"  LTP: {vix_data['last_price']}")
            print(f"  Change: {vix_data.get('net_change', 0)} ({vix_change_pct:.2f}%)")
            
        except Exception as vix_error:
            print(f"\nVIX data not available: {vix_error}")
        
        print(f"\n✅ Market data test successful!")
        
        # Save sample data for reference  
        save_sample_data({
            "nifty": {
                "ltp": nifty_data['last_price'],
                "change": nifty_data.get('net_change', 0),
                "volume": nifty_data.get('volume', 0),
                "ohlc": nifty_data.get('ohlc', {})
            },
            "banknifty": {
                "ltp": banknifty_data['last_price'],
                "change": banknifty_data.get('net_change', 0),
                "volume": banknifty_data.get('volume', 0)
            },
            "instruments_count": {
                "nifty_options": len(nifty_options),
                "banknifty_options": len(banknifty_options)
            },
            "timestamp": datetime.now().isoformat()
        })
        
        return True
        
    except Exception as e:
        print(f"\n❌ Market data test failed: {e}")
        print("This might be due to market hours or API field changes")
        return False


def save_sample_data(data: dict):
    """Save sample data to JSON file for reference"""
    try:
        with open('sample_market_data.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print("📄 Sample market data saved to sample_market_data.json")
    except Exception as e:
        print(f"Warning: Could not save sample data: {e}")


def test_websocket_connection():
    """Test WebSocket connection (simplified)"""
    print("\n=== Testing WebSocket Connection ===")
    
    try:
        # This is a simplified test - actual WebSocket testing requires more setup
        print("WebSocket testing requires the full MCP client implementation")
        print("Once you start the service with valid credentials, it will test WebSocket automatically")
        
        # Basic WebSocket test
        import asyncio
        import websockets
        
        async def test_ws():
            try:
                # Test basic WebSocket connectivity to Kite
                uri = "wss://api.kite.trade/ws"
                async with websockets.connect(uri, timeout=5) as websocket:
                    print("✅ WebSocket connection test successful")
                    return True
            except Exception as e:
                print(f"❌ WebSocket connection test failed: {e}")
                return False
        
        # Run async test
        result = asyncio.run(test_ws())
        return result
        
    except Exception as e:
        print(f"WebSocket test error: {e}")
        return False


def validate_existing_env():
    """Validate existing .env file"""
    if not os.path.exists('.env'):
        print("No .env file found. Please run setup first.")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('KITE_API_KEY')
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if not api_key or not access_token:
            print("Missing credentials in .env file")
            return False
        
        # Test connection
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        profile = kite.profile()
        print(f"✅ Existing credentials valid for: {profile['user_name']} ({profile['email']})")
        
        # Show account details
        print(f"   Account ID: {profile['user_id']}")
        print(f"   Broker: {profile['broker']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Credential validation failed: {e}")
        print("You may need to regenerate your access token (they expire daily)")
        return False


def show_account_info():
    """Show detailed account information"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('KITE_API_KEY')
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if not api_key or not access_token:
            print("No credentials found. Please run setup first.")
            return
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        print("\n=== Account Information ===")
        
        # Get profile
        profile = kite.profile()
        print(f"Name: {profile['user_name']}")
        print(f"Email: {profile['email']}")
        print(f"Phone: {profile['phone']}")
        print(f"User ID: {profile['user_id']}")
        print(f"Broker: {profile['broker']}")
        
        # Get margins
        margins = kite.margins()
        print(f"\n=== Account Margins ===")
        for segment, data in margins.items():
            print(f"{segment.upper()}:")
            print(f"  Available: ₹{data.get('available', {}).get('cash', 0):,.2f}")
            print(f"  Used: ₹{data.get('utilised', {}).get('debits', 0):,.2f}")
        
        # Get positions (if any)
        try:
            positions = kite.positions()
            if positions['day'] or positions['net']:
                print(f"\n=== Current Positions ===")
                for pos in positions['net']:
                    if pos['quantity'] != 0:
                        print(f"{pos['tradingsymbol']}: {pos['quantity']} @ ₹{pos['average_price']}")
            else:
                print(f"\n=== Current Positions ===")
                print("No open positions")
        except Exception as pos_error:
            print(f"Could not fetch positions: {pos_error}")
        
    except Exception as e:
        print(f"Error getting account info: {e}")


def regenerate_access_token():
    """Regenerate access token (they expire daily)"""
    print("\n=== Regenerate Access Token ===")
    print("Access tokens expire daily and need to be regenerated")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('KITE_API_KEY')
        if not api_key:
            print("No API key found. Please run full setup first.")
            return False
        
        api_secret = input("Enter your Kite API Secret: ").strip()
        if not api_secret:
            print("API Secret is required!")
            return False
        
        # Generate new login URL
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        
        print(f"\n1. Open this URL in your browser:")
        print(f"   {login_url}")
        print("\n2. Login and get the request_token from redirect URL")
        
        request_token = input("\nEnter the new request_token: ").strip()
        if not request_token:
            print("Request token is required!")
            return False
        
        # Generate new session
        data = kite.generate_session(request_token, api_secret=api_secret)
        new_access_token = data["access_token"]
        
        # Update .env file
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                content = f.read()
            
            # Replace access token line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('KITE_ACCESS_TOKEN='):
                    lines[i] = f'KITE_ACCESS_TOKEN={new_access_token}'
                    break
            
            with open('.env', 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"\n✅ Access token updated successfully!")
            print(f"New token: {new_access_token}")
            
            # Test new token
            kite.set_access_token(new_access_token)
            profile = kite.profile()
            print(f"✅ Token validated for: {profile['user_name']}")
            
            return True
        
    except Exception as e:
        print(f"\n❌ Error regenerating token: {e}")
        return False


def main():
    """Main setup function"""
    print("Zerodha API Setup and Testing Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Setup new credentials")
        print("2. Validate existing credentials")
        print("3. Test market data")
        print("4. Show account information")
        print("5. Regenerate access token")
        print("6. Test WebSocket connection")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            setup_credentials()
        elif choice == '2':
            validate_existing_env()
        elif choice == '3':
            if validate_existing_env():
                from dotenv import load_dotenv
                load_dotenv()
                kite = KiteConnect(api_key=os.getenv('KITE_API_KEY'))
                kite.set_access_token(os.getenv('KITE_ACCESS_TOKEN'))
                test_market_data(kite)
        elif choice == '4':
            show_account_info()
        elif choice == '5':
            regenerate_access_token()
        elif choice == '6':
            test_websocket_connection()
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()