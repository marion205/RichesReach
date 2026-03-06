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

  // Voice / TTS preview — return valid shape so VoiceAI doesn't throw "Failed to generate preview"
  (url, options) => {
    if ((url.includes('/api/preview') || url.includes('/api/preview/')) && options?.method === 'POST') {
      return jsonResponse({
        success: true,
        audio_url: 'data:audio/mpeg;base64,//uQx',
        format: 'mp3',
      });
    }
    return null;
  },

  // Whisper / transcribe — demo transcription so voice flows don't break
  (url, options) => {
    if (url.includes('/api/transcribe-audio/') && options?.method === 'POST') {
      return jsonResponse({
        success: true,
        transcript: 'Demo transcription.',
        response: { transcription: 'Demo transcription.', whisper_used: false },
      });
    }
    return null;
  },

  // Connectivity check (e.g. Google generate_204) — return 204 No Content, no body
  (url) => {
    if (url.includes('generate_204')) {
      return new Response(null, { status: 204 });
    }
    return null;
  },

  // Tutor module (Learn → Generate) — demo content so "Generate" shows something in demo mode
  (url, options) => {
    if (url.includes('/tutor/module') && options?.method === 'POST') {
      return jsonResponse({
        title: 'Risk Management',
        difficulty: 'beginner',
        estimated_time: 10,
        description: 'Learn how to identify, measure, and manage risk in your portfolio. This module covers position sizing, stop losses, and diversification.',
        sections: [
          {
            title: 'What is risk?',
            content: 'Risk is the chance that your investment may lose value. In trading, we manage risk by limiting how much we could lose on any single trade and across our portfolio.',
            key_points: ['Risk can be measured (e.g. volatility, drawdown).', 'Diversification reduces unsystematic risk.', 'Position sizing limits loss per trade.'],
            examples: ['Example: Never risk more than 1–2% of your account on one trade.'],
          },
          {
            title: 'Position sizing',
            content: 'Position sizing means choosing how many shares or contracts to trade so that if the trade hits your stop loss, you only lose a set amount (e.g. 1% of account).',
            key_points: ['Size = (Account × Risk%) ÷ (Entry − Stop).', 'Smaller size = smaller loss if stopped out.', 'Adjust size when volatility changes.'],
          },
          {
            title: 'Putting it together',
            content: 'Combine stop losses with position sizing and diversification. Review your risk regularly and adjust as your account or goals change.',
            key_points: ['Use stops on every trade.', 'Diversify across sectors and timeframes.', 'Revisit risk rules when markets change.'],
          },
        ],
        quiz: {
          questions: [
            { id: 'q1', question: 'What is a key benefit of position sizing?', question_type: 'multiple_choice', options: ['Larger profits', 'Limited loss per trade', 'Faster execution'], correct_answer: 'Limited loss per trade' },
            { id: 'q2', question: 'True or false: Diversification can reduce unsystematic risk.', question_type: 'true_false', options: ['True', 'False'], correct_answer: 'True' },
          ],
        },
      });
    }
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

  // Options copilot + AI options REST endpoints
  (url, options) => {
    if (!url.includes('/api/options') && !url.includes('/api/ai-options')) return null;

    // AI Options — recommendations (POST /api/ai-options/recommendations)
    if (url.includes('/api/ai-options/recommendations')) {
      return jsonResponse({
        symbol: 'AAPL',
        current_price: 189.30,
        generated_at: new Date().toISOString(),
        total_recommendations: 2,
        market_analysis: {
          symbol: 'AAPL', current_price: 189.30, volatility: 0.22, implied_volatility: 0.26,
          volume: 52000000, market_cap: 2940000000000, sector: 'Technology',
          sentiment_score: 0.68, trend_direction: 'bullish',
          support_levels: [182.00, 178.50], resistance_levels: [196.00, 202.50],
          earnings_date: '2026-05-01', dividend_yield: 0.005, beta: 1.2,
        },
        recommendations: [
          {
            strategy_name: 'Bull Call Spread',
            strategy_type: 'speculation',
            confidence_score: 0.82,
            symbol: 'AAPL', current_price: 189.30, risk_score: 0.32,
            days_to_expiration: 21,
            created_at: new Date().toISOString(),
            options: [
              { type: 'call', action: 'buy',  strike: 190, expiration: '2026-04-18', premium: 4.20, quantity: 1 },
              { type: 'call', action: 'sell', strike: 195, expiration: '2026-04-18', premium: 2.10, quantity: 1 },
            ],
            analytics: { max_profit: 540, max_loss: 210, probability_of_profit: 0.64, expected_return: 0.18, breakeven: 192.10 },
            reasoning: {
              market_outlook: 'Bullish momentum with IV rank at 42%',
              strategy_rationale: 'Defined-risk spread captures upside to $195 resistance while limiting max loss to premium paid.',
              risk_factors: ['Earnings volatility', 'Tech sector rotation'],
              key_benefits: ['Defined max loss', 'Positive theta after 10 DTE', 'Lower cost than outright call'],
            },
          },
          {
            strategy_name: 'Cash-Secured Put',
            strategy_type: 'income',
            confidence_score: 0.75,
            symbol: 'AAPL', current_price: 189.30, risk_score: 0.25,
            days_to_expiration: 14,
            created_at: new Date().toISOString(),
            options: [
              { type: 'put', action: 'sell', strike: 185, expiration: '2026-04-04', premium: 2.20, quantity: 1 },
            ],
            analytics: { max_profit: 220, max_loss: 18280, probability_of_profit: 0.72, expected_return: 0.012, breakeven: 182.80 },
            reasoning: {
              market_outlook: 'Support holds at $182 with strong buyer demand',
              strategy_rationale: 'Sell put at support level to collect premium. If assigned, acquire AAPL at effective cost of $182.80.',
              risk_factors: ['Broad market selloff', 'Support level break'],
              key_benefits: ['High probability of profit', 'Generates income', 'Gets long AAPL at discount if assigned'],
            },
          },
        ],
      });
    }

    // AI Options — market analysis (POST /api/ai-options/market-analysis)
    if (url.includes('/api/ai-options/market-analysis')) {
      return jsonResponse({
        symbol: 'AAPL', current_price: 189.30, volatility: 0.22, implied_volatility: 0.26,
        volume: 52000000, market_cap: 2940000000000, sector: 'Technology',
        sentiment_score: 0.68, trend_direction: 'bullish',
        support_levels: [182.00, 178.50], resistance_levels: [196.00, 202.50],
        earnings_date: '2026-05-01', dividend_yield: 0.005, beta: 1.2,
      });
    }

    // AI Options — strategy optimization, model status, health
    if (url.includes('/api/ai-options')) {
      return jsonResponse({ success: true, status: 'ok', message: 'Demo mode' });
    }

    // Options copilot (legacy endpoint)
    if (url.includes('/api/options/copilot')) {
      return jsonResponse({
        recommendations: [
          { strategy: 'Bull Call Spread', confidence: 0.82, max_profit: 540, max_loss: 210, breakeven: 192.10 },
        ],
        chain: [],
        pnl: { max_profit: 540, max_loss: 210, breakeven: 192.10 },
        risk: { delta: 0.48, gamma: 0.032, theta: -0.09, vega: 0.21 },
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

  // ── External stock data APIs — intercept so StockDetailScreen works in demo mode ──

  // Shared demo price table (reused across all API handlers below)
  (url) => {
    // Only handle known external stock API domains
    const isStockApi = (
      url.includes('finnhub.io') ||
      url.includes('api.polygon.io') ||
      url.includes('data.alpaca.markets') ||
      url.includes('alphavantage.co') ||
      url.includes('newsapi.org')
    );
    if (!isStockApi) return null;

    // Per-symbol demo data (matches the /api/market/quotes table above)
    const DEMO_STOCKS_DATA: Record<string, {
      c: number; d: number; dp: number; v: number; h: number; l: number; o: number; pc: number;
      name: string; sector: string; marketCap: number; pe: number; pb: number; eps: number;
    }> = {
      AAPL:  { c: 189.30, d: 2.10,  dp: 1.12,  v: 52000000, h: 190.50, l: 188.10, o: 188.50, pc: 187.20, name: 'Apple Inc.',            sector: 'Technology',          marketCap: 2940000, pe: 28.5, pb: 45.2, eps: 6.64 },
      MSFT:  { c: 415.80, d: 5.60,  dp: 1.37,  v: 24000000, h: 417.00, l: 414.00, o: 414.50, pc: 410.20, name: 'Microsoft Corporation',  sector: 'Technology',          marketCap: 3090000, pe: 35.2, pb: 12.8, eps: 11.81 },
      NVDA:  { c: 875.40, d: 36.18, dp: 4.31,  v: 48000000, h: 882.00, l: 860.00, o: 862.00, pc: 839.22, name: 'NVIDIA Corporation',     sector: 'Technology',          marketCap: 2160000, pe: 65.4, pb: 38.1, eps: 13.39 },
      TSLA:  { c: 196.50, d: 3.20,  dp: 1.66,  v: 88000000, h: 198.00, l: 195.00, o: 195.80, pc: 193.30, name: 'Tesla Inc.',             sector: 'Consumer Cyclical',   marketCap: 625000,  pe: 48.2, pb: 11.4, eps: 4.07 },
      META:  { c: 502.30, d: 8.40,  dp: 1.70,  v: 19000000, h: 505.00, l: 499.00, o: 500.00, pc: 493.90, name: 'Meta Platforms Inc.',    sector: 'Communication',       marketCap: 1280000, pe: 24.8, pb: 7.3,  eps: 20.25 },
      GOOGL: { c: 175.60, d: 2.80,  dp: 1.62,  v: 20000000, h: 176.50, l: 174.50, o: 174.80, pc: 172.80, name: 'Alphabet Inc.',          sector: 'Communication',       marketCap: 2180000, pe: 22.6, pb: 6.8,  eps: 7.77 },
      AMZN:  { c: 198.40, d: 3.60,  dp: 1.85,  v: 32000000, h: 199.50, l: 197.00, o: 197.20, pc: 194.80, name: 'Amazon.com Inc.',        sector: 'Consumer Cyclical',   marketCap: 2090000, pe: 41.3, pb: 8.9,  eps: 4.80 },
      AMD:   { c: 168.20, d: 4.10,  dp: 2.50,  v: 38000000, h: 169.50, l: 166.80, o: 167.00, pc: 164.10, name: 'Advanced Micro Devices', sector: 'Technology',          marketCap: 272000,  pe: 44.1, pb: 3.6,  eps: 3.81 },
      NFLX:  { c: 625.10, d: 11.20, dp: 1.82,  v: 9000000,  h: 628.00, l: 622.00, o: 623.00, pc: 613.90, name: 'Netflix Inc.',           sector: 'Communication',       marketCap: 268000,  pe: 38.7, pb: 16.2, eps: 16.15 },
      COIN:  { c: 228.50, d: -8.30, dp: -3.51, v: 14000000, h: 238.00, l: 226.00, o: 237.00, pc: 236.80, name: 'Coinbase Global Inc.',   sector: 'Financial Services',  marketCap: 58000,   pe: 32.1, pb: 4.8,  eps: 7.11 },
      SPY:   { c: 524.00, d: 4.20,  dp: 0.81,  v: 72000000, h: 525.50, l: 522.00, o: 522.50, pc: 519.80, name: 'SPDR S&P 500 ETF',      sector: 'ETF',                 marketCap: 505000,  pe: 22.1, pb: 4.1,  eps: 23.71 },
      PYPL:  { c: 65.40,  d: 1.20,  dp: 1.87,  v: 22000000, h: 66.20,  l: 64.80,  o: 65.00,  pc: 64.20,  name: 'PayPal Holdings Inc.',   sector: 'Financial Services',  marketCap: 70000,   pe: 15.8, pb: 2.9,  eps: 4.14 },
      UBER:  { c: 78.60,  d: 2.10,  dp: 2.74,  v: 24000000, h: 79.20,  l: 77.80,  o: 78.00,  pc: 76.50,  name: 'Uber Technologies Inc.', sector: 'Technology',          marketCap: 165000,  pe: 29.4, pb: 8.1,  eps: 2.67 },
    };

    // Helper — get demo data for any symbol (fallback for unknowns)
    const extractSymbol = (u: string): string => {
      // Try common query param patterns: symbol=X, ticker=X, symbols=X
      const symMatch = u.match(/[?&](?:symbol|ticker|symbols)=([A-Z.]+)/i);
      if (symMatch) return symMatch[1].toUpperCase().split(',')[0];
      // Polygon/Alpaca path pattern: /ticker/AAPL/ or /stocks/AAPL/
      const pathMatch = u.match(/\/(?:ticker|stocks|aggs\/ticker)\/([A-Z.]+)\//i);
      if (pathMatch) return pathMatch[1].toUpperCase();
      return 'AAPL';
    };

    const sym = extractSymbol(url);
    const d = DEMO_STOCKS_DATA[sym] ?? { ...DEMO_STOCKS_DATA.AAPL, name: `${sym} Corp`, c: 100.00, d: 0.50, dp: 0.50, v: 5000000, h: 101.00, l: 99.00, o: 100.00, pc: 99.50 };

    // ── Finnhub: /quote ──────────────────────────────────────────────────────
    if (url.includes('finnhub.io') && url.includes('/quote')) {
      return jsonResponse({ c: d.c, d: d.d, dp: d.dp, h: d.h, l: d.l, o: d.o, pc: d.pc, v: d.v, t: Date.now() });
    }

    // ── Finnhub: /stock/profile2 ─────────────────────────────────────────────
    if (url.includes('finnhub.io') && url.includes('profile2')) {
      return jsonResponse({
        name: d.name, ticker: sym, finnhubIndustry: d.sector, country: 'US',
        currency: 'USD', exchange: 'NASDAQ', ipo: '1980-12-12',
        marketCapitalization: d.marketCap, shareOutstanding: Math.round(d.marketCap / d.c),
        logo: '', weburl: `https://www.${sym.toLowerCase()}.com`,
        phone: '1-800-555-0100',
      });
    }

    // ── Finnhub: /stock/candle ───────────────────────────────────────────────
    if (url.includes('finnhub.io') && url.includes('/stock/candle')) {
      const count = 30;
      const now = Math.floor(Date.now() / 1000);
      let price = d.c * 0.92;
      const t: number[] = [], o: number[] = [], h: number[] = [], l: number[] = [], c: number[] = [], v: number[] = [];
      for (let i = count - 1; i >= 0; i--) {
        const open = price + (Math.random() - 0.48) * d.c * 0.01;
        const close = open + (Math.random() - 0.46) * d.c * 0.015;
        t.push(now - i * 86400);
        o.push(parseFloat(open.toFixed(2)));
        h.push(parseFloat((Math.max(open, close) + Math.random() * d.c * 0.005).toFixed(2)));
        l.push(parseFloat((Math.min(open, close) - Math.random() * d.c * 0.005).toFixed(2)));
        c.push(parseFloat(close.toFixed(2)));
        v.push(Math.floor(d.v * (0.7 + Math.random() * 0.6)));
        price = close;
      }
      return jsonResponse({ s: 'ok', t, o, h, l, c, v });
    }

    // ── Finnhub: /stock/recommendation ──────────────────────────────────────
    if (url.includes('finnhub.io') && url.includes('recommendation')) {
      return jsonResponse([
        { buy: 18, hold: 8, sell: 2, strongBuy: 12, strongSell: 1, period: '2026-03-01', symbol: sym },
        { buy: 16, hold: 9, sell: 3, strongBuy: 10, strongSell: 1, period: '2026-02-01', symbol: sym },
      ]);
    }

    // ── Finnhub: insider transactions ────────────────────────────────────────
    if (url.includes('finnhub.io') && url.includes('insider-transaction')) {
      return jsonResponse({
        data: [
          { name: 'John Smith', share: 50000, change: 50000, transactionDate: '2026-02-15', transactionPrice: d.c * 0.95, transactionCode: 'P' },
          { name: 'Jane Doe', share: -20000, change: -20000, transactionDate: '2026-02-10', transactionPrice: d.c * 1.02, transactionCode: 'S' },
        ],
        symbol: sym,
      });
    }

    // ── Finnhub: institutional ownership ─────────────────────────────────────
    if (url.includes('finnhub.io') && url.includes('institutional')) {
      return jsonResponse({
        data: [
          { name: 'Vanguard Group', share: 1200000000, change: 5000000, reportDate: '2025-12-31' },
          { name: 'BlackRock Inc.', share: 980000000, change: -2000000, reportDate: '2025-12-31' },
          { name: 'State Street Corporation', share: 640000000, change: 1000000, reportDate: '2025-12-31' },
        ],
        symbol: sym,
      });
    }

    // ── Polygon: /v2/aggs/ticker ─────────────────────────────────────────────
    if (url.includes('api.polygon.io') && url.includes('/aggs/ticker')) {
      const count = 30;
      const now = Date.now();
      let price = d.c * 0.92;
      const results = Array.from({ length: count }, (_, i) => {
        const open = price + (Math.random() - 0.48) * d.c * 0.01;
        const close = open + (Math.random() - 0.46) * d.c * 0.015;
        const result = {
          t: now - (count - 1 - i) * 86400000,
          o: parseFloat(open.toFixed(2)),
          h: parseFloat((Math.max(open, close) + Math.random() * d.c * 0.005).toFixed(2)),
          l: parseFloat((Math.min(open, close) - Math.random() * d.c * 0.005).toFixed(2)),
          c: parseFloat(close.toFixed(2)),
          v: Math.floor(d.v * (0.7 + Math.random() * 0.6)),
          vw: parseFloat(close.toFixed(2)),
          n: Math.floor(40000 + Math.random() * 20000),
        };
        price = close;
        return result;
      });
      return jsonResponse({ ticker: sym, queryCount: count, resultsCount: count, adjusted: true, results, status: 'OK', request_id: 'demo' });
    }

    // ── Alpaca: /v2/stocks/bars ──────────────────────────────────────────────
    if (url.includes('data.alpaca.markets') && url.includes('/bars')) {
      const count = 30;
      const now = Date.now();
      let price = d.c * 0.92;
      const bars = Array.from({ length: count }, (_, i) => {
        const open = price + (Math.random() - 0.48) * d.c * 0.01;
        const close = open + (Math.random() - 0.46) * d.c * 0.015;
        const bar = {
          t: new Date(now - (count - 1 - i) * 86400000).toISOString(),
          o: parseFloat(open.toFixed(2)),
          h: parseFloat((Math.max(open, close) + Math.random() * d.c * 0.005).toFixed(2)),
          l: parseFloat((Math.min(open, close) - Math.random() * d.c * 0.005).toFixed(2)),
          c: parseFloat(close.toFixed(2)),
          v: Math.floor(d.v * (0.7 + Math.random() * 0.6)),
          vw: parseFloat(close.toFixed(2)),
          n: Math.floor(40000 + Math.random() * 20000),
        };
        price = close;
        return bar;
      });
      return jsonResponse({ bars: { [sym]: bars }, next_page_token: null });
    }

    // ── Alpha Vantage: OVERVIEW ──────────────────────────────────────────────
    if (url.includes('alphavantage.co')) {
      return jsonResponse({
        Symbol: sym, Name: d.name, Description: `${d.name} is a leading company in ${d.sector}.`,
        Sector: d.sector, Industry: d.sector, MarketCapitalization: String(d.marketCap * 1000000),
        PERatio: String(d.pe), PriceToBookRatio: String(d.pb), EPS: String(d.eps),
        DividendYield: '0.0050', DividendPerShare: '0.24', PayoutRatio: '0.15',
        RevenuePerShareTTM: String((d.c * 0.8).toFixed(2)),
        ProfitMargin: '0.25', OperatingMarginTTM: '0.30',
        ReturnOnAssetsTTM: '0.18', ReturnOnEquityTTM: '1.47',
        RevenueTTM: String(Math.round(d.marketCap * 1000000 * 0.12)),
        GrossProfitTTM: String(Math.round(d.marketCap * 1000000 * 0.05)),
        EBITDATTm: String(Math.round(d.marketCap * 1000000 * 0.04)),
        QuarterlyRevenueGrowthYOY: '0.08', QuarterlyEarningsGrowthYOY: '0.12',
        AnalystTargetPrice: String((d.c * 1.18).toFixed(2)),
        '52WeekHigh': String((d.c * 1.32).toFixed(2)), '52WeekLow': String((d.c * 0.68).toFixed(2)),
        '50DayMovingAverage': String((d.c * 0.97).toFixed(2)), '200DayMovingAverage': String((d.c * 0.88).toFixed(2)),
        SharesOutstanding: String(Math.round(d.marketCap * 1000000 / d.c)),
        Beta: '1.20', ForwardPE: String((d.pe * 0.85).toFixed(1)),
      });
    }

    // ── NewsAPI ──────────────────────────────────────────────────────────────
    if (url.includes('newsapi.org')) {
      return jsonResponse({
        status: 'ok', totalResults: 3,
        articles: [
          { title: `${d.name} beats Q4 earnings estimates`, description: `${sym} reported strong earnings, exceeding analyst expectations with solid revenue growth.`, url: `https://example.com/${sym}-earnings`, publishedAt: new Date(Date.now() - 3600000).toISOString(), source: { name: 'Reuters' }, sentiment: 'positive' },
          { title: `Analysts raise price target on ${sym}`, description: `Several Wall Street analysts have raised their price targets following the earnings beat.`, url: `https://example.com/${sym}-pt`, publishedAt: new Date(Date.now() - 7200000).toISOString(), source: { name: 'Bloomberg' }, sentiment: 'positive' },
          { title: `${d.sector} sector outlook for 2026`, description: `Industry analysts weigh in on the ${d.sector} sector's prospects amid macro headwinds.`, url: `https://example.com/${d.sector.toLowerCase()}-outlook`, publishedAt: new Date(Date.now() - 86400000).toISOString(), source: { name: 'CNBC' }, sentiment: 'neutral' },
        ],
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

    // Fallback: return empty 200 so app doesn't crash (log only in __DEV__ to reduce noise)
    if (__DEV__) {
      console.warn(`[DemoMode] Unhandled fetch: ${url} — returning empty 200`);
    }
    return Promise.resolve(jsonResponse({}));
  };
}

export function uninstallDemoFetch() {
  if (!_installed) return;
  global.fetch = _originalFetch;
  _installed = false;
}
