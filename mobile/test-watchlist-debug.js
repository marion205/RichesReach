#!/usr/bin/env node

/**
 * Debug script to test watchlist mutation and identify the 500 error
 */

const http = require('http');

const PROD_URL = 'http://54.160.139.56:8000';
const GRAPHQL_URL = `${PROD_URL}/graphql/`;

console.log('🔍 Debug Watchlist 500 Error');
console.log('============================');

// Test 1: Simple query (should work)
function testSimpleQuery() {
  return new Promise((resolve) => {
    console.log('🔍 Testing simple query...');
    
    const postData = JSON.stringify({
      query: 'query { ping }'
    });
    
    const req = http.request(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: 10000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`   Status: ${res.statusCode}`);
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(data);
            console.log(`   Response: ${JSON.stringify(response)}`);
            resolve(true);
          } catch (e) {
            console.log(`   Raw response: ${data}`);
            resolve(false);
          }
        } else {
          console.log(`   Error response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`   Error: ${err.message}`);
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Test 2: Watchlist mutation without auth (should fail with specific error)
function testWatchlistWithoutAuth() {
  return new Promise((resolve) => {
    console.log('🔍 Testing watchlist mutation without authentication...');
    
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
        notes: "Test without auth"
      }
    });
    
    const req = http.request(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: 10000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`   Status: ${res.statusCode}`);
        console.log(`   Response: ${data}`);
        
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(data);
            if (response.errors) {
              console.log('   GraphQL Errors:');
              response.errors.forEach(error => {
                console.log(`     - ${error.message}`);
              });
              resolve(true); // Expected to have errors
            } else {
              console.log('   Unexpected success without auth');
              resolve(false);
            }
          } catch (e) {
            console.log('   Response not JSON');
            resolve(false);
          }
        } else {
          console.log('   HTTP error (might be expected)');
          resolve(true);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`   Error: ${err.message}`);
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Test 3: Check if we can get user info
function testUserQuery() {
  return new Promise((resolve) => {
    console.log('🔍 Testing user query...');
    
    const postData = JSON.stringify({
      query: 'query { me { id email } }'
    });
    
    const req = http.request(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: 10000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`   Status: ${res.statusCode}`);
        console.log(`   Response: ${data}`);
        resolve(true);
      });
    });
    
    req.on('error', (err) => {
      console.log(`   Error: ${err.message}`);
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Run tests
async function runTests() {
  console.log('Starting debug tests...\n');
  
  const queryOk = await testSimpleQuery();
  console.log('');
  
  const userOk = await testUserQuery();
  console.log('');
  
  const mutationOk = await testWatchlistWithoutAuth();
  console.log('');
  
  console.log('📊 Debug Results:');
  console.log(`Simple Query: ${queryOk ? '✅' : '❌'}`);
  console.log(`User Query: ${userOk ? '✅' : '❌'}`);
  console.log(`Watchlist Mutation: ${mutationOk ? '✅' : '❌'}`);
  
  console.log('\n🔧 Analysis:');
  if (!queryOk) {
    console.log('❌ Basic GraphQL is broken');
  } else if (!userOk) {
    console.log('⚠️  User authentication might be the issue');
  } else {
    console.log('✅ GraphQL is working, issue is likely in the mutation resolver');
  }
}

runTests().catch(console.error);
