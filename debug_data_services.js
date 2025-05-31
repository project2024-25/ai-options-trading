// File: debug_data_services.js
// Check actual data format from services

async function debugDataServices() {
    console.log('Debugging Data Services...\n');
    
    try {
      // Test market data service
      console.log('=== MARKET DATA SERVICE (8001) ===');
      const marketResponse = await fetch('http://localhost:8001/api/data/nifty-snapshot');
      const marketData = await marketResponse.json();
      console.log('Full response:', JSON.stringify(marketData, null, 2));
      
      console.log('\n=== VIX DATA SERVICE (8001) ===');
      const vixResponse = await fetch('http://localhost:8001/api/data/vix-data');
      const vixData = await vixResponse.json();
      console.log('Full response:', JSON.stringify(vixData, null, 2));
      
      console.log('\n=== TECHNICAL ANALYSIS SERVICE (8002) ===');
      const technicalResponse = await fetch('http://localhost:8002/api/analysis/nifty-indicators/1hr');
      const technicalData = await technicalResponse.json();
      console.log('Full response:', JSON.stringify(technicalData, null, 2));
      
      console.log('\n=== DATA EXTRACTION ANALYSIS ===');
      
      // Analyze market data structure
      console.log('Market Data Analysis:');
      if (marketData.data) {
        console.log('- Has data object:', Object.keys(marketData.data));
        console.log('- Price field:', marketData.data.price || marketData.data.last_price || marketData.data.ltp || 'NOT FOUND');
      } else if (marketData.price) {
        console.log('- Direct price field:', marketData.price);
      } else {
        console.log('- Price extraction paths to try:', Object.keys(marketData));
      }
      
      // Analyze VIX data structure
      console.log('\nVIX Data Analysis:');
      if (vixData.data) {
        console.log('- Has data object:', Object.keys(vixData.data));
        console.log('- VIX field:', vixData.data.current_vix || vixData.data.vix || vixData.data.value || 'NOT FOUND');
      } else if (vixData.vix) {
        console.log('- Direct vix field:', vixData.vix);
      } else {
        console.log('- VIX extraction paths to try:', Object.keys(vixData));
      }
      
      // Analyze technical data structure
      console.log('\nTechnical Data Analysis:');
      if (technicalData.data) {
        console.log('- Has data object:', Object.keys(technicalData.data));
        console.log('- RSI field:', technicalData.data.rsi || technicalData.data.RSI || 'NOT FOUND');
      } else if (technicalData.rsi) {
        console.log('- Direct RSI field:', technicalData.rsi);
      } else {
        console.log('- RSI extraction paths to try:', Object.keys(technicalData));
      }
      
    } catch (error) {
      console.error('Error debugging data services:', error.message);
    }
  }
  
  debugDataServices();