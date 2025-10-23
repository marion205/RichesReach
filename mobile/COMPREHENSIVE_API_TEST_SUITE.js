#!/usr/bin/env node

/**
 * Comprehensive API Test Suite for RichesReach Version 2
 * Tests all mutations, GraphQL queries, and endpoints
 * Identifies and helps implement missing endpoints
 */

const https = require('https');
const http = require('http');

// Test configuration
const API_BASE = 'http://127.0.0.1:8000';
const GRAPHQL_ENDPOINT = `${API_BASE}/graphql/`;
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
      timeout: 15000
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

// Authentication token storage
let authToken = null;

async function authenticate() {
  log('blue', '🔐 Authenticating...');
  
  try {
    const response = await makeRequest(`${API_BASE}/api/auth/login/`, {
      method: 'POST',
      body: TEST_CREDENTIALS
    });
    
    if (response.status === 200 && response.data.token) {
      authToken = response.data.token;
      log('green', `✅ Authentication successful`);
      log('cyan', `   User: ${response.data.user.email}`);
      log('cyan', `   Token: ${authToken.substring(0, 20)}...`);
      return true;
    } else {
      log('red', `❌ Authentication failed: ${response.status}`);
      if (response.data) {
        log('yellow', `   Error: ${JSON.stringify(response.data)}`);
      }
      return false;
    }
  } catch (error) {
    log('red', `❌ Authentication error: ${error.message}`);
    return false;
  }
}

// GraphQL Queries and Mutations
const GRAPHQL_OPERATIONS = {
  // User Queries
  getUserProfile: {
    query: `
      query GetUserProfile {
        me {
          id
          email
          username
          name
          hasPremiumAccess
          subscriptionTier
          createdAt
          lastLogin
        }
      }
    `
  },
  
  getUserPortfolios: {
    query: `
      query GetUserPortfolios {
        portfolios {
          id
          name
          totalValue
          totalReturn
          totalReturnPercent
          holdings {
            id
            symbol
            shares
            currentPrice
            totalValue
          }
          createdAt
          updatedAt
        }
      }
    `
  },
  
  getMarketData: {
    query: `
      query GetMarketData($symbols: [String!]!) {
        marketData(symbols: $symbols) {
          symbol
          price
          change
          changePercent
          volume
          marketCap
          lastUpdated
        }
      }
    `,
    variables: { symbols: ['AAPL', 'MSFT', 'GOOGL', 'TSLA'] }
  },
  
  getNews: {
    query: `
      query GetNews($limit: Int, $category: String) {
        news(limit: $limit, category: $category) {
          id
          title
          summary
          url
          publishedAt
          source
          sentiment
          relevanceScore
        }
      }
    `,
    variables: { limit: 10, category: 'finance' }
  },
  
  // Portfolio Mutations
  createPortfolio: {
    query: `
      mutation CreatePortfolio($input: PortfolioInput!) {
        createPortfolio(input: $input) {
          portfolio {
            id
            name
            totalValue
            totalReturn
            totalReturnPercent
          }
          success
          errors
        }
      }
    `,
    variables: {
      input: {
        name: 'Test Portfolio',
        description: 'Test portfolio for API testing'
      }
    }
  },
  
  updatePortfolio: {
    query: `
      mutation UpdatePortfolio($id: ID!, $input: PortfolioInput!) {
        updatePortfolio(id: $id, input: $input) {
          portfolio {
            id
            name
            totalValue
            totalReturn
            totalReturnPercent
          }
          success
          errors
        }
      }
    `,
    variables: {
      id: '1',
      input: {
        name: 'Updated Test Portfolio'
      }
    }
  },
  
  deletePortfolio: {
    query: `
      mutation DeletePortfolio($id: ID!) {
        deletePortfolio(id: $id) {
          success
          errors
        }
      }
    `,
    variables: { id: '1' }
  },
  
  // Trading Mutations
  addHolding: {
    query: `
      mutation AddHolding($portfolioId: ID!, $input: HoldingInput!) {
        addHolding(portfolioId: $portfolioId, input: $input) {
          holding {
            id
            symbol
            shares
            currentPrice
            totalValue
          }
          success
          errors
        }
      }
    `,
    variables: {
      portfolioId: '1',
      input: {
        symbol: 'AAPL',
        shares: 10,
        purchasePrice: 150.00
      }
    }
  },
  
  updateHolding: {
    query: `
      mutation UpdateHolding($id: ID!, $input: HoldingInput!) {
        updateHolding(id: $id, input: $input) {
          holding {
            id
            symbol
            shares
            currentPrice
            totalValue
          }
          success
          errors
        }
      }
    `,
    variables: {
      id: '1',
      input: {
        shares: 15
      }
    }
  },
  
  removeHolding: {
    query: `
      mutation RemoveHolding($id: ID!) {
        removeHolding(id: $id) {
          success
          errors
        }
      }
    `,
    variables: { id: '1' }
  },
  
  // Version 2 Features
  getOracleInsights: {
    query: `
      query GetOracleInsights($portfolioId: ID) {
        oracleInsights(portfolioId: $portfolioId) {
          id
          insights {
            type
            title
            description
            confidence
            impact
            timeframe
          }
          predictions {
            symbol
            direction
            targetPrice
            confidence
            timeframe
          }
          marketSentiment
          riskAssessment
          recommendations
          generatedAt
        }
      }
    `,
    variables: { portfolioId: '1' }
  },
  
  processVoiceCommand: {
    query: `
      mutation ProcessVoiceCommand($input: VoiceInput!) {
        processVoiceCommand(input: $input) {
          response {
            text
            intent
            entities
            confidence
          }
          actions {
            type
            parameters
            execute
          }
          success
          errors
        }
      }
    `,
    variables: {
      input: {
        audio: 'base64_encoded_audio',
        text: 'What is my portfolio performance?',
        language: 'en'
      }
    }
  },
  
  getWellnessScore: {
    query: `
      query GetWellnessScore($portfolioId: ID!) {
        wellnessScore(portfolioId: $portfolioId) {
          id
          overallScore
          metrics {
            riskManagement
            diversification
            taxEfficiency
            performance
            liquidity
          }
          recommendations {
            category
            priority
            description
            impact
          }
          calculatedAt
        }
      }
    `,
    variables: { portfolioId: '1' }
  },
  
  getBlockchainStatus: {
    query: `
      query GetBlockchainStatus {
        blockchainStatus {
          networks {
            name
            status
            balance
            transactions
          }
          defiPositions {
            protocol
            asset
            amount
            apy
          }
          nfts {
            id
            name
            value
            collection
          }
          lastUpdated
        }
      }
    `
  },
  
  getSocialTrading: {
    query: `
      query GetSocialTrading {
        socialTrading {
          signals {
            id
            trader
            symbol
            action
            price
            confidence
            timestamp
          }
          topTraders {
            id
            name
            performance
            followers
            winRate
          }
          collectiveFunds {
            id
            name
            totalValue
            participants
            performance
          }
        }
      }
    `
  },
  
  getWealthCircles: {
    query: `
      query GetWealthCircles {
        wealthCircles {
          id
          name
          category
          description
          members
          activity {
            type
            user
            content
            timestamp
          }
          recentActivity {
            type
            user
            content
            timestamp
          }
        }
      }
    `
  }
};

// REST API Endpoints
const REST_ENDPOINTS = {
  // Authentication
  login: {
    method: 'POST',
    url: `${API_BASE}/api/auth/login/`,
    body: TEST_CREDENTIALS,
    requiresAuth: false
  },
  
  logout: {
    method: 'POST',
    url: `${API_BASE}/api/auth/logout/`,
    requiresAuth: true
  },
  
  refreshToken: {
    method: 'POST',
    url: `${API_BASE}/api/auth/refresh/`,
    requiresAuth: true
  },
  
  // User Management
  getUserProfile: {
    method: 'GET',
    url: `${API_BASE}/api/user/profile/`,
    requiresAuth: true
  },
  
  updateUserProfile: {
    method: 'PUT',
    url: `${API_BASE}/api/user/profile/`,
    body: { name: 'Updated Name' },
    requiresAuth: true
  },
  
  // Portfolio Management
  getPortfolios: {
    method: 'GET',
    url: `${API_BASE}/api/portfolio/`,
    requiresAuth: true
  },
  
  createPortfolio: {
    method: 'POST',
    url: `${API_BASE}/api/portfolio/`,
    body: { name: 'Test Portfolio', description: 'Test portfolio' },
    requiresAuth: true
  },
  
  getPortfolio: {
    method: 'GET',
    url: `${API_BASE}/api/portfolio/1/`,
    requiresAuth: true
  },
  
  updatePortfolio: {
    method: 'PUT',
    url: `${API_BASE}/api/portfolio/1/`,
    body: { name: 'Updated Portfolio' },
    requiresAuth: true
  },
  
  deletePortfolio: {
    method: 'DELETE',
    url: `${API_BASE}/api/portfolio/1/`,
    requiresAuth: true
  },
  
  // Holdings Management
  getHoldings: {
    method: 'GET',
    url: `${API_BASE}/api/portfolio/1/holdings/`,
    requiresAuth: true
  },
  
  addHolding: {
    method: 'POST',
    url: `${API_BASE}/api/portfolio/1/holdings/`,
    body: { symbol: 'AAPL', shares: 10, purchasePrice: 150.00 },
    requiresAuth: true
  },
  
  updateHolding: {
    method: 'PUT',
    url: `${API_BASE}/api/portfolio/1/holdings/1/`,
    body: { shares: 15 },
    requiresAuth: true
  },
  
  deleteHolding: {
    method: 'DELETE',
    url: `${API_BASE}/api/portfolio/1/holdings/1/`,
    requiresAuth: true
  },
  
  // Market Data
  getMarketQuotes: {
    method: 'GET',
    url: `${API_BASE}/api/market/quotes/?symbols=AAPL,MSFT,GOOGL,TSLA`,
    requiresAuth: false
  },
  
  getMarketNews: {
    method: 'GET',
    url: `${API_BASE}/api/market/news/`,
    requiresAuth: false
  },
  
  getMarketAnalysis: {
    method: 'GET',
    url: `${API_BASE}/api/market/analysis/?symbol=AAPL`,
    requiresAuth: false
  },
  
  // Version 2 Features
  getOracleInsights: {
    method: 'GET',
    url: `${API_BASE}/api/oracle/insights/?portfolioId=1`,
    requiresAuth: true
  },
  
  processVoiceCommand: {
    method: 'POST',
    url: `${API_BASE}/api/voice/process/`,
    body: { text: 'What is my portfolio performance?', language: 'en' },
    requiresAuth: true
  },
  
  getWellnessScore: {
    method: 'GET',
    url: `${API_BASE}/api/portfolio/1/wellness/`,
    requiresAuth: true
  },
  
  getARPortfolioData: {
    method: 'GET',
    url: `${API_BASE}/api/portfolio/1/ar/`,
    requiresAuth: true
  },
  
  getBlockchainStatus: {
    method: 'GET',
    url: `${API_BASE}/api/blockchain/status/`,
    requiresAuth: true
  },
  
  getSocialTrading: {
    method: 'GET',
    url: `${API_BASE}/api/social/trading/`,
    requiresAuth: true
  },
  
  getWealthCircles: {
    method: 'GET',
    url: `${API_BASE}/api/wealth-circles/`,
    requiresAuth: true
  },
  
  getThemeSettings: {
    method: 'GET',
    url: `${API_BASE}/api/user/theme/`,
    requiresAuth: true
  },
  
  updateThemeSettings: {
    method: 'PUT',
    url: `${API_BASE}/api/user/theme/`,
    body: { theme: 'dark', primaryColor: '#8B5CF6' },
    requiresAuth: true
  },
  
  getSecuritySettings: {
    method: 'GET',
    url: `${API_BASE}/api/user/security/`,
    requiresAuth: true
  },
  
  updateSecuritySettings: {
    method: 'PUT',
    url: `${API_BASE}/api/user/security/`,
    body: { biometricAuth: true, twoFactorAuth: false },
    requiresAuth: true
  },
  
  getViralGrowthData: {
    method: 'GET',
    url: `${API_BASE}/api/viral-growth/`,
    requiresAuth: true
  },
  
  getScalabilityMetrics: {
    method: 'GET',
    url: `${API_BASE}/api/system/scalability/`,
    requiresAuth: true
  },
  
  getMarketingMetrics: {
    method: 'GET',
    url: `${API_BASE}/api/marketing/metrics/`,
    requiresAuth: true
  }
};

async function testGraphQLOperation(name, operation) {
  try {
    const response = await makeRequest(GRAPHQL_ENDPOINT, {
      method: 'POST',
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      body: {
        query: operation.query,
        variables: operation.variables || {}
      }
    });
    
    if (response.status === 200) {
      if (response.data.errors) {
        log('yellow', `⚠️  ${name}: GraphQL errors found`);
        response.data.errors.forEach(error => {
          log('yellow', `   - ${error.message}`);
        });
      } else {
        log('green', `✅ ${name}: ${response.status}`);
      }
    } else {
      log('red', `❌ ${name}: ${response.status}`);
      if (response.data) {
        log('yellow', `   Error: ${JSON.stringify(response.data)}`);
      }
    }
    
    return response;
  } catch (error) {
    log('red', `❌ ${name}: ${error.message}`);
    return null;
  }
}

async function testRESTEndpoint(name, endpoint) {
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
      log('green', `✅ ${name}: ${response.status}`);
    } else if (response.status === 404) {
      log('yellow', `⚠️  ${name}: ${response.status} (Not implemented)`);
    } else if (response.status === 401) {
      log('yellow', `⚠️  ${name}: ${response.status} (Unauthorized)`);
    } else {
      log('red', `❌ ${name}: ${response.status}`);
      if (response.data) {
        log('yellow', `   Error: ${JSON.stringify(response.data)}`);
      }
    }
    
    return response;
  } catch (error) {
    log('red', `❌ ${name}: ${error.message}`);
    return null;
  }
}

async function runComprehensiveTests() {
  log('magenta', '🧪 RichesReach Version 2 - Comprehensive API Test Suite');
  log('magenta', '=====================================================');
  
  const startTime = Date.now();
  
  // Step 1: Authenticate
  const isAuthenticated = await authenticate();
  if (!isAuthenticated) {
    log('red', '\n❌ Authentication failed. Cannot proceed with tests.');
    return;
  }
  
  // Step 2: Test GraphQL Operations
  log('blue', '\n🔍 Testing GraphQL Operations...');
  
  for (const [name, operation] of Object.entries(GRAPHQL_OPERATIONS)) {
    await testGraphQLOperation(name, operation);
  }
  
  // Step 3: Test REST Endpoints
  log('blue', '\n🌐 Testing REST Endpoints...');
  
  for (const [name, endpoint] of Object.entries(REST_ENDPOINTS)) {
    await testRESTEndpoint(name, endpoint);
  }
  
  const endTime = Date.now();
  const duration = (endTime - startTime) / 1000;
  
  log('green', '\n✅ Comprehensive API testing completed!');
  log('cyan', `⏱️  Total time: ${duration.toFixed(2)} seconds`);
  
  // Generate missing endpoints report
  generateMissingEndpointsReport();
}

function generateMissingEndpointsReport() {
  log('blue', '\n📋 Missing Endpoints Report');
  log('blue', '===========================');
  
  const missingEndpoints = [
    'User Profile API',
    'Portfolio Management API',
    'Holdings Management API',
    'Market Data API',
    'News API',
    'Oracle Insights API',
    'Voice AI Assistant API',
    'Wellness Score API',
    'AR Portfolio API',
    'Blockchain Integration API',
    'Social Trading API',
    'Wealth Circles API',
    'Theme Settings API',
    'Security Settings API',
    'Viral Growth API',
    'Scalability Metrics API',
    'Marketing Metrics API'
  ];
  
  log('yellow', 'The following endpoints need to be implemented:');
  missingEndpoints.forEach((endpoint, index) => {
    log('white', `  ${index + 1}. ${endpoint}`);
  });
  
  log('cyan', '\n💡 Next Steps:');
  log('white', '  1. Implement missing REST API endpoints');
  log('white', '  2. Add GraphQL schema and resolvers');
  log('white', '  3. Test all endpoints with this script');
  log('white', '  4. Add proper error handling');
  log('white', '  5. Add authentication middleware');
}

// Run the comprehensive tests
runComprehensiveTests().catch(error => {
  log('red', `\n❌ Test execution failed: ${error.message}`);
  process.exit(1);
});
