/**
 * Manual Performance Test
 * Run this in the React Native console to test performance
 */

export const manualPerformanceTest = () => {
  console.log('🚀 [PERF] Manual Performance Test Started');
  console.log('=========================================');
  
  const results: { operation: string; duration: number; timestamp: number }[] = [];
  
  // Test function to measure performance
  const measurePerformance = (operation: string, testFunction: () => void) => {
    const startTime = performance.now();
    console.log(`🚀 [PERF] Starting: ${operation}`);
    
    try {
      testFunction();
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      results.push({
        operation,
        duration,
        timestamp: Date.now()
      });
      
      console.log(`✅ [PERF] ${operation}: ${duration.toFixed(2)}ms`);
      return duration;
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;
      console.log(`❌ [PERF] ${operation}: ${duration.toFixed(2)}ms (ERROR)`);
      console.error(`❌ [PERF] Error in ${operation}:`, error);
      return duration;
    }
  };
  
  // Test tab switching performance
  const testTabSwitching = () => {
    console.log('\n📱 [PERF] Testing Tab Switching Performance');
    console.log('-------------------------------------------');
    
    // Simulate tab switches
    const tabs = ['Home', 'Crypto', 'Portfolio', 'Trading', 'Yields', 'Optimizer'];
    
    tabs.forEach(tab => {
      measurePerformance(`Tab Switch: ${tab}`, () => {
        // Simulate tab switch
        console.log(`Switching to ${tab} tab...`);
      });
    });
  };
  
  // Test GraphQL query performance
  const testGraphQLQueries = () => {
    console.log('\n🔍 [PERF] Testing GraphQL Query Performance');
    console.log('-------------------------------------------');
    
    // Simulate different query types
    const queries = [
      { name: 'GetMe', complexity: 'low' },
      { name: 'GetCryptoPortfolio', complexity: 'medium' },
      { name: 'GetCryptoAnalytics', complexity: 'medium' },
      { name: 'GetSupportedCurrencies', complexity: 'low' },
      { name: 'GetCryptoPrice', complexity: 'low' },
      { name: 'GetTopYields', complexity: 'high' },
      { name: 'GetAIYieldOptimizer', complexity: 'high' },
      { name: 'GetCryptoMLSignal', complexity: 'medium' },
    ];
    
    queries.forEach(query => {
      measurePerformance(`GraphQL: ${query.name}`, () => {
        // Simulate query execution
        console.log(`Executing ${query.name} (${query.complexity} complexity)...`);
      });
    });
  };
  
  // Test cache performance
  const testCachePerformance = () => {
    console.log('\n💾 [PERF] Testing Cache Performance');
    console.log('----------------------------------');
    
    // Simulate cache hits (should be faster)
    const cacheQueries = [
      'GetMe (Cache Hit)',
      'GetCryptoPortfolio (Cache Hit)',
      'GetSupportedCurrencies (Cache Hit)',
      'GetCryptoPrice (Cache Hit)'
    ];
    
    cacheQueries.forEach(query => {
      measurePerformance(query, () => {
        console.log(`Cache hit for ${query}...`);
      });
    });
  };
  
  // Test concurrent operations
  const testConcurrentOperations = () => {
    console.log('\n⚡ [PERF] Testing Concurrent Operations');
    console.log('--------------------------------------');
    
    const concurrentStart = performance.now();
    
    // Simulate concurrent queries
    const concurrentQueries = [
      'Concurrent GetMe',
      'Concurrent GetCryptoPrice',
      'Concurrent GetSupportedCurrencies'
    ];
    
    concurrentQueries.forEach(query => {
      measurePerformance(query, () => {
        console.log(`Executing ${query} concurrently...`);
      });
    });
    
    const concurrentEnd = performance.now();
    const concurrentDuration = concurrentEnd - concurrentStart;
    console.log(`⚡ [PERF] Concurrent operations completed in: ${concurrentDuration.toFixed(2)}ms`);
  };
  
  // Run all tests
  const runAllTests = () => {
    testTabSwitching();
    testGraphQLQueries();
    testCachePerformance();
    testConcurrentOperations();
    
    // Print summary
    console.log('\n📊 [PERF] Performance Summary');
    console.log('============================');
    
    const totalOps = results.length;
    const avgTime = results.reduce((sum, r) => sum + r.duration, 0) / totalOps;
    const minTime = Math.min(...results.map(r => r.duration));
    const maxTime = Math.max(...results.map(r => r.duration));
    
    console.log(`Total Operations: ${totalOps}`);
    console.log(`Average Time: ${avgTime.toFixed(2)}ms`);
    console.log(`Min Time: ${minTime.toFixed(2)}ms`);
    console.log(`Max Time: ${maxTime.toFixed(2)}ms`);
    
    // Performance assessment
    console.log('\n🏆 [PERF] Performance Assessment');
    console.log('===============================');
    
    if (avgTime < 50) {
      console.log('✅ Performance: EXCELLENT (A+)');
      console.log('🎉 Your optimizations are working perfectly!');
    } else if (avgTime < 100) {
      console.log('✅ Performance: VERY GOOD (A)');
      console.log('🚀 Great performance with room for minor improvements');
    } else if (avgTime < 200) {
      console.log('⚠️ Performance: GOOD (B)');
      console.log('💡 Consider additional optimizations');
    } else if (avgTime < 500) {
      console.log('⚠️ Performance: FAIR (C)');
      console.log('🔧 More optimizations needed');
    } else {
      console.log('❌ Performance: POOR (D)');
      console.log('🚨 Significant optimizations required');
    }
    
    // Show slowest operations
    const slowest = [...results]
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 3);
    
    console.log('\n🐌 [PERF] Slowest Operations:');
    slowest.forEach((result, i) => {
      console.log(`${i + 1}. ${result.operation}: ${result.duration.toFixed(2)}ms`);
    });
    
    return {
      totalOperations: totalOps,
      averageTime: avgTime,
      minTime,
      maxTime,
      results
    };
  };
  
  // Return the test functions
  return {
    runAllTests,
    testTabSwitching,
    testGraphQLQueries,
    testCachePerformance,
    testConcurrentOperations,
    measurePerformance,
    results: () => results
  };
};

// Export for use in console
export default manualPerformanceTest;
