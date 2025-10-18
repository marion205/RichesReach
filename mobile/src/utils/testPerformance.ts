/**
 * Direct Performance Test Runner
 * Run this to test performance without UI
 */

import { runComprehensivePerformanceTests, quickPerformanceTest } from './runPerformanceTests';

// Run the tests
const runTests = async () => {
  console.log('🚀 Starting Performance Tests...');
  console.log('================================');
  
  try {
    // Run quick test first
    console.log('\n⚡ Running Quick Test...');
    await quickPerformanceTest();
    
    // Wait a bit
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Run full comprehensive test
    console.log('\n🔍 Running Full Comprehensive Test...');
    const results = await runComprehensivePerformanceTests();
    
    console.log('\n🎉 All Performance Tests Complete!');
    console.log('==================================');
    console.log('Results Summary:');
    console.log(`- Login Time: ${results.loginTime.toFixed(2)}ms`);
    console.log(`- GraphQL Average: ${results.graphqlTime.toFixed(2)}ms`);
    console.log(`- Query Average: ${results.queryTime.toFixed(2)}ms`);
    console.log(`- Tab Switch Average: ${results.tabTime.toFixed(2)}ms`);
    console.log(`- Total Operations: ${results.totalOperations}`);
    console.log(`- Success Rate: ${results.successRate.toFixed(1)}%`);
    
    // Performance assessment
    console.log('\n📊 Performance Assessment:');
    if (results.loginTime < 500) {
      console.log('✅ Login performance: EXCELLENT');
    } else if (results.loginTime < 1000) {
      console.log('⚠️ Login performance: GOOD');
    } else {
      console.log('❌ Login performance: NEEDS IMPROVEMENT');
    }
    
    if (results.graphqlTime < 300) {
      console.log('✅ GraphQL performance: EXCELLENT');
    } else if (results.graphqlTime < 600) {
      console.log('⚠️ GraphQL performance: GOOD');
    } else {
      console.log('❌ GraphQL performance: NEEDS IMPROVEMENT');
    }
    
    if (results.tabTime < 100) {
      console.log('✅ Tab switching: EXCELLENT');
    } else if (results.tabTime < 200) {
      console.log('⚠️ Tab switching: GOOD');
    } else {
      console.log('❌ Tab switching: NEEDS IMPROVEMENT');
    }
    
  } catch (error) {
    console.error('❌ Performance test failed:', error);
  }
};

// Export for use in other files
export { runTests };

// Run if this file is executed directly
if (require.main === module) {
  runTests();
}
