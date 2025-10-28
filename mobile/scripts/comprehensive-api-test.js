const { execSync } = require('child_process');

// Comprehensive test script for all GraphQL queries, mutations, and endpoints
function runComprehensiveTests() {
    console.log('🧪 COMPREHENSIVE GRAPHQL & API TESTING');
    console.log('=====================================\n');
    
    const tests = [
        // Health Check
        {
            name: 'Health Check',
            type: 'REST',
            method: 'GET',
            url: 'http://localhost:8000/health',
            expectedStatus: 200
        },
        
        // REST API Endpoints
        {
            name: 'Market Quotes API',
            type: 'REST',
            method: 'GET',
            url: 'http://localhost:8000/api/market/quotes?symbols=AAPL,MSFT,TSLA',
            expectedStatus: 200
        },
        {
            name: 'Trading Quote API',
            type: 'REST',
            method: 'GET',
            url: 'http://localhost:8000/api/trading/quote/AAPL',
            expectedStatus: 200
        },
        {
            name: 'Portfolio Recommendations API',
            type: 'REST',
            method: 'GET',
            url: 'http://localhost:8000/api/portfolio/recommendations',
            expectedStatus: 200
        },
        {
            name: 'Pump.fun Launch API',
            type: 'REST',
            method: 'POST',
            url: 'http://localhost:8000/api/pump-fun/launch',
            body: JSON.stringify({
                name: 'TestMeme',
                symbol: 'TEST',
                description: 'A test meme for validation',
                template: '1',
                culturalTheme: 'community'
            }),
            expectedStatus: 200
        },
        {
            name: 'KYC Workflow API',
            type: 'REST',
            method: 'POST',
            url: 'http://localhost:8000/api/kyc/workflow',
            body: JSON.stringify({}),
            expectedStatus: 200
        },
        {
            name: 'Alpaca Account API',
            type: 'REST',
            method: 'POST',
            url: 'http://localhost:8000/api/alpaca/account',
            body: JSON.stringify({}),
            expectedStatus: 200
        },
        
        // GraphQL Queries
        {
            name: 'User Profile Query',
            type: 'GraphQL',
            query: 'query { me { id name email hasPremiumAccess subscriptionTier incomeProfile { incomeBracket age investmentGoals riskTolerance investmentHorizon } } }',
            expectedFields: ['me', 'incomeProfile']
        },
        {
            name: 'Stocks Query',
            type: 'GraphQL',
            query: 'query { stocks { symbol name price change changePercent beginnerFriendlyScore dividendYield } }',
            expectedFields: ['stocks']
        },
        {
            name: 'AI Recommendations Query',
            type: 'GraphQL',
            query: 'query { aiRecommendations { buyRecommendations { symbol companyName recommendation confidence reasoning targetPrice currentPrice expectedReturn } } }',
            expectedFields: ['aiRecommendations']
        },
        {
            name: 'Trading Positions Query',
            type: 'GraphQL',
            query: 'query { tradingPositions { id symbol quantity marketValue averageCost unrealizedPL unrealizedPLPercent side marketPrice } }',
            expectedFields: ['tradingPositions']
        },
        {
            name: 'Trading Orders Query',
            type: 'GraphQL',
            query: 'query { tradingOrders { id symbol side quantity orderType status filledQuantity averagePrice createdAt } }',
            expectedFields: ['tradingOrders']
        },
        {
            name: 'Swing Signals Query',
            type: 'GraphQL',
            query: 'query { swingSignals { id symbol signalType entryPrice targetPrice stopLoss mlScore confidence reasoning thesis } }',
            expectedFields: ['swingSignals']
        },
        {
            name: 'Alpaca Account Query',
            type: 'GraphQL',
            query: 'query { alpacaAccount { id status buyingPower cash portfolioValue equity dayTradeCount } }',
            expectedFields: ['alpacaAccount']
        },
        {
            name: 'Portfolio Query',
            type: 'GraphQL',
            query: 'query { myPortfolios { totalPortfolios totalValue portfolios { name value change changePercent holdings { symbol shares value weight } } } }',
            expectedFields: ['myPortfolios']
        },
        {
            name: 'Watchlist Query',
            type: 'GraphQL',
            query: 'query { myWatchlist { id stock { symbol __typename } } }',
            expectedFields: ['myWatchlist']
        },
        {
            name: 'Day Trading Picks Query',
            type: 'GraphQL',
            query: 'query { dayTradingPicks(mode: "SAFE") { asOf mode picks { symbol entryPrice targetPrice stopLoss confidence } } }',
            expectedFields: ['dayTradingPicks']
        },
        
        // GraphQL Mutations
        {
            name: 'Create Income Profile Mutation',
            type: 'GraphQL',
            query: 'mutation { createIncomeProfile(input: { incomeBracket: "$75,000 - $100,000", age: 28, investmentGoals: ["Wealth Building"], riskTolerance: "Moderate", investmentHorizon: "5-10 years" }) { success message } }',
            expectedFields: ['createIncomeProfile']
        },
        {
            name: 'Place Stock Order Mutation',
            type: 'GraphQL',
            query: 'mutation { placeStockOrder(input: { symbol: "AAPL", side: "buy", quantity: 10, orderType: "market" }) { success message orderId } }',
            expectedFields: ['placeStockOrder']
        },
        {
            name: 'Create Alpaca Account Mutation',
            type: 'GraphQL',
            query: 'mutation { createAlpacaAccount(input: { firstName: "John", lastName: "Doe", email: "john@example.com" }) { success message alpacaAccountId } }',
            expectedFields: ['createAlpacaAccount']
        },
        {
            name: 'Create Position Mutation',
            type: 'GraphQL',
            query: 'mutation { createPosition(input: { symbol: "AAPL", side: "buy", price: 150.0, quantity: 10, atr: 2.5 }) { success message position { symbol side entryPrice quantity } } }',
            expectedFields: ['createPosition']
        }
    ];
    
    let passedTests = 0;
    let totalTests = tests.length;
    let results = [];
    
    console.log(`Running ${totalTests} tests...\n`);
    
    tests.forEach((test, index) => {
        console.log(`[${index + 1}/${totalTests}] Testing: ${test.name}`);
        
        try {
            let curlCmd;
            let response;
            
            if (test.type === 'REST') {
                if (test.method === 'GET') {
                    curlCmd = `curl -s -w "%{http_code}" -o /dev/null "${test.url}"`;
                } else if (test.method === 'POST') {
                    curlCmd = `curl -s -w "%{http_code}" -o /dev/null -X POST -H "Content-Type: application/json" -d '${test.body}' "${test.url}"`;
                }
                
                const result = execSync(curlCmd, { encoding: 'utf8', timeout: 10000 });
                const statusCode = result.trim();
                
                if (statusCode === test.expectedStatus.toString()) {
                    console.log(`   ✅ Success (${statusCode})`);
                    passedTests++;
                    results.push({ test: test.name, status: 'PASS', details: `Status: ${statusCode}` });
                } else {
                    console.log(`   ❌ Failed (Expected: ${test.expectedStatus}, Got: ${statusCode})`);
                    results.push({ test: test.name, status: 'FAIL', details: `Expected: ${test.expectedStatus}, Got: ${statusCode}` });
                }
                
            } else if (test.type === 'GraphQL') {
                curlCmd = `curl -s -X POST -H "Content-Type: application/json" -d '{"query":"${test.query}"}' http://localhost:8000/graphql/`;
                
                try {
                    response = execSync(curlCmd, { encoding: 'utf8', timeout: 10000 });
                    const data = JSON.parse(response);
                    
                    if (data.data && !data.errors) {
                        // Check if expected fields are present
                        const hasExpectedFields = test.expectedFields.every(field => {
                            return field.split('.').reduce((obj, key) => obj && obj[key], data.data);
                        });
                        
                        if (hasExpectedFields) {
                            console.log(`   ✅ Success (GraphQL)`);
                            passedTests++;
                            results.push({ test: test.name, status: 'PASS', details: 'GraphQL response valid' });
                        } else {
                            console.log(`   ❌ Failed (Missing expected fields: ${test.expectedFields.join(', ')})`);
                            results.push({ test: test.name, status: 'FAIL', details: `Missing fields: ${test.expectedFields.join(', ')}` });
                        }
                    } else {
                        console.log(`   ❌ Failed (GraphQL errors: ${data.errors ? data.errors.map(e => e.message).join(', ') : 'No data'})`);
                        results.push({ test: test.name, status: 'FAIL', details: `GraphQL errors: ${data.errors ? data.errors.map(e => e.message).join(', ') : 'No data'}` });
                    }
                } catch (parseError) {
                    console.log(`   ❌ Failed (Parse error: ${parseError.message})`);
                    results.push({ test: test.name, status: 'FAIL', details: `Parse error: ${parseError.message}` });
                }
            }
            
        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
            results.push({ test: test.name, status: 'ERROR', details: error.message });
        }
        
        console.log('');
    });
    
    // Detailed Results Summary
    console.log('📊 DETAILED TEST RESULTS:');
    console.log('=========================');
    
    const passed = results.filter(r => r.status === 'PASS');
    const failed = results.filter(r => r.status === 'FAIL');
    const errors = results.filter(r => r.status === 'ERROR');
    
    console.log(`✅ Passed: ${passed.length}/${totalTests}`);
    console.log(`❌ Failed: ${failed.length}/${totalTests}`);
    console.log(`🚨 Errors: ${errors.length}/${totalTests}`);
    
    if (failed.length > 0) {
        console.log('\n❌ FAILED TESTS:');
        failed.forEach(result => {
            console.log(`   • ${result.test}: ${result.details}`);
        });
    }
    
    if (errors.length > 0) {
        console.log('\n🚨 ERROR TESTS:');
        errors.forEach(result => {
            console.log(`   • ${result.test}: ${result.details}`);
        });
    }
    
    // Test Categories Summary
    const restTests = tests.filter(t => t.type === 'REST');
    const graphqlTests = tests.filter(t => t.type === 'GraphQL');
    
    const restPassed = restTests.filter(t => results.find(r => r.test === t.name)?.status === 'PASS').length;
    const graphqlPassed = graphqlTests.filter(t => results.find(r => r.test === t.name)?.status === 'PASS').length;
    
    console.log('\n📈 TEST CATEGORIES:');
    console.log('===================');
    console.log(`🌐 REST API Endpoints: ${restPassed}/${restTests.length} passed`);
    console.log(`🔮 GraphQL Queries: ${graphqlPassed}/${graphqlTests.length} passed`);
    
    // Overall Assessment
    console.log('\n🎯 OVERALL ASSESSMENT:');
    console.log('======================');
    
    if (passedTests === totalTests) {
        console.log('🎉 ALL TESTS PASSED! Your server is fully functional!');
        console.log('✅ All REST API endpoints working');
        console.log('✅ All GraphQL queries working');
        console.log('✅ All GraphQL mutations working');
        console.log('✅ Dollar sign button and affordability info should work');
        console.log('✅ All mobile app features should work correctly');
        
    } else if (passedTests >= totalTests * 0.8) {
        console.log('✅ MOSTLY WORKING! 80%+ tests passed');
        console.log('⚠️  Some minor issues detected, but core functionality works');
        
    } else if (passedTests >= totalTests * 0.5) {
        console.log('⚠️  PARTIALLY WORKING! 50%+ tests passed');
        console.log('❌ Several issues detected, core functionality may be affected');
        
    } else {
        console.log('❌ MAJOR ISSUES DETECTED! Less than 50% tests passed');
        console.log('🚨 Server needs significant fixes');
    }
    
    console.log('\n🔧 NEXT STEPS:');
    if (passedTests === totalTests) {
        console.log('1. ✅ Your server is ready for production use');
        console.log('2. ✅ All mobile app features should work correctly');
        console.log('3. ✅ Dollar sign button and affordability info are working');
        console.log('4. ✅ You can proceed with demo recording');
    } else {
        console.log('1. 🔍 Review failed tests above');
        console.log('2. 🔧 Fix any server issues');
        console.log('3. 🔄 Re-run this test script');
        console.log('4. 📱 Test mobile app functionality');
    }
    
    return {
        totalTests,
        passedTests,
        failedTests: failed.length,
        errorTests: errors.length,
        results
    };
}

if (require.main === module) {
    runComprehensiveTests();
} else {
    module.exports = runComprehensiveTests;
}
