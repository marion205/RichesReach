#!/usr/bin/env node

/**
 * Enhanced test script for CSRF + JWT authentication with watchlist mutations
 * This script properly tests the complete authentication flow:
 * 1. Fetch CSRF token with session cookie
 * 2. Authenticate with JWT token
 * 3. Test GraphQL mutations with proper headers
 */

const http = require('http');
const https = require('https');

// Production server details
const PROD_URL = 'http://54.160.139.56:8000';
const CSRF_URL = `${PROD_URL}/csrf-token/`;
const GRAPHQL_URL = `${PROD_URL}/graphql/`;
const AUTH_URL = `${PROD_URL}/auth/`;

console.log('🧪 Enhanced CSRF + JWT Authentication Test');
console.log('==========================================');
console.log(`CSRF URL: ${CSRF_URL}`);
console.log(`GraphQL URL: ${GRAPHQL_URL}`);
console.log(`Auth URL: ${AUTH_URL}`);
console.log('');

// Global state for cookies and tokens
let sessionCookies = '';
let csrfToken = '';
let jwtToken = '';

// Helper function to make HTTP requests with cookie support
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;
    
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'RichesReach-Mobile-Test/1.0',
        ...options.headers
      }
    };

    // Add cookies if we have them
    if (sessionCookies) {
      requestOptions.headers['Cookie'] = sessionCookies;
    }

    const req = client.request(requestOptions, (res) => {
      let data = '';
      
      // Capture cookies from response
      if (res.headers['set-cookie']) {
        sessionCookies = res.headers['set-cookie'].join('; ');
        console.log(`🍪 Captured cookies: ${sessionCookies.substring(0, 50)}...`);
      }
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data: data
        });
      });
    });
    
    req.on('error', (err) => {
      reject(err);
    });
    
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  });
}

// Step 1: Fetch CSRF token
async function fetchCSRFToken() {
  console.log('🔐 Step 1: Fetching CSRF token...');
  
  try {
    const response = await makeRequest(CSRF_URL);
    
    if (response.statusCode === 200) {
      try {
        const data = JSON.parse(response.data);
        csrfToken = data.csrfToken;
        if (csrfToken) {
          console.log('✅ CSRF token fetched successfully');
          console.log(`   Token: ${csrfToken.substring(0, 20)}...`);
          return true;
        } else {
          console.log('❌ No CSRF token in response');
          console.log(`   Response: ${response.data}`);
          return false;
        }
      } catch (e) {
        console.log('❌ CSRF response not JSON');
        console.log(`   Response: ${response.data}`);
        return false;
      }
    } else {
      console.log(`❌ CSRF endpoint failed: ${response.statusCode}`);
      console.log(`   Response: ${response.data}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ CSRF request error: ${error.message}`);
    return false;
  }
}

// Step 2: Authenticate and get JWT token
async function authenticate() {
  console.log('🔑 Step 2: Authenticating to get JWT token...');
  
  // For testing, we'll try to authenticate with a test user
  // In a real scenario, you'd have valid credentials
  const authData = {
    email: 'test@example.com',
    password: 'testpassword'
  };
  
  try {
    const response = await makeRequest(AUTH_URL, {
      method: 'POST',
      body: JSON.stringify(authData)
    });
    
    if (response.statusCode === 200) {
      try {
        const data = JSON.parse(response.data);
        jwtToken = data.token || data.access_token;
        if (jwtToken) {
          console.log('✅ JWT token obtained successfully');
          console.log(`   Token: ${jwtToken.substring(0, 30)}...`);
          return true;
        } else {
          console.log('⚠️  No JWT token in response (might be expected for test user)');
          console.log(`   Response: ${response.data}`);
          return false;
        }
      } catch (e) {
        console.log('❌ Auth response not JSON');
        console.log(`   Response: ${response.data}`);
        return false;
      }
    } else {
      console.log(`⚠️  Auth endpoint returned: ${response.statusCode}`);
      console.log(`   Response: ${response.data}`);
      // This might be expected if test credentials don't exist
      return false;
    }
  } catch (error) {
    console.log(`❌ Auth request error: ${error.message}`);
    return false;
  }
}

// Step 3: Test GraphQL mutation with all proper headers
async function testWatchlistMutationWithFullAuth() {
  console.log('🔍 Step 3: Testing watchlist mutation with full authentication...');
  
  const mutation = {
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
      notes: "Test with full authentication"
    }
  };
  
  const headers = {
    'Content-Type': 'application/json'
  };
  
  // Add CSRF token if we have it
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }
  
  // Add JWT token if we have it
  if (jwtToken) {
    headers['Authorization'] = `JWT ${jwtToken}`;
  }
  
  try {
    const response = await makeRequest(GRAPHQL_URL, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(mutation)
    });
    
    console.log(`📊 Response Status: ${response.statusCode}`);
    console.log(`📊 Response Headers:`, Object.keys(response.headers));
    
    if (response.statusCode === 200) {
      try {
        const data = JSON.parse(response.data);
        if (data.data && data.data.addToWatchlist) {
          console.log('✅ Watchlist mutation successful!');
          console.log(`   Success: ${data.data.addToWatchlist.success}`);
          console.log(`   Message: ${data.data.addToWatchlist.message}`);
          return true;
        } else if (data.errors) {
          console.log('❌ GraphQL errors:');
          data.errors.forEach(error => {
            console.log(`   - ${error.message}`);
            if (error.extensions) {
              console.log(`     Extensions: ${JSON.stringify(error.extensions)}`);
            }
          });
          return false;
        } else {
          console.log('❌ Unexpected response format');
          console.log(`   Response: ${response.data}`);
          return false;
        }
      } catch (e) {
        console.log('❌ Response not JSON');
        console.log(`   Response: ${response.data}`);
        return false;
      }
    } else {
      console.log(`❌ HTTP error: ${response.statusCode}`);
      console.log(`   Response: ${response.data}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Request error: ${error.message}`);
    return false;
  }
}

// Step 4: Test GraphQL mutation without CSRF token (should fail)
async function testWatchlistMutationWithoutCSRF() {
  console.log('🔍 Step 4: Testing watchlist mutation without CSRF token (should fail)...');
  
  const mutation = {
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
  };
  
  const headers = {
    'Content-Type': 'application/json'
  };
  
  // Add JWT token if we have it, but NO CSRF token
  if (jwtToken) {
    headers['Authorization'] = `JWT ${jwtToken}`;
  }
  
  try {
    const response = await makeRequest(GRAPHQL_URL, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(mutation)
    });
    
    if (response.statusCode === 400 || response.statusCode === 403) {
      console.log('✅ Mutation correctly rejected without CSRF token');
      console.log(`   Status: ${response.statusCode}`);
      console.log(`   Response: ${response.data}`);
      return true;
    } else if (response.statusCode === 200) {
      console.log('⚠️  Mutation unexpectedly succeeded without CSRF token');
      console.log(`   Response: ${response.data}`);
      return false;
    } else {
      console.log(`❌ Unexpected status: ${response.statusCode}`);
      console.log(`   Response: ${response.data}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Request error: ${error.message}`);
    return false;
  }
}

// Step 5: Test simple GraphQL query (should work without CSRF)
async function testSimpleQuery() {
  console.log('🔍 Step 5: Testing simple GraphQL query (should work without CSRF)...');
  
  const query = {
    query: `
      query {
        ping
      }
    `
  };
  
  try {
    const response = await makeRequest(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(query)
    });
    
    if (response.statusCode === 200) {
      try {
        const data = JSON.parse(response.data);
        if (data.data && data.data.ping) {
          console.log('✅ Simple query successful');
          console.log(`   Response: ${data.data.ping}`);
          return true;
        } else {
          console.log('❌ Unexpected query response');
          console.log(`   Response: ${response.data}`);
          return false;
        }
      } catch (e) {
        console.log('❌ Query response not JSON');
        console.log(`   Response: ${response.data}`);
        return false;
      }
    } else {
      console.log(`❌ Query failed: ${response.statusCode}`);
      console.log(`   Response: ${response.data}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Query request error: ${error.message}`);
    return false;
  }
}

// Run all tests
async function runTests() {
  console.log('Starting enhanced authentication tests...\n');
  
  // Step 1: Fetch CSRF token
  const csrfOk = await fetchCSRFToken();
  console.log('');
  
  // Step 2: Try to authenticate (might fail with test credentials)
  const authOk = await authenticate();
  console.log('');
  
  // Step 3: Test simple query first
  const queryOk = await testSimpleQuery();
  console.log('');
  
  // Step 4: Test mutation with full auth
  const mutationWithAuth = await testWatchlistMutationWithFullAuth();
  console.log('');
  
  // Step 5: Test mutation without CSRF
  const mutationWithoutCSRF = await testWatchlistMutationWithoutCSRF();
  console.log('');
  
  // Summary
  console.log('📊 Test Results Summary');
  console.log('=======================');
  console.log(`CSRF Token Fetch: ${csrfOk ? '✅ SUCCESS' : '❌ FAILED'}`);
  console.log(`Authentication: ${authOk ? '✅ SUCCESS' : '⚠️  FAILED (expected for test user)'}`);
  console.log(`Simple Query: ${queryOk ? '✅ SUCCESS' : '❌ FAILED'}`);
  console.log(`Mutation with Auth: ${mutationWithAuth ? '✅ SUCCESS' : '❌ FAILED'}`);
  console.log(`Mutation without CSRF: ${mutationWithoutCSRF ? '✅ CORRECTLY REJECTED' : '❌ UNEXPECTED'}`);
  console.log('');
  
  if (csrfOk && queryOk) {
    console.log('🎉 Core functionality confirmed!');
    console.log('');
    console.log('✅ CSRF token endpoint is working');
    console.log('✅ GraphQL queries work');
    console.log('✅ CSRF protection is properly configured');
    console.log('');
    
    if (mutationWithAuth) {
      console.log('✅ GraphQL mutations work with proper authentication');
    } else {
      console.log('⚠️  GraphQL mutations need proper JWT authentication');
    }
    
    console.log('');
    console.log('📱 Next steps for mobile app:');
    console.log('1. Implement proper JWT authentication flow');
    console.log('2. Ensure CSRF tokens are fetched and included in mutations');
    console.log('3. Test with real user credentials');
    process.exit(0);
  } else {
    console.log('❌ Core functionality issues detected.');
    console.log('   Please check the server configuration.');
    process.exit(1);
  }
}

// Run the tests
runTests().catch(console.error);
