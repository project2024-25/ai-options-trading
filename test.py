# simple_technical_test.py
import asyncio
import sys
import os
import pandas as pd
import numpy as np

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from database.sqlite_db_service import get_sqlite_database_service

async def simple_technical_analysis():
    """Simple technical analysis test on your NIFTY data"""
    print("🚀 Simple Technical Analysis Test")
    print("📊 Testing basic RSI calculation on your NIFTY data")
    
    try:
        # Get database connection
        db = await get_sqlite_database_service()
        
        # Get your NIFTY data
        candles = await db.get_market_data('NIFTY', '5min', limit=20)
        
        if not candles:
            print("❌ No NIFTY data found!")
            return False
        
        print(f"📈 Found {len(candles)} NIFTY candles")
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df['close'] = pd.to_numeric(df['close'])
        df = df.sort_values('timestamp')
        
        current_price = float(df['close'].iloc[-1])
        print(f"💰 Current NIFTY Price: ₹{current_price}")
        
        # Simple RSI calculation
        if len(df) >= 14:
            delta = df['close'].diff()
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            avg_gains = gains.rolling(window=14).mean()
            avg_losses = losses.rolling(window=14).mean()
            
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = float(rsi.iloc[-1])
            
            print(f"📊 Current RSI: {current_rsi:.2f}")
            
            # RSI interpretation
            if current_rsi > 70:
                signal = "OVERBOUGHT - Consider selling calls"
            elif current_rsi < 30:
                signal = "OVERSOLD - Consider buying calls"
            elif current_rsi > 50:
                signal = "BULLISH - Consider long positions"
            else:
                signal = "BEARISH - Consider short positions"
            
            print(f"🎯 RSI Signal: {signal}")
            
        else:
            print("⚠️ Not enough data for RSI calculation")
        
        # Simple Moving Average
        if len(df) >= 9:
            ma_9 = df['close'].rolling(window=9).mean().iloc[-1]
            ma_21 = df['close'].rolling(window=min(21, len(df))).mean().iloc[-1]
            
            print(f"📈 MA(9): ₹{ma_9:.2f}")
            print(f"📈 MA(21): ₹{ma_21:.2f}")
            
            if current_price > ma_9:
                print("🎯 Price above MA(9) - Short term bullish")
            else:
                print("🎯 Price below MA(9) - Short term bearish")
        
        print("\n✅ Simple technical analysis completed!")
        print("🚀 Basic indicators are working on your NIFTY data!")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple technical analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_technical_analysis())
    if success:
        print("\n🎉 Basic technical analysis working!")
        print("📊 Ready to implement full technical analysis service!")
    else:
        print("\n❌ Need to debug basic setup first.")



        {
	"blocks": [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "🚨 *TRADING SIGNAL ALERT*\n*Index:* NIFTY\n*Strategy:* Bull Call Spread (DEBIT)\n*Confidence:* 73.5%\n*Entry:* Buy: ₹245.66, Sell: ₹202.58\n*Target:* ₹1,385\n*Stop Loss:* ₹8,615"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"emoji": true,
						"text": "Approve"
					},
					"style": "primary",
					"action_id": "approve_trade",
					"value": "2025-06-01 11:14:48_NIFTY_Bull_Call_Spread_(DEBIT)"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"emoji": true,
						"text": "Reject"
					},
					"style": "danger",
					"action_id": "reject_trade",
					"value": "2025-06-01 11:14:48_NIFTY_Bull_Call_Spread_(DEBIT)"
				}
			]
		}
	]
}