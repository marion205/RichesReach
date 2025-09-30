#!/usr/bin/env node
/**
 * Test script to verify the React Native app configuration
 */

const { execSync } = require('child_process');

console.log('🧪 Testing React Native App Configuration...');
console.log('=' * 50);

// Test 1: Check if local server is running
try {
  const healthResponse = execSync('curl -s http://localhost:8000/health/', { encoding: 'utf8' });
  console.log('✅ Local Django server is running');
  console.log(`   Response: ${healthResponse.trim()}`);
} catch (error) {
  console.log('❌ Local Django server is not running');
  console.log(`   Error: ${error.message}`);
}

// Test 2: Test GraphQL endpoint
try {
  const graphqlResponse = execSync('curl -s -X POST http://localhost:8000/graphql/ -H "Content-Type: application/json" -d \'{"query": "{ stocks { companyName currentPrice beginnerFriendlyScore dividendScore } }"}\'', { encoding: 'utf8' });
  const data = JSON.parse(graphqlResponse);
  if (data.data && data.data.stocks && data.data.stocks.length > 0) {
    console.log('✅ GraphQL endpoint is working');
    console.log(`   Found ${data.data.stocks.length} stocks`);
  } else {
    console.log('❌ GraphQL endpoint returned no data');
  }
} catch (error) {
  console.log('❌ GraphQL endpoint test failed');
  console.log(`   Error: ${error.message}`);
}

// Test 3: Test JWT authentication
try {
  const authResponse = execSync('curl -s -X POST http://localhost:8000/api/auth/login/ -H "Content-Type: application/json" -d \'{"email":"test@example.com","password":"test"}\'', { encoding: 'utf8' });
  const authData = JSON.parse(authResponse);
  if (authData.token && authData.token.includes('.')) {
    console.log('✅ JWT authentication is working');
    console.log(`   Token format: ${authData.token.substring(0, 20)}...`);
  } else {
    console.log('❌ JWT authentication failed');
  }
} catch (error) {
  console.log('❌ JWT authentication test failed');
  console.log(`   Error: ${error.message}`);
}

console.log('=' * 50);
console.log('🎯 Configuration test complete!');
console.log('');
console.log('📱 Next steps:');
console.log('1. Make sure Expo is running: npm start');
console.log('2. Open the app in iOS simulator');
console.log('3. Try logging in with: test@example.com / test');
console.log('4. Check that all pages work without 400 errors');
