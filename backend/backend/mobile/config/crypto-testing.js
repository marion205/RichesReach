/**
 * Crypto Testing Configuration
 * Use this to test the crypto UI with mock data
 */

export const CRYPTO_CONFIG = {
  // API Endpoints
  API_BASE_URL: 'http://localhost:8127',
  REPAY_API_URL: 'http://localhost:8128',
  
  // GraphQL Endpoints
  GRAPHQL_URL: 'http://localhost:8127/graphql',
  REPAY_GRAPHQL_URL: 'http://localhost:8128/graphql',
  
  // Testing Features
  ENABLE_MOCK_DATA: true,
  ENABLE_DEBUG_LOGGING: true,
  ENABLE_PERFORMANCE_MONITORING: true,
  
  // Mock Data Settings
  MOCK_PORTFOLIO_VALUE: 47754.25,
  MOCK_PNL_PERCENTAGE: -3.33,
  MOCK_HOLDINGS_COUNT: 3,
  
  // Performance Thresholds
  MAX_API_RESPONSE_TIME: 100, // ms
  MAX_UI_RENDER_TIME: 16, // ms (60fps)
  
  // Testing Scenarios
  TEST_SCENARIOS: {
    BULLISH_MARKET: {
      btc_signal: 'BIG_UP_DAY',
      btc_probability: 0.78,
      portfolio_pnl: 15.5
    },
    BEARISH_MARKET: {
      btc_signal: 'BIG_DOWN_DAY', 
      btc_probability: 0.65,
      portfolio_pnl: -8.2
    },
    NEUTRAL_MARKET: {
      btc_signal: 'NEUTRAL',
      btc_probability: 0.48,
      portfolio_pnl: 2.1
    }
  }
};

export const TEST_DATA = {
  CURRENCIES: [
    { symbol: 'BTC', name: 'Bitcoin', price: 46981.94 },
    { symbol: 'ETH', name: 'Ethereum', price: 3400.25 },
    { symbol: 'SOL', name: 'Solana', price: 150.75 }
  ],
  
  PORTFOLIO: {
    total_value_usd: 47754.25,
    total_pnl: -1650.50,
    total_pnl_percentage: -3.33,
    holdings: [
      { symbol: 'BTC', quantity: 0.5, value: 23490.97, pnl_pct: 12.5 },
      { symbol: 'ETH', quantity: 2.0, value: 6800.50, pnl_pct: -8.3 },
      { symbol: 'SOL', quantity: 50.0, value: 7537.50, pnl_pct: -5.2 }
    ]
  },
  
  LOANS: [
    { id: 'loan_1', symbol: 'BTC', amount: 5000, rate: 0.05, status: 'ACTIVE' },
    { id: 'loan_2', symbol: 'ETH', amount: 2500, rate: 0.06, status: 'ACTIVE' }
  ]
};
