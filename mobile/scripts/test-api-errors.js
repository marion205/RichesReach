const { execSync } = require('child_process');

// Test script to identify API errors
async function testAPIEndpoints() {
    console.log('🔍 Testing API Endpoints for 400/500 Errors...\n');
    
    const baseUrl = 'http://localhost:8002';
    const endpoints = [
        '/graphql/',
        '/api/auth/login/',
        '/api/pump-fun/launch',
        '/api/trading/quote',
        '/api/portfolio/recommendations',
        '/api/kyc/workflow',
        '/api/alpaca/account'
    ];
    
    for (const endpoint of endpoints) {
        console.log(`📡 Testing: ${baseUrl}${endpoint}`);
        
        try {
            const response = await fetch(`${baseUrl}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            console.log(`   Status: ${response.status} ${response.statusText}`);
            
            if (response.status >= 400) {
                const text = await response.text();
                console.log(`   Error: ${text.substring(0, 200)}...`);
            }
            
        } catch (error) {
            console.log(`   Error: ${error.message}`);
        }
        
        console.log('');
    }
}

// Test GraphQL mutations with missing fields
async function testGraphQLMutations() {
    console.log('🧪 Testing GraphQL Mutations...\n');
    
    const baseUrl = 'http://localhost:8002/graphql/';
    
    const mutations = [
        {
            name: 'CreatePosition (missing required fields)',
            query: `
                mutation {
                    createPosition(symbol: "AAPL") {
                        success
                        message
                    }
                }
            `
        },
        {
            name: 'CreateIncomeProfile (missing required fields)',
            query: `
                mutation {
                    createIncomeProfile(incomeBracket: "test") {
                        success
                        message
                    }
                }
            `
        },
        {
            name: 'PlaceStockOrder (missing required fields)',
            query: `
                mutation {
                    placeStockOrder(symbol: "AAPL") {
                        success
                        message
                    }
                }
            `
        }
    ];
    
    for (const mutation of mutations) {
        console.log(`📡 Testing: ${mutation.name}`);
        
        try {
            const response = await fetch(baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: mutation.query
                })
            });
            
            const result = await response.json();
            console.log(`   Status: ${response.status}`);
            
            if (result.errors) {
                console.log(`   GraphQL Errors:`);
                result.errors.forEach((error, index) => {
                    console.log(`     ${index + 1}. ${error.message}`);
                });
            } else {
                console.log(`   Success: ${JSON.stringify(result.data)}`);
            }
            
        } catch (error) {
            console.log(`   Error: ${error.message}`);
        }
        
        console.log('');
    }
}

// Test REST API endpoints with missing fields
async function testRESTEndpoints() {
    console.log('🌐 Testing REST API Endpoints...\n');
    
    const baseUrl = 'http://localhost:8002';
    
    const testCases = [
        {
            name: 'Pump.fun Launch (missing fields)',
            url: `${baseUrl}/api/pump-fun/launch`,
            method: 'POST',
            body: {
                name: 'TestMeme'
                // Missing: symbol, description, template, culturalTheme
            }
        },
        {
            name: 'Alpaca Account Creation (missing fields)',
            url: `${baseUrl}/api/alpaca/account`,
            method: 'POST',
            body: {
                firstName: 'John'
                // Missing: lastName, email, dateOfBirth, etc.
            }
        }
    ];
    
    for (const testCase of testCases) {
        console.log(`📡 Testing: ${testCase.name}`);
        
        try {
            const response = await fetch(testCase.url, {
                method: testCase.method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(testCase.body)
            });
            
            const text = await response.text();
            console.log(`   Status: ${response.status} ${response.statusText}`);
            
            if (response.status >= 400) {
                console.log(`   Error Response: ${text.substring(0, 300)}...`);
            }
            
        } catch (error) {
            console.log(`   Error: ${error.message}`);
        }
        
        console.log('');
    }
}

async function runAllTests() {
    console.log('🚀 Starting API Error Detection Tests...\n');
    
    await testAPIEndpoints();
    await testGraphQLMutations();
    await testRESTEndpoints();
    
    console.log('✅ All tests completed!');
}

if (require.main === module) {
    runAllTests();
} else {
    module.exports = { testAPIEndpoints, testGraphQLMutations, testRESTEndpoints };
}
