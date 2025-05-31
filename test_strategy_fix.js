// File: test_strategy_fix.js
// Quick test script to verify the strategy service integration

async function testStrategyIntegration() {
    console.log('Testing Strategy Service Integration...\n');
    
    try {
      // Test 1: Get market data
      console.log('1. Testing market data...');
      const marketResponse = await fetch('http://localhost:8001/api/data/nifty-snapshot');
      const marketData = await marketResponse.json();
      console.log('Market data:', marketData.data?.price || 'No price data');
      
      // Test 2: Get VIX data
      console.log('\n2. Testing VIX data...');
      const vixResponse = await fetch('http://localhost:8001/api/data/vix-data');
      const vixData = await vixResponse.json();
      console.log('VIX data:', vixData.data?.current_vix || 'No VIX data');
      
      // Test 3: Get technical analysis
      console.log('\n3. Testing technical analysis...');
      const technicalResponse = await fetch('http://localhost:8002/api/analysis/nifty-indicators/1hr');
      const technicalData = await technicalResponse.json();
      console.log('RSI:', technicalData.data?.rsi || 'No RSI data');
      
      // Test 4: Call strategy service with real parameters
      console.log('\n4. Testing strategy recommendation...');
      
      const currentSpot = marketData.data?.price || 24750;
      const currentVix = vixData.data?.current_vix || 15;
      const rsi = technicalData.data?.rsi || 50;
      
      // Calculate volatility percentile
      const volatilityPercentile = Math.min(Math.max((currentVix - 12) / (30 - 12) * 100, 0), 100);
      
      // Determine market sentiment
      let marketSentiment = 'neutral';
      if (rsi > 60) marketSentiment = 'bullish';
      else if (rsi < 40) marketSentiment = 'bearish';
      
      // Calculate days to expiry (next weekly expiry)
      const today = new Date();
      const nextThursday = new Date(today);
      nextThursday.setDate(today.getDate() + (4 - today.getDay() + 7) % 7);
      const daysToExpiry = Math.ceil((nextThursday - today) / (1000 * 60 * 60 * 24));
      
      const params = new URLSearchParams({
        symbol: 'NIFTY',
        current_spot: currentSpot,
        volatility_percentile: Math.round(volatilityPercentile),
        days_to_expiry: daysToExpiry,
        market_sentiment: marketSentiment,
        event_proximity: false,
        account_size: 500000
      });
      
      console.log('Strategy parameters:');
      console.log('- Symbol: NIFTY');
      console.log('- Current Spot:', currentSpot);
      console.log('- Volatility Percentile:', Math.round(volatilityPercentile));
      console.log('- Days to Expiry:', daysToExpiry);
      console.log('- Market Sentiment:', marketSentiment);
      console.log('- Account Size: ₹500,000');
      
      const strategyResponse = await fetch(
        `http://localhost:8004/api/strategy/strategy-recommendation?${params}`
      );
      
      if (!strategyResponse.ok) {
        throw new Error(`Strategy API error: ${strategyResponse.status}`);
      }
      
      const strategyData = await strategyResponse.json();
      
      console.log('\n✅ Strategy Recommendation:');
      console.log('- Strategy:', strategyData.recommended_strategy?.name);
      console.log('- Rationale:', strategyData.recommended_strategy?.rationale);
      console.log('- Confidence:', strategyData.recommended_strategy?.confidence + '/10');
      console.log('- Probability of Profit:', (strategyData.recommended_strategy?.probability_of_profit * 100).toFixed(1) + '%');
      console.log('- Volatility Regime:', strategyData.market_regime_analysis?.volatility_regime);
      console.log('- Expected Return:', strategyData.recommended_strategy?.expected_return + '%');
      
      console.log('\n🎉 Strategy service integration working correctly!');
      
    } catch (error) {
      console.error('❌ Error testing strategy integration:', error.message);
      console.log('\nDebugging steps:');
      console.log('1. Ensure all services are running (ports 8001, 8002, 8004)');
      console.log('2. Check service health: curl http://localhost:8004/health');
      console.log('3. Verify API documentation: http://localhost:8004/docs');
    }
  }
  
  // Run the test
  testStrategyIntegration();