/* FinancialChatbotService.ts
 * Single-file financial Q&A service with deterministic helpers.
 * No external imports required.
 */

export interface StockRecommendation {
  symbol: string;
  companyName: string;
  currentPrice: number;
  targetPrice: number;
  recommendation: string; // BUY/HOLD/SELL
  riskLevel: 'Low' | 'Medium' | 'High';
  expectedReturn: number; // %
  sector: string;
  reason: string;
}

export interface InvestmentContext {
  amount: number;
  timeHorizon: 'short' | 'medium' | 'long';
  goal:
    | 'general investment'
    | 'retirement'
    | 'home purchase'
    | 'education'
    | 'travel fund';
  riskTolerance: 'low' | 'medium' | 'high';
}

/** Optional provider you can replace with a real API later. */
export interface RecommendationProvider {
  fetchRecommendations(ctx: InvestmentContext): Promise<StockRecommendation[]>;
}

/** Default mock provider (safe fallback) */
class MockRecommendationProvider implements RecommendationProvider {
  async fetchRecommendations(ctx: InvestmentContext): Promise<StockRecommendation[]> {
    const mock: StockRecommendation[] = [
      {
        symbol: 'AAPL',
        companyName: 'Apple Inc.',
        currentPrice: 175.5,
        targetPrice: 200,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 14.0,
        sector: 'Technology',
        reason: 'Strong ecosystem, recurring revenue, steady growth.',
      },
      {
        symbol: 'MSFT',
        companyName: 'Microsoft Corporation',
        currentPrice: 380.25,
        targetPrice: 420,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 10.5,
        sector: 'Technology',
        reason: 'Cloud leadership, diversified enterprise revenue, AI tailwinds.',
      },
      {
        symbol: 'GOOGL',
        companyName: 'Alphabet Inc.',
        currentPrice: 140.8,
        targetPrice: 160,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 13.6,
        sector: 'Technology',
        reason: 'Dominant ads/search, optionality in AI and cloud.',
      },
      {
        symbol: 'SPY',
        companyName: 'SPDR S&P 500 ETF',
        currentPrice: 445.2,
        targetPrice: 480,
        recommendation: 'BUY',
        riskLevel: 'Low',
        expectedReturn: 7.8,
        sector: 'Diversified',
        reason: 'Broad U.S. market exposure at low cost.',
      },
      {
        symbol: 'QQQ',
        companyName: 'Invesco QQQ Trust',
        currentPrice: 375.4,
        targetPrice: 410,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 9.2,
        sector: 'Technology',
        reason: 'Nasdaq-100 growth exposure.',
      },
    ];

    if (ctx.riskTolerance === 'low') return mock.filter(r => r.riskLevel === 'Low');
    if (ctx.riskTolerance === 'high') return mock.filter(r => r.riskLevel !== 'Low');
    return mock.filter(r => r.riskLevel === 'Medium' || r.riskLevel === 'Low');
  }
}

/** AlphaVantage-backed provider (real data).
 *  - Uses GLOBAL_QUOTE for current price.
 *  - Applies a simple, deterministic target/expectedReturn model so the service stays predictable.
 *  - You can harden this or replace the heuristics with your own logic later.
 */
export class AlphaVantageRecommendationProvider implements RecommendationProvider {
  private apiKey: string;
  private base = 'https://www.alphavantage.co/query';
  private disabled = true; // Disabled - use backend API instead
  // A small, curated universe (keeps within free API limits).
  // You can expand/segment by risk/goals below.
  private universe = {
    low:    ['SPY', 'VTI', 'BND', 'AGG', 'VNQ'],
    medium: ['AAPL', 'MSFT', 'GOOGL', 'VTI', 'VXUS', 'QQQ'],
    high:   ['QQQ', 'NVDA', 'TSLA', 'META', 'ARKK'],
  };

  constructor(apiKey: string) {
    if (!apiKey) throw new Error('Alpha Vantage API key required');
    this.apiKey = apiKey;
  }

  private async fetchGlobalQuote(symbol: string): Promise<{ price: number; previousClose?: number }> {
    try {
      const url = `${this.base}?function=GLOBAL_QUOTE&symbol=${encodeURIComponent(symbol)}&apikey=${this.apiKey}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`AlphaVantage error for ${symbol}: ${res.status}`);
      const json = await res.json();
      
      // Check for API error messages
      if (json['Error Message']) {
        throw new Error(`AlphaVantage API error: ${json['Error Message']}`);
      }
      if (json['Note']) {
        throw new Error(`AlphaVantage rate limit: ${json['Note']}`);
      }
      
      const q = json['Global Quote'];
      if (!q) {
        throw new Error(`No Global Quote data for ${symbol}`);
      }
      
      const price = parseFloat(String(q['05. price'] ?? 'NaN'));
      const prev = parseFloat(String(q['08. previous close'] ?? 'NaN'));
      
      if (!isFinite(price)) {
        console.log(`AlphaVantage response for ${symbol}:`, json);
        throw new Error(`Invalid price data for ${symbol}: ${q['05. price']}`);
      }
      
      return { price, previousClose: isFinite(prev) ? prev : undefined };
    } catch (error) {
      console.error(`AlphaVantage fetch error for ${symbol}:`, error);
      throw error;
    }
  }

  private pickUniverse(risk: 'low'|'medium'|'high'): string[] {
    if (risk === 'low') return this.universe.low;
    if (risk === 'high') return this.universe.high;
    return this.universe.medium;
  }

  /** Simple deterministic target model:
   *   - base uplift by goal/time/risk
   *   - bounds & floors so output stays stable
   */
  private computeTarget(price: number, opts: {
    risk: 'low'|'medium'|'high',
    time: 'short'|'medium'|'long',
    goal: InvestmentContext['goal']
  }): { target: number; expectedReturnPct: number; riskLevel: 'Low'|'Medium'|'High' } {
    let uplift = 0.0;

    // Time horizon: longer → higher target allowance
    if (opts.time === 'short') uplift += 0.03;
    if (opts.time === 'medium') uplift += 0.08;
    if (opts.time === 'long') uplift += 0.15;

    // Risk tolerance
    if (opts.risk === 'low') uplift += 0.03;
    if (opts.risk === 'medium') uplift += 0.08;
    if (opts.risk === 'high') uplift += 0.15;

    // Goal nudges
    if (opts.goal === 'retirement') uplift += 0.04;
    if (opts.goal === 'education') uplift += 0.03;
    if (opts.goal === 'home purchase') uplift += 0.02;
    // "general investment" keeps base; "travel fund" gets no extra uplift

    // Clamp uplift for sanity
    uplift = Math.max(0.02, Math.min(uplift, 0.45));
    const target = +(price * (1 + uplift)).toFixed(2);
    const expectedReturnPct = +(uplift * 100).toFixed(1);
    const riskLevel = opts.risk === 'high' ? 'High' : opts.risk === 'low' ? 'Low' : 'Medium';
    return { target, expectedReturnPct, riskLevel };
  }

  private describe(symbol: string): { companyName: string; sector: string; reason: string } {
    // Lightweight mapping (keeps it deterministic & offline-friendly for names/sectors).
    const map: Record<string, { companyName: string; sector: string; reason: string }> = {
      AAPL: { companyName: 'Apple Inc.', sector: 'Technology', reason: 'Ecosystem, services, cash flow.' },
      MSFT: { companyName: 'Microsoft Corporation', sector: 'Technology', reason: 'Cloud leadership, AI leverage.' },
      GOOGL:{ companyName: 'Alphabet Inc.', sector: 'Technology', reason: 'Ads/search scale; optionality.' },
      NVDA: { companyName: 'NVIDIA Corporation', sector: 'Semiconductors', reason: 'AI/accelerator demand.' },
      TSLA: { companyName: 'Tesla, Inc.', sector: 'Consumer Discretionary', reason: 'EV scale; software margin.' },
      META: { companyName: 'Meta Platforms, Inc.', sector: 'Communication Services', reason: 'Ads scale; AI; efficiency.' },
      SPY:  { companyName: 'SPDR S&P 500 ETF', sector: 'Diversified', reason: 'Broad U.S. market exposure.' },
      VTI:  { companyName: 'Vanguard Total Stock Market ETF', sector: 'Diversified', reason: 'Low-cost total market.' },
      VXUS: { companyName: 'Vanguard Total Intl. Stock ETF', sector: 'Diversified', reason: 'International diversification.' },
      BND:  { companyName: 'Vanguard Total Bond Market ETF', sector: 'Fixed Income', reason: 'Core bond exposure.' },
      AGG:  { companyName: 'iShares Core U.S. Aggregate Bond ETF', sector: 'Fixed Income', reason: 'Broad bond market.' },
      VNQ:  { companyName: 'Vanguard Real Estate ETF', sector: 'Real Estate', reason: 'REIT income & diversification.' },
      QQQ:  { companyName: 'Invesco QQQ Trust', sector: 'Technology', reason: 'Nasdaq-100 growth tilt.' },
      ARKK: { companyName: 'ARK Innovation ETF', sector: 'Thematic', reason: 'Disruptive innovation basket.' },
    };
    return map[symbol] ?? { companyName: symbol, sector: 'Unknown', reason: 'Universe constituent.' };
  }

  async fetchRecommendations(ctx: InvestmentContext): Promise<StockRecommendation[]> {
    if (this.disabled) {
      // Return empty array when disabled - use backend API instead
      return [];
    }
    const risk = ctx.riskTolerance;
    const time = ctx.timeHorizon;
    const tickers = this.pickUniverse(risk);
    const out: StockRecommendation[] = [];

    // Keep to <= 5 symbols to respect free-tier rate limits.
    for (const symbol of tickers.slice(0, 5)) {
      try {
        const { price } = await this.fetchGlobalQuote(symbol);
        const { target, expectedReturnPct, riskLevel } =
          this.computeTarget(price, { risk, time, goal: ctx.goal });
        const meta = this.describe(symbol);

        out.push({
          symbol,
          companyName: meta.companyName,
          currentPrice: +price.toFixed(2),
          targetPrice: target,
          recommendation: expectedReturnPct >= 8 ? 'BUY' : expectedReturnPct >= 4 ? 'HOLD' : 'HOLD',
          riskLevel,
          expectedReturn: expectedReturnPct,
          sector: meta.sector,
          reason: meta.reason,
        });

        // Gentle pacing to avoid burst limits (Alpha Vantage is strict).
        await new Promise(r => setTimeout(r, 250));
      } catch {
        // Skip symbol on failure; continue
      }
    }

    // Fallback: if API failed across the board, return a minimal safe set from mock
    if (!out.length) {
      const mock = new MockRecommendationProvider();
      return mock.fetchRecommendations(ctx);
    }

    return out;
  }
}

class FinancialChatbotService {
  private static instance: FinancialChatbotService;
  private recommender: RecommendationProvider;

  private constructor(provider?: RecommendationProvider) {
    if (provider) {
      this.recommender = provider;
    } else if (typeof process !== 'undefined' && process.env?.ALPHA_VANTAGE_KEY) {
      this.recommender = new AlphaVantageRecommendationProvider(process.env.ALPHA_VANTAGE_KEY as string);
    } else {
      this.recommender = new MockRecommendationProvider();
    }
  }

  public static getInstance(provider?: RecommendationProvider): FinancialChatbotService {
    if (!FinancialChatbotService.instance) {
      FinancialChatbotService.instance = new FinancialChatbotService(provider);
    }
    return FinancialChatbotService.instance;
  }

  /* ----------------------------- INTENT HELPERS ---------------------------- */

  /** Treat “should I buy/get/purchase …” as financial (spending) and handle first. */
  private isPurchaseQuestion(input: string): boolean {
    const txt = input.toLowerCase().trim();
    const buyRegex = /\bshould\s+i\s+(buy|get|purchase)\b/;
    const worthRegex = /\bis\s+it\s+worth\s+(buying|get|getting|purchase|purchasing)\b/;
    return buyRegex.test(txt) || worthRegex.test(txt);
  }

  /** Broad financial classifier (budgeting, investing, debt, etc.). */
  public isFinancialQuestion(userInput: string): boolean {
    const input = userInput.toLowerCase();

    // Short-circuit: purchase decisions count as financial.
    if (this.isPurchaseQuestion(input)) return true;

    const financialKeywords = [
      'invest',
      'investment',
      'stock',
      'stocks',
      'etf',
      'mutual fund',
      'bond',
      'bonds',
      'portfolio',
      'diversify',
      'diversification',
      'risk',
      'return',
      'market',
      'trading',
      'buy',
      'sell',
      'hold',
      'dividend',
      'yield',
      'volatility',
      'retirement',
      'ira',
      '401k',
      'roth',
      'traditional',
      'pension',
      'annuity',
      'budget',
      'budgeting',
      'save',
      'saving',
      'savings',
      'debt',
      'credit',
      'loan',
      'mortgage',
      'insurance',
      'tax',
      'finance',
      'money',
      'wealth',
      'asset',
      'liability',
      'net worth',
      'income',
      'expense',
      'compound',
      'interest',
      'inflation',
      'recession',
      'market cap',
      'pe ratio',
      'earnings',
      'revenue',
      'cash flow',
      'options',
      'crypto',
      'robinhood',
      'fidelity',
      'vanguard',
      'schwab',
      'dollar cost averaging',
      'dca',
      'rebalancing',
      'allocation',
      'sector',
      'growth',
      'value',
      'capital gains',
      'tax loss harvesting',
      'sbloc',
      'securities based line of credit',
      'portfolio lending',
      'borrow against portfolio',
      'margin loan',
      'liquidity',
      'borrowing power',
      // Spending / purchases
      'purchase',
      'spend',
      'price',
      'afford',
      'worth it',
      'buy',
      'get',
      'item',
      'product',
      'goal',
      'paycheck',
      'biweekly',
      'weekly',
      'monthly',
      'salary',
      'wage',
    ];

    const nonFinancialKeywords = [
      'weather',
      'cooking',
      'recipe',
      'movie',
      'music',
      'sports',
      'game',
      'relationship',
      'medical',
      'doctor',
      'exercise',
      'fitness',
      'diet',
      'politics',
      'election',
      'government',
      'law',
      'education',
      'programming',
      'software',
      'hardware',
      'computer',
      'job interview',
    ];

    if (nonFinancialKeywords.some(k => input.includes(k))) return false;
    return financialKeywords.some(k => input.includes(k));
  }

  /* ------------------------- CONTEXT & LIGHT PARSING ------------------------ */

  public extractInvestmentContext(userInput: string): InvestmentContext {
    const input = userInput.toLowerCase();

    // Amount (handles 1,200 / 1.2k / $500 / 2m)
    const amt = (() => {
      const m = input.match(/\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(\s*[kmb])?/i);
      if (!m) return 0;
      const base = parseFloat(m[1].replace(/,/g, ''));
      const suf = (m[2] || '').trim().toLowerCase();
      const mult = suf === 'k' ? 1_000 : suf === 'm' ? 1_000_000 : suf === 'b' ? 1_000_000_000 : 1;
      return isNaN(base) ? 0 : base * mult;
    })();

    let timeHorizon: InvestmentContext['timeHorizon'] = 'medium';
    if (/\b(year|years|annual|long)\b/.test(input)) timeHorizon = 'long';
    else if (/\b(month|months|short)\b/.test(input)) timeHorizon = 'short';

    let goal: InvestmentContext['goal'] = 'general investment';
    const travel = ['trip', 'travel', 'vacation', 'holiday', 'getaway', 'miami'];
    const spending = ['spend', 'spending', 'cost', 'budget', 'cash', 'dollars'];
    if (travel.some(w => input.includes(w)) && spending.some(w => input.includes(w))) goal = 'travel fund';
    else if (input.includes('retirement')) goal = 'retirement';
    else if (/(house|home|property)/.test(input)) goal = 'home purchase';
    else if (/(education|college|school)/.test(input)) goal = 'education';

    let risk: InvestmentContext['riskTolerance'] = 'medium';
    if (/(conservative|safe|low risk)/.test(input)) risk = 'low';
    if (/(aggressive|high risk|risky)/.test(input)) risk = 'high';

    return { amount: amt, timeHorizon, goal, riskTolerance: risk };
  }

  /* ------------------------------- MAIN FLOW -------------------------------- */

  public async processUserInput(userInput: string): Promise<string> {
    const lower = userInput.toLowerCase();

    // 1) Purchase decisions handled first (so “jordans” doesn’t get rejected)
    if (this.isPurchaseQuestion(lower)) {
      return this.generatePurchaseDecisionResponse(userInput);
    }

    // 2) Not financial? graceful redirect
    if (!this.isFinancialQuestion(userInput)) {
      return this.generateNonFinancialResponse();
    }

    // 3) NEW: handle low-risk / high-risk queries explicitly
    if (/\b(low[- ]?risk|conservative|safe|stable)\b/.test(lower)) {
      const ctx: InvestmentContext = {
        amount: 1000,
        timeHorizon: 'long',
        goal: 'general investment',
        riskTolerance: 'low',
      };
      return this.generateInvestmentAdvice("low risk investment", ctx);
    }

    if (/\b(high[- ]?risk|aggressive|risky|volatile)\b/.test(lower)) {
      const ctx: InvestmentContext = {
        amount: 1000,
        timeHorizon: 'long',
        goal: 'general investment',
        riskTolerance: 'high',
      };
      return this.generateInvestmentAdvice("high risk investment", ctx);
    }

    if (/\b(medium|balanced|moderate)[- ]?risk\b|\bbalanced\s+portfolio\b/.test(lower)) {
      const ctx: InvestmentContext = {
        amount: 1000,
        timeHorizon: 'long',
        goal: 'general investment',
        riskTolerance: 'medium',
      };
      return this.generateInvestmentAdvice("medium risk investment", ctx);
    }

    // 4) Savings calculation questions (e.g., paycheck → goal by December)
    const hasSavingsKeywords =
      /(save|goal|saving|savings|accumulate|build|grow|achieve|reach)/.test(lower);
    const hasIncomeKeywords =
      /(paycheck|biweekly|every two weeks|earn|make|weekly|monthly|salary|wage)/.test(lower);
    if (hasSavingsKeywords && hasIncomeKeywords) {
      return this.generateSavingsCalculationResponse(userInput);
    }

    // 5) Investment advice only if clearly about investing
    const ctx = this.extractInvestmentContext(userInput);
    const isInvestmentQuestion =
      ctx.amount > 0 &&
      /(invest|investment|portfolio|stock|stocks|etf|mutual fund|retirement|401k|ira)/.test(lower);

    if (isInvestmentQuestion) {
      return this.generateInvestmentAdvice(userInput, ctx);
    }

    // 6) Otherwise general financial education
    return this.generateGeneralFinancialResponse(userInput);
  }

  /* -------------------------- PURCHASE DECISION PATH ------------------------- */

  private generatePurchaseDecisionResponse(userInput: string): string {
    const input = userInput.toLowerCase();

    // Extract item after buy/get/purchase
    const mItem = input.match(/\b(?:buy|get|purchase)\s+(.*?)(?:\?|$)/);
    const rawItem = (mItem?.[1] || 'this item').replace(/\s+for\s+.*$/, '').trim();
    const item = rawItem.length ? rawItem : 'this item';

    // Price (optional): $250 / 250 / 1,200 / 1.2k
    let price: number | null = null;
    const priceMatch = input.match(/\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(\s*[km])?/i);
    if (priceMatch) {
      const base = parseFloat(priceMatch[1].replace(/,/g, ''));
      const suffix = (priceMatch[2] || '').trim().toLowerCase();
      const mult = suffix === 'k' ? 1_000 : suffix === 'm' ? 1_000_000 : 1;
      if (!isNaN(base)) price = base * mult;
    }

    // Biweekly income if mentioned (optional)
    let incomeBiweekly: number | null = null;
    const payMatch = input.match(
      /(?:paycheck|biweekly|every\s+two\s+weeks)[^\d$]*\$?\s*(\d{2,6}(?:,\d{3})?)/i
    );
    if (payMatch) {
      const val = parseFloat(payMatch[1].replace(/,/g, ''));
      if (!isNaN(val)) incomeBiweekly = val;
    }

    let affordability = '';
    if (price && incomeBiweekly) {
      const funMid = incomeBiweekly * 0.15;
      const ratio = price / incomeBiweekly;
      affordability =
        `• Price vs paycheck: $${Math.round(price).toLocaleString()} ≈ ${(ratio * 100).toFixed(
          0
        )}% of one biweekly paycheck\n` +
        `• Typical “fun money” range: ~10–20% → $${Math.round(
          incomeBiweekly * 0.1
        ).toLocaleString()}–$${Math.round(incomeBiweekly * 0.2).toLocaleString()} per paycheck\n` +
        (price <= funMid
          ? '• ✅ This can fit a typical discretionary slice if other priorities are covered.\n'
          : '• ⚠️ Above a typical discretionary slice—consider saving across a few paychecks.\n');
    } else if (price) {
      affordability = `• Price noted: ~$${Math.round(
        price
      ).toLocaleString()}. Try to keep one-off buys within ~10–20% of a paycheck.\n`;
    }

    return `**Should you buy ${item}? A quick, numbers-first check**

**1) Financial health**
• 3–6 month emergency fund funded?  
• Any high-interest debt open?  
• Retirement/investing on track this month?  

**2) Budget fit**
${affordability || '• Rule of thumb: keep one-off discretionary buys within ~10–20% of a paycheck.\n'}\
• If it doesn’t fit today, create a short “sinking fund” and split the cost across paychecks.

**3) Value test**
• Need vs want: will you use it 30+ times in the next 12 months?  
• Cost per use = price ÷ expected uses. Lower is better.  
• Alternatives: used/refurbished, last season, wait for a sale.

**4) Credit impact**
• Avoid financing discretionary items. If you use a rewards card, pay in full.  
• Keep utilization under 30% (ideally <10%) after the purchase.

**5) Impulse guard**
• Use a 48-hour cooling-off period. If it still fits and you still want it, enjoy it—guilt-free.

*Educational information only; not financial advice.*`;
  }

  /* ----------------------------- INVESTING PATH ----------------------------- */

  private async getStockRecommendations(context: InvestmentContext): Promise<StockRecommendation[]> {
    // Swappable provider; default is deterministic mock above.
    return this.recommender.fetchRecommendations(context);
  }

  public async generateInvestmentAdvice(
    userInput: string,
    context: InvestmentContext
  ): Promise<string> {
    const { amount, timeHorizon, goal, riskTolerance } = context;

    // Special case: tiny travel/spending amounts → keep liquid.
    const travelWords = ['trip', 'travel', 'vacation', 'holiday', 'getaway', 'miami'];
    const spendingWords = ['spending', 'spend', 'cost', 'money', 'budget', 'cash', 'dollars'];
    const hasTravelWord = travelWords.some(w => userInput.toLowerCase().includes(w));
    const hasSpendingWord = spendingWords.some(w => userInput.toLowerCase().includes(w));
    if (amount > 0 && amount < 2000 && (goal === 'travel fund' || (hasTravelWord && hasSpendingWord))) {
      return `For $${amount.toLocaleString()} in **trip spending money**, consider:
**Short-term parking:** high-yield savings or money market for 4–5% APY  
**Tips:** daily cap, use a rewards card but pay in full, carry a little cash  
Given the short timeline, investing risk isn’t rewarded here.

*Educational info, not financial advice.*`;
    }

    const recs = await this.getStockRecommendations(context);

    let resp = `Based on **${goal}** with **$${amount.toLocaleString()}** over a **${timeHorizon}** horizon:\n\n`;
    if (riskTolerance === 'low') {
      resp += `**Conservative (Low Risk)**\n• 60% Bonds/ETFs (BND, AGG)\n• 30% Broad stocks (VTI, SPY)\n• 10% Cash reserves\n\n`;
    } else if (riskTolerance === 'high') {
      resp += `**Aggressive (High Risk)**\n• 70% Growth (QQQ, ARKK)\n• 20% Individual stocks (AAPL, MSFT, GOOGL)\n• 10% International (VXUS)\n\n`;
    } else {
      resp += `**Balanced (Medium Risk)**\n• 50% Broad ETFs (VTI, SPY)\n• 30% Individual stocks\n• 20% Bonds/REITs (BND, VNQ)\n\n`;
    }

    if (recs.length) {
      resp += `**Specific ideas (illustrative):**\n`;
      recs.slice(0, 5).forEach((r, i) => {
        resp += `${i + 1}. **${r.symbol}** (${r.companyName}) — $${r.currentPrice} → target $${r.targetPrice} • exp. ${r.expectedReturn}% • ${r.riskLevel}\n   Reason: ${r.reason}\n`;
      });
      resp += '\n';
    }

    if (timeHorizon === 'short') {
      resp += `**Short-term (1–2y)**: favor stability/dividends, HYSA for cash needs, avoid high volatility.\n\n`;
    } else if (timeHorizon === 'long') {
      resp += `**Long-term (5+y)**: emphasize growth ETFs/stocks, dollar-cost average, rebalance quarterly.\n\n`;
    }

    if (goal === 'travel fund') {
      resp += `**Travel fund tip**: keep ~20% liquid for bookings; watch FX rates if going abroad.\n\n`;
    }

    resp += `**Notes:** diversify, mind taxes, and consider professional advice.  
*Educational information only; not financial advice.*`;
    return resp;
  }

  /* --------------------------- SAVINGS CALCULATOR --------------------------- */

  private generateSavingsCalculationResponse(userInput: string): string {
    const input = userInput.toLowerCase();

    const matches = input.match(/(\d+)(?:\s?(k|thousand))?/gi);
    if (!matches || matches.length < 2) {
      return `To calculate what to save per paycheck, please share:  
• Your **biweekly income** amount  
• Your **goal** amount  
For example: “I make **$600** every two weeks and want to save **$5000** by December.”`;
    }

    // first number = income, second = goal (supports “k/thousand”)
    const parseNum = (s: string) => {
      const m = s.match(/(\d+)(k|thousand)?/i);
      if (!m) return 0;
      const n = parseInt(m[1], 10);
      const mult = m[2] ? 1000 : 1;
      return n * mult;
    };

    const income = parseNum(matches[0]);
    let goal = parseNum(matches[1]);

    // months until December (approx)
    const now = new Date();
    const currentMonth = now.getMonth();
    const december = 11;
    const monthsLeft = currentMonth <= december ? december - currentMonth : 12 - currentMonth + december;

    const biweeklyPeriods = Math.ceil((monthsLeft * 30) / 14);
    const savePerCheck = Math.ceil(goal / Math.max(1, biweeklyPeriods));
    const pct = ((savePerCheck / Math.max(1, income)) * 100).toFixed(1);
    const total = savePerCheck * biweeklyPeriods;
    const extra = total - goal;

    let out = `**Save $${goal.toLocaleString()} by December**\n\n`;
    out += `• Biweekly income: $${income.toLocaleString()}\n`;
    out += `• Periods left: ~${biweeklyPeriods}\n`;
    out += `• Save **$${savePerCheck.toLocaleString()}** each paycheck (**${pct}%** of income)\n`;
    out += `• Total by December: **$${total.toLocaleString()}**`;
    if (extra > 0) out += ` (≈ $${extra.toLocaleString()} extra)\n`;
    out += `\n**Tips**: auto-transfer on payday, treat savings like a bill, use HYSA (4–5% APY).\n\n`;
    if (parseFloat(pct) > 20) {
      out += `⚠️ **Aggressive**. Make sure essentials are covered first.\n\n`;
    }
    out += `*Educational info only; not financial advice.*`;
    return out;
  }

  /* -------------------- DETERMINISTIC UTILITY CALCULATORS ------------------- */

  /** Debt Snowball schedule (smallest balance first). */
  public calculateDebtSnowballSchedule(params: {
    debts: { name: string; balance: number; apr: number; minPayment: number }[];
    monthlyExtra: number; // extra amount applied to snowball
  }): { months: number; schedule: Array<{ month: number; payments: Record<string, number>; balances: Record<string, number> }> } {
    const debts = params.debts
      .map(d => ({ ...d }))
      .sort((a, b) => a.balance - b.balance); // smallest balance first

    const schedule: Array<{
      month: number;
      payments: Record<string, number>;
      balances: Record<string, number>;
    }> = [];

    let month = 0;
    const monthlyRate = (apr: number) => apr / 100 / 12;

    const allZero = () => debts.every(d => d.balance <= 0.01);

    while (!allZero() && month < 600) {
      month += 1;
      const payments: Record<string, number> = {};
      const balancesBefore = Object.fromEntries(debts.map(d => [d.name, Math.max(0, d.balance)]));

      // interest accrual for the month
      debts.forEach(d => {
        if (d.balance > 0) d.balance += d.balance * monthlyRate(d.apr);
      });

      // pay minimums
      let extra = params.monthlyExtra;
      debts.forEach(d => {
        const pay = Math.min(d.minPayment, d.balance);
        d.balance -= pay;
        payments[d.name] = pay;
      });

      // apply snowball extra to smallest active
      for (let i = 0; i < debts.length && extra > 0.01; i++) {
        const d = debts[i];
        if (d.balance <= 0) continue;
        const pay = Math.min(extra, d.balance);
        d.balance -= pay;
        payments[d.name] = (payments[d.name] || 0) + pay;
        extra -= pay;
      }

      const balancesAfter = Object.fromEntries(debts.map(d => [d.name, Math.max(0, +d.balance.toFixed(2))]));
      schedule.push({ month, payments, balances: balancesAfter });
    }

    return { months: month, schedule };
  }

  /** Credit utilization optimizer: how much to pay to reach a target utilization. */
  public optimizeCreditUtilization(params: {
    cards: { name: string; balance: number; limit: number }[];
    targetUtilization?: number; // default 0.1 (10%)
  }): {
    totalLimit: number;
    currentUtilization: number;
    targetUtilization: number;
    targetTotalBalance: number;
    requiredPaydown: number;
    perCardSuggestion: Array<{ name: string; pay: number }>;
  } {
    const target = params.targetUtilization ?? 0.1;
    const totalLimit = params.cards.reduce((s, c) => s + c.limit, 0);
    const totalBalance = params.cards.reduce((s, c) => s + c.balance, 0);
    const currentUtil = totalLimit > 0 ? totalBalance / totalLimit : 0;

    const targetTotalBalance = totalLimit * target;
    const requiredPaydown = Math.max(0, totalBalance - targetTotalBalance);

    // Suggest paying down highest-utilization cards first
    const sorted = [...params.cards].sort(
      (a, b) => b.balance / Math.max(1, b.limit) - a.balance / Math.max(1, a.limit)
    );
    let remaining = requiredPaydown;
    const perCard: Array<{ name: string; pay: number }> = [];
    for (const c of sorted) {
      if (remaining <= 0.01) {
        perCard.push({ name: c.name, pay: 0 });
        continue;
      }
      const currentCardUtil = c.limit > 0 ? c.balance / c.limit : 1;
      const desiredBalance = Math.max(0, c.limit * target); // simple proportional target
      const need = Math.max(0, c.balance - desiredBalance);
      const pay = Math.min(need, remaining);
      perCard.push({ name: c.name, pay: +pay.toFixed(2) });
      remaining -= pay;
    }

    return {
      totalLimit,
      currentUtilization: +currentUtil.toFixed(3),
      targetUtilization: target,
      targetTotalBalance: +targetTotalBalance.toFixed(2),
      requiredPaydown: +requiredPaydown.toFixed(2),
      perCardSuggestion: perCard,
    };
  }

  /* -------------------------- GENERAL RESPONSES ----------------------------- */

  private generateNonFinancialResponse(): string {
    return `I'm focused on **personal finance**: investing, budgeting, debt, credit, retirement, savings plans, and portfolio lending.
Ask me things like:
• "How much should I save from my paycheck?"  
• "Roth vs Traditional IRA?"  
• "Should I buy this?"  
• "How do index funds work?"
• "What is SBLOC?"
• "How can I access liquidity without selling stocks?"`;
  }

  /** Comparative questions & education topics are handled here (trimmed for brevity). */
  private generateComparativeFinancialResponse(userInput: string): string {
    const input = userInput.toLowerCase();

    if (input.includes('roth') && input.includes('traditional') && input.includes('ira')) {
      return `**Roth vs Traditional IRA** … (educational summary)\n*Educational info only; not financial advice.*`;
    }
    if (input.includes('401k') && input.includes('ira')) {
      return `**401(k) vs IRA** … (educational summary)\n*Educational info only; not financial advice.*`;
    }
    if (input.includes('cash') && (input.includes('credit') || input.includes('debt'))) {
      return `**Cash vs Credit** … (framework & rules of thumb)\n*Educational info only; not financial advice.*`;
    }
    if (input.includes('invest') && input.includes('save')) {
      return `**Investing vs Saving** … (time horizon & growth)\n*Educational info only; not financial advice.*`;
    }

    return `**Financial Comparison Framework**  
Consider: current finances, goals & timeline, risk tolerance, taxes, and opportunity cost.  
Short-term needs → safer; long-term goals → take calculated risk.  
*Educational info only; not financial advice.*`;
  }

  private generateETFResponse(): string {
    return `**ETFs (Exchange-Traded Funds)** offer low-cost diversification and trade like stocks. Start simple: VTI + BND, dollar-cost average, rebalance annually. *Educational info only; not financial advice.*`;
  }

  private generateBudgetingResponse(): string {
    return `**Budgeting:** 50/30/20 rule (needs/wants/saving), or zero-based budgeting if you want detail. Automate savings, review weekly, adjust monthly.`;
  }

  private generateDebtPayoffResponse(): string {
    return `**Debt payoff:** Snowball (motivation) vs Avalanche (interest-optimal). Pay minimums on all, put extra on the smallest/highest-APR respectively. Build $1k buffer first.`;
  }

  private generateEmergencyFundResponse(): string {
    return `**Emergency fund:** 3–6 months expenses in HYSA/money market (4–5% APY). Not for planned purchases; rebuild quickly after use.`;
  }

  private generateCreditResponse(): string {
    return `**Credit:** Pay on time, keep utilization <30% (ideally <10%), don’t close old accounts, space applications. Use rewards cards only if you pay in full.`;
  }

  private generateRetirementResponse(): string {
    return `**Retirement:** Get the 401(k) match → Max IRA → Back to 401(k). Aim 15%+ of income, stock-heavy when young, rebalance yearly.`;
  }

  private generateSBLOCResponse(): string {
    return `**SBLOC (Securities-Based Line of Credit)** lets you borrow against your investment portfolio without selling stocks.

**How it works:**
• Borrow up to 50% of eligible securities value
• Interest-only payments (typically 6.5-8.5% APR)
• No monthly principal payments required
• Variable rates tied to market benchmarks

**When to consider:**
• Need liquidity but want to keep investments growing
• Lower rates than credit cards (18-25% APR)
• Tax advantages (interest may be deductible)
• Avoid capital gains from selling appreciated stocks

**Important risks:**
• Market volatility can reduce borrowing power
• Margin calls if portfolio value drops significantly
• Variable interest rates can increase
• Not FDIC insured

**Best practices:**
• Only borrow what you can comfortably repay
• Keep loan-to-value ratio well below 50%
• Have a plan for market downturns
• Consider alternatives like home equity loans

*Educational information only; not financial advice.*`;
  }

  private generateLiquidityResponse(): string {
    return `**Portfolio Liquidity Options:**

**1. SBLOC (Securities-Based Line of Credit)**
• Borrow against investments without selling
• 6.5-8.5% interest rates
• Keep your investments growing
• Best for: Large expenses, avoiding capital gains

**2. Margin Trading**
• Similar to SBLOC but for active trading
• Higher risk, stricter rules
• Best for: Experienced traders only

**3. Selling Securities**
• Immediate cash but triggers capital gains/losses
• May miss future appreciation
• Best for: One-time needs, rebalancing

**4. Emergency Fund**
• 3-6 months expenses in HYSA
• 4-5% APY, FDIC insured
• Best for: True emergencies

**5. Home Equity**
• HELOC or home equity loan
• Often lower rates than SBLOC
• Best for: Homeowners with equity

*Educational information only; not financial advice.*`;
  }

  private generateGeneralFinancialResponse(userInput: string): string {
    const input = userInput.toLowerCase();

    // Re-route comparative questions
    if (
      input.includes('would you rather') ||
      input.includes('versus') ||
      input.includes('vs') ||
      input.includes('better than') ||
      input.includes('worse than') ||
      input.includes('compared to') ||
      input.includes('worth more') ||
      input.includes('choice between')
    ) {
      return this.generateComparativeFinancialResponse(userInput);
    }

    if (input.includes('etf')) return this.generateETFResponse();
    if (input.includes('budget')) return this.generateBudgetingResponse();
    if (input.includes('debt') && (input.includes('pay') || input.includes('payoff') || input.includes('eliminate')))
      return this.generateDebtPayoffResponse();
    if (input.includes('emergency fund')) return this.generateEmergencyFundResponse();
    if (input.includes('credit score') || input.includes('credit card')) return this.generateCreditResponse();
    if (input.includes('retirement')) return this.generateRetirementResponse();
    if (input.includes('sbloc') || input.includes('securities based line of credit') || input.includes('portfolio lending'))
      return this.generateSBLOCResponse();
    if (input.includes('liquidity') || input.includes('borrow against portfolio') || input.includes('borrowing power'))
      return this.generateLiquidityResponse();
    if (/(dca|dollar cost averaging)/.test(input))
      return `**DCA:** invest a fixed amount on a schedule; reduces timing risk and builds habit. Lump sum often wins statistically, but DCA feels safer.`;
    if (/(options?)/.test(input))
      return `**Options basics:** Calls = right to buy; Puts = right to sell. Know strike, expiration, premium, and time decay. Start with paper trading.`;
    if (/(market cap)/.test(input))
      return `**Market cap:** price × shares. Large-cap = stable; small-cap = higher risk/higher potential. Diversify across sizes.`;
    if (/(p\/?e|pe ratio|price to earnings)/.test(input))
      return `**P/E ratio:** price ÷ earnings per share. Compare within an industry; know limitations.`;
    if (/(dividend)/.test(input))
      return `**Dividends:** company profit paid to shareholders; mind yield, payout ratio, and dividend growth. Not guaranteed.`;
    if (/(volatility|beta)/.test(input))
      return `**Volatility & beta:** higher = bigger swings (risk). Manage with diversification and allocation; keep long-term view.`;

    // Default gentle prompt
    return `I can help with saving, budgeting, credit, debt, investing, retirement, and portfolio lending.  
Ask me: "How much should I save from my paycheck?", "Roth vs Traditional IRA?", "Should I buy ___?", or "What is SBLOC?"`;
  }
}

export default FinancialChatbotService;