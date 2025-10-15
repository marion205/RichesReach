#!/usr/bin/env node

// Quick connection test for mobile app
const API_URL = 'http://172.20.10.8:8000';

console.log('🧪 Testing Mobile App Connection...');
console.log('=====================================');

async function testConnection() {
  try {
    // Test health endpoint
    console.log('1. Testing health endpoint...');
    const healthResponse = await fetch(`${API_URL}/health/`);
    const healthData = await healthResponse.json();
    console.log('✅ Health check:', healthData);
    
    // Test GraphQL endpoint
    console.log('\n2. Testing GraphQL endpoint...');
    const graphqlResponse = await fetch(`${API_URL}/graphql/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: '{ stocks { symbol companyName currentPrice } }'
      })
    });
    const graphqlData = await graphqlResponse.json();
    console.log('✅ GraphQL response:', graphqlData.data ? 'SUCCESS' : 'FAILED');
    if (graphqlData.data) {
      console.log('   Sample stocks:', graphqlData.data.stocks.slice(0, 3));
    }
    
    console.log('\n🎉 All tests passed! Mobile app should connect successfully.');
    console.log('\n📱 Next steps:');
    console.log('1. Scan the QR code in Expo');
    console.log('2. The app should now connect to:', API_URL);
    console.log('3. Check the logs for "🔧 API Configuration" to confirm the IP');
    
  } catch (error) {
    console.error('❌ Connection failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('1. Make sure Django server is running on 0.0.0.0:8000');
    console.log('2. Check if 172.20.10.8 is your current hotspot IP');
    console.log('3. Try running: ./scripts/fix-hotspot-connection.sh');
  }
}

testConnection();
