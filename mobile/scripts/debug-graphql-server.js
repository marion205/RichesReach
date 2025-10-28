const { execSync } = require('child_process');

// Simple test to debug GraphQL server issues
function debugGraphQLServer() {
    console.log('🔍 DEBUGGING GRAPHQL SERVER ISSUES\n');
    
    // Test 1: Health check
    console.log('1. Testing Health Check...');
    try {
        const healthResult = execSync('curl -s http://localhost:8000/health', { encoding: 'utf8' });
        console.log('   ✅ Health check works:', JSON.parse(healthResult).status);
    } catch (error) {
        console.log('   ❌ Health check failed:', error.message);
    }
    
    // Test 2: Simple GraphQL query
    console.log('\n2. Testing Simple GraphQL Query...');
    try {
        const simpleQuery = 'curl -s -X POST http://localhost:8000/graphql/ -H "Content-Type: application/json" -d \'{"query":"query { me { id name } }"}\'';
        const result = execSync(simpleQuery, { encoding: 'utf8' });
        console.log('   ✅ Simple query result:', result.substring(0, 100) + '...');
    } catch (error) {
        console.log('   ❌ Simple query failed:', error.message);
    }
    
    // Test 3: Stocks query
    console.log('\n3. Testing Stocks Query...');
    try {
        const stocksQuery = 'curl -s -X POST http://localhost:8000/graphql/ -H "Content-Type: application/json" -d \'{"query":"query { stocks { symbol name } }"}\'';
        const result = execSync(stocksQuery, { encoding: 'utf8' });
        console.log('   ✅ Stocks query result:', result.substring(0, 100) + '...');
        
        // Check if it contains stocks data
        if (result.includes('"stocks"')) {
            console.log('   ✅ Contains stocks data!');
        } else if (result.includes('"me"')) {
            console.log('   ❌ Still returning me data instead of stocks');
        } else {
            console.log('   ❓ Unexpected response format');
        }
    } catch (error) {
        console.log('   ❌ Stocks query failed:', error.message);
    }
    
    // Test 4: Check server logs
    console.log('\n4. Checking Server Process...');
    try {
        const processResult = execSync('lsof -i :8000', { encoding: 'utf8' });
        console.log('   ✅ Server process:', processResult.trim());
    } catch (error) {
        console.log('   ❌ No server process found');
    }
    
    console.log('\n🔧 DIAGNOSIS:');
    console.log('=============');
    console.log('The issue appears to be that the GraphQL server is always returning');
    console.log('the "me" query response regardless of what query is sent.');
    console.log('');
    console.log('This could be due to:');
    console.log('1. Server code logic error (if/elif statements)');
    console.log('2. Caching issues');
    console.log('3. Multiple server instances');
    console.log('4. Query parsing issues');
    console.log('');
    console.log('SOLUTION: Need to fix the server logic to properly handle different queries.');
}

if (require.main === module) {
    debugGraphQLServer();
} else {
    module.exports = debugGraphQLServer;
}
