/**
* Network Connection Test Script
* Tests connectivity between mobile app and backend server
*/
const testEndpoints = [
'http://localhost:8000/graphql/',
'http://127.0.0.1:8000/graphql/',
'http://192.168.1.151:8000/graphql/',
];
const testQuery = {
query: `{ __schema { types { name } } }`
};
console.log(' Testing Network Connectivity...\n');
async function testEndpoint(url) {
try {
console.log(` Testing: ${url}`);
const startTime = Date.now();
const response = await fetch(url, {
method: 'POST',
headers: {
'Content-Type': 'application/json',
},
body: JSON.stringify(testQuery),
});
const endTime = Date.now();
const responseTime = endTime - startTime;
if (response.ok) {
console.log(` SUCCESS: ${url} - ${responseTime}ms`);
return { url, success: true, time: responseTime };
} else {
console.log(` FAILED: ${url} - Status: ${response.status}`);
return { url, success: false, status: response.status };
}
} catch (error) {
console.log(` ERROR: ${url} - ${error.message}`);
return { url, success: false, error: error.message };
}
}
async function runTests() {
const results = [];
for (const endpoint of testEndpoints) {
const result = await testEndpoint(endpoint);
results.push(result);
console.log(''); // Empty line for readability
}
console.log(' Test Results Summary:');
console.log('========================');
const successful = results.filter(r => r.success);
const failed = results.filter(r => !r.success);
if (successful.length > 0) {
console.log(' Working endpoints:');
successful.forEach(r => {
console.log(` ${r.url} (${r.time}ms)`);
});
}
if (failed.length > 0) {
console.log(' Failed endpoints:');
failed.forEach(r => {
console.log(` ${r.url} - ${r.error || `Status: ${r.status}`}`);
});
}
console.log('\n Recommendations:');
if (successful.length > 0) {
const fastest = successful.reduce((prev, current) => 
(prev.time < current.time) ? prev : current
);
console.log(` Use: ${fastest.url} (fastest at ${fastest.time}ms)`);
} else {
console.log(' No working endpoints found!');
console.log(' Check if backend server is running on port 8000');
console.log(' Try: cd backend && python manage.py runserver 0.0.0.0:8000');
}
}
// Run the tests
runTests().catch(console.error);
