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
