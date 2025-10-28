const { execSync } = require('child_process');

// Simple test to check if backend server is running and test API endpoints
function testBackendServer() {
    console.log('🔍 Testing Backend Server Status...\n');
    
    const endpoints = [
        { url: 'http://localhost:8000/health', name: 'Health Check' },
        { url: 'http://localhost:8000/graphql', name: 'GraphQL Endpoint' },
        { url: 'http://localhost:8001/api/pump-fun/launch', name: 'Pump.fun API' }
    ];
    
    endpoints.forEach(endpoint => {
        console.log(`📡 Testing: ${endpoint.name}`);
        console.log(`   URL: ${endpoint.url}`);
        
        try {
            const result = execSync(`curl -s -w "%{http_code}" -o /dev/null "${endpoint.url}"`, { 
                encoding: 'utf8',
                timeout: 5000 
            });
            
            const statusCode = result.trim();
            
            if (statusCode === '200') {
                console.log(`   ✅ Server responding (${statusCode})`);
            } else if (statusCode.startsWith('4')) {
                console.log(`   ⚠️  Client error (${statusCode}) - Server running but endpoint issue`);
            } else if (statusCode.startsWith('5')) {
                console.log(`   ❌ Server error (${statusCode}) - Backend issue`);
            } else {
                console.log(`   ❓ Unexpected response (${statusCode})`);
            }
            
        } catch (error) {
            if (error.message.includes('timeout')) {
                console.log(`   ⏰ Timeout - Server not responding`);
            } else if (error.message.includes('Connection refused')) {
                console.log(`   ❌ Connection refused - Server not running`);
            } else {
                console.log(`   ❌ Error: ${error.message}`);
            }
        }
        
        console.log('');
    });
    
    console.log('🔧 RECOMMENDATIONS:');
    console.log('==================');
    console.log('1. If servers are not running, start them:');
    console.log('   cd /Users/marioncollins/RichesReach');
    console.log('   python test_server_fresh.py');
    console.log('');
    console.log('2. If getting 400/500 errors, check:');
    console.log('   • Required fields are being sent');
    console.log('   • Data types are correct');
    console.log('   • Authentication tokens are valid');
    console.log('');
    console.log('3. Test the fixed MemeQuest API call:');
    console.log('   • Description field is now validated');
    console.log('   • Cultural theme has fallback value');
    console.log('   • Better error messages provided');
}

if (require.main === module) {
    testBackendServer();
} else {
    module.exports = testBackendServer;
}
