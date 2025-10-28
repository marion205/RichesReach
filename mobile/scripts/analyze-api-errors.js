const fs = require('fs');
const path = require('path');

// Test script to identify 400/500 missing fields errors in the mobile app
function analyzeAPIErrors() {
    console.log('🔍 Analyzing Mobile App for 400/500 Missing Fields Errors...\n');
    
    const issues = [];
    
    // Check GraphQL mutations for missing required fields
    console.log('📡 Checking GraphQL Mutations...');
    
    const mutationsToCheck = [
        {
            file: 'mobile/src/features/portfolio/screens/AIPortfolioScreen.tsx',
            mutation: 'createIncomeProfile',
            requiredFields: ['incomeBracket', 'age', 'investmentGoals', 'riskTolerance', 'investmentHorizon'],
            line: 1210
        },
        {
            file: 'mobile/src/features/stocks/screens/TradingScreen.tsx',
            mutation: 'placeStockOrder',
            requiredFields: ['symbol', 'side', 'quantity', 'orderType'],
            line: 108
        },
        {
            file: 'mobile/src/features/stocks/screens/TradingScreen.tsx',
            mutation: 'createAlpacaAccount',
            requiredFields: ['firstName', 'lastName', 'email', 'dateOfBirth', 'streetAddress', 'city', 'state', 'postalCode'],
            line: 118
        },
        {
            file: 'mobile/src/graphql/riskManagement.ts',
            mutation: 'createPosition',
            requiredFields: ['symbol', 'side', 'price', 'atr'],
            line: 45
        }
    ];
    
    mutationsToCheck.forEach(mutation => {
        console.log(`\n🔍 Checking ${mutation.mutation} in ${mutation.file}`);
        
        try {
            const filePath = path.join('/Users/marioncollins/RichesReach', mutation.file);
            const content = fs.readFileSync(filePath, 'utf8');
            
            // Look for the mutation usage
            const mutationUsage = content.match(new RegExp(`${mutation.mutation}[\\s\\S]*?variables:\\s*{([\\s\\S]*?)}`, 'g'));
            
            if (mutationUsage) {
                console.log(`   ✅ Found ${mutation.mutation} usage`);
                
                // Check if all required fields are being passed
                const usageText = mutationUsage[0];
                const missingFields = mutation.requiredFields.filter(field => 
                    !usageText.includes(field)
                );
                
                if (missingFields.length > 0) {
                    console.log(`   ❌ Missing required fields: ${missingFields.join(', ')}`);
                    issues.push({
                        type: 'Missing Required Fields',
                        mutation: mutation.mutation,
                        file: mutation.file,
                        missingFields: missingFields,
                        line: mutation.line
                    });
                } else {
                    console.log(`   ✅ All required fields present`);
                }
            } else {
                console.log(`   ⚠️  ${mutation.mutation} usage not found in file`);
            }
            
        } catch (error) {
            console.log(`   ❌ Error reading file: ${error.message}`);
        }
    });
    
    // Check REST API calls for missing fields
    console.log('\n🌐 Checking REST API Calls...');
    
    const restAPIsToCheck = [
        {
            file: 'mobile/src/features/social/screens/MemeQuestScreen.tsx',
            endpoint: '/api/pump-fun/launch',
            requiredFields: ['name', 'symbol', 'description', 'template', 'culturalTheme'],
            line: 339
        }
    ];
    
    restAPIsToCheck.forEach(api => {
        console.log(`\n🔍 Checking ${api.endpoint} in ${api.file}`);
        
        try {
            const filePath = path.join('/Users/marioncollins/RichesReach', api.file);
            const content = fs.readFileSync(filePath, 'utf8');
            
            // Look for the API call
            const apiCall = content.match(new RegExp(`fetch\\([\\s\\S]*?${api.endpoint}[\\s\\S]*?body:\\s*JSON\\.stringify\\(([\\s\\S]*?)\\)`, 'g'));
            
            if (apiCall) {
                console.log(`   ✅ Found ${api.endpoint} call`);
                
                // Check if all required fields are being passed
                const callText = apiCall[0];
                const missingFields = api.requiredFields.filter(field => 
                    !callText.includes(field)
                );
                
                if (missingFields.length > 0) {
                    console.log(`   ❌ Missing required fields: ${missingFields.join(', ')}`);
                    issues.push({
                        type: 'Missing Required Fields',
                        endpoint: api.endpoint,
                        file: api.file,
                        missingFields: missingFields,
                        line: api.line
                    });
                } else {
                    console.log(`   ✅ All required fields present`);
                }
            } else {
                console.log(`   ⚠️  ${api.endpoint} call not found in file`);
            }
            
        } catch (error) {
            console.log(`   ❌ Error reading file: ${error.message}`);
        }
    });
    
    // Check for common validation issues
    console.log('\n🔧 Checking Common Validation Issues...');
    
    const validationIssues = [
        {
            file: 'mobile/src/features/auth/screens/SignUpScreen.tsx',
            issue: 'Email validation',
            description: 'Check if email format validation is proper'
        },
        {
            file: 'mobile/src/features/auth/screens/SignUpScreen.tsx',
            issue: 'Password validation',
            description: 'Check if password meets requirements'
        },
        {
            file: 'mobile/src/features/portfolio/screens/AIPortfolioScreen.tsx',
            issue: 'Age validation',
            description: 'Check if age is a valid number'
        },
        {
            file: 'mobile/src/features/stocks/screens/TradingScreen.tsx',
            issue: 'Order quantity validation',
            description: 'Check if quantity is a positive integer'
        }
    ];
    
    validationIssues.forEach(validation => {
        console.log(`\n🔍 Checking ${validation.issue} in ${validation.file}`);
        console.log(`   📝 ${validation.description}`);
        
        try {
            const filePath = path.join('/Users/marioncollins/RichesReach', validation.file);
            const content = fs.readFileSync(filePath, 'utf8');
            
            // Look for validation patterns
            const hasValidation = content.includes('validation') || 
                                 content.includes('validate') || 
                                 content.includes('Alert.alert') ||
                                 content.includes('if (!') ||
                                 content.includes('if (');
            
            if (hasValidation) {
                console.log(`   ✅ Found validation logic`);
            } else {
                console.log(`   ⚠️  Limited validation found`);
                issues.push({
                    type: 'Validation Issue',
                    file: validation.file,
                    issue: validation.issue,
                    description: validation.description
                });
            }
            
        } catch (error) {
            console.log(`   ❌ Error reading file: ${error.message}`);
        }
    });
    
    // Summary
    console.log('\n📊 SUMMARY OF ISSUES FOUND:');
    console.log('================================');
    
    if (issues.length === 0) {
        console.log('✅ No obvious missing field issues found in the code analysis.');
        console.log('💡 The 400/500 errors might be coming from:');
        console.log('   • Backend server not running');
        console.log('   • Network connectivity issues');
        console.log('   • Database connection problems');
        console.log('   • Authentication token issues');
        console.log('   • Environment variable problems');
    } else {
        issues.forEach((issue, index) => {
            console.log(`\n${index + 1}. ${issue.type}`);
            console.log(`   File: ${issue.file}`);
            if (issue.missingFields) {
                console.log(`   Missing Fields: ${issue.missingFields.join(', ')}`);
            }
            if (issue.endpoint) {
                console.log(`   Endpoint: ${issue.endpoint}`);
            }
            if (issue.description) {
                console.log(`   Description: ${issue.description}`);
            }
        });
    }
    
    console.log('\n🔧 RECOMMENDED FIXES:');
    console.log('=====================');
    
    if (issues.length > 0) {
        issues.forEach((issue, index) => {
            console.log(`\n${index + 1}. Fix ${issue.type}:`);
            if (issue.missingFields) {
                console.log(`   • Add missing fields: ${issue.missingFields.join(', ')}`);
            }
            if (issue.file) {
                console.log(`   • Check file: ${issue.file}`);
            }
        });
    } else {
        console.log('1. Start the backend server:');
        console.log('   cd /Users/marioncollins/RichesReach/backend');
        console.log('   python server/main.py');
        console.log('');
        console.log('2. Check network connectivity:');
        console.log('   curl http://localhost:8000/health');
        console.log('');
        console.log('3. Check environment variables:');
        console.log('   Verify EXPO_PUBLIC_API_BASE_URL is set correctly');
        console.log('');
        console.log('4. Check authentication:');
        console.log('   Verify user tokens are valid and not expired');
    }
}

if (require.main === module) {
    analyzeAPIErrors();
} else {
    module.exports = analyzeAPIErrors;
}
