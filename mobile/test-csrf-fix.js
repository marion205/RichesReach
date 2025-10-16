#!/usr/bin/env node

/**
 * Test script to verify CSRF token fix for watchlist mutations
 * This will test the complete flow: fetch CSRF token, then use it in GraphQL mutation
 */

const http = require('http');

// Production server details
const PROD_URL = 'http://54.160.139.56:8000';
const CSRF_URL = `${PROD_URL}/csrf-token/`;
const GRAPHQL_URL = `${PROD_URL}/graphql/`;

console.log('🧪 Testing CSRF Token Fix for Watchlist Mutations');
console.log('==================================================');
console.log(`CSRF URL: ${CSRF_URL}`);
console.log(`GraphQL URL: ${GRAPHQL_URL}`);
console.log('');

// Step 1: Fetch CSRF token
function fetchCSRFToken() {
  return new Promise((resolve, reject) => {
    console.log('🔐 Step 1: Fetching CSRF token...');
    
    const req = http.get(CSRF_URL, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(data);
            const token = response.csrfToken;
            if (token) {
              console.log('✅ CSRF token fetched successfully');
              console.log(`   Token: ${token.substring(0, 20)}...`);
              resolve(token);
            } else {
              console.log('❌ No CSRF token in response');
              console.log(`   Response: ${data}`);
              resolve(null);
            }
          } catch (e) {
            console.log('❌ CSRF response not JSON');
            console.log(`   Response: ${data}`);
            resolve(null);
          }
        } else {
          console.log(`❌ CSRF endpoint failed: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(null);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`❌ CSRF request error: ${err.message}`);
      resolve(null);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ CSRF request timeout');
      req.destroy();
      resolve(null);
    });
  });
}

// Step 2: Test watchlist mutation with CSRF token
function testWatchlistMutationWithCSRF(csrfToken) {
  return new Promise((resolve, reject) => {
    console.log('🔍 Step 2: Testing watchlist mutation with CSRF token...');
    
    const postData = JSON.stringify({
      query: `
        mutation AddToWatchlist($symbol: String!, $notes: String) {
          addToWatchlist(symbol: $symbol, notes: $notes) {
            success
            message
          }
        }
      `,
      variables: {
        symbol: "AAPL",
        notes: "Test with CSRF token"
      }
    });
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'X-CSRF-Token': csrfToken
      }
    };
    
    const req = http.request(GRAPHQL_URL, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(data);
            if (response.data && response.data.addToWatchlist) {
              console.log('✅ Watchlist mutation successful with CSRF token!');
              console.log(`   Success: ${response.data.addToWatchlist.success}`);
              console.log(`   Message: ${response.data.addToWatchlist.message}`);
              resolve(true);
            } else if (response.errors) {
              console.log('❌ GraphQL errors:');
              response.errors.forEach(error => {
                console.log(`   - ${error.message}`);
              });
              resolve(false);
            } else {
              console.log('❌ Unexpected response format');
              console.log(`   Response: ${data}`);
              resolve(false);
            }
          } catch (e) {
            console.log('❌ Response not JSON');
            console.log(`   Response: ${data}`);
            resolve(false);
          }
        } else {
          console.log(`❌ HTTP error: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`❌ Request error: ${err.message}`);
      resolve(false);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ Request timeout');
      req.destroy();
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Step 3: Test watchlist mutation without CSRF token (should fail)
function testWatchlistMutationWithoutCSRF() {
  return new Promise((resolve, reject) => {
    console.log('🔍 Step 3: Testing watchlist mutation without CSRF token (should fail)...');
    
    const postData = JSON.stringify({
      query: `
        mutation AddToWatchlist($symbol: String!, $notes: String) {
          addToWatchlist(symbol: $symbol, notes: $notes) {
            success
            message
          }
        }
      `,
      variables: {
        symbol: "AAPL",
        notes: "Test without CSRF token"
      }
    });
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
        // No X-CSRF-Token header
      }
    };
    
    const req = http.request(GRAPHQL_URL, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 400 || res.statusCode === 403) {
          console.log('✅ Mutation correctly rejected without CSRF token');
          console.log(`   Status: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(true); // Expected to fail
        } else if (res.statusCode === 200) {
          console.log('⚠️  Mutation unexpectedly succeeded without CSRF token');
          console.log(`   Response: ${data}`);
          resolve(false);
        } else {
          console.log(`❌ Unexpected status: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`❌ Request error: ${err.message}`);
      resolve(false);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ Request timeout');
      req.destroy();
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Run all tests
async function runTests() {
  console.log('Starting CSRF token tests...\n');
  
  // Step 1: Fetch CSRF token
  const csrfToken = await fetchCSRFToken();
  console.log('');
  
  if (!csrfToken) {
    console.log('❌ Cannot proceed without CSRF token');
    process.exit(1);
  }
  
  // Step 2: Test with CSRF token
  const withCSRF = await testWatchlistMutationWithCSRF(csrfToken);
  console.log('');
  
  // Step 3: Test without CSRF token
  const withoutCSRF = await testWatchlistMutationWithoutCSRF();
  console.log('');
  
  // Summary
  console.log('📊 Test Results Summary');
  console.log('=======================');
  console.log(`CSRF Token Fetch: ${csrfToken ? '✅ SUCCESS' : '❌ FAILED'}`);
  console.log(`Mutation with CSRF: ${withCSRF ? '✅ SUCCESS' : '❌ FAILED'}`);
  console.log(`Mutation without CSRF: ${withoutCSRF ? '✅ CORRECTLY REJECTED' : '❌ UNEXPECTED'}`);
  console.log('');
  
  if (csrfToken && withCSRF && withoutCSRF) {
    console.log('🎉 CSRF fix confirmed! The mobile app should now work correctly.');
    console.log('');
    console.log('✅ CSRF token endpoint is working');
    console.log('✅ GraphQL mutations work with CSRF token');
    console.log('✅ GraphQL mutations are properly rejected without CSRF token');
    console.log('');
    console.log('📱 Next steps:');
    console.log('1. Restart your mobile app to pick up the changes');
    console.log('2. Test the watchlist functionality');
    console.log('3. The 400/500 errors should be resolved');
    process.exit(0);
  } else {
    console.log('❌ Some tests failed. Please check the implementation.');
    process.exit(1);
  }
}

// Run the tests
runTests().catch(console.error);
