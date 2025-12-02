/**
 * Verify Credit Building Feature Reachability
 * Checks that all credit components are imported and accessible
 */

const fs = require('fs');
const path = require('path');

const results = {
  components: [],
  services: [],
  screens: [],
  integrations: [],
  errors: []
};

// Check component imports
function checkImports() {
  const portfolioScreenPath = path.join(__dirname, 'mobile/src/features/portfolio/screens/PortfolioScreen.tsx');
  const portfolioScreen = fs.readFileSync(portfolioScreenPath, 'utf8');
  
  // Check CreditQuestScreen import
  if (portfolioScreen.includes('CreditQuestScreen')) {
    results.integrations.push('✅ CreditQuestScreen imported in PortfolioScreen');
  } else {
    results.errors.push('❌ CreditQuestScreen not imported in PortfolioScreen');
  }
  
  // Check credit button
  if (portfolioScreen.includes('showCreditQuest')) {
    results.integrations.push('✅ Credit Quest state managed in PortfolioScreen');
  } else {
    results.errors.push('❌ Credit Quest state not found in PortfolioScreen');
  }
  
  if (portfolioScreen.includes('creditButton')) {
    results.integrations.push('✅ Credit button rendered in PortfolioScreen header');
  } else {
    results.errors.push('❌ Credit button not found in PortfolioScreen');
  }
  
  // Check learning paths
  const learningPathsPath = path.join(__dirname, 'mobile/src/shared/learningPaths.ts');
  const learningPaths = fs.readFileSync(learningPathsPath, 'utf8');
  
  if (learningPaths.includes('CREDIT_BUILDING')) {
    results.integrations.push('✅ Credit Building learning path defined');
  } else {
    results.errors.push('❌ Credit Building learning path not found');
  }
}

// Check file existence
function checkFiles() {
  const files = [
    'mobile/src/features/credit/types/CreditTypes.ts',
    'mobile/src/features/credit/services/CreditScoreService.ts',
    'mobile/src/features/credit/services/CreditUtilizationService.ts',
    'mobile/src/features/credit/services/CreditCardService.ts',
    'mobile/src/features/credit/components/CreditScoreOrb.tsx',
    'mobile/src/features/credit/components/CreditUtilizationGauge.tsx',
    'mobile/src/features/credit/screens/CreditQuestScreen.tsx',
    'deployment_package/backend/core/credit_models.py',
    'deployment_package/backend/core/credit_api.py',
  ];
  
  files.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      results.components.push(`✅ ${file} exists`);
    } else {
      results.errors.push(`❌ ${file} missing`);
    }
  });
}

// Check backend registration
function checkBackend() {
  const mainServerPath = path.join(__dirname, 'main_server.py');
  const mainServer = fs.readFileSync(mainServerPath, 'utf8');
  
  if (mainServer.includes('credit_router')) {
    results.integrations.push('✅ Credit API router registered in main_server.py');
  } else {
    results.errors.push('❌ Credit API router not registered');
  }
  
  if (mainServer.includes('Credit Building API router registered')) {
    results.integrations.push('✅ Credit router registration message present');
  }
}

// Check tests
function checkTests() {
  const testFiles = [
    'deployment_package/backend/core/tests/test_credit_api.py',
    'mobile/src/features/credit/services/__tests__/CreditScoreService.test.ts',
    'mobile/src/features/credit/services/__tests__/CreditUtilizationService.test.ts',
    'mobile/src/features/credit/services/__tests__/CreditCardService.test.ts',
    'mobile/src/features/credit/components/__tests__/CreditScoreOrb.test.tsx',
    'mobile/src/features/credit/components/__tests__/CreditUtilizationGauge.test.tsx',
    'mobile/src/features/credit/screens/__tests__/CreditQuestScreen.test.tsx',
  ];
  
  testFiles.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      results.services.push(`✅ ${file} exists`);
    } else {
      results.errors.push(`❌ ${file} missing`);
    }
  });
}

// Run all checks
checkFiles();
checkImports();
checkBackend();
checkTests();

// Print results
console.log('\n📊 Credit Building Feature Reachability Report\n');
console.log('='.repeat(60));
console.log('\n✅ Components & Files:');
results.components.forEach(item => console.log(`  ${item}`));

console.log('\n✅ Services & Tests:');
results.services.forEach(item => console.log(`  ${item}`));

console.log('\n✅ Integrations:');
results.integrations.forEach(item => console.log(`  ${item}`));

if (results.errors.length > 0) {
  console.log('\n❌ Errors:');
  results.errors.forEach(item => console.log(`  ${item}`));
} else {
  console.log('\n✅ No errors found!');
}

console.log('\n' + '='.repeat(60));
console.log(`\nSummary: ${results.components.length + results.services.length + results.integrations.length} checks passed, ${results.errors.length} errors\n`);

process.exit(results.errors.length > 0 ? 1 : 0);

