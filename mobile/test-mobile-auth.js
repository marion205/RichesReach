#!/usr/bin/env node

/**
 * Test script to verify mobile app authentication and GraphQL connectivity
 */

const fetch = require('node-fetch');

const BASE_URL = 'http://localhost:8000';
const GRAPHQL_URL = `${BASE_URL}/graphql/`;
const LOGIN_URL = `${BASE_URL}/api/auth/login/`;

async function testHealthCheck() {
  console.log('🔍 Testing health check...');
  try {
    const response = await fetch(`${BASE_URL}/healthz`);
    const data = await response.json();
    console.log('✅ Health check:', data);
    return true;
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    return false;
  }
}

async function testAuthentication() {
  console.log('\n🔐 Testing authentication...');
  try {
    const response = await fetch(LOGIN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'admin@example.com',
        password: 'password123'
      })
    });

    const data = await response.json();
    console.log('✅ Authentication response:', {
      success: data.success,
      token: data.token ? `${data.token.substring(0, 50)}...` : 'No token',
      user: data.user ? data.user.email : 'No user data'
    });

    if (data.token) {
      return data.token;
    } else {
      console.error('❌ No token in response');
      return null;
    }
  } catch (error) {
    console.error('❌ Authentication failed:', error.message);
    return null;
  }
}

async function testGraphQLMutation(token) {
  console.log('\n📊 Testing GraphQL mutation...');
  try {
    const response = await fetch(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        query: `
          mutation {
            addToWatchlist(symbol: "AAPL", companyName: "Apple Inc.", notes: "Mobile test") {
              success
              message
            }
          }
        `
      })
    });

    const data = await response.json();
    console.log('✅ GraphQL mutation response:', data);

    if (data.data && data.data.addToWatchlist && data.data.addToWatchlist.success) {
      console.log('🎉 Watchlist mutation successful!');
      return true;
    } else {
      console.error('❌ GraphQL mutation failed:', data);
      return false;
    }
  } catch (error) {
    console.error('❌ GraphQL mutation error:', error.message);
    return false;
  }
}

async function testGraphQLQuery(token) {
  console.log('\n📋 Testing GraphQL query...');
  try {
    const response = await fetch(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        query: `
          query {
            myWatchlist {
              id
              stock {
                symbol
                companyName
              }
              notes
              addedAt
            }
          }
        `
      })
    });

    const data = await response.json();
    console.log('✅ GraphQL query response:', data);
    return true;
  } catch (error) {
    console.error('❌ GraphQL query error:', error.message);
    return false;
  }
}

async function runTests() {
  console.log('🧪 Testing Mobile App Backend Connectivity\n');
  console.log('=' .repeat(50));

  // Test 1: Health check
  const healthOk = await testHealthCheck();
  if (!healthOk) {
    console.log('\n❌ Backend server is not running. Please start it first.');
    process.exit(1);
  }

  // Test 2: Authentication
  const token = await testAuthentication();
  if (!token) {
    console.log('\n❌ Authentication failed. Cannot proceed with GraphQL tests.');
    process.exit(1);
  }

  // Test 3: GraphQL mutation
  const mutationOk = await testGraphQLMutation(token);
  
  // Test 4: GraphQL query
  const queryOk = await testGraphQLQuery(token);

  console.log('\n' + '=' .repeat(50));
  console.log('📊 Test Results:');
  console.log(`✅ Health Check: ${healthOk ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Authentication: ${token ? 'PASS' : 'FAIL'}`);
  console.log(`✅ GraphQL Mutation: ${mutationOk ? 'PASS' : 'FAIL'}`);
  console.log(`✅ GraphQL Query: ${queryOk ? 'PASS' : 'FAIL'}`);

  if (healthOk && token && mutationOk && queryOk) {
    console.log('\n🎉 All tests passed! Mobile app should work correctly.');
    console.log('\n📱 Next steps:');
    console.log('1. Start the mobile app: cd mobile && ./start-local-test.sh');
    console.log('2. Login with: admin@example.com / password123');
    console.log('3. Test watchlist functionality');
  } else {
    console.log('\n❌ Some tests failed. Check the errors above.');
  }
}

runTests().catch(console.error);
