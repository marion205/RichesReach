/**
 * Comprehensive Performance Test Suite
 * Tests login, GraphQL calls, and tab switching performance
 */

import { perfTracker, testLoginPerformance, testTabSwitchPerformance, testQueryPerformance } from './performanceTest';

// Mock functions for testing (replace with actual implementations)
const mockLogin = async () => {
  // Simulate login API call
  await new Promise(resolve => setTimeout(resolve, 200));
  return { token: 'mock-token', user: { id: '1', email: 'test@example.com' } };
};

const mockGraphQLQueries = {
  getMe: async () => {
    await new Promise(resolve => setTimeout(resolve, 150));
    return { me: { id: '1', email: 'test@example.com' } };
  },
  
  getCryptoPortfolio: async () => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return { cryptoPortfolio: { totalValue: 10000, holdings: [] } };
  },
  
  getCryptoAnalytics: async () => {
    await new Promise(resolve => setTimeout(resolve, 250));
    return { cryptoAnalytics: { totalReturn: 1000, totalReturnPercent: 10 } };
  },
  
  getSupportedCurrencies: async () => {
    await new Promise(resolve => setTimeout(resolve, 100));
    return { supportedCurrencies: [{ symbol: 'BTC', name: 'Bitcoin' }] };
  },
  
  getCryptoPrice: async () => {
    await new Promise(resolve => setTimeout(resolve, 120));
    return { cryptoPrice: { price: 50000, change24h: 2.5 } };
  },
  
  getTopYields: async () => {
    await new Promise(resolve => setTimeout(resolve, 400));
    return { topYields: [{ id: '1', protocol: 'Aave', apy: 4.2 }] };
  },
  
  getAIYieldOptimizer: async () => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { aiYieldOptimizer: { expectedApy: 4.8, allocations: [] } };
  },
  
  getCryptoMLSignal: async () => {
    await new Promise(resolve => setTimeout(resolve, 200));
    return { cryptoMlSignal: { predictionType: 'BULLISH', probability: 0.75 } };
  }
};

const mockTabSwitches = {
  home: () => console.log('Switching to Home tab'),
  crypto: () => console.log('Switching to Crypto tab'),
  portfolio: () => console.log('Switching to Portfolio tab'),
  trading: () => console.log('Switching to Trading tab'),
  yields: () => console.log('Switching to Yields tab'),
  optimizer: () => console.log('Switching to Optimizer tab')
};

export const runComprehensivePerformanceTests = async () => {
  console.log('🚀 [PERF] Starting Comprehensive Performance Tests');
  console.log('================================================');
  
  perfTracker.clear();
  
  // Test 1: Login Performance
  console.log('\n🔐 [PERF] Test 1: Login Performance');
  console.log('-----------------------------------');
  await testLoginPerformance(mockLogin);
  
  // Test 2: Initial GraphQL Queries (Cold Start)
  console.log('\n🔍 [PERF] Test 2: Initial GraphQL Queries (Cold Start)');
  console.log('------------------------------------------------------');
  
  await testQueryPerformance('GetMe', mockGraphQLQueries.getMe);
  await testQueryPerformance('GetCryptoPortfolio', mockGraphQLQueries.getCryptoPortfolio);
  await testQueryPerformance('GetCryptoAnalytics', mockGraphQLQueries.getCryptoAnalytics);
  await testQueryPerformance('GetSupportedCurrencies', mockGraphQLQueries.getSupportedCurrencies);
  
  // Test 3: Tab Switching Performance
  console.log('\n📱 [PERF] Test 3: Tab Switching Performance');
  console.log('-------------------------------------------');
  
  Object.entries(mockTabSwitches).forEach(([tabName, switchFunction]) => {
    testTabSwitchPerformance(tabName, switchFunction);
  });
  
  // Test 4: Crypto-Specific Queries
  console.log('\n💰 [PERF] Test 4: Crypto-Specific Queries');
  console.log('----------------------------------------');
  
  await testQueryPerformance('GetCryptoPrice', mockGraphQLQueries.getCryptoPrice);
  await testQueryPerformance('GetTopYields', mockGraphQLQueries.getTopYields);
  await testQueryPerformance('GetAIYieldOptimizer', mockGraphQLQueries.getAIYieldOptimizer);
  await testQueryPerformance('GetCryptoMLSignal', mockGraphQLQueries.getCryptoMLSignal);
  
  // Test 5: Cache Performance (Simulate second calls)
  console.log('\n💾 [PERF] Test 5: Cache Performance (Second Calls)');
  console.log('-------------------------------------------------');
  
  // Simulate cache hits (should be much faster)
  await testQueryPerformance('GetMe (Cache)', mockGraphQLQueries.getMe);
  await testQueryPerformance('GetCryptoPortfolio (Cache)', mockGraphQLQueries.getCryptoPortfolio);
  await testQueryPerformance('GetSupportedCurrencies (Cache)', mockGraphQLQueries.getSupportedCurrencies);
  
  // Test 6: Concurrent Queries
  console.log('\n⚡ [PERF] Test 6: Concurrent Queries');
  console.log('-----------------------------------');
  
  const concurrentStart = performance.now();
  await Promise.all([
    testQueryPerformance('Concurrent GetMe', mockGraphQLQueries.getMe),
    testQueryPerformance('Concurrent GetCryptoPrice', mockGraphQLQueries.getCryptoPrice),
    testQueryPerformance('Concurrent GetSupportedCurrencies', mockGraphQLQueries.getSupportedCurrencies)
  ]);
  const concurrentEnd = performance.now();
  console.log(`⚡ [PERF] Concurrent queries completed in: ${(concurrentEnd - concurrentStart).toFixed(2)}ms`);
  
  // Test 7: Heavy Operations
  console.log('\n🏋️ [PERF] Test 7: Heavy Operations');
  console.log('---------------------------------');
  
  await testQueryPerformance('Heavy TopYields', mockGraphQLQueries.getTopYields);
  await testQueryPerformance('Heavy AIYieldOptimizer', mockGraphQLQueries.getAIYieldOptimizer);
  
  // Wait a bit for all async operations to complete
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Print comprehensive summary
  console.log('\n📊 [PERF] Final Performance Summary');
  console.log('==================================');
  perfTracker.printSummary();
  
  // Performance benchmarks
  console.log('\n🎯 [PERF] Performance Benchmarks');
  console.log('================================');
  
  const loginTime = perfTracker.getAverageTime('Login');
  const graphqlTime = perfTracker.getAverageTime('GraphQL');
  const queryTime = perfTracker.getAverageTime('Query');
  const tabTime = perfTracker.getAverageTime('Tab Switch');
  
  console.log(`Login Time: ${loginTime.toFixed(2)}ms (Target: <500ms)`);
  console.log(`GraphQL Average: ${graphqlTime.toFixed(2)}ms (Target: <300ms)`);
  console.log(`Query Average: ${queryTime.toFixed(2)}ms (Target: <200ms)`);
  console.log(`Tab Switch Average: ${tabTime.toFixed(2)}ms (Target: <100ms)`);
  
  // Performance grades
  const getGrade = (time: number, target: number) => {
    if (time < target * 0.5) return 'A+';
    if (time < target * 0.75) return 'A';
    if (time < target) return 'B';
    if (time < target * 1.5) return 'C';
    return 'D';
  };
  
  console.log('\n🏆 [PERF] Performance Grades');
  console.log('===========================');
  console.log(`Login: ${getGrade(loginTime, 500)} (${loginTime.toFixed(2)}ms)`);
  console.log(`GraphQL: ${getGrade(graphqlTime, 300)} (${graphqlTime.toFixed(2)}ms)`);
  console.log(`Queries: ${getGrade(queryTime, 200)} (${queryTime.toFixed(2)}ms)`);
  console.log(`Tab Switches: ${getGrade(tabTime, 100)} (${tabTime.toFixed(2)}ms)`);
  
  return {
    loginTime,
    graphqlTime,
    queryTime,
    tabTime,
    totalOperations: perfTracker.getMetrics().length,
    successRate: perfTracker.getSuccessRate()
  };
};

// Quick performance test for specific operations
export const quickPerformanceTest = async () => {
  console.log('⚡ [PERF] Quick Performance Test');
  console.log('===============================');
  
  perfTracker.clear();
  
  // Test the most critical operations
  await testLoginPerformance(mockLogin);
  await testQueryPerformance('GetMe', mockGraphQLQueries.getMe);
  await testQueryPerformance('GetCryptoPortfolio', mockGraphQLQueries.getCryptoPortfolio);
  
  testTabSwitchPerformance('crypto', mockTabSwitches.crypto);
  testTabSwitchPerformance('yields', mockTabSwitches.yields);
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  console.log('\n⚡ [PERF] Quick Test Results:');
  perfTracker.printSummary();
  
  return perfTracker.getMetrics();
};

export default runComprehensivePerformanceTests;
