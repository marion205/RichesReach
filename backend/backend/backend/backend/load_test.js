import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p95<200', 'p99<500'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function () {
  // Test ML Signal endpoint
  const mlQuery = JSON.stringify({
    query: `query { 
      cryptoMlSignal(symbol: "BTC") { 
        symbol 
        probability 
        confidenceLevel 
        explanation 
        features 
      } 
    }`
  });
  
  const mlRes = http.post('http://localhost:8123/graphql/', mlQuery, {
    headers: { 'Content-Type': 'application/json' }
  });
  
  check(mlRes, {
    'ML Signal 200': r => r.status === 200,
    'ML Signal has probability': r => JSON.parse(r.body).data?.cryptoMlSignal?.probability !== undefined,
    'ML Signal response time < 1s': r => r.timings.duration < 1000,
  });

  sleep(0.1);

  // Test Recommendations endpoint
  const recQuery = JSON.stringify({
    query: `query { 
      cryptoRecommendations(limit: 5) { 
        symbol 
        score 
        probability 
        confidenceLevel 
        priceUsd 
        explanation 
      } 
    }`
  });
  
  const recRes = http.post('http://localhost:8123/graphql/', recQuery, {
    headers: { 'Content-Type': 'application/json' }
  });
  
  check(recRes, {
    'Recommendations 200': r => r.status === 200,
    'Recommendations has data': r => JSON.parse(r.body).data?.cryptoRecommendations?.length > 0,
    'Recommendations response time < 2s': r => r.timings.duration < 2000,
  });

  sleep(0.1);

  // Test Health endpoint
  const healthRes = http.get('http://localhost:8123/health');
  check(healthRes, {
    'Health 200': r => r.status === 200,
    'Health response time < 100ms': r => r.timings.duration < 100,
  });

  sleep(0.1);

  // Test Metrics endpoint
  const metricsRes = http.get('http://localhost:8123/metrics');
  check(metricsRes, {
    'Metrics 200': r => r.status === 200,
    'Metrics has content': r => r.body.length > 100,
  });

  sleep(0.1);
}
