/**
 * Demo Mode REST Interceptor
 *
 * Monkey-patches global `fetch` when demo mode is active.
 * Any request whose URL matches a known API pattern returns a static
 * JSON Response immediately — no network call is made.
 *
 * Call `installDemoFetch()` once at app startup (before any fetch calls).
 */

import {
  DEMO_MARKET_BRIEF,
  DEMO_DAILY_BRIEF,
  DEMO_BRIEF_PROGRESS,
  DEMO_FUTURES,
  DEMO_CREDIT_SNAPSHOT,
  getDemoHoldingInsight,
} from '../services/demoMockData';

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

// Pattern → handler
type Handler = (url: string, options?: RequestInit) => Response | null;

const HANDLERS: Handler[] = [
  // Auth — always succeed in demo mode
  (url) => {
    if (url.includes('/api/auth/login/')) {
      return jsonResponse({
        access_token: 'DEMO_TOKEN_NOT_A_REAL_JWT',
        user: {
          id: 'demo-user-1',
          email: 'demo@richesreach.com',
          username: 'demo',
          name: 'Alex Demo',
          hasPremiumAccess: true,
          subscriptionTier: 'premium',
        },
      });
    }
    return null;
  },

  // Health check
  (url) => {
    if (url.includes('/health')) return jsonResponse({ status: 'ok', demo: true });
    return null;
  },

  // Market brief
  (url) => {
    if (url.includes('/api/market/brief') || url.includes('/api/market/status')) {
      return jsonResponse(DEMO_MARKET_BRIEF);
    }
    return null;
  },

  // Daily brief — today
  (url) => {
    if (url.match(/\/api\/daily-brief\/(today)?$/)) {
      return jsonResponse(DEMO_DAILY_BRIEF);
    }
    return null;
  },

  // Daily brief — complete
  (url, options) => {
    if (url.includes('/api/daily-brief/complete') && options?.method === 'POST') {
      return jsonResponse({ success: true, message: 'Daily brief completed', achievements_unlocked: [], streak: 7 });
    }
    return null;
  },

  // Daily brief — progress
  (url) => {
    if (url.includes('/api/daily-brief/progress')) {
      return jsonResponse(DEMO_BRIEF_PROGRESS);
    }
    return null;
  },

  // Lessons
  (url, options) => {
    if (url.match(/\/api\/lessons\/\w+\/complete/) && options?.method === 'POST') {
      return jsonResponse({ success: true, xp_earned: 50, new_level: null });
    }
    return null;
  },

  // Holding insight
  (url) => {
    const match = url.match(/\/api\/coach\/holding-insight\?ticker=([A-Z]+)/);
    if (match) {
      const ticker = match[1];
      return jsonResponse(getDemoHoldingInsight(ticker));
    }
    return null;
  },

  // Futures
  (url) => {
    if (url.includes('/api/futures/recommendations')) {
      return jsonResponse(DEMO_FUTURES.recommendations);
    }
    if (url.includes('/api/futures/positions')) {
      return jsonResponse(DEMO_FUTURES.positions);
    }
    if (url.match(/\/api\/futures\/price\//)) {
      const sym = url.split('/').pop()?.split('?')[0] ?? 'ES';
      const price = (DEMO_FUTURES.prices as any)[sym] ?? { price: 0, change: 0, changePercent: 0 };
      return jsonResponse(price);
    }
    return null;
  },

  // Options copilot
  (url) => {
    if (url.includes('/api/options/copilot')) {
      return jsonResponse({
        recommendations: [],
        chain: [],
        pnl: { max_profit: 450, max_loss: 150, breakeven: 178.50 },
        risk: { delta: 0.42, gamma: 0.018, theta: -3.2, vega: 12.4 },
      });
    }
    return null;
  },

  // Community / wealth circles
  (url) => {
    if (url.match(/\/api\/wealth-circles\/\w+\/posts\//)) {
      return jsonResponse({
        results: [
          { id: 'p1', author: 'Alex Demo', content: 'Great week for tech! NVDA earnings looking strong.', created_at: new Date().toISOString(), likes: 12 },
          { id: 'p2', author: 'Jordan K.', content: 'Anyone watching LLY ahead of the FDA decision?', created_at: new Date().toISOString(), likes: 8 },
        ],
        count: 2,
      });
    }
    return null;
  },

  // User profile
  (url) => {
    if (url.includes('/api/user/profile/')) {
      return jsonResponse({
        id: 'demo-user-1',
        email: 'demo@richesreach.com',
        name: 'Alex Demo',
        hasPremiumAccess: true,
        subscriptionTier: 'premium',
      });
    }
    return null;
  },

  // Credit — full snapshot + individual endpoints
  (url) => {
    if (url.includes('/api/credit/snapshot')) {
      return jsonResponse(DEMO_CREDIT_SNAPSHOT);
    }
    if (url.includes('/api/credit/score/refresh')) {
      return jsonResponse(DEMO_CREDIT_SNAPSHOT.score);
    }
    if (url.includes('/api/credit/score')) {
      return jsonResponse(DEMO_CREDIT_SNAPSHOT.score);
    }
    if (url.includes('/api/credit/projection')) {
      return jsonResponse(DEMO_CREDIT_SNAPSHOT.projection);
    }
    return null;
  },

  // Market quotes — /api/market/quotes?symbols=AAPL,NVDA,...
  (url) => {
    if (!url.includes('/api/market/quotes')) return null;
    const symbolsParam = new URL(url, 'http://localhost').searchParams.get('symbols') ?? '';
    const symbols = symbolsParam.split(',').map(s => s.trim().toUpperCase()).filter(Boolean);
    const PRICES: Record<string, { price: number; change: number; change_percent: number; volume: number; high: number; low: number; open: number; previous_close: number }> = {
      AAPL:  { price: 189.30, change: 2.10, change_percent: 1.12,  volume: 52000000,  high: 190.50, low: 188.10, open: 188.50, previous_close: 187.20 },
      MSFT:  { price: 415.80, change: 5.60, change_percent: 1.37,  volume: 24000000,  high: 417.00, low: 414.00, open: 414.50, previous_close: 410.20 },
      NVDA:  { price: 875.40, change: 36.18, change_percent: 4.31, volume: 48000000,  high: 882.00, low: 860.00, open: 862.00, previous_close: 839.22 },
      TSLA:  { price: 196.50, change: 3.20, change_percent: 1.66,  volume: 88000000,  high: 198.00, low: 195.00, open: 195.80, previous_close: 193.30 },
      META:  { price: 502.30, change: 8.40, change_percent: 1.70,  volume: 19000000,  high: 505.00, low: 499.00, open: 500.00, previous_close: 493.90 },
      NFLX:  { price: 625.10, change: 11.20, change_percent: 1.82, volume: 9000000,   high: 628.00, low: 622.00, open: 623.00, previous_close: 613.90 },
      PYPL:  { price: 65.40, change: 1.20, change_percent: 1.87,   volume: 22000000,  high: 66.20, low: 64.80, open: 65.00, previous_close: 64.20 },
      UBER:  { price: 78.60, change: 2.10, change_percent: 2.74,   volume: 24000000,  high: 79.20, low: 77.80, open: 78.00, previous_close: 76.50 },
      T:     { price: 17.85, change: 0.15, change_percent: 0.85,   volume: 95000000,  high: 18.00, low: 17.70, open: 17.75, previous_close: 17.70 },
      GOOGL: { price: 175.60, change: 2.80, change_percent: 1.62,  volume: 20000000,  high: 176.50, low: 174.50, open: 174.80, previous_close: 172.80 },
      AMZN:  { price: 198.40, change: 3.60, change_percent: 1.85,  volume: 32000000,  high: 199.50, low: 197.00, open: 197.20, previous_close: 194.80 },
      AMD:   { price: 168.20, change: 4.10, change_percent: 2.50,  volume: 38000000,  high: 169.50, low: 166.80, open: 167.00, previous_close: 164.10 },
      COIN:  { price: 228.50, change: -8.30, change_percent: -3.51, volume: 14000000, high: 238.00, low: 226.00, open: 237.00, previous_close: 236.80 },
      SPY:   { price: 524.00, change: 4.20, change_percent: 0.81,  volume: 72000000,  high: 525.50, low: 522.00, open: 522.50, previous_close: 519.80 },
    };
    const quotes = symbols.map(sym => {
      const p = PRICES[sym] ?? { price: 100.00, change: 0.50, change_percent: 0.50, volume: 1000000, high: 101.00, low: 99.00, open: 100.00, previous_close: 99.50 };
      return { symbol: sym, ...p, updated: Date.now(), provider: 'demo' };
    });
    return jsonResponse(quotes);
  },

  // GraphQL — let mock Apollo client handle it (don't intercept)
  // No handler needed; graphql requests go through Apollo not fetch directly.
];

let _installed = false;
const _originalFetch = global.fetch;

export function installDemoFetch() {
  if (_installed) return;
  _installed = true;

  global.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : (input as Request).url;

    // Skip GraphQL requests — handled by Apollo mock client
    if (url.includes('/graphql')) {
      return _originalFetch(input, init);
    }

    for (const handler of HANDLERS) {
      const result = handler(url, init);
      if (result !== null) {
        console.log(`[DemoMode] Intercepted: ${init?.method ?? 'GET'} ${url}`);
        return Promise.resolve(result);
      }
    }

    // Fallback: log and return empty 200 so app doesn't crash on unknown endpoints
    console.warn(`[DemoMode] Unhandled fetch: ${url} — returning empty 200`);
    return Promise.resolve(jsonResponse({}));
  };
}

export function uninstallDemoFetch() {
  if (!_installed) return;
  global.fetch = _originalFetch;
  _installed = false;
}
