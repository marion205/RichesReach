#!/usr/bin/env node

/**
 * Test script to verify connection to production API
 * This will help us ensure the mobile app can connect to the production servers
 */

const https = require('https');
const http = require('http');

// Production server details
const PROD_URL = 'http://54.160.139.56:8000';
const GRAPHQL_URL = `${PROD_URL}/graphql/`;
const HEALTH_URL = `${PROD_URL}/healthz`;

console.log('🧪 Testing Production API Connection');
console.log('=====================================');
console.log(`Production URL: ${PROD_URL}`);
console.log(`GraphQL URL: ${GRAPHQL_URL}`);
console.log(`Health URL: ${HEALTH_URL}`);
console.log('');

// Test health endpoint
function testHealthEndpoint() {
  return new Promise((resolve, reject) => {
    console.log('🔍 Testing Health Endpoint...');
    
    const req = http.get(HEALTH_URL, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ Health endpoint working');
          console.log(`   Response: ${data}`);
          resolve(true);
        } else {
          console.log(`❌ Health endpoint failed: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`❌ Health endpoint error: ${err.message}`);
      resolve(false);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ Health endpoint timeout');
      req.destroy();
      resolve(false);
    });
  });
}

// Test GraphQL endpoint
function testGraphQLEndpoint() {
  return new Promise((resolve, reject) => {
    console.log('🔍 Testing GraphQL Endpoint...');
    
    const postData = JSON.stringify({
      query: 'query { ping }'
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
            if (response.data && response.data.ping) {
              console.log('✅ GraphQL endpoint working');
              console.log(`   Response: ${JSON.stringify(response, null, 2)}`);
              resolve(true);
            } else {
              console.log('❌ GraphQL response invalid');
              console.log(`   Response: ${data}`);
              resolve(false);
            }
          } catch (e) {
            console.log('❌ GraphQL response not JSON');
            console.log(`   Response: ${data}`);
            resolve(false);
          }
        } else {
          console.log(`❌ GraphQL endpoint failed: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`❌ GraphQL endpoint error: ${err.message}`);
      resolve(false);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ GraphQL endpoint timeout');
      req.destroy();
      resolve(false);
    });
    
    req.write(postData);
    req.end();
  });
}

// Test authentication endpoint
function testAuthEndpoint() {
  return new Promise((resolve, reject) => {
    console.log('🔍 Testing Authentication Endpoint...');
    
    const authUrl = `${PROD_URL}/me/`;
    const req = http.get(authUrl, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ Authentication endpoint accessible');
          console.log(`   Response: ${data}`);
          resolve(true);
        } else {
          console.log(`❌ Authentication endpoint failed: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (err) => {
      console.log(`❌ Authentication endpoint error: ${err.message}`);
      resolve(false);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ Authentication endpoint timeout');
      req.destroy();
      resolve(false);
    });
  });
}

// Run all tests
async function runTests() {
  console.log('Starting production API tests...\n');
  
  const healthOk = await testHealthEndpoint();
  console.log('');
  
  const graphqlOk = await testGraphQLEndpoint();
  console.log('');
  
  const authOk = await testAuthEndpoint();
  console.log('');
  
  // Summary
  console.log('📊 Test Results Summary');
  console.log('=======================');
  console.log(`Health Endpoint: ${healthOk ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`GraphQL Endpoint: ${graphqlOk ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Auth Endpoint: ${authOk ? '✅ PASS' : '❌ FAIL'}`);
  console.log('');
  
  if (healthOk && graphqlOk && authOk) {
    console.log('🎉 All tests passed! Production API is ready for mobile app testing.');
    console.log('');
    console.log('Next steps:');
    console.log('1. Start the mobile app: npm start');
    console.log('2. Open Expo Go on your phone');
    console.log('3. Scan the QR code to test the app');
    process.exit(0);
  } else {
    console.log('❌ Some tests failed. Please check the production server status.');
    process.exit(1);
  }
}

// Run the tests
runTests().catch(console.error);
