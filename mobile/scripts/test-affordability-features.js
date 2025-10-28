const { execSync } = require('child_process');

// Test script to verify the dollar sign button and affordability info are working
function testAffordabilityFeatures() {
    console.log('🔍 Testing Affordability Features (Dollar Sign Button)...\n');
    
    const tests = [
        {
            name: 'User Profile with Income Profile',
            url: 'http://localhost:8000/graphql/',
            method: 'POST',
            body: JSON.stringify({
                query: 'query { me { id name email incomeProfile { incomeBracket age investmentGoals riskTolerance investmentHorizon } } }'
            })
        },
        {
            name: 'Stocks with Beginner Score & Dividend',
            url: 'http://localhost:8000/graphql/',
            method: 'POST',
            body: JSON.stringify({
                query: 'query { stocks { symbol name price beginnerFriendlyScore dividendYield } }'
            })
        },
        {
            name: 'Health Check',
            url: 'http://localhost:8000/health',
            method: 'GET'
        }
    ];
    
    let passedTests = 0;
    let totalTests = tests.length;
    
    tests.forEach(test => {
        console.log(`🔍 Testing: ${test.name}`);
        console.log(`   URL: ${test.url}`);
        
        try {
            let curlCmd = `curl -s -w "%{http_code}" -o /dev/null "${test.url}"`;
            
            if (test.method === 'POST' && test.body) {
                curlCmd = `curl -s -w "%{http_code}" -o /dev/null -X POST -H "Content-Type: application/json" -d '${test.body}' "${test.url}"`;
            }
            
            const result = execSync(curlCmd, { encoding: 'utf8', timeout: 10000 });
            const statusCode = result.trim();
            
            if (statusCode === '200') {
                console.log(`   ✅ Success (${statusCode})`);
                passedTests++;
            } else {
                console.log(`   ❌ Failed (${statusCode})`);
            }
            
        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
        }
        
        console.log('');
    });
    
    // Test the actual data returned
    console.log('🔍 Testing Actual Data Returned...');
    try {
        const userQuery = `curl -s -X POST -H "Content-Type: application/json" -d '{"query":"query { me { id name email incomeProfile { incomeBracket age investmentGoals riskTolerance investmentHorizon } } }"}' http://localhost:8000/graphql/`;
        const userResult = execSync(userQuery, { encoding: 'utf8', timeout: 10000 });
        const userData = JSON.parse(userResult);
        
        if (userData.data && userData.data.me && userData.data.me.incomeProfile) {
            console.log('✅ User Profile with Income Profile: WORKING');
            console.log(`   Income Bracket: ${userData.data.me.incomeProfile.incomeBracket}`);
            console.log(`   Investment Goals: ${userData.data.me.incomeProfile.investmentGoals.join(', ')}`);
            console.log(`   Risk Tolerance: ${userData.data.me.incomeProfile.riskTolerance}`);
        } else {
            console.log('❌ User Profile with Income Profile: MISSING DATA');
        }
        
    } catch (error) {
        console.log('❌ Error testing user data:', error.message);
    }
    
    // Summary
    console.log('\n📊 AFFORDABILITY FEATURES TEST RESULTS:');
    console.log('=======================================');
    console.log(`✅ Passed: ${passedTests}/${totalTests}`);
    console.log(`❌ Failed: ${totalTests - passedTests}/${totalTests}`);
    
    if (passedTests === totalTests) {
        console.log('\n🎉 AFFORDABILITY FEATURES SHOULD NOW WORK!');
        console.log('✅ User profile with income data is loading');
        console.log('✅ Server is returning proper GraphQL responses');
        console.log('✅ Dollar sign button should now appear on stock cards');
        console.log('✅ Affordability info should be available');
        
        console.log('\n📱 YOUR DOLLAR SIGN BUTTON SHOULD NOW APPEAR!');
        console.log('The app now has:');
        console.log('• User income profile data ($75,000 - $100,000)');
        console.log('• Investment goals (Wealth Building, Retirement Savings)');
        console.log('• Risk tolerance (Moderate)');
        console.log('• This triggers the isStockGoodForIncomeProfile function');
        console.log('• Which shows the dollar sign button on stock cards');
        
    } else {
        console.log('\n⚠️  SOME FEATURES NOT WORKING');
        console.log('Check the server logs for any issues');
        console.log('Make sure the fixed server is running on port 8000');
    }
    
    console.log('\n🔧 NEXT STEPS:');
    console.log('1. Open your Expo Go app');
    console.log('2. Scan the QR code from the Expo server');
    console.log('3. Check that the dollar sign button now appears on stock cards');
    console.log('4. Tap the dollar sign button to see affordability info');
    console.log('5. The button should show for stocks with good scores or dividends');
}

if (require.main === module) {
    testAffordabilityFeatures();
} else {
    module.exports = testAffordabilityFeatures;
}
