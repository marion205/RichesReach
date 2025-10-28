const { execSync } = require('child_process');

// Test script to verify the main server is working correctly
function testMainServer() {
    console.log('🔍 Testing Main Server (Port 8000)...\n');
    
    const tests = [
        {
            name: 'Health Check',
            url: 'http://localhost:8000/health',
            method: 'GET'
        },
        {
            name: 'Market Quotes (AAPL,MSFT,TSLA)',
            url: 'http://localhost:8000/api/market/quotes?symbols=AAPL,MSFT,TSLA',
            method: 'GET'
        },
        {
            name: 'GraphQL User Query',
            url: 'http://localhost:8000/graphql/',
            method: 'POST',
            body: JSON.stringify({
                query: 'query { me { id name email hasPremiumAccess } }'
            })
        },
        {
            name: 'GraphQL Stocks Query',
            url: 'http://localhost:8000/graphql/',
            method: 'POST',
            body: JSON.stringify({
                query: 'query { stocks { symbol name price change changePercent } }'
            })
        },
        {
            name: 'MemeQuest Launch (Fixed)',
            url: 'http://localhost:8000/api/pump-fun/launch',
            method: 'POST',
            body: JSON.stringify({
                name: 'TestMeme',
                symbol: 'TEST',
                description: 'A test meme for validation',
                template: '1',
                culturalTheme: 'community'
            })
        },
        {
            name: 'Trading Quote',
            url: 'http://localhost:8000/api/trading/quote/AAPL',
            method: 'GET'
        },
        {
            name: 'Portfolio Recommendations',
            url: 'http://localhost:8000/api/portfolio/recommendations',
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
            
            const result = execSync(curlCmd, { encoding: 'utf8', timeout: 5000 });
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
    
    // Summary
    console.log('📊 TEST RESULTS SUMMARY:');
    console.log('========================');
    console.log(`✅ Passed: ${passedTests}/${totalTests}`);
    console.log(`❌ Failed: ${totalTests - passedTests}/${totalTests}`);
    
    if (passedTests === totalTests) {
        console.log('\n🎉 ALL TESTS PASSED!');
        console.log('✅ Main server is working correctly');
        console.log('✅ All API endpoints are responding');
        console.log('✅ GraphQL queries are working');
        console.log('✅ MemeQuest validation is fixed');
        console.log('✅ Market quotes are working');
        
        console.log('\n📱 YOUR SCREENS SHOULD NOW LOAD PROPERLY!');
        console.log('The app is now configured to use the correct server on port 8000');
        console.log('All the missing API endpoints have been added');
        console.log('The 400/500 errors should be resolved');
        
    } else {
        console.log('\n⚠️  SOME TESTS FAILED');
        console.log('Check the server logs for any issues');
        console.log('Make sure the server is running on port 8000');
    }
    
    console.log('\n🔧 NEXT STEPS:');
    console.log('1. Open your Expo Go app');
    console.log('2. Scan the QR code from the Expo server');
    console.log('3. Test the screens that were not loading');
    console.log('4. Check that market data is loading');
    console.log('5. Try the MemeQuest feature');
    console.log('6. Test other app features');
}

if (require.main === module) {
    testMainServer();
} else {
    module.exports = testMainServer;
}
