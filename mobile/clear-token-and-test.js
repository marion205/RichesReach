#!/usr/bin/env node

/**
 * Clear stored token and test fresh authentication
 */

const fetch = require('node-fetch');

const BASE_URL = 'http://localhost:8000';
const GRAPHQL_URL = `${BASE_URL}/graphql/`;
const LOGIN_URL = `${BASE_URL}/api/auth/login/`;

async function testFreshToken() {
  console.log('🔄 Testing with fresh token...');
  
  try {
    // Get a fresh token
    const loginResponse = await fetch(LOGIN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'admin@example.com',
        password: 'password123'
      })
    });

    const loginData = await loginResponse.json();
    
    if (!loginData.token) {
      console.error('❌ No token received from login');
      return false;
    }

    console.log('✅ Fresh token received:', `${loginData.token.substring(0, 50)}...`);

    // Test the fresh token immediately
    const graphqlResponse = await fetch(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${loginData.token}`
      },
      body: JSON.stringify({
        query: `
          mutation {
            addToWatchlist(symbol: "AAPL", companyName: "Apple Inc.", notes: "Fresh token test") {
              success
              message
            }
          }
        `
      })
    });

    const graphqlData = await graphqlResponse.json();
    console.log('📊 GraphQL response:', graphqlData);

    if (graphqlData.data && graphqlData.data.addToWatchlist && graphqlData.data.addToWatchlist.success) {
      console.log('🎉 Fresh token works! The issue is likely an expired token in the mobile app.');
      return true;
    } else {
      console.error('❌ Fresh token failed:', graphqlData);
      return false;
    }

  } catch (error) {
    console.error('❌ Error testing fresh token:', error.message);
    return false;
  }
}

async function main() {
  console.log('🧪 Testing Fresh Token Authentication\n');
  console.log('=' .repeat(50));
  
  const success = await testFreshToken();
  
  console.log('\n' + '=' .repeat(50));
  if (success) {
    console.log('✅ Fresh token works perfectly!');
    console.log('\n📱 Solution for mobile app:');
    console.log('1. Clear the app storage/cache');
    console.log('2. Force close and restart the app');
    console.log('3. Login again with admin@example.com / password123');
    console.log('4. The new token should work for 60 minutes');
  } else {
    console.log('❌ Even fresh tokens are failing. There may be a deeper issue.');
  }
}

main().catch(console.error);
