#!/usr/bin/env node

/**
 * Simple, fast CSRF test to identify the core issue
 */

const http = require('http');

const PROD_URL = 'http://54.160.139.56:8000';
const CSRF_URL = `${PROD_URL}/csrf-token/`;
const GRAPHQL_URL = `${PROD_URL}/graphql/`;

console.log('🧪 Simple CSRF Test');
console.log('==================');

// Test 1: Check if CSRF endpoint exists
function testCSRFEndpoint() {
  return new Promise((resolve) => {
    console.log('🔍 Testing CSRF endpoint...');
    
    const req = http.get(CSRF_URL, { timeout: 5000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`   Status: ${res.statusCode}`);
        console.log(`   Response: ${data.substring(0, 100)}...`);
        resolve(res.statusCode === 200);
      });
    });
    
    req.on('error', (err) => {
      console.log(`   Error: ${err.message}`);
      resolve(false);
    });
    
    req.on('timeout', () => {
      console.log('   Timeout');
      req.destroy();
      resolve(false);
    });
  });
}

// Test 2: Check GraphQL endpoint
function testGraphQLEndpoint() {
  return new Promise((resolve) => {
    console.log('🔍 Testing GraphQL endpoint...');
    
    const postData = JSON.stringify({
      query: 'query { ping }'
    });
    
    const req = http.request(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: 5000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`   Status: ${res.statusCode}`);
        console.log(`   Response: ${data.substring(0, 100)}...`);
        resolve(res.statusCode === 200);
      });
    });
    
    req.on('error', (err) => {
      console.log(`   Error: ${err.message}`);
      resolve(false);
    });
    
    req.on('timeout', () => {
      console.log('   Timeout');
      req.destroy();
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Test 3: Try watchlist mutation without CSRF (should fail)
function testWatchlistWithoutCSRF() {
  return new Promise((resolve) => {
    console.log('🔍 Testing watchlist mutation without CSRF...');
    
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
        notes: "Test"
      }
    });
    
    const req = http.request(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: 5000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`   Status: ${res.statusCode}`);
        console.log(`   Response: ${data.substring(0, 200)}...`);
        
        // Should fail with 400 or 403
        resolve(res.statusCode === 400 || res.statusCode === 403);
      });
    });
    
    req.on('error', (err) => {
      console.log(`   Error: ${err.message}`);
      resolve(false);
    });
    
    req.on('timeout', () => {
      console.log('   Timeout');
      req.destroy();
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Run tests
async function runTests() {
  console.log('Starting simple tests...\n');
  
  const csrfOk = await testCSRFEndpoint();
  console.log('');
  
  const graphqlOk = await testGraphQLEndpoint();
  console.log('');
  
  const mutationFails = await testWatchlistWithoutCSRF();
  console.log('');
  
  // Summary
  console.log('📊 Results:');
  console.log(`CSRF Endpoint: ${csrfOk ? '✅ EXISTS' : '❌ MISSING'}`);
  console.log(`GraphQL Endpoint: ${graphqlOk ? '✅ WORKS' : '❌ BROKEN'}`);
  console.log(`Mutation Protection: ${mutationFails ? '✅ PROTECTED' : '❌ NOT PROTECTED'}`);
  
  if (!csrfOk) {
    console.log('\n🔧 Fix needed: Add CSRF endpoint to backend');
  }
  
  if (!graphqlOk) {
    console.log('\n🔧 Fix needed: Check GraphQL server');
  }
  
  if (!mutationFails) {
    console.log('\n🔧 Fix needed: CSRF protection not working');
  }
}

runTests().catch(console.error);
