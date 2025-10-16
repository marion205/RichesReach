#!/usr/bin/env node

/**
 * Test script to verify the watchlist mutation fix
 * This will test the corrected GraphQL mutation against the production API
 */

const http = require('http');

// Production server details
const PROD_URL = 'http://54.160.139.56:8000';
const GRAPHQL_URL = `${PROD_URL}/graphql/`;

console.log('🧪 Testing Watchlist Mutation Fix');
console.log('==================================');
console.log(`GraphQL URL: ${GRAPHQL_URL}`);
console.log('');

// Test the corrected mutation
function testWatchlistMutation() {
  return new Promise((resolve, reject) => {
    console.log('🔍 Testing AddToWatchlist mutation with correct parameters...');
    
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
        notes: "Test from mobile app"
      }
    });
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
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
              console.log('✅ Watchlist mutation successful!');
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

// Test the old (broken) mutation for comparison
function testOldWatchlistMutation() {
  return new Promise((resolve, reject) => {
    console.log('🔍 Testing old (broken) AddToWatchlist mutation...');
    
    const postData = JSON.stringify({
      query: `
        mutation AddToWatchlist($stockSymbol: String!, $notes: String) {
          addToWatchlist(stockSymbol: $stockSymbol, notes: $notes) {
            success
            message
          }
        }
      `,
      variables: {
        stockSymbol: "AAPL",
        notes: "Test with old parameters"
      }
    });
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
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
            if (response.errors) {
              console.log('❌ Old mutation failed as expected:');
              response.errors.forEach(error => {
                console.log(`   - ${error.message}`);
              });
              resolve(false); // Expected to fail
            } else {
              console.log('⚠️  Old mutation unexpectedly succeeded');
              resolve(true);
            }
          } catch (e) {
            console.log('❌ Old mutation response not JSON');
            console.log(`   Response: ${data}`);
            resolve(false);
          }
        } else {
          console.log(`❌ Old mutation HTTP error: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`❌ Old mutation request error: ${err.message}`);
      resolve(false);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ Old mutation request timeout');
      req.destroy();
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Run tests
async function runTests() {
  console.log('Starting watchlist mutation tests...\n');
  
  // Test the old (broken) mutation first
  const oldMutationFailed = await testOldWatchlistMutation();
  console.log('');
  
  // Test the corrected mutation
  const newMutationWorked = await testWatchlistMutation();
  console.log('');
  
  // Summary
  console.log('📊 Test Results Summary');
  console.log('=======================');
  console.log(`Old Mutation (stockSymbol): ${oldMutationFailed ? '❌ FAILED (expected)' : '⚠️  UNEXPECTED SUCCESS'}`);
  console.log(`New Mutation (symbol): ${newMutationWorked ? '✅ SUCCESS' : '❌ FAILED'}`);
  console.log('');
  
  if (oldMutationFailed && newMutationWorked) {
    console.log('🎉 Fix confirmed! The parameter name mismatch has been resolved.');
    console.log('');
    console.log('✅ The mobile app should now work correctly with the production API.');
    console.log('✅ Watchlist mutations will no longer return 500 errors.');
    process.exit(0);
  } else if (newMutationWorked) {
    console.log('✅ The new mutation works, but the old one should have failed.');
    console.log('   This might indicate the backend is more flexible than expected.');
    process.exit(0);
  } else {
    console.log('❌ The fix did not work as expected.');
    console.log('   Please check the backend mutation implementation.');
    process.exit(1);
  }
}

// Run the tests
runTests().catch(console.error);
