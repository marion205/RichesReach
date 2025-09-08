const AsyncStorage = require('@react-native-async-storage/async-storage');

async function setupApiKey() {
  try {
    const apiKey = 'OHYSFF1AE446O7CR';
    
    // Set the API key
    await AsyncStorage.setItem('alpha_vantage_api_key', apiKey);
    await AsyncStorage.setItem('real_market_data_enabled', 'true');
    
    console.log('✅ API key configured successfully!');
    console.log('🔑 API Key:', apiKey);
    console.log('📊 Real market data: ENABLED');
    console.log('');
    console.log('🚀 Your app will now fetch real market data from Alpha Vantage!');
    console.log('');
    console.log('📈 Available features:');
    console.log('  • Real-time stock prices');
    console.log('  • Historical data');
    console.log('  • Market news');
    console.log('  • Market hours detection');
    console.log('  • Stock search');
    
  } catch (error) {
    console.error('❌ Failed to setup API key:', error);
  }
}

setupApiKey();
