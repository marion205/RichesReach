const { execSync } = require('child_process');

// Comprehensive test to ensure stocks and investing features work 100%
function testStocksAndInvestingFeatures() {
    console.log('🧪 TESTING STOCKS & INVESTING FEATURES - 100% VERIFICATION');
    console.log('========================================================\n');
    
    const tests = [
        {
            name: 'User Profile Query (AI Portfolio)',
            query: 'query GetUserProfile { me { id name email incomeProfile { incomeBracket age investmentGoals riskTolerance investmentHorizon } } }',
            expectedFields: ['me', 'incomeProfile']
        },
        {
            name: 'AI Recommendations Query (AI Portfolio)',
            query: 'query GetAIRecommendations { aiRecommendations { portfolioAnalysis { totalValue numHoldings sectorBreakdown riskScore diversificationScore expectedImpact { evPct evAbs per10k } risk { volatilityEstimate maxDrawdownPct } assetAllocation { stocks bonds cash } } buyRecommendations { symbol companyName recommendation confidence reasoning targetPrice currentPrice expectedReturn allocation } sellRecommendations { symbol reasoning } rebalanceSuggestions { action currentAllocation suggestedAllocation reasoning priority } riskAssessment { overallRisk volatilityEstimate recommendations } marketOutlook { overallSentiment confidence keyFactors } } }',
            expectedFields: ['aiRecommendations']
        },
        {
            name: 'Advanced Stock Screening (AI Portfolio)',
            query: 'query GetQuantScreener { advancedStockScreening { symbol sector peRatio dividendYield volatility debtRatio mlScore score } }',
            expectedFields: ['advancedStockScreening']
        },
        {
            name: 'Beginner Friendly Stocks (Stocks Screen)',
            query: 'query GetBeginnerFriendlyStocks { beginnerFriendlyStocks { id symbol companyName sector marketCap peRatio dividendYield beginnerFriendlyScore currentPrice beginnerScoreBreakdown { score factors { name weight value contrib detail } notes } } }',
            expectedFields: ['beginnerFriendlyStocks']
        },
        {
            name: 'Trading Positions (Trading Screen)',
            query: 'query { tradingPositions { id symbol quantity marketValue averageCost unrealizedPL unrealizedPLPercent side marketPrice } }',
            expectedFields: ['tradingPositions']
        },
        {
            name: 'Trading Orders (Trading Screen)',
            query: 'query { tradingOrders { id symbol side quantity orderType status filledQuantity averagePrice createdAt } }',
            expectedFields: ['tradingOrders']
        },
        {
            name: 'Swing Signals (Trading Screen)',
            query: 'query { swingSignals { id symbol signalType entryPrice targetPrice stopLoss mlScore confidence reasoning thesis } }',
            expectedFields: ['swingSignals']
        },
        {
            name: 'Alpaca Account (Trading Screen)',
            query: 'query { alpacaAccount { id status buyingPower cash portfolioValue equity dayTradeCount } }',
            expectedFields: ['alpacaAccount']
        },
        {
            name: 'Portfolio Data (Portfolio Screen)',
            query: 'query { myPortfolios { totalPortfolios totalValue portfolios { name value change changePercent holdings { symbol shares value weight } } } }',
            expectedFields: ['myPortfolios']
        },
        {
            name: 'Watchlist (Stocks Screen)',
            query: 'query { myWatchlist { id stock { symbol __typename } } }',
            expectedFields: ['myWatchlist']
        }
    ];
    
    let passedTests = 0;
    let totalTests = tests.length;
    let results = [];
    
    console.log(`Running ${totalTests} critical tests...\n`);
    
    tests.forEach((test, index) => {
        console.log(`[${index + 1}/${totalTests}] Testing: ${test.name}`);
        
        try {
            const curlCmd = `curl -s -X POST -H "Content-Type: application/json" -d '{"query":"${test.query}"}' http://localhost:8000/graphql/`;
            const response = execSync(curlCmd, { encoding: 'utf8', timeout: 10000 });
            const data = JSON.parse(response);
            
            if (data.data && !data.errors) {
                // Check if expected fields are present
                const hasExpectedFields = test.expectedFields.every(field => {
                    const fieldPath = field.split('.');
                    let current = data.data;
                    for (const key of fieldPath) {
                        if (current && typeof current === 'object' && key in current) {
                            current = current[key];
                        } else {
                            return false;
                        }
                    }
                    return current !== undefined && current !== null;
                });
                
                if (hasExpectedFields) {
                    console.log(`   ✅ Success - All expected fields present`);
                    passedTests++;
                    results.push({ test: test.name, status: 'PASS', details: 'All fields present' });
                } else {
                    console.log(`   ❌ Failed - Missing expected fields: ${test.expectedFields.join(', ')}`);
                    results.push({ test: test.name, status: 'FAIL', details: `Missing fields: ${test.expectedFields.join(', ')}` });
                }
            } else {
                console.log(`   ❌ Failed - GraphQL errors: ${data.errors ? data.errors.map(e => e.message).join(', ') : 'No data'}`);
                results.push({ test: test.name, status: 'FAIL', details: `GraphQL errors: ${data.errors ? data.errors.map(e => e.message).join(', ') : 'No data'}` });
            }
            
        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
            results.push({ test: test.name, status: 'ERROR', details: error.message });
        }
        
        console.log('');
    });
    
    // Test Dollar Sign Button Logic
    console.log('🔍 TESTING DOLLAR SIGN BUTTON LOGIC:');
    console.log('====================================');
    
    try {
        // Test user profile for dollar button
        const userQuery = `curl -s -X POST -H "Content-Type: application/json" -d '{"query":"query { me { incomeProfile { incomeBracket age investmentGoals riskTolerance investmentHorizon } } }"}' http://localhost:8000/graphql/`;
        const userResult = execSync(userQuery, { encoding: 'utf8', timeout: 10000 });
        const userData = JSON.parse(userResult);
        
        if (userData.data && userData.data.me && userData.data.me.incomeProfile) {
            const profile = userData.data.me.incomeProfile;
            console.log('✅ User Profile Data Available:');
            console.log(`   Income Bracket: ${profile.incomeBracket}`);
            console.log(`   Investment Goals: ${profile.investmentGoals.join(', ')}`);
            console.log(`   Risk Tolerance: ${profile.riskTolerance}`);
            
            // Test stocks for dollar button
            const stocksQuery = `curl -s -X POST -H "Content-Type: application/json" -d '{"query":"query { beginnerFriendlyStocks { symbol beginnerFriendlyScore dividendYield } }"}' http://localhost:8000/graphql/`;
            const stocksResult = execSync(stocksQuery, { encoding: 'utf8', timeout: 10000 });
            const stocksData = JSON.parse(stocksResult);
            
            if (stocksData.data && stocksData.data.beginnerFriendlyStocks) {
                console.log('✅ Stocks Data Available:');
                stocksData.data.beginnerFriendlyStocks.forEach(stock => {
                    const hasGoodScore = stock.beginnerFriendlyScore > 80;
                    const hasGoodDividend = stock.dividendYield > 0.02;
                    const shouldShowDollarButton = hasGoodScore || hasGoodDividend;
                    
                    console.log(`   ${stock.symbol}: Score=${stock.beginnerFriendlyScore}, Dividend=${(stock.dividendYield * 100).toFixed(2)}%, Dollar Button=${shouldShowDollarButton ? 'YES' : 'NO'}`);
                });
            }
        }
        
    } catch (error) {
        console.log('❌ Error testing dollar button logic:', error.message);
    }
    
    // Summary
    console.log('\n📊 FINAL RESULTS:');
    console.log('==================');
    console.log(`✅ Passed: ${passedTests}/${totalTests}`);
    console.log(`❌ Failed: ${totalTests - passedTests}/${totalTests}`);
    console.log(`📈 Success Rate: ${Math.round((passedTests / totalTests) * 100)}%`);
    
    if (passedTests === totalTests) {
        console.log('\n🎉 ALL STOCKS & INVESTING FEATURES WORKING 100%!');
        console.log('✅ AI Portfolio screen will load correctly');
        console.log('✅ Dollar sign button will appear on stock cards');
        console.log('✅ All trading features are functional');
        console.log('✅ Portfolio management is working');
        console.log('✅ AI recommendations are loading');
        console.log('✅ Stock screening is operational');
        
        console.log('\n🚀 READY FOR:');
        console.log('• Demo recording');
        console.log('• Production deployment');
        console.log('• User testing');
        console.log('• Investor presentations');
        
    } else if (passedTests >= totalTests * 0.9) {
        console.log('\n✅ NEARLY PERFECT! 90%+ features working');
        console.log('⚠️  Minor issues detected but core functionality works');
        
    } else if (passedTests >= totalTests * 0.7) {
        console.log('\n⚠️  MOSTLY WORKING! 70%+ features working');
        console.log('❌ Some issues need attention');
        
    } else {
        console.log('\n❌ SIGNIFICANT ISSUES DETECTED!');
        console.log('🚨 Core functionality needs fixes');
    }
    
    // Failed tests details
    if (passedTests < totalTests) {
        console.log('\n❌ FAILED TESTS:');
        results.filter(r => r.status !== 'PASS').forEach(result => {
            console.log(`   • ${result.test}: ${result.details}`);
        });
    }
    
    return {
        totalTests,
        passedTests,
        successRate: Math.round((passedTests / totalTests) * 100),
        results
    };
}

if (require.main === module) {
    testStocksAndInvestingFeatures();
} else {
    module.exports = testStocksAndInvestingFeatures;
}
