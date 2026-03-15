/**
 * Mock Apollo Client for Demo Mode
 *
 * Creates an Apollo client whose InMemoryCache is pre-seeded with all demo
 * data. Every useQuery call resolves instantly from cache — no network needed.
 *
 * Approach: ApolloClient with a terminating ApolloLink that returns mock data
 * for every operation, plus a pre-seeded InMemoryCache as a fast-path fallback.
 */

import { ApolloClient, InMemoryCache, ApolloLink, Observable, gql } from '@apollo/client';
import {
  DEMO_ME,
  DEMO_GQL_PORTFOLIO_METRICS,
  DEMO_MY_PORTFOLIOS,
  DEMO_PORTFOLIO_RISK_REPORT,
  DEMO_AI_RECOMMENDATIONS,
  DEMO_TRADE_DEBRIEF,
  DEMO_DAY_TRADING_PICKS,
  DEMO_MARKET_DATA,
  DEMO_SECTOR_DATA,
  DEMO_VOLATILITY_DATA,
  DEMO_PERFORMANCE_METRICS,
  DEMO_RECENT_TRADES,
  DEMO_MARKET_NEWS,
  DEMO_SENTIMENT_INDICATORS,
  DEMO_RAHA_SIGNALS,
  DEMO_RAHA_METRICS,
  DEMO_STOCKS,
  DEMO_QUANT_SCREENER,
  DEMO_BUDGET_DATA,
  DEMO_SPENDING_ANALYSIS,
  DEMO_TRANSPARENCY_DASHBOARD,
  DEMO_TRANSPARENCY_PERFORMANCE,
  DEMO_ORACLE_INSIGHTS,
  DEMO_FINANCIAL_LEAKS,
  DEMO_WEALTH_ARRIVAL,
  DEMO_NET_WORTH_HISTORY,
  DEMO_FINANCIAL_HEALTH,
  DEMO_INCOME_INTELLIGENCE,
  DEMO_LIFE_DECISION,
  DEMO_REALLOCATION_STRATEGIES,
  DEMO_BUILD_PORTFOLIO,
  DEMO_QUIZ_QUESTIONS,
  DEMO_INVESTOR_PROFILE,
  DEMO_NEXT_BEST_ACTIONS,
  DEMO_LEAK_REDIRECT,
  DEMO_WEEKLY_DIGEST,
  DEMO_IDENTITY_GAPS,
} from '../services/demoMockData';

// Build swing signals with full GetSwingSignals schema (triggeredAt, signalType, stopPrice, etc.)
// so Apollo cache never sees missing fields. Inlined here so demo mode always returns correct shape.
function getMockSwingSignals(): Record<string, unknown>[] {
  const now = Date.now();
  const createdBy = { id: 'demo-1', username: 'system', name: 'AI Signals', __typename: 'User' as const };
  const techList = (obj: Record<string, number | string>) =>
    Object.entries(obj).map(([name, value]) => ({
      name: name.toUpperCase(),
      value: typeof value === 'number' ? value : 0,
      signal: typeof value === 'string' ? value : 'neutral',
      strength: 'medium',
      description: `${name}: ${value}`,
      __typename: 'TechnicalIndicator' as const,
    }));
  const patternList = (names: string[], tf: string) =>
    names.map(name => ({
      name,
      confidence: 0.85,
      signal: 'bullish',
      description: `Pattern: ${name.replace(/_/g, ' ')}`,
      timeframe: tf,
      __typename: 'PatternRecognition' as const,
    }));
  return [
    {
      id: 'sig-1',
      symbol: 'MSFT',
      companyName: 'Microsoft Corporation',
      timeframe: '2-4 weeks',
      triggeredAt: new Date(now - 2 * 86400000).toISOString(),
      signalType: 'LONG',
      entryPrice: 415,
      stopPrice: 398,
      targetPrice: 455,
      mlScore: 0.87,
      thesis: 'Azure growth re-acceleration; AI Copilot uptake stronger than expected. Technical: consolidation above 20-week MA with rising volume.',
      riskRewardRatio: 2.35,
      daysSinceTriggered: 2,
      isLikedByUser: false,
      userLikeCount: 142,
      features: {},
      isActive: true,
      isValidated: true,
      validationPrice: 416.5,
      validationTimestamp: new Date(now - 86400000).toISOString(),
      createdBy,
      technicalIndicators: techList({ rsi: 58, macd: 'bullish_cross', bb_position: 'mid', adx: 32 }),
      patterns: patternList(['ascending_triangle', 'volume_accumulation'], '2-4 weeks'),
      __typename: 'SwingSignal' as const,
    },
    {
      id: 'sig-2',
      symbol: 'JPM',
      companyName: 'JPMorgan Chase',
      timeframe: '3-6 weeks',
      triggeredAt: new Date(now - 3 * 86400000).toISOString(),
      signalType: 'LONG',
      entryPrice: 198.5,
      stopPrice: 190,
      targetPrice: 218,
      mlScore: 0.81,
      thesis: 'Net interest income still expanding; credit quality holding. Trading below historical P/B with 2.8% dividend yield as cushion.',
      riskRewardRatio: 2.24,
      daysSinceTriggered: 3,
      isLikedByUser: false,
      userLikeCount: 98,
      features: {},
      isActive: true,
      isValidated: true,
      validationPrice: 199.2,
      validationTimestamp: new Date(now - 2 * 86400000).toISOString(),
      createdBy,
      technicalIndicators: techList({ rsi: 52, macd: 'positive', bb_position: 'lower_mid', adx: 28 }),
      patterns: patternList(['bull_flag', 'support_hold'], '3-6 weeks'),
      __typename: 'SwingSignal' as const,
    },
    {
      id: 'sig-3',
      symbol: 'LLY',
      companyName: 'Eli Lilly',
      timeframe: '4-8 weeks',
      triggeredAt: new Date(now - 5 * 86400000).toISOString(),
      signalType: 'LONG',
      entryPrice: 780,
      stopPrice: 748,
      targetPrice: 850,
      mlScore: 0.79,
      thesis: 'GLP-1 demand continues to outpace supply. Pipeline optionality in Alzheimer\'s space. Defensive growth in uncertain macro.',
      riskRewardRatio: 2.19,
      daysSinceTriggered: 5,
      isLikedByUser: false,
      userLikeCount: 203,
      features: {},
      isActive: true,
      isValidated: true,
      validationPrice: 782,
      validationTimestamp: new Date(now - 4 * 86400000).toISOString(),
      createdBy,
      technicalIndicators: techList({ rsi: 61, macd: 'bullish', bb_position: 'upper_mid', adx: 38 }),
      patterns: patternList(['cup_and_handle', 'breakout_pending'], '4-8 weeks'),
      __typename: 'SwingSignal' as const,
    },
  ];
}

// ─── Operation → mock data map ────────────────────────────────────────────────
// Keys match operationName from the client query.
const MOCK_RESPONSES: Record<string, Record<string, unknown>> = {
  // Auth / User
  GetMe:          { me: DEMO_ME },
  Me:             { me: DEMO_ME },
  GetUserProfile: { me: DEMO_ME },  // AIPortfolioScreen uses this operation name

  // Portfolio
  GetPortfolioMetrics:   { portfolioMetrics: DEMO_GQL_PORTFOLIO_METRICS },
  GetMyPortfolios:       { myPortfolios: DEMO_MY_PORTFOLIOS },
  MyPortfolios:          { myPortfolios: DEMO_MY_PORTFOLIOS },
  GetPortfolioRiskReport: { portfolioRiskReport: DEMO_PORTFOLIO_RISK_REPORT },

  // Active Repairs (options repair workflow)
  GetPortfolioWithRepairs: {
    portfolio: {
      totalDelta: 0.12,
      totalGamma: 0.02,
      totalTheta: 45,
      totalVega: 120,
      portfolioHealthStatus: 'healthy',
      repairsAvailable: 0,
      totalMaxLoss: 8500,
      __typename: 'Portfolio',
    },
    positions: [
      {
        id: 'pos-demo-1',
        ticker: 'AAPL',
        strategyType: 'Covered Call',
        entryPrice: 178.5,
        currentPrice: 182.2,
        quantity: 100,
        unrealizedPnl: 370,
        daysToExpiration: 42,
        expirationDate: new Date(Date.now() + 42 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        greeks: { delta: 0.35, gamma: 0.02, theta: -0.8, vega: 12, rho: 0.1 },
        maxLoss: 4200,
        probabilityOfProfit: 0.72,
        status: 'open',
        __typename: 'Position',
      },
    ],
    repair_plans: [],
  },

  PortfolioKellyMetrics: {
    portfolioKellyMetrics: {
      totalPortfolioValue: 14303.52,
      aggregateKellyFraction: 0.22,
      aggregateRecommendedFraction: 0.11,
      portfolioMaxDrawdownRisk: 0.082,
      weightedWinRate: 0.68,
      positionCount: 5,
      totalPositions: 5,
      __typename: 'PortfolioKellyMetrics',
    },
  },

  // Benchmark series (SPY, QQQ, etc.) — used by PortfolioPerformanceCardWithBenchmark, PortfolioComparison
  GetBenchmarkSeries: (() => {
    const now = Date.now();
    let val = 500;
    const dataPoints = Array.from({ length: 30 }, (_, i) => {
      const ts = new Date(now - (29 - i) * 24 * 60 * 60 * 1000).toISOString();
      const prev = val;
      val = parseFloat((val * (1 + (Math.random() - 0.48) * 0.02)).toFixed(2));
      const change = val - prev;
      const changePercent = prev ? (change / prev) * 100 : 0;
      return { timestamp: ts, value: val, change, changePercent };
    });
    const startValue = dataPoints[0]?.value ?? 500;
    const endValue = dataPoints[dataPoints.length - 1]?.value ?? val;
    const totalReturn = endValue - startValue;
    const totalReturnPercent = startValue ? (totalReturn / startValue) * 100 : 0;
    return {
      benchmarkSeries: {
        symbol: 'SPY',
        name: 'S&P 500',
        timeframe: '1D',
        dataPoints,
        startValue,
        endValue,
        totalReturn,
        totalReturnPercent,
        volatility: 0.12,
        __typename: 'BenchmarkSeriesType',
      },
    };
  })(),

  // Portfolio history (time series for portfolio value chart)
  GetPortfolioHistory: (() => {
    const now = Date.now();
    let v = 12158;
    const portfolioHistory = Array.from({ length: 90 }, (_, i) => {
      const date = new Date(now - (89 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      const prev = v;
      v = parseFloat((v * (1 + (Math.random() - 0.48) * 0.015)).toFixed(2));
      const change = v - prev;
      const changePercent = prev ? (change / prev) * 100 : 0;
      return { date, value: v, change, changePercent, __typename: 'PortfolioHistoryPoint' };
    });
    return { portfolioHistory };
  })(),

  // Stock Chart Data (demo: generate candles so Price & P&L chart renders)
  GetStockChartData: (() => {
    const points = 30;
    const candles: Array<{ timestamp: string; open: number; high: number; low: number; close: number; volume: number }> = [];
    let price = 780;
    const now = Date.now();
    for (let i = points - 1; i >= 0; i--) {
      const ts = new Date(now - i * 24 * 60 * 60 * 1000).toISOString();
      const open = price + (Math.random() - 0.48) * 12;
      const close = open + (Math.random() - 0.46) * 18;
      const high = Math.max(open, close) + Math.random() * 8;
      const low = Math.min(open, close) - Math.random() * 8;
      price = close;
      candles.push({
        timestamp: ts,
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: Math.floor(30000000 + Math.random() * 20000000),
      });
    }
    return {
      stockChartData: {
        symbol: 'NVDA',
        currentPrice: 875.40,
        change: 36.18,
        changePercent: 4.31,
        __typename: 'StockChartDataType',
        data: candles,
      },
    };
  })(),
  GetAdvancedChartData: (() => {
    // Generate 30 days of realistic NVDA-like OHLCV candles
    const candles = [];
    let price = 780;
    const now = Date.now();
    for (let i = 29; i >= 0; i--) {
      const ts = new Date(now - i * 24 * 60 * 60 * 1000).toISOString();
      const open = price + (Math.random() - 0.48) * 12;
      const close = open + (Math.random() - 0.46) * 18;
      const high = Math.max(open, close) + Math.random() * 8;
      const low = Math.min(open, close) - Math.random() * 8;
      price = close;
      candles.push({
        timestamp: ts,
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: Math.floor(30000000 + Math.random() * 20000000),
        __typename: 'ChartDataPointType',
      });
    }
    return {
      stockChartData: {
        symbol: 'NVDA',
        interval: '1D',
        limit: 30,
        currentPrice: 875.40,
        change: 36.18,
        changePercent: 4.31,
        __typename: 'StockChartDataType',
        data: candles,
        indicators: {
          SMA20: 842.10,
          SMA50: 810.55,
          EMA12: 858.30,
          EMA26: 835.70,
          BBUpper: 910.20,
          BBMiddle: 842.10,
          BBLower: 774.00,
          RSI14: 61.4,
          MACD: 22.6,
          MACDSignal: 18.1,
          MACDHist: 4.5,
          __typename: 'IndicatorsType',
        },
      },
    };
  })(),

  // AI
  GetAIRecommendations:  { aiRecommendations: DEMO_AI_RECOMMENDATIONS },
  GetQuantScreener:      { advancedStockScreening: DEMO_QUANT_SCREENER },

  // AI stock recommendations (profile-based) — shape: aiRecommendations { buyRecommendations, spendingInsights }
  GetAIStockRecommendations: (() => {
    const buy = DEMO_AI_RECOMMENDATIONS.buyRecommendations.slice(0, 3).map((r: Record<string, unknown>) => ({
      symbol: r.symbol,
      companyName: r.companyName,
      recommendation: r.recommendation,
      confidence: r.confidence,
      reasoning: r.reasoning,
      targetPrice: r.targetPrice,
      currentPrice: r.currentPrice,
      expectedReturn: r.expectedReturn,
      spendingGrowth: r.spendingGrowth ?? null,
      __typename: 'StockRecommendation',
    }));
    return {
      aiRecommendations: {
        buyRecommendations: buy,
        spendingInsights: {
          discretionaryIncome: 1850,
          suggestedBudget: 400,
          spendingHealth: 'good',
          topCategories: ['Technology', 'Travel', 'Dining'],
          sectorPreferences: ['Technology', 'Healthcare'],
          __typename: 'SpendingInsightsType',
        },
        __typename: 'AIRecommendationsType',
      },
    };
  })(),

  // Advanced stock screening (search/filters) — full screener shape with volatility, debtRatio, reasoning
  GetAdvancedStockScreening: (() => {
    const base = DEMO_QUANT_SCREENER as Array<Record<string, unknown>>;
    return {
      advancedStockScreening: base.map((r, i) => ({
        ...r,
        volatility: 0.18 + (i * 0.02),
        debtRatio: 0.12 + (i * 0.05),
        reasoning: `Strong ${r.sector} name with score ${r.score}; ML score ${r.mlScore}.`,
        __typename: 'ScreenerResult',
      })),
    };
  })(),

  // ML stock screening (same root field, subset of fields)
  GetMLStockScreening: { advancedStockScreening: DEMO_QUANT_SCREENER },

  // Alpaca brokerage account (demo: not linked)
  GetAlpacaAccount: {
    alpacaAccount: {
      id: 0,
      status: 'NOT_LINKED',
      alpacaAccountId: null,
      approvedAt: null,
      buyingPower: 0,
      cash: 0,
      portfolioValue: 0,
      createdAt: null,
      __typename: 'AlpacaAccountType',
    },
  },

  // Security Fortress / Zero Trust
  ZeroTrustSummary: {
    zeroTrustSummary: {
      userId: 'demo-user-1',
      devices: 2,
      averageTrustScore: 85,
      lastVerification: new Date().toISOString(),
      requiresMfa: true,
      riskLevel: 'LOW',
      __typename: 'ZeroTrustSummaryType',
    },
  },
  SecurityInsights: {
    securityScore: {
      id: 'demo-score-1',
      score: 85,
      factors: ['MFA enabled', 'Device trust verified', 'No recent threats'],
      calculatedAt: new Date().toISOString(),
      __typename: 'SecurityScoreType',
    },
    zeroTrustSummary: {
      averageTrustScore: 85,
      riskLevel: 'LOW',
      requiresMfa: true,
      __typename: 'ZeroTrustSummaryType',
    },
    securityEvents: [
      {
        id: 'evt-1',
        eventType: 'LOGIN',
        threatLevel: 'LOW',
        description: 'Successful login from trusted device',
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        __typename: 'SecurityEventType',
      },
    ],
  },
  SecurityScore: {
    securityScore: {
      id: 'demo-score-1',
      score: 85,
      factors: ['MFA enabled', 'Device trust verified'],
      calculatedAt: new Date().toISOString(),
      __typename: 'SecurityScoreType',
    },
  },
  SecurityEvents: {
    securityEvents: [
      {
        id: 'evt-1',
        eventType: 'LOGIN',
        threatLevel: 'LOW',
        description: 'Successful login from trusted device',
        metadata: null,
        resolved: true,
        resolvedAt: new Date().toISOString(),
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        __typename: 'SecurityEventType',
      },
    ],
  },

  // Trade Debrief
  GetTradeDebrief:       { tradeDebrief: DEMO_TRADE_DEBRIEF },

  // Day Trading
  GetDayTradingPicks:    { dayTradingPicks: DEMO_DAY_TRADING_PICKS },
  GetExecutionSuggestion: {
    executionSuggestion: {
      orderType: 'LIMIT',
      priceBand: { low: 872.00, high: 878.00 },
      entryStrategy: 'Scale in — buy 50% at open, add 50% on first pullback',
      bracketLegs: { stopLoss: 850.00, target: 940.00 },
      suggestedSize: 2,
      __typename: 'ExecutionSuggestion',
    },
  },
  GetEntryTimingSuggestion: {
    entryTimingSuggestion: {
      recommendation: 'WAIT',
      waitReason: 'Pre-market gap up — let price stabilise in first 15 minutes before entering',
      pullbackTarget: 870.00,
      __typename: 'EntryTimingSuggestion',
    },
  },

  // Swing Trading (full schema inlined so cache never sees missing fields)
  GetSwingSignals:        { swingSignals: getMockSwingSignals() },
  GetMarketData:          { marketData: DEMO_MARKET_DATA },
  GetSectorData:          { sectorData: DEMO_SECTOR_DATA },
  GetVolatilityData:      { volatilityData: DEMO_VOLATILITY_DATA },
  GetPerformanceMetrics:  { performanceMetrics: DEMO_PERFORMANCE_METRICS },
  GetRecentTrades:        { recentTrades: DEMO_RECENT_TRADES },
  GetMarketNews:          { marketNews: DEMO_MARKET_NEWS },
  GetSentimentIndicators: { sentimentIndicators: DEMO_SENTIMENT_INDICATORS },

  // RAHA
  GetRAHASignals:  { rahaSignals: DEMO_RAHA_SIGNALS },
  GetRAHAMetrics:  { rahaMetrics: DEMO_RAHA_METRICS },

  // Oracle Insights (AI / Oracle)
  GetOracleInsights: { oracleInsights: DEMO_ORACLE_INSIGHTS },

  // Transparency Dashboard
  TransparencyDashboard:   { transparencyDashboard: DEMO_TRANSPARENCY_DASHBOARD },
  TransparencyPerformance: { transparencyPerformance: DEMO_TRANSPARENCY_PERFORMANCE },
  
  // RAHA Strategy Store
  GetStrategies: {
    strategies: [
      // Momentum Strategies
      {
        id: 'strat-1',
        slug: 'rsi-momentum-breakout',
        name: 'RSI Momentum Breakout',
        category: 'MOMENTUM',
        description: 'Captures strong momentum moves using RSI divergence and volume confirmation. Best suited for trending markets with clear directional bias.',
        marketType: 'STOCKS',
        timeframeSupported: ['1H', '4H', 'D'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-1', version: 1, configSchema: {}, logicRef: 'rsi_momentum_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      {
        id: 'strat-2',
        slug: 'macd-crossover-pro',
        name: 'MACD Crossover Pro',
        category: 'MOMENTUM',
        description: 'Advanced MACD strategy with histogram confirmation and trend filters. Optimized for swing trading with 2-5 day hold periods.',
        marketType: 'STOCKS',
        timeframeSupported: ['4H', 'D', 'W'],
        influencerRef: 'mark_minervini',
        enabled: true,
        defaultVersion: { id: 'v1-2', version: 2, configSchema: {}, logicRef: 'macd_crossover_v2', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      {
        id: 'strat-3',
        slug: 'volume-surge-momentum',
        name: 'Volume Surge Momentum',
        category: 'MOMENTUM',
        description: 'Identifies unusual volume spikes combined with price momentum. Designed to catch institutional accumulation patterns.',
        marketType: 'STOCKS',
        timeframeSupported: ['1H', '4H'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-3', version: 1, configSchema: {}, logicRef: 'volume_surge_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      // Reversal Strategies
      {
        id: 'strat-4',
        slug: 'mean-reversion-rsi',
        name: 'Mean Reversion RSI',
        category: 'REVERSAL',
        description: 'Identifies oversold and overbought conditions for mean reversion trades. Uses dynamic support/resistance levels.',
        marketType: 'STOCKS',
        timeframeSupported: ['15M', '1H', '4H'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-4', version: 1, configSchema: {}, logicRef: 'mean_reversion_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      {
        id: 'strat-5',
        slug: 'bollinger-squeeze-reversal',
        name: 'Bollinger Squeeze Reversal',
        category: 'REVERSAL',
        description: 'Captures volatility expansion after Bollinger Band squeeze. Identifies high-probability reversal points with tight risk management.',
        marketType: 'STOCKS',
        timeframeSupported: ['1H', '4H', 'D'],
        influencerRef: 'john_bollinger',
        enabled: true,
        defaultVersion: { id: 'v1-5', version: 1, configSchema: {}, logicRef: 'bb_squeeze_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      // Futures Strategies
      {
        id: 'strat-6',
        slug: 'es-trend-following',
        name: 'ES Trend Following',
        category: 'MOMENTUM',
        description: 'Trend-following strategy optimized for E-mini S&P 500 futures. Uses multiple timeframe analysis for high-probability entries.',
        marketType: 'FUTURES',
        timeframeSupported: ['5M', '15M', '1H'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-6', version: 1, configSchema: {}, logicRef: 'es_trend_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      {
        id: 'strat-7',
        slug: 'nq-scalper',
        name: 'NQ Scalper',
        category: 'MOMENTUM',
        description: 'Fast-paced scalping strategy for Nasdaq futures. Targets quick moves with tight stops during high-volatility sessions.',
        marketType: 'FUTURES',
        timeframeSupported: ['1M', '5M', '15M'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-7', version: 1, configSchema: {}, logicRef: 'nq_scalp_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      // Forex Strategies
      {
        id: 'strat-8',
        slug: 'eurusd-session-breakout',
        name: 'EUR/USD Session Breakout',
        category: 'MOMENTUM',
        description: 'Trades breakouts during London and New York session overlaps. Optimized for EUR/USD with dynamic position sizing.',
        marketType: 'FOREX',
        timeframeSupported: ['15M', '1H'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-8', version: 1, configSchema: {}, logicRef: 'eurusd_breakout_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      {
        id: 'strat-9',
        slug: 'gbpjpy-reversal',
        name: 'GBP/JPY Reversal Hunter',
        category: 'REVERSAL',
        description: 'Targets reversals in volatile GBP/JPY pair using pivot points and momentum divergence. Best during Asian session.',
        marketType: 'FOREX',
        timeframeSupported: ['1H', '4H'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-9', version: 1, configSchema: {}, logicRef: 'gbpjpy_reversal_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      // Crypto Strategies
      {
        id: 'strat-10',
        slug: 'btc-trend-rider',
        name: 'BTC Trend Rider',
        category: 'MOMENTUM',
        description: 'Rides Bitcoin trends using EMA crossovers and volume analysis. Designed for swing trading with 1-2 week hold periods.',
        marketType: 'CRYPTO',
        timeframeSupported: ['4H', 'D', 'W'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-10', version: 1, configSchema: {}, logicRef: 'btc_trend_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      {
        id: 'strat-11',
        slug: 'eth-mean-reversion',
        name: 'ETH Mean Reversion',
        category: 'REVERSAL',
        description: 'Identifies oversold conditions in Ethereum using on-chain metrics and technical indicators. Targets 5-10% reversals.',
        marketType: 'CRYPTO',
        timeframeSupported: ['1H', '4H', 'D'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-11', version: 1, configSchema: {}, logicRef: 'eth_reversion_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
      {
        id: 'strat-12',
        slug: 'altcoin-momentum',
        name: 'Altcoin Momentum Scanner',
        category: 'MOMENTUM',
        description: 'Scans top altcoins for momentum breakouts. Uses relative strength vs BTC and volume confirmation for entry timing.',
        marketType: 'CRYPTO',
        timeframeSupported: ['1H', '4H'],
        influencerRef: null,
        enabled: true,
        defaultVersion: { id: 'v1-12', version: 1, configSchema: {}, logicRef: 'altcoin_momentum_v1', __typename: 'StrategyVersion' },
        __typename: 'Strategy',
      },
    ],
  },
  GetUserStrategySettings: {
    userStrategySettings: [
      {
        id: 'uss-1',
        strategyVersion: {
          id: 'v1-1',
          version: 1,
          strategy: { id: 'strat-1', name: 'RSI Momentum Breakout', slug: 'rsi-momentum-breakout', category: 'MOMENTUM', __typename: 'Strategy' },
          __typename: 'StrategyVersion',
        },
        parameters: {},
        enabled: true,
        autoTradeEnabled: false,
        maxDailyLossPercent: 2.0,
        maxConcurrentPositions: 3,
        createdAt: new Date(Date.now() - 7 * 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
        __typename: 'UserStrategySettings',
      },
      {
        id: 'uss-2',
        strategyVersion: {
          id: 'v1-10',
          version: 1,
          strategy: { id: 'strat-10', name: 'BTC Trend Rider', slug: 'btc-trend-rider', category: 'MOMENTUM', __typename: 'Strategy' },
          __typename: 'StrategyVersion',
        },
        parameters: {},
        enabled: true,
        autoTradeEnabled: true,
        maxDailyLossPercent: 3.0,
        maxConcurrentPositions: 2,
        createdAt: new Date(Date.now() - 14 * 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 2 * 86400000).toISOString(),
        __typename: 'UserStrategySettings',
      },
    ],
  },
  GetUserBacktests: (() => {
    const now = Date.now();
    
    // Generate equity curve helper
    const generateEquityCurve = (startEquity: number, totalReturn: number, days: number, volatility: number) => {
      const curve = [];
      let equity = startEquity;
      const dailyReturn = Math.pow(1 + totalReturn, 1 / days) - 1;
      
      for (let i = 0; i < days; i++) {
        const timestamp = new Date(now - (days - i) * 86400000).toISOString();
        const randomFactor = 1 + (Math.random() - 0.5) * volatility;
        equity = equity * (1 + dailyReturn) * randomFactor;
        curve.push({ timestamp, equity: parseFloat(equity.toFixed(2)), __typename: 'EquityPoint' });
      }
      return curve;
    };

    return {
      userBacktests: [
        {
          id: 'bt-1',
          symbol: 'AAPL',
          timeframe: '4H',
          startDate: new Date(now - 90 * 86400000).toISOString().split('T')[0],
          endDate: new Date(now - 1 * 86400000).toISOString().split('T')[0],
          status: 'COMPLETED',
          parameters: { rsiPeriod: 14, rsiOverbought: 70, rsiOversold: 30 },
          metrics: {
            winRate: 0.68,
            sharpeRatio: 1.85,
            maxDrawdown: -0.12,
            expectancy: 1.42,
            totalTrades: 47,
            winningTrades: 32,
            losingTrades: 15,
            avgWin: 245.80,
            avgLoss: 142.30,
            profitFactor: 2.31,
            __typename: 'BacktestMetrics',
          },
          equityCurve: generateEquityCurve(10000, 0.28, 90, 0.02),
          tradeLog: [],
          createdAt: new Date(now - 2 * 86400000).toISOString(),
          completedAt: new Date(now - 2 * 86400000 + 180000).toISOString(),
          strategyVersion: {
            id: 'v1-1',
            strategy: { id: 'strat-1', name: 'RSI Momentum Breakout', __typename: 'Strategy' },
            __typename: 'StrategyVersion',
          },
          __typename: 'BacktestRun',
        },
        {
          id: 'bt-2',
          symbol: 'MSFT',
          timeframe: 'D',
          startDate: new Date(now - 180 * 86400000).toISOString().split('T')[0],
          endDate: new Date(now - 5 * 86400000).toISOString().split('T')[0],
          status: 'COMPLETED',
          parameters: { macdFast: 12, macdSlow: 26, macdSignal: 9 },
          metrics: {
            winRate: 0.62,
            sharpeRatio: 1.52,
            maxDrawdown: -0.18,
            expectancy: 1.15,
            totalTrades: 28,
            winningTrades: 17,
            losingTrades: 11,
            avgWin: 412.50,
            avgLoss: 198.40,
            profitFactor: 1.92,
            __typename: 'BacktestMetrics',
          },
          equityCurve: generateEquityCurve(10000, 0.22, 175, 0.025),
          tradeLog: [],
          createdAt: new Date(now - 7 * 86400000).toISOString(),
          completedAt: new Date(now - 7 * 86400000 + 240000).toISOString(),
          strategyVersion: {
            id: 'v1-2',
            strategy: { id: 'strat-2', name: 'MACD Crossover Pro', __typename: 'Strategy' },
            __typename: 'StrategyVersion',
          },
          __typename: 'BacktestRun',
        },
        {
          id: 'bt-3',
          symbol: 'NVDA',
          timeframe: '1H',
          startDate: new Date(now - 60 * 86400000).toISOString().split('T')[0],
          endDate: new Date(now - 3 * 86400000).toISOString().split('T')[0],
          status: 'COMPLETED',
          parameters: { volumeMultiplier: 1.5, lookbackPeriod: 20 },
          metrics: {
            winRate: 0.71,
            sharpeRatio: 2.12,
            maxDrawdown: -0.09,
            expectancy: 1.78,
            totalTrades: 63,
            winningTrades: 45,
            losingTrades: 18,
            avgWin: 186.20,
            avgLoss: 124.80,
            profitFactor: 2.65,
            __typename: 'BacktestMetrics',
          },
          equityCurve: generateEquityCurve(10000, 0.35, 57, 0.03),
          tradeLog: [],
          createdAt: new Date(now - 4 * 86400000).toISOString(),
          completedAt: new Date(now - 4 * 86400000 + 120000).toISOString(),
          strategyVersion: {
            id: 'v1-3',
            strategy: { id: 'strat-3', name: 'Volume Surge Momentum', __typename: 'Strategy' },
            __typename: 'StrategyVersion',
          },
          __typename: 'BacktestRun',
        },
        {
          id: 'bt-4',
          symbol: 'BTC/USD',
          timeframe: '4H',
          startDate: new Date(now - 120 * 86400000).toISOString().split('T')[0],
          endDate: new Date(now - 10 * 86400000).toISOString().split('T')[0],
          status: 'COMPLETED',
          parameters: { emaPeriod: 21, trendFilter: true },
          metrics: {
            winRate: 0.58,
            sharpeRatio: 1.34,
            maxDrawdown: -0.24,
            expectancy: 0.92,
            totalTrades: 38,
            winningTrades: 22,
            losingTrades: 16,
            avgWin: 520.40,
            avgLoss: 285.60,
            profitFactor: 1.68,
            __typename: 'BacktestMetrics',
          },
          equityCurve: generateEquityCurve(10000, 0.18, 110, 0.04),
          tradeLog: [],
          createdAt: new Date(now - 12 * 86400000).toISOString(),
          completedAt: new Date(now - 12 * 86400000 + 300000).toISOString(),
          strategyVersion: {
            id: 'v1-10',
            strategy: { id: 'strat-10', name: 'BTC Trend Rider', __typename: 'Strategy' },
            __typename: 'StrategyVersion',
          },
          __typename: 'BacktestRun',
        },
        {
          id: 'bt-5',
          symbol: 'SPY',
          timeframe: 'D',
          startDate: new Date(now - 365 * 86400000).toISOString().split('T')[0],
          endDate: new Date(now - 15 * 86400000).toISOString().split('T')[0],
          status: 'COMPLETED',
          parameters: { bbPeriod: 20, bbStdDev: 2, squeezeThreshold: 0.05 },
          metrics: {
            winRate: 0.65,
            sharpeRatio: 1.68,
            maxDrawdown: -0.15,
            expectancy: 1.28,
            totalTrades: 52,
            winningTrades: 34,
            losingTrades: 18,
            avgWin: 328.90,
            avgLoss: 178.50,
            profitFactor: 2.18,
            __typename: 'BacktestMetrics',
          },
          equityCurve: generateEquityCurve(10000, 0.42, 350, 0.015),
          tradeLog: [],
          createdAt: new Date(now - 20 * 86400000).toISOString(),
          completedAt: new Date(now - 20 * 86400000 + 600000).toISOString(),
          strategyVersion: {
            id: 'v1-5',
            strategy: { id: 'strat-5', name: 'Bollinger Squeeze Reversal', __typename: 'Strategy' },
            __typename: 'StrategyVersion',
          },
          __typename: 'BacktestRun',
        },
      ],
    };
  })(),
  
  // Single backtest detail (used when clicking on a backtest card)
  GetBacktestRun: (() => {
    const now = Date.now();
    const generateEquityCurve = (startEquity: number, totalReturn: number, days: number, volatility: number) => {
      const curve = [];
      let equity = startEquity;
      const dailyReturn = Math.pow(1 + totalReturn, 1 / days) - 1;
      for (let i = 0; i < days; i++) {
        const timestamp = new Date(now - (days - i) * 86400000).toISOString();
        const randomFactor = 1 + (Math.random() - 0.5) * volatility;
        equity = equity * (1 + dailyReturn) * randomFactor;
        curve.push({ timestamp, equity: parseFloat(equity.toFixed(2)), __typename: 'EquityPoint' });
      }
      return curve;
    };
    return {
      backtestRun: {
        id: 'bt-1',
        symbol: 'AAPL',
        timeframe: '4H',
        startDate: new Date(now - 90 * 86400000).toISOString().split('T')[0],
        endDate: new Date(now - 1 * 86400000).toISOString().split('T')[0],
        status: 'COMPLETED',
        parameters: { rsiPeriod: 14, rsiOverbought: 70, rsiOversold: 30 },
        metrics: {
          winRate: 0.68,
          sharpeRatio: 1.85,
          maxDrawdown: -0.12,
          expectancy: 1.42,
          totalTrades: 47,
          winningTrades: 32,
          losingTrades: 15,
          avgWin: 245.80,
          avgLoss: 142.30,
          profitFactor: 2.31,
          __typename: 'BacktestMetrics',
        },
        equityCurve: generateEquityCurve(10000, 0.28, 90, 0.02),
        tradeLog: [],
        createdAt: new Date(now - 2 * 86400000).toISOString(),
        completedAt: new Date(now - 2 * 86400000 + 180000).toISOString(),
        strategyVersion: {
          id: 'v1-1',
          strategy: { id: 'strat-1', name: 'RSI Momentum Breakout', __typename: 'Strategy' },
          __typename: 'StrategyVersion',
        },
        __typename: 'BacktestRun',
      },
    };
  })(),

  // Single strategy detail (used when clicking on a strategy card)
  GetStrategy: {
    strategy: {
      id: 'strat-1',
      slug: 'rsi-momentum-breakout',
      name: 'RSI Momentum Breakout',
      category: 'MOMENTUM',
      description: 'Captures strong momentum moves using RSI divergence and volume confirmation. Best suited for trending markets with clear directional bias. This strategy identifies overbought and oversold conditions combined with price action confirmation to enter high-probability trades.',
      marketType: 'STOCKS',
      timeframeSupported: ['1H', '4H', 'D'],
      influencerRef: null,
      enabled: true,
      versions: [
        {
          id: 'v1-1',
          version: 1,
          configSchema: {
            rsiPeriod: { type: 'number', default: 14, min: 5, max: 30 },
            rsiOverbought: { type: 'number', default: 70, min: 60, max: 90 },
            rsiOversold: { type: 'number', default: 30, min: 10, max: 40 },
            volumeMultiplier: { type: 'number', default: 1.5, min: 1.0, max: 3.0 },
          },
          logicRef: 'rsi_momentum_v1',
          isDefault: true,
          createdAt: new Date(Date.now() - 90 * 86400000).toISOString(),
          __typename: 'StrategyVersion',
        },
      ],
      __typename: 'Strategy',
    },
  },

  // Stocks
  Stocks:          { stocks: DEMO_STOCKS },
  MyWatchlist:     { myWatchlist: [] },

  // ── Options Intelligence (StockScreen "Options" tab) ─────────────────────────

  // OneTapTrades — "Do This Exact Trade" card in OneTapTradeButton
  GetOneTapTrades: {
    oneTapTrades: [
      {
        symbol: 'AAPL',
        strategy: 'Bull Call Spread',
        strategyType: 'DEBIT_SPREAD',
        entryPrice: 189.30,
        expectedEdge: 18,
        confidence: 82,
        takeProfit: 205.00,
        stopLoss: 182.00,
        reasoning: 'Strong momentum into earnings with IV rank at 42%. Defined-risk structure limits downside while capturing upside to resistance at $205.',
        maxLoss: 210.00,
        maxProfit: 540.00,
        probabilityOfProfit: 0.64,
        daysToExpiration: 21,
        totalCost: 210.00,
        totalCredit: 0,
        legs: [
          { action: 'BUY', optionType: 'CALL', strike: 190, expiration: '2026-04-18', quantity: 1, premium: 4.20, __typename: 'OneTapLegType' },
          { action: 'SELL', optionType: 'CALL', strike: 195, expiration: '2026-04-18', quantity: 1, premium: 2.10, __typename: 'OneTapLegType' },
        ],
        __typename: 'OneTapTradeType',
      },
    ],
  },

  // Options chain analysis — OptionChainCard, Premium Analytics Options tab
  // Include contracts for the first expiration (2026-03-21) + premium fields (marketSentiment, recommendedStrategies)
  GetOptionsAnalysis: {
    optionsAnalysis: {
      underlyingSymbol: 'AAPL',
      underlyingPrice: 189.30,
      __typename: 'OptionsAnalysisType',
      marketSentiment: {
        sentiment: 'BULLISH',
        sentimentDescription: 'Call volume and open interest favor upside; put/call ratio below 1.',
        __typename: 'MarketSentimentType',
      },
      putCallRatio: 0.82,
      impliedVolatilityRank: 42,
      skew: -0.04,
      sentimentScore: 68,
      sentimentDescription: 'Moderately bullish — call volume elevated relative to puts.',
      unusualFlow: {
        symbol: 'AAPL',
        totalVolume: 52000000,
        unusualVolume: 12400000,
        unusualVolumePercent: 24,
        sweepTrades: 8,
        blockTrades: 3,
        lastUpdated: new Date().toISOString(),
        __typename: 'UnusualFlowType',
      },
      recommendedStrategies: [
        {
          strategyName: 'Bull Call Spread',
          strategyType: 'DEBIT_SPREAD',
          description: 'Buy 190C, sell 195C — defined risk with upside to resistance.',
          riskLevel: 'MODERATE',
          marketOutlook: 'BULLISH',
          maxProfit: 540,
          maxLoss: 210,
          breakevenPoints: [192.1],
          probabilityOfProfit: 0.64,
          riskRewardRatio: 2.57,
          daysToExpiration: 21,
          totalCost: 210,
          totalCredit: 0,
          __typename: 'RecommendedStrategyType',
        },
        {
          strategyName: 'Cash-Secured Put',
          strategyType: 'INCOME',
          description: 'Sell 185P to collect premium; acquire shares at discount if assigned.',
          riskLevel: 'LOW',
          marketOutlook: 'NEUTRAL',
          maxProfit: 220,
          maxLoss: 18280,
          breakevenPoints: [182.8],
          probabilityOfProfit: 0.72,
          riskRewardRatio: 0.01,
          daysToExpiration: 14,
          totalCost: 0,
          totalCredit: 220,
          __typename: 'RecommendedStrategyType',
        },
      ],
      optionsChain: {
        __typename: 'OptionsChainType',
        expirationDates: ['2026-03-21', '2026-04-18', '2026-05-16'],
        calls: [
          { strike: 185, bid: 6.20, ask: 6.35, volume: 15200, expirationDate: '2026-03-21', delta: 0.68, gamma: 0.032, theta: -0.12, vega: 0.14, impliedVolatility: 0.30, __typename: 'OptionContractType' },
          { strike: 190, bid: 4.10, ask: 4.25, volume: 31200, expirationDate: '2026-03-21', delta: 0.52, gamma: 0.035, theta: -0.11, vega: 0.16, impliedVolatility: 0.28, __typename: 'OptionContractType' },
          { strike: 195, bid: 2.55, ask: 2.70, volume: 22100, expirationDate: '2026-03-21', delta: 0.38, gamma: 0.033, theta: -0.10, vega: 0.15, impliedVolatility: 0.26, __typename: 'OptionContractType' },
          { strike: 200, bid: 1.35, ask: 1.48, volume: 16800, expirationDate: '2026-03-21', delta: 0.24, gamma: 0.028, theta: -0.08, vega: 0.12, impliedVolatility: 0.25, __typename: 'OptionContractType' },
          { strike: 205, bid: 0.58, ask: 0.72, volume: 10200, expirationDate: '2026-03-21', delta: 0.14, gamma: 0.018, theta: -0.05, vega: 0.09, impliedVolatility: 0.24, __typename: 'OptionContractType' },
          { strike: 185, bid: 5.80, ask: 5.90, volume: 12400, expirationDate: '2026-04-18', delta: 0.62, gamma: 0.028, theta: -0.08, vega: 0.18, impliedVolatility: 0.28, __typename: 'OptionContractType' },
          { strike: 190, bid: 3.90, ask: 4.00, volume: 28600, expirationDate: '2026-04-18', delta: 0.48, gamma: 0.032, theta: -0.09, vega: 0.21, impliedVolatility: 0.26, __typename: 'OptionContractType' },
          { strike: 195, bid: 2.40, ask: 2.50, volume: 19200, expirationDate: '2026-04-18', delta: 0.35, gamma: 0.030, theta: -0.08, vega: 0.20, impliedVolatility: 0.25, __typename: 'OptionContractType' },
          { strike: 200, bid: 1.30, ask: 1.40, volume: 14800, expirationDate: '2026-04-18', delta: 0.22, gamma: 0.024, theta: -0.06, vega: 0.16, impliedVolatility: 0.24, __typename: 'OptionContractType' },
          { strike: 205, bid: 0.65, ask: 0.70, volume: 9100,  expirationDate: '2026-04-18', delta: 0.13, gamma: 0.016, theta: -0.04, vega: 0.11, impliedVolatility: 0.23, __typename: 'OptionContractType' },
        ],
        puts: [
          { strike: 185, bid: 2.35, ask: 2.48, volume: 9200,  expirationDate: '2026-03-21', delta: -0.32, gamma: 0.032, theta: -0.09, vega: 0.14, impliedVolatility: 0.31, __typename: 'OptionContractType' },
          { strike: 190, bid: 3.85, ask: 3.98, volume: 17800, expirationDate: '2026-03-21', delta: -0.48, gamma: 0.035, theta: -0.10, vega: 0.16, impliedVolatility: 0.29, __typename: 'OptionContractType' },
          { strike: 195, bid: 6.10, ask: 6.25, volume: 11800, expirationDate: '2026-03-21', delta: -0.62, gamma: 0.033, theta: -0.09, vega: 0.15, impliedVolatility: 0.28, __typename: 'OptionContractType' },
          { strike: 200, bid: 9.00, ask: 9.18, volume: 8100,  expirationDate: '2026-03-21', delta: -0.76, gamma: 0.025, theta: -0.07, vega: 0.13, impliedVolatility: 0.27, __typename: 'OptionContractType' },
          { strike: 185, bid: 2.10, ask: 2.20, volume: 8400,  expirationDate: '2026-04-18', delta: -0.38, gamma: 0.028, theta: -0.07, vega: 0.18, impliedVolatility: 0.29, __typename: 'OptionContractType' },
          { strike: 190, bid: 3.60, ask: 3.70, volume: 16200, expirationDate: '2026-04-18', delta: -0.52, gamma: 0.032, theta: -0.08, vega: 0.21, impliedVolatility: 0.27, __typename: 'OptionContractType' },
          { strike: 195, bid: 5.80, ask: 5.90, volume: 10500, expirationDate: '2026-04-18', delta: -0.65, gamma: 0.030, theta: -0.07, vega: 0.20, impliedVolatility: 0.26, __typename: 'OptionContractType' },
          { strike: 200, bid: 8.60, ask: 8.70, volume: 7200,  expirationDate: '2026-04-18', delta: -0.78, gamma: 0.022, theta: -0.05, vega: 0.15, impliedVolatility: 0.25, __typename: 'OptionContractType' },
        ],
      },
    },
  },

  // Edge Predictor Heatmap — EdgePredictorHeatmap component
  GetEdgePredictions: {
    edgePredictions: [
      { strike: 190, expiration: '2026-04-18', optionType: 'CALL', currentEdge: 12.4, predictedEdge15min: 13.1, predictedEdge1hr: 14.8, predictedEdge1day: 16.2, confidence: 0.78, explanation: 'Momentum aligns with bullish regime; call skew favorable', edgeChangeDollars: 0.68, currentPremium: 3.95, predictedPremium15min: 4.12, predictedPremium1hr: 4.63, __typename: 'EdgePredictionType' },
      { strike: 195, expiration: '2026-04-18', optionType: 'CALL', currentEdge: 8.6,  predictedEdge15min: 9.0,  predictedEdge1hr: 10.4, predictedEdge1day: 12.1, confidence: 0.72, explanation: 'Near resistance — edge improving on breakout probability', edgeChangeDollars: 0.42, currentPremium: 2.45, predictedPremium15min: 2.58, predictedPremium1hr: 2.87, __typename: 'EdgePredictionType' },
      { strike: 185, expiration: '2026-04-18', optionType: 'PUT',  currentEdge: -4.2, predictedEdge15min: -3.8, predictedEdge1hr: -2.9, predictedEdge1day: -1.4, confidence: 0.65, explanation: 'Put edge deteriorating as support holds; IV declining', edgeChangeDollars: -0.22, currentPremium: 2.15, predictedPremium15min: 2.08, predictedPremium1hr: 1.94, __typename: 'EdgePredictionType' },
      { strike: 185, expiration: '2026-03-21', optionType: 'CALL', currentEdge: 6.1,  predictedEdge15min: 6.4,  predictedEdge1hr: 7.0,  predictedEdge1day: 8.3,  confidence: 0.60, explanation: 'Short-dated theta decay accelerating — edge modest', edgeChangeDollars: 0.18, currentPremium: 5.82, predictedPremium15min: 5.90, predictedPremium1hr: 6.08, __typename: 'EdgePredictionType' },
    ],
  },

  // IV Surface Forecast — IVSurfaceForecast component
  GetIVSurfaceForecast: {
    ivSurfaceForecast: {
      symbol: 'AAPL',
      currentIv: 0.26,
      predictedIv1hr: 0.25,
      predictedIv24hr: 0.24,
      confidence: 0.74,
      regime: 'NORMAL_CONTANGO',
      timestamp: new Date().toISOString(),
      __typename: 'IVSurfaceForecastType',
      ivChangeHeatmap: [
        { strike: 185, expiration: '2026-03-21', currentIv: 0.30, predictedIv1hr: 0.29, predictedIv24hr: 0.27, ivChange1hrPct: -2.1, ivChange24hrPct: -8.4, confidence: 0.72, __typename: 'IVHeatmapPoint' },
        { strike: 190, expiration: '2026-03-21', currentIv: 0.27, predictedIv1hr: 0.26, predictedIv24hr: 0.25, ivChange1hrPct: -1.8, ivChange24hrPct: -6.2, confidence: 0.74, __typename: 'IVHeatmapPoint' },
        { strike: 195, expiration: '2026-03-21', currentIv: 0.25, predictedIv1hr: 0.24, predictedIv24hr: 0.23, ivChange1hrPct: -1.4, ivChange24hrPct: -5.1, confidence: 0.70, __typename: 'IVHeatmapPoint' },
        { strike: 185, expiration: '2026-04-18', currentIv: 0.29, predictedIv1hr: 0.28, predictedIv24hr: 0.27, ivChange1hrPct: -1.6, ivChange24hrPct: -5.8, confidence: 0.76, __typename: 'IVHeatmapPoint' },
        { strike: 190, expiration: '2026-04-18', currentIv: 0.26, predictedIv1hr: 0.25, predictedIv24hr: 0.24, ivChange1hrPct: -1.2, ivChange24hrPct: -4.4, confidence: 0.78, __typename: 'IVHeatmapPoint' },
        { strike: 195, expiration: '2026-04-18', currentIv: 0.24, predictedIv1hr: 0.24, predictedIv24hr: 0.23, ivChange1hrPct: -0.8, ivChange24hrPct: -3.6, confidence: 0.74, __typename: 'IVHeatmapPoint' },
      ],
    },
  },

  // Rust Options Analysis — RustOptionsAnalysisWidget
  GetRustOptionsAnalysis: {
    rustOptionsAnalysis: {
      symbol: 'AAPL',
      underlyingPrice: 189.30,
      putCallRatio: 0.82,
      impliedVolatilityRank: 42,
      timestamp: new Date().toISOString(),
      __typename: 'RustOptionsAnalysisType',
      volatilitySurface: {
        atmVol: 0.26, skew: -0.04, termStructure: [0.28, 0.26, 0.25, 0.24],
        __typename: 'VolatilitySurfaceType',
      },
      greeks: { delta: 0.48, gamma: 0.032, theta: -0.09, vega: 0.21, rho: 0.06, __typename: 'PortfolioGreeksType' },
      recommendedStrikes: [
        { strike: 190, expiration: '2026-04-18', optionType: 'CALL', expectedReturn: 0.18, riskScore: 0.32, greeks: { delta: 0.48, gamma: 0.032, theta: -0.09, vega: 0.21, rho: 0.06, __typename: 'PortfolioGreeksType' }, __typename: 'RecommendedStrikeType' },
        { strike: 185, expiration: '2026-04-18', optionType: 'PUT',  expectedReturn: 0.09, riskScore: 0.28, greeks: { delta: -0.38, gamma: 0.028, theta: -0.07, vega: 0.18, rho: -0.04, __typename: 'PortfolioGreeksType' }, __typename: 'RecommendedStrikeType' },
      ],
    },
  },

  // Rust Correlation Analysis — StockScreen (shows symbol vs SPY/BTC correlation)
  GetRustCorrelationAnalysis: {
    rustCorrelationAnalysis: {
      primarySymbol: 'AAPL', secondarySymbol: 'SPY',
      correlation1d: 0.72, correlation7d: 0.68, correlation30d: 0.61,
      btcDominance: 0.12, spyCorrelation: 0.72, regime: 'RISK_ON',
      timestamp: new Date().toISOString(),
      __typename: 'RustCorrelationAnalysisType',
    },
  },

  // Chan Quant Signals — ChanQuantSignalsCard on Options tab
  ChanQuantSignals: {
    chanQuantSignals: {
      symbol: 'AAPL',
      __typename: 'ChanQuantSignalsType',
      meanReversion: {
        deviationSigma: 1.4, reversionProbability: 0.68, expectedDrawdown: 0.035,
        timeframeDays: 5, confidence: 0.74,
        explanation: 'Price is 1.4σ above 20-day mean. Mean reversion probability elevated — consider selling premium or waiting for pullback entry.',
        __typename: 'MeanReversionSignalType',
      },
      momentum: {
        timingConfidence: 0.72, momentumDecayProbability: 0.28, trendPersistenceHalfLife: 8.4,
        momentumAlignment: { daily: 0.78, weekly: 0.65, monthly: 0.52, __typename: 'MomentumAlignmentType' },
        confidence: 0.70,
        explanation: 'Daily and weekly momentum aligned bullish. Monthly trend less clear. Half-life suggests trend may persist ~8 more days.',
        __typename: 'MomentumSignalType',
      },
      kellyPositionSize: {
        kellyFraction: 0.22, recommendedFraction: 0.11, maxDrawdownRisk: 0.082,
        winRate: 0.58, avgWin: 0.094, avgLoss: 0.062,
        explanation: 'Full Kelly 22%; using half-Kelly (11%) for risk management. Win rate 58% with 1.52 win/loss ratio supports moderate position.',
        __typename: 'KellyPositionSizeType',
      },
      regimeRobustness: {
        robustnessScore: 0.76, regimesTested: 8,
        worstRegimePerformance: -0.12, bestRegimePerformance: 0.38,
        explanation: 'Strategy tested across 8 market regimes. Robust in 6/8 scenarios. Underperforms in high-volatility bear markets.',
        __typename: 'RegimeRobustnessType',
      },
    },
  },

  // Research Hub — Research tab in StockScreen
  Research: {
    researchHub: {
      symbol: 'AAPL', updatedAt: new Date().toISOString(),
      peers: ['MSFT', 'GOOGL', 'META', 'AMZN'],
      __typename: 'ResearchHubType',
      company: { name: 'Apple Inc.', sector: 'Technology', marketCap: 2940000000000, country: 'US', website: 'https://apple.com', __typename: 'CompanySnapshotType' },
      quote: { currentPrice: 189.30, change: 2.10, changePercent: 1.12, high: 190.50, low: 188.10, volume: 52000000, __typename: 'QuoteType' },
      technicals: { rsi: 58.4, macd: 1.82, macdhistogram: 0.42, movingAverage50: 184.20, movingAverage200: 172.80, supportLevel: 182.00, resistanceLevel: 196.00, impliedVolatility: 0.26, __typename: 'TechnicalsType' },
      sentiment: { sentiment_label: 'bullish', sentiment_score: 0.68, articleCount: 24, confidence: 0.82, __typename: 'SentimentType' },
      macro: { vix: 16.4, market_sentiment: 'risk_on', risk_appetite: 'moderate', __typename: 'MacroType' },
      marketRegime: { marketRegime: 'BULL_TREND', confidence: 0.72, recommendedStrategy: 'Momentum / Long Bias', __typename: 'MarketRegimeType' },
    },
  },

  // StockScreen Chart query (uses operation name "Chart" — different from GetStockChartData)
  Chart: (() => {
    let price = 187;
    const now = Date.now();
    const data = Array.from({ length: 30 }, (_, i) => {
      const ts = new Date(now - (29 - i) * 86400000).toISOString();
      const open = price + (Math.random() - 0.48) * 3;
      const close = open + (Math.random() - 0.46) * 4;
      price = close;
      return { timestamp: ts, open: parseFloat(open.toFixed(2)), high: parseFloat((Math.max(open, close) + Math.random() * 1.5).toFixed(2)), low: parseFloat((Math.min(open, close) - Math.random() * 1.5).toFixed(2)), close: parseFloat(close.toFixed(2)), volume: Math.floor(40000000 + Math.random() * 20000000) };
    });
    return { stockChartData: { symbol: 'AAPL', data, __typename: 'StockChartDataType' } };
  })(),

  // Rust Sentiment Analysis (used by RustSentimentWidget on Stock Detail insights tab)
  GetRustSentimentAnalysis: {
    rustSentimentAnalysis: {
      symbol: 'NVDA',
      overallSentiment: 'BULLISH',
      sentimentScore: 0.72,
      newsSentiment: {
        score: 0.75,
        articleCount: 24,
        positiveArticles: 16,
        negativeArticles: 4,
        neutralArticles: 4,
        topHeadlines: [
          'NVDA beats Q4 earnings estimates by wide margin',
          'Analysts raise price targets following strong results',
          'AI chip demand drives record revenue quarter',
        ],
        __typename: 'NewsSentimentType',
      },
      socialSentiment: {
        score: 0.68,
        mentions24h: 48200,
        positiveMentions: 31000,
        negativeMentions: 8400,
        engagementScore: 0.82,
        trending: true,
        __typename: 'SocialSentimentType',
      },
      confidence: 0.88,
      timestamp: new Date().toISOString(),
      __typename: 'SentimentAnalysisType',
    },
  },

  // Stock Moments (used by StockMomentsIntegration on Chart tab - Key Moments view)
  GetStockMoments: (() => {
    const now = Date.now();
    return {
      stockMoments: [
        {
          id: 'moment-earnings-1',
          symbol: 'NVDA',
          timestamp: new Date(now - 7 * 86400000).toISOString(),
          category: 'EARNINGS',
          title: 'Q4 Earnings Beat Expectations',
          quickSummary: 'NVDA reported EPS of $5.16 vs $4.64 estimated — 11% beat',
          deepSummary: 'NVIDIA crushed Q4 estimates driven by explosive data center revenue growth of 409% YoY. CEO Jensen Huang cited unprecedented AI infrastructure demand. Management guided Q1 revenue above consensus, sending shares up 9% after-hours.',
          importanceScore: 0.95,
          sourceLinks: ['https://example.com/nvda-earnings'],
          impact1D: 9.2,
          impact7D: 14.8,
          __typename: 'StockMomentType',
        },
        {
          id: 'moment-analyst-1',
          symbol: 'NVDA',
          timestamp: new Date(now - 18 * 86400000).toISOString(),
          category: 'ANALYST',
          title: 'Multiple Analysts Raise Price Targets',
          quickSummary: '7 analysts raised targets, average new PT: $1,050',
          deepSummary: 'Following the earnings beat, Goldman Sachs, Morgan Stanley, and five other firms raised their NVDA price targets. The consensus PT moved to $1,050 from $875, implying 20% upside. All firms maintained Buy/Overweight ratings.',
          importanceScore: 0.78,
          sourceLinks: ['https://example.com/nvda-pt-raises'],
          impact1D: 2.4,
          impact7D: 5.1,
          __typename: 'StockMomentType',
        },
        {
          id: 'moment-product-1',
          symbol: 'NVDA',
          timestamp: new Date(now - 32 * 86400000).toISOString(),
          category: 'PRODUCT',
          title: 'Blackwell Architecture Launch',
          quickSummary: 'Next-gen GPU architecture unveiled at GTC conference',
          deepSummary: 'NVIDIA unveiled its Blackwell GPU architecture at the GTC Developer Conference. The new chips promise 2.5x performance improvement over Hopper for AI training workloads. Major cloud providers announced immediate adoption plans.',
          importanceScore: 0.88,
          sourceLinks: ['https://example.com/nvda-blackwell'],
          impact1D: 5.7,
          impact7D: 11.3,
          __typename: 'StockMomentType',
        },
      ],
    };
  })(),

  // Stock Detail — Analysis (used by StockDetailScreen insights tab)
  GetStockAnalysis: (() => {
    const now = Date.now();
    // spendingData needs: date, spending, spendingChange, price, priceChange
    // ConsumerSpendingSurgeChart multiplies spendingChange/priceChange * 100 for display
    let basePrice = 840;
    let baseSpending = 820000000;
    const spendingData = Array.from({ length: 12 }, (_, i) => {
      const spendingChange = parseFloat((0.04 + (Math.random() - 0.45) * 0.06).toFixed(4));
      const priceChange = parseFloat((0.03 + (Math.random() - 0.48) * 0.08).toFixed(4));
      baseSpending = Math.round(baseSpending * (1 + spendingChange));
      basePrice = parseFloat((basePrice * (1 + priceChange)).toFixed(2));
      return {
        date: new Date(now - (11 - i) * 30 * 86400000).toISOString().split('T')[0],
        spending: baseSpending,
        spendingChange,
        price: basePrice,
        priceChange,
        __typename: 'SpendingDataPoint',
      };
    });
    // optionsFlowData needs: date, price, unusualVolumePercent, sweepCount, putCallRatio
    // SmartMoneyFlowChart uses opt.price for the price line on the chart
    let optPrice = 870;
    const optionsFlowData = Array.from({ length: 8 }, (_, i) => {
      optPrice = parseFloat((optPrice + (Math.random() - 0.47) * 12).toFixed(2));
      return {
        date: new Date(now - (7 - i) * 86400000).toISOString().split('T')[0],
        price: optPrice,
        unusualVolumePercent: parseFloat((15 + Math.random() * 40).toFixed(1)),
        sweepCount: Math.floor(Math.random() * 5),
        putCallRatio: parseFloat((0.6 + Math.random() * 0.8).toFixed(2)),
        callVolume: Math.floor(50000 + Math.random() * 100000),
        putVolume: Math.floor(20000 + Math.random() * 60000),
        callOI: Math.floor(200000 + Math.random() * 300000),
        putOI: Math.floor(100000 + Math.random() * 200000),
        unusualActivity: Math.random() > 0.6,
        __typename: 'OptionsFlowDataPoint',
      };
    });
    const signalContributions = [
      { name: 'Momentum', contribution: 0.38, color: '#22c55e', description: 'Price momentum and trend strength', __typename: 'SignalContribution' as const },
      { name: 'Volume', contribution: 0.25, color: '#3b82f6', description: 'Trading volume and liquidity', __typename: 'SignalContribution' as const },
      { name: 'Options Flow', contribution: 0.22, color: '#8b5cf6', description: 'Options and smart money flow', __typename: 'SignalContribution' as const },
      { name: 'Sentiment', contribution: 0.15, color: '#f59e0b', description: 'News and social sentiment', __typename: 'SignalContribution' as const },
    ];
    const shapValues = [
      { feature: 'RSI', value: 0.18, importance: 0.18, __typename: 'ShapValue' as const },
      { feature: 'MACD', value: 0.14, importance: 0.14, __typename: 'ShapValue' as const },
      { feature: 'Volume Surge', value: 0.22, importance: 0.22, __typename: 'ShapValue' as const },
      { feature: 'Options Gamma', value: 0.19, importance: 0.19, __typename: 'ShapValue' as const },
      { feature: 'News Sentiment', value: 0.12, importance: 0.12, __typename: 'ShapValue' as const },
    ];
    return {
      rustStockAnalysis: {
        symbol: 'NVDA',
        spendingData,
        optionsFlowData,
        signalContributions,
        shapValues,
        shapExplanation: 'Multi-factor model combining momentum, volume, options flow, and sentiment. Current reading is moderately bullish with momentum and volume leading.',
        __typename: 'RustStockAnalysis' as const,
      },
    };
  })(),

  // Budget / Spending
  GetBudgetData:      { budgetData: DEMO_BUDGET_DATA },
  GetSpendingAnalysis: { spendingAnalysis: DEMO_SPENDING_ANALYSIS },

  // Portfolio Analytics (Premium)
  GetPortfolioAnalytics: {
    premiumPortfolioMetrics: {
      totalValue: 14303.52,
      totalCost: 12158.00,
      volatility: 18.5,
      sharpeRatio: 1.42,
      maxDrawdown: -8.2,
      beta: 1.15,
      alpha: 2.3,
      sectorAllocation: { Technology: 45.2, ETF: 44.1, 'Consumer Cyclical': 2.8, Automotive: 5.5, Other: 2.4 },
      __typename: 'PremiumPortfolioMetrics',
    },
  },

  // Premium Analytics screen — query uses root field portfolioMetrics (not premiumPortfolioMetrics)
  // riskMetrics must be a JSON string (screen uses JSON.parse(displayMetrics.riskMetrics))
  GetPremiumPortfolioMetrics: (() => {
    const holdings = (DEMO_GQL_PORTFOLIO_METRICS as any).holdings || [];
    const riskMetricsObj = { beta: 1.15, alpha: 2.3, volatility: 18.5, sharpeRatio: 1.42, maxDrawdown: -8.2, diversificationScore: 0.72 };
    return {
      portfolioMetrics: {
        totalValue: DEMO_GQL_PORTFOLIO_METRICS.totalValue,
        totalCost: DEMO_GQL_PORTFOLIO_METRICS.totalCost,
        totalReturn: DEMO_GQL_PORTFOLIO_METRICS.totalReturn,
        totalReturnPercent: DEMO_GQL_PORTFOLIO_METRICS.totalReturnPercent,
        dayChange: 142.50,
        dayChangePercent: 1.0,
        volatility: 18.5,
        sharpeRatio: 1.42,
        maxDrawdown: -8.2,
        beta: 1.15,
        alpha: 2.3,
        sectorAllocation: { Technology: 45.2, ETF: 44.1, 'Consumer Cyclical': 2.8, Automotive: 5.5, Other: 2.4 },
        riskMetrics: JSON.stringify(riskMetricsObj),
        holdings: holdings.map((h: any) => ({
          symbol: h.symbol,
          companyName: h.companyName,
          shares: h.shares,
          currentPrice: h.currentPrice,
          totalValue: h.totalValue,
          costBasis: h.costBasis,
          returnAmount: h.returnAmount,
          returnPercent: h.returnPercent,
          sector: h.sector,
          __typename: 'HoldingMetric',
        })),
        __typename: 'PortfolioMetrics',
      },
    };
  })(),
  GetExecutionQualityTrends: {
    executionQualityTrends: {
      avgSlippagePct: 0.08,
      avgQualityScore: 87,
      chasedCount: 2,
      totalFills: 12,
      __typename: 'ExecutionQualityTrends',
    },
  },
  // Day Trading / Swing Trading — Execution Quality Dashboard (ExecutionQualityDashboard.tsx)
  GetExecutionQualityStats: {
    executionQualityStats: {
      avgSlippagePct: 0.18,
      avgQualityScore: 7.5,
      chasedCount: 3,
      totalFills: 24,
      periodDays: 30,
      improvementTips: [
        'Consider using limit orders to reduce slippage',
        'Avoid chasing price movements — wait for pullbacks',
        'Your execution quality is improving — keep it up!',
      ],
      __typename: 'ExecutionQualityStatsType',
    },
  },
  GetCreditScoreHistory: {
    creditScoreHistory: [
      { date: '2025-01-01', score: 710, factors: ['On-time payments', 'Low utilisation'] },
      { date: '2025-02-01', score: 718, factors: ['Credit age improving'] },
      { date: '2025-03-01', score: 725, factors: ['New account mix'] },
    ],
  },

  // AI Scans (AIScansScreen)
  GetAIScans: {
    aiScans: [
      {
        id: 'scan-demo-1',
        name: 'Momentum Breakout',
        description: 'Stocks breaking out on volume with positive momentum.',
        category: 'MOMENTUM',
        riskLevel: 'MODERATE',
        timeHorizon: 'SWING',
        isActive: true,
        lastRun: new Date(Date.now() - 3600000).toISOString(),
        results: [
          { id: 'r1', symbol: 'NVDA', currentPrice: 138.5, changePercent: 2.4, confidence: 0.82, score: 0.78 },
          { id: 'r2', symbol: 'META', currentPrice: 512.2, changePercent: 1.8, confidence: 0.75, score: 0.72 },
        ],
        playbook: { id: 'pb-1', name: 'Breakout Playbook', performance: { successRate: 0.68, averageReturn: 0.12 } },
      },
      {
        id: 'scan-demo-2',
        name: 'Value + Quality',
        description: 'Undervalued names with strong fundamentals.',
        category: 'VALUE',
        riskLevel: 'LOW',
        timeHorizon: 'LONG',
        isActive: true,
        lastRun: new Date(Date.now() - 7200000).toISOString(),
        results: [
          { id: 'r3', symbol: 'PYPL', currentPrice: 68.4, changePercent: -0.5, confidence: 0.71, score: 0.65 },
        ],
        playbook: { id: 'pb-2', name: 'Value Playbook', performance: { successRate: 0.62, averageReturn: 0.08 } },
      },
    ],
  },

  // Playbooks (AIScansScreen playbooks tab)
  GetPlaybooks: {
    playbooks: [
      {
        id: 'playbook-demo-1',
        name: 'Momentum Breakout',
        author: 'RichesReach Research',
        riskLevel: 'MODERATE',
        performance: { successRate: 0.68, averageReturn: 0.12 },
        tags: ['momentum', 'breakout', 'swing'],
      },
      {
        id: 'playbook-demo-2',
        name: 'Value & Quality',
        author: 'RichesReach Research',
        riskLevel: 'LOW',
        performance: { successRate: 0.62, averageReturn: 0.08 },
        tags: ['value', 'fundamentals', 'long-term'],
      },
    ],
  },

  // ── Financial GPS Screens ───────────────────────────────────────────────────
  
  // Leak Detector
  GetFinancialLeaks: { financialLeaks: DEMO_FINANCIAL_LEAKS },
  
  // Wealth Arrival
  GetWealthArrival: { wealthArrival: DEMO_WEALTH_ARRIVAL },
  
  // Net Worth
  GetNetWorthHistory: { netWorthHistory: DEMO_NET_WORTH_HISTORY },
  
  // Financial Health Score
  GetFinancialHealth: { financialHealth: DEMO_FINANCIAL_HEALTH },
  
  // Income Intelligence
  GetIncomeIntelligence: { incomeIntelligence: DEMO_INCOME_INTELLIGENCE },
  
  // Life Decision Simulator
  GetLifeDecision: { lifeDecision: DEMO_LIFE_DECISION },
  SimulateDecision: {
    simulateDecision: {
      userId: 1,
      decisionType: 'major_purchase',
      description: 'Buy a $60K car',
      amount: 60000,
      monthlyCost: 850,
      opportunityCost10yr: 142000,
      netWorthDelta10yr: -98000,
      monthlySurplusImpact: -850,
      breakEvenYears: null,
      currentNetWorth: 145000,
      investableSurplusMonthly: 2200,
      returnRate: 0.07,
      projectionYears: 10,
      headlineSentence: 'This purchase would delay your millionaire goal by 4.2 years.',
      recommendation: 'Consider a more affordable option or delay the purchase to minimize impact on your wealth trajectory.',
      dataQuality: 'actual',
      yearByYear: Array.from({ length: 10 }, (_, i) => {
        const year = 2026 + i;
        const withoutPurchase = Math.round(145000 * Math.pow(1.07, i) + 26400 * ((Math.pow(1.07, i) - 1) / 0.07));
        const withPurchase = Math.round(85000 * Math.pow(1.07, i) + 16200 * ((Math.pow(1.07, i) - 1) / 0.07));
        return { year, netWorthWith: withPurchase, netWorthWithout: withoutPurchase, delta: withPurchase - withoutPurchase };
      }),
      __typename: 'DecisionSimulationType',
    },
  },
  
  // Money Reallocation Engine
  GetReallocationStrategies: { reallocationStrategies: DEMO_REALLOCATION_STRATEGIES },
  
  // AI Portfolio Builder
  BuildPortfolio: { buildPortfolio: DEMO_BUILD_PORTFOLIO },
  GetBuildPortfolio: { buildPortfolio: DEMO_BUILD_PORTFOLIO },
  
  // Investor Profile & Behavioral Identity
  GetInvestorQuizQuestions: { investorQuizQuestions: DEMO_QUIZ_QUESTIONS },
  InvestorQuizQuestions: { investorQuizQuestions: DEMO_QUIZ_QUESTIONS },
  GetInvestorProfile: { investorProfile: DEMO_INVESTOR_PROFILE },
  InvestorProfile: { investorProfile: DEMO_INVESTOR_PROFILE },
  GetNextBestActions: { nextBestActions: DEMO_NEXT_BEST_ACTIONS },
  NextBestActions: { nextBestActions: DEMO_NEXT_BEST_ACTIONS },
  GetLeakRedirectSuggestion: { leakRedirectSuggestion: DEMO_LEAK_REDIRECT },
  LeakRedirectSuggestion: { leakRedirectSuggestion: DEMO_LEAK_REDIRECT },
  GetWeeklyDigest: { weeklyWealthDigest: DEMO_WEEKLY_DIGEST },
  WeeklyWealthDigest: { weeklyWealthDigest: DEMO_WEEKLY_DIGEST },
  GetIdentityGaps: { identityGaps: DEMO_IDENTITY_GAPS },
  IdentityGaps: { identityGaps: DEMO_IDENTITY_GAPS },
  GetBehavioralConsistency: {
    behavioralConsistency: {
      consistencyScore: 0.85,
      drift: null,
      __typename: 'BehavioralConsistency',
    },
  },
  BehavioralConsistency: {
    behavioralConsistency: {
      consistencyScore: 0.85,
      drift: null,
      __typename: 'BehavioralConsistency',
    },
  },
  GetBehavioralBiasSignal: {
    behavioralBiasSignal: {
      suggestedBiasTypes: [] as string[],
      confidence: 0,
      showInUi: false,
      __typename: 'BehavioralBiasSignal',
    },
  },
  BehavioralBiasSignal: {
    behavioralBiasSignal: {
      suggestedBiasTypes: [] as string[],
      confidence: 0,
      showInUi: false,
      __typename: 'BehavioralBiasSignal',
    },
  },

  // Alternative operation name variants (snake_case → camelCase)
  getReallocationStrategies: { reallocationStrategies: DEMO_REALLOCATION_STRATEGIES },
  getFinancialLeaks: { financialLeaks: DEMO_FINANCIAL_LEAKS },
  getWealthArrival: { wealthArrival: DEMO_WEALTH_ARRIVAL },
  getFinancialHealth: { financialHealth: DEMO_FINANCIAL_HEALTH },
  getIncomeIntelligence: { incomeIntelligence: DEMO_INCOME_INTELLIGENCE },

  // Mutations — return success shapes
  GenerateAIRecommendations: {
    generateAiRecommendations: {
      success: true,
      message: 'Recommendations generated',
      recommendations: null,
    },
  },
  CreateIncomeProfile: {
    createIncomeProfile: {
      success: true,
      message: 'Profile created',
      incomeProfile: {
        id: 'demo-ip-1',
        incomeBracket: '$75,000 - $100,000',
        age: 32,
        investmentGoals: ['Wealth Building', 'Retirement Savings'],
        riskTolerance: 'Moderate',
        investmentHorizon: '5-10 years',
        __typename: 'IncomeProfileType',
      },
    },
  },
  LikeSignal:    { likeSignal: { success: true } },
  CommentSignal: { commentSignal: { success: true } },
  AddToWatchlist:    { addToWatchlist: { success: true } },
  RemoveFromWatchlist: { removeFromWatchlist: { success: true } },
  EnableStrategy:  { enableStrategy: { success: true } },
  DisableStrategy: { disableStrategy: { success: true } },
  RunBacktest:     { runBacktest: { id: 'bt-demo-1', status: 'running' } },
  LogBehavioralEvent: { logBehavioralEvent: { success: true } },
};

// ─── Mock terminating link ────────────────────────────────────────────────────
const mockLink = new ApolloLink((operation) => {
  return new Observable((observer) => {
    const operationName = operation.operationName || '';
    const mockData = MOCK_RESPONSES[operationName];

    // Small artificial delay so loading states flash naturally (better demo UX)
    const delay = Math.random() * 200 + 100; // 100-300ms

    const timer = setTimeout(() => {
      if (mockData) {
        observer.next({ data: mockData });
      } else {
        // Unknown operation — return empty data so the app doesn't crash
        console.warn(`[DemoMode] No mock data for operation: ${operationName}`);
        observer.next({ data: {} });
      }
      observer.complete();
    }, delay);

    return () => clearTimeout(timer);
  });
});

// ─── Factory ──────────────────────────────────────────────────────────────────
export function makeMockApolloClient() {
  return new ApolloClient({
    link: mockLink,
    cache: new InMemoryCache(),
    defaultOptions: {
      watchQuery: {
        fetchPolicy: 'network-only', // Always re-run through mockLink
        errorPolicy: 'all',
      },
      query: {
        fetchPolicy: 'network-only',
        errorPolicy: 'all',
      },
    },
    assumeImmutableResults: true,
  });
}
