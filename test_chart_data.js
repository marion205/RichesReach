/**
 * Test script to verify chart data retrieval and transformation
 * Run with: node test_chart_data.js
 */

// Simulate the toMs and toNum functions from StockScreen.tsx
const toMs = (t) => {
  if (t == null) {
    console.warn('[toMs] ⚠️ Null/undefined timestamp');
    return NaN;
  }
  
  if (typeof t === 'number') {
    return t > 1e12 ? t : t * 1000;
  }
  
  if (t instanceof Date) {
    return t.getTime();
  }
  
  if (typeof t === 'string') {
    const numVal = Number(t);
    if (!isNaN(numVal) && t.trim() === String(numVal)) {
      return numVal > 1e12 ? numVal : numVal * 1000;
    }
    const date = new Date(t);
    const ms = date.getTime();
    if (isNaN(ms)) {
      console.warn('[toMs] ⚠️ Failed to parse timestamp:', t);
      return NaN;
    }
    return ms;
  }
  
  console.warn('[toMs] ⚠️ Unexpected timestamp type:', typeof t, t);
  return NaN;
};

const toNum = (v) => {
  if (v == null || v === '') return null;
  const num = Number(v);
  return isNaN(num) ? null : num;
};

// Test data transformation
function testChartDataTransformation(data) {
  console.log('\n=== Testing Chart Data Transformation ===\n');
  
  if (!data || !data.stockChartData) {
    console.error('❌ No stockChartData in response');
    return false;
  }
  
  const chartData = data.stockChartData;
  console.log('✅ Chart data structure found');
  console.log(`   Symbol: ${chartData.symbol}`);
  console.log(`   Interval: ${chartData.interval}`);
  console.log(`   Data points: ${chartData.data?.length || 0}`);
  console.log(`   Source: ${chartData.source || 'unknown'}`);
  console.log(`   Error: ${chartData.error || 'none'}`);
  
  if (!chartData.data || chartData.data.length === 0) {
    console.error('❌ No data points in chartData.data');
    return false;
  }
  
  console.log('\n--- Testing Data Transformation ---');
  const rows = chartData.data;
  const firstRow = rows[0];
  const lastRow = rows[rows.length - 1];
  
  console.log(`\nFirst row:`, firstRow);
  console.log(`Last row:`, lastRow);
  
  // Test transformation
  const mapped = rows.map((r, idx) => {
    const timestamp = toMs(r.timestamp);
    const close = toNum(r.close);
    
    if (idx === 0 || idx === rows.length - 1) {
      console.log(`\nRow ${idx}:`);
      console.log(`  timestamp: "${r.timestamp}" → ${timestamp} (${new Date(timestamp).toISOString()})`);
      console.log(`  close: ${r.close} → ${close}`);
    }
    
    return {
      t: timestamp,
      o: toNum(r.open),
      h: toNum(r.high),
      l: toNum(r.low),
      c: close,
      v: toNum(r.volume),
    };
  });
  
  console.log(`\n✅ Mapped ${mapped.length} points`);
  
  // Filter valid points
  const filtered = mapped.filter(p => {
    const isValid = Number.isFinite(p.t) && Number.isFinite(p.c);
    if (!isValid) {
      console.warn(`⚠️ Invalid point: t=${p.t}, c=${p.c}`);
    }
    return isValid;
  });
  
  console.log(`✅ Filtered to ${filtered.length} valid points`);
  
  if (filtered.length === 0) {
    console.error('❌ All points were filtered out!');
    console.log('\nSample invalid points:');
    mapped.slice(0, 3).forEach((p, i) => {
      console.log(`  Point ${i}: t=${p.t}, c=${p.c}, isValid=${Number.isFinite(p.t) && Number.isFinite(p.c)}`);
    });
    return false;
  }
  
  // Validate timestamp range
  const firstTs = filtered[0].t;
  const lastTs = filtered[filtered.length - 1].t;
  const year2000 = 946684800000;
  const year2100 = 4102444800000;
  
  console.log(`\n--- Timestamp Validation ---`);
  console.log(`First timestamp: ${firstTs} (${new Date(firstTs).toISOString()})`);
  console.log(`Last timestamp: ${lastTs} (${new Date(lastTs).toISOString()})`);
  
  if (firstTs < year2000 || firstTs > year2100 || lastTs < year2000 || lastTs > year2100) {
    console.error('❌ Timestamp out of valid range (2000-2100)');
    return false;
  }
  
  console.log('✅ Timestamps are in valid range');
  console.log(`\n✅ SUCCESS: Chart data is valid and ready to render!`);
  console.log(`   Total points: ${filtered.length}`);
  console.log(`   Date range: ${new Date(firstTs).toISOString()} → ${new Date(lastTs).toISOString()}`);
  
  return true;
}

// Test with mock data
function testWithMockData() {
  console.log('\n=== Testing with Mock Data ===\n');
  
  const mockData = {
    stockChartData: {
      symbol: "AAPL",
      interval: "1D",
      limit: 180,
      currentPrice: 150.0,
      change: 2.5,
      changePercent: 1.69,
      data: [
        {
          timestamp: "2026-01-27T16:36:02.859605",
          open: 149.0,
          high: 151.0,
          low: 148.5,
          close: 150.0,
          volume: 1000000
        },
        {
          timestamp: "2026-01-27T16:41:02.859605",
          open: 150.0,
          high: 150.5,
          low: 149.5,
          close: 150.2,
          volume: 950000
        }
      ],
      indicators: {},
      error: null,
      source: "mock"
    }
  };
  
  return testChartDataTransformation(mockData);
}

// Main test function
async function runTests() {
  console.log('🧪 Chart Data Transformation Test\n');
  console.log('='.repeat(50));
  
  // Test 1: Mock data
  const mockTest = testWithMockData();
  
  // Test 2: Real backend data (if available)
  console.log('\n' + '='.repeat(50));
  console.log('\n=== Testing with Real Backend Data ===\n');
  
  try {
    const response = await fetch('http://127.0.0.1:8000/graphql/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dev-token-1769202953'
      },
      body: JSON.stringify({
        operationName: "Chart",
        variables: {
          symbol: "AAPL",
          tf: "1D",
          iv: "1D",
          limit: 10, // Small limit for testing
          inds: []
        },
        query: `query Chart($symbol: String!, $tf: String!, $iv: String, $limit: Int, $inds: [String!]) {
          stockChartData(symbol: $symbol, timeframe: $tf, interval: $iv, limit: $limit, indicators: $inds) {
            symbol
            interval
            limit
            currentPrice
            change
            changePercent
            data {
              timestamp
              open
              high
              low
              close
              volume
            }
            indicators {
              SMA20
              SMA50
            }
            error
            source
          }
        }`
      })
    });
    
    const result = await response.json();
    
    if (result.errors) {
      console.error('❌ GraphQL errors:', result.errors);
      return;
    }
    
    if (result.data) {
      const realTest = testChartDataTransformation(result.data);
      console.log('\n' + '='.repeat(50));
      console.log('\n📊 Test Summary:');
      console.log(`   Mock data: ${mockTest ? '✅ PASS' : '❌ FAIL'}`);
      console.log(`   Real data: ${realTest ? '✅ PASS' : '❌ FAIL'}`);
    } else {
      console.error('❌ No data in response');
    }
  } catch (error) {
    console.error('❌ Error fetching from backend:', error.message);
    console.log('\n💡 Make sure the backend is running on port 8000');
  }
}

// Run tests
if (typeof fetch !== 'undefined') {
  runTests();
} else {
  console.log('⚠️ fetch is not available. Running mock test only...');
  testWithMockData();
}

