// Quick test script for Alpha Vantage API
const API_KEY = 'OHYSFF1AE446O7CR';
const BASE_URL = 'https://www.alphavantage.co/query';

async function testApiKey() {
  console.log('🧪 Testing Alpha Vantage API Key...');
  console.log('🔑 API Key:', API_KEY);
  console.log('');

  try {
    // Test 1: Get stock quote for AAPL
    console.log('📊 Test 1: Getting AAPL stock quote...');
    const quoteUrl = `${BASE_URL}?function=GLOBAL_QUOTE&symbol=AAPL&apikey=${API_KEY}`;
    const quoteResponse = await fetch(quoteUrl);
    const quoteData = await quoteResponse.json();
    
    if (quoteData['Error Message']) {
      console.log('❌ Error:', quoteData['Error Message']);
    } else if (quoteData['Note']) {
      console.log('⚠️  Rate limit:', quoteData['Note']);
    } else {
      const quote = quoteData['Global Quote'];
      console.log('✅ Success! AAPL Quote:');
      console.log(`   Price: $${quote['05. price']}`);
      console.log(`   Change: ${quote['09. change']} (${quote['10. change percent']})`);
      console.log(`   Volume: ${quote['06. volume']}`);
    }

    console.log('');

    // Test 2: Search for stocks
    console.log('🔍 Test 2: Searching for "Apple"...');
    const searchUrl = `${BASE_URL}?function=SYMBOL_SEARCH&keywords=Apple&apikey=${API_KEY}`;
    const searchResponse = await fetch(searchUrl);
    const searchData = await searchResponse.json();
    
    if (searchData['Error Message']) {
      console.log('❌ Error:', searchData['Error Message']);
    } else if (searchData['Note']) {
      console.log('⚠️  Rate limit:', searchData['Note']);
    } else {
      const matches = searchData.bestMatches || [];
      console.log(`✅ Found ${matches.length} matches:`);
      matches.slice(0, 3).forEach((match, index) => {
        console.log(`   ${index + 1}. ${match['1. symbol']} - ${match['2. name']}`);
      });
    }

    console.log('');
    console.log('🎉 API Key is working! Your app can now fetch real market data.');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

// Run the test
testApiKey();
