#!/usr/bin/env node

/**
 * Comprehensive Error Testing Script for RichesReach Version 2
 * Tests for missing fields, 400s, 500s, and other errors
 */

const https = require('https');
const http = require('http');

// Test configuration
const API_BASE = 'http://127.0.0.1:8000';
const TEST_CREDENTIALS = {
  email: 'demo@example.com',
  password: 'demo123'
};

// Colors for console output
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  reset: '\x1b[0m'
};

function log(color, message) {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const isHttps = url.startsWith('https');
    const client = isHttps ? https : http;
    
    const req = client.request(url, {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      timeout: 10000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const jsonData = data ? JSON.parse(data) : {};
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: jsonData,
            rawData: data
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: null,
            rawData: data
          });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => reject(new Error('Request timeout')));
    
    if (options.body) {
      req.write(JSON.stringify(options.body));
    }
    
    req.end();
  });
}

async function testBackendHealth() {
  log('blue', '\n🔍 Testing Backend Health...');
  
  try {
    const response = await makeRequest(`${API_BASE}/health`);
    
    if (response.status === 200) {
      log('green', '✅ Backend is healthy');
      return true;
    } else {
      log('red', `❌ Backend health check failed: ${response.status}`);
      return false;
    }
  } catch (error) {
    log('red', `❌ Backend connection failed: ${error.message}`);
    return false;
  }
}

async function testAuthentication() {
  log('blue', '\n🔐 Testing Authentication...');
  
  const tests = [
    {
      name: 'Valid Login',
      url: `${API_BASE}/api/auth/login/`,
      method: 'POST',
      body: TEST_CREDENTIALS,
      expectedStatus: 200
    },
    {
      name: 'Invalid Login',
      url: `${API_BASE}/api/auth/login/`,
      method: 'POST',
      body: { email: 'invalid@test.com', password: 'wrong' },
      expectedStatus: 401
    },
    {
      name: 'Missing Email',
      url: `${API_BASE}/api/auth/login/`,
      method: 'POST',
      body: { password: 'demo123' },
      expectedStatus: 400
    },
    {
      name: 'Missing Password',
      url: `${API_BASE}/api/auth/login/`,
      method: 'POST',
      body: { email: 'demo@example.com' },
      expectedStatus: 400
    }
  ];

  let authToken = null;
  
  for (const test of tests) {
    try {
      const response = await makeRequest(test.url, {
        method: test.method,
        body: test.body
      });
      
      if (response.status === test.expectedStatus) {
        log('green', `✅ ${test.name}: ${response.status}`);
        
        if (test.name === 'Valid Login' && response.data.token) {
          authToken = response.data.token;
          log('cyan', `   Token received: ${authToken.substring(0, 20)}...`);
        }
      } else {
        log('red', `❌ ${test.name}: Expected ${test.expectedStatus}, got ${response.status}`);
        if (response.data) {
          log('yellow', `   Response: ${JSON.stringify(response.data)}`);
        }
      }
    } catch (error) {
      log('red', `❌ ${test.name}: ${error.message}`);
    }
  }
  
  return authToken;
}

async function testAPIEndpoints(authToken) {
  log('blue', '\n🌐 Testing API Endpoints...');
  
  const endpoints = [
    {
      name: 'User Profile',
      url: `${API_BASE}/api/user/profile/`,
      method: 'GET',
      requiresAuth: true
    },
    {
      name: 'Portfolio List',
      url: `${API_BASE}/api/portfolio/`,
      method: 'GET',
      requiresAuth: true
    },
    {
      name: 'Market Data',
      url: `${API_BASE}/api/market/quotes/?symbols=AAPL,MSFT,GOOGL`,
      method: 'GET',
      requiresAuth: false
    },
    {
      name: 'News Feed',
      url: `${API_BASE}/api/news/`,
      method: 'GET',
      requiresAuth: false
    },
    {
      name: 'GraphQL Endpoint',
      url: `${API_BASE}/graphql/`,
      method: 'POST',
      requiresAuth: false,
      body: {
        query: '{ __schema { types { name } } }'
      }
    }
  ];

  for (const endpoint of endpoints) {
    try {
      const headers = {};
      if (endpoint.requiresAuth && authToken) {
        headers.Authorization = `Bearer ${authToken}`;
      }
      
      const response = await makeRequest(endpoint.url, {
        method: endpoint.method,
        headers,
        body: endpoint.body
      });
      
      if (response.status >= 200 && response.status < 300) {
        log('green', `✅ ${endpoint.name}: ${response.status}`);
        
        // Check for missing fields in response
        if (response.data) {
          checkForMissingFields(endpoint.name, response.data);
        }
      } else if (response.status === 401) {
        log('yellow', `⚠️  ${endpoint.name}: ${response.status} (Unauthorized - may need auth)`);
      } else if (response.status === 404) {
        log('yellow', `⚠️  ${endpoint.name}: ${response.status} (Not Found)`);
      } else {
        log('red', `❌ ${endpoint.name}: ${response.status}`);
        if (response.data) {
          log('yellow', `   Error: ${JSON.stringify(response.data)}`);
        }
      }
    } catch (error) {
      log('red', `❌ ${endpoint.name}: ${error.message}`);
    }
  }
}

function checkForMissingFields(endpointName, data) {
  const commonIssues = [];
  
  // Check for null/undefined values
  function checkObject(obj, path = '') {
    for (const [key, value] of Object.entries(obj)) {
      const currentPath = path ? `${path}.${key}` : key;
      
      if (value === null) {
        commonIssues.push(`Null value at ${currentPath}`);
      } else if (value === undefined) {
        commonIssues.push(`Undefined value at ${currentPath}`);
      } else if (typeof value === 'object' && value !== null) {
        checkObject(value, currentPath);
      }
    }
  }
  
  checkObject(data);
  
  if (commonIssues.length > 0) {
    log('yellow', `   ⚠️  Potential issues in ${endpointName}:`);
    commonIssues.slice(0, 5).forEach(issue => {
      log('yellow', `      - ${issue}`);
    });
    if (commonIssues.length > 5) {
      log('yellow', `      - ... and ${commonIssues.length - 5} more issues`);
    }
  }
}

async function testVersion2Features(authToken) {
  log('blue', '\n🚀 Testing Version 2 Features...');
  
  const v2Endpoints = [
    {
      name: 'Oracle Insights',
      url: `${API_BASE}/api/oracle/insights/`,
      method: 'GET',
      requiresAuth: true
    },
    {
      name: 'Voice AI Assistant',
      url: `${API_BASE}/api/voice/process/`,
      method: 'POST',
      requiresAuth: true,
      body: { message: 'test message' }
    },
    {
      name: 'Wellness Score',
      url: `${API_BASE}/api/portfolio/wellness/`,
      method: 'GET',
      requiresAuth: true
    },
    {
      name: 'Blockchain Integration',
      url: `${API_BASE}/api/blockchain/status/`,
      method: 'GET',
      requiresAuth: true
    },
    {
      name: 'Social Trading',
      url: `${API_BASE}/api/social/trading/`,
      method: 'GET',
      requiresAuth: true
    },
    {
      name: 'Wealth Circles',
      url: `${API_BASE}/api/wealth-circles/`,
      method: 'GET',
      requiresAuth: true
    }
  ];

  for (const endpoint of v2Endpoints) {
    try {
      const headers = {};
      if (endpoint.requiresAuth && authToken) {
        headers.Authorization = `Bearer ${authToken}`;
      }
      
      const response = await makeRequest(endpoint.url, {
        method: endpoint.method,
        headers,
        body: endpoint.body
      });
      
      if (response.status >= 200 && response.status < 300) {
        log('green', `✅ ${endpoint.name}: ${response.status}`);
        
        // Check for specific Version 2 data structures
        if (response.data) {
          checkVersion2DataStructure(endpoint.name, response.data);
        }
      } else if (response.status === 404) {
        log('yellow', `⚠️  ${endpoint.name}: ${response.status} (Endpoint not implemented yet)`);
      } else if (response.status === 401) {
        log('yellow', `⚠️  ${endpoint.name}: ${response.status} (Unauthorized)`);
      } else {
        log('red', `❌ ${endpoint.name}: ${response.status}`);
        if (response.data) {
          log('yellow', `   Error: ${JSON.stringify(response.data)}`);
        }
      }
    } catch (error) {
      log('red', `❌ ${endpoint.name}: ${error.message}`);
    }
  }
}

function checkVersion2DataStructure(featureName, data) {
  const expectedFields = {
    'Oracle Insights': ['insights', 'predictions', 'confidence'],
    'Voice AI Assistant': ['response', 'intent', 'entities'],
    'Wellness Score': ['score', 'metrics', 'recommendations'],
    'Blockchain Integration': ['status', 'networks', 'balance'],
    'Social Trading': ['signals', 'traders', 'performance'],
    'Wealth Circles': ['circles', 'categories', 'members']
  };
  
  const expected = expectedFields[featureName];
  if (expected) {
    const missing = expected.filter(field => !(field in data));
    if (missing.length > 0) {
      log('yellow', `   ⚠️  Missing expected fields: ${missing.join(', ')}`);
    }
  }
}

async function testErrorHandling() {
  log('blue', '\n🚨 Testing Error Handling...');
  
  const errorTests = [
    {
      name: 'Invalid Endpoint',
      url: `${API_BASE}/api/invalid/endpoint/`,
      method: 'GET',
      expectedStatus: 404
    },
    {
      name: 'Malformed JSON',
      url: `${API_BASE}/api/auth/login/`,
      method: 'POST',
      body: 'invalid json',
      expectedStatus: 400
    },
    {
      name: 'Large Payload',
      url: `${API_BASE}/api/auth/login/`,
      method: 'POST',
      body: { email: 'a'.repeat(10000), password: 'demo123' },
      expectedStatus: 400
    }
  ];

  for (const test of errorTests) {
    try {
      const response = await makeRequest(test.url, {
        method: test.method,
        body: test.body
      });
      
      if (response.status === test.expectedStatus) {
        log('green', `✅ ${test.name}: ${response.status} (Expected error handled correctly)`);
      } else {
        log('red', `❌ ${test.name}: Expected ${test.expectedStatus}, got ${response.status}`);
      }
    } catch (error) {
      log('red', `❌ ${test.name}: ${error.message}`);
    }
  }
}

async function runComprehensiveTests() {
  log('magenta', '🧪 RichesReach Version 2 - Comprehensive Error Testing');
  log('magenta', '==================================================');
  
  const startTime = Date.now();
  
  // Test 1: Backend Health
  const isHealthy = await testBackendHealth();
  if (!isHealthy) {
    log('red', '\n❌ Backend is not accessible. Please start the backend server first.');
    log('yellow', 'Run: cd ../backend && python manage.py runserver');
    return;
  }
  
  // Test 2: Authentication
  const authToken = await testAuthentication();
  
  // Test 3: API Endpoints
  await testAPIEndpoints(authToken);
  
  // Test 4: Version 2 Features
  await testVersion2Features(authToken);
  
  // Test 5: Error Handling
  await testErrorHandling();
  
  const endTime = Date.now();
  const duration = (endTime - startTime) / 1000;
  
  log('green', '\n✅ Comprehensive testing completed!');
  log('cyan', `⏱️  Total time: ${duration.toFixed(2)} seconds`);
  
  log('blue', '\n📊 Summary:');
  log('white', '  • Backend health: Checked');
  log('white', '  • Authentication: Tested');
  log('white', '  • API endpoints: Tested');
  log('white', '  • Version 2 features: Tested');
  log('white', '  • Error handling: Tested');
  
  log('yellow', '\n⚠️  Note: Some Version 2 endpoints may return 404 if not implemented yet.');
  log('yellow', 'This is expected for features that are still in development.');
}

// Run the tests
runComprehensiveTests().catch(error => {
  log('red', `\n❌ Test execution failed: ${error.message}`);
  process.exit(1);
});
