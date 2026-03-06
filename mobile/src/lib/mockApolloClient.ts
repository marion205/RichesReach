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
  DEMO_SWING_SIGNALS,
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
} from '../services/demoMockData';

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

  // Swing Trading
  GetSwingSignals:        { swingSignals: DEMO_SWING_SIGNALS },
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
  GetStrategies:   { strategies: [] },
  GetUserBacktests: { userBacktests: [] },

  // Stocks
  Stocks:          { stocks: DEMO_STOCKS },
  MyWatchlist:     { myWatchlist: [] },

  // Stock Detail — Analysis (used by StockDetailScreen insights tab)
  GetStockAnalysis: (() => {
    const now = Date.now();
    const spendingData = Array.from({ length: 12 }, (_, i) => ({
      date: new Date(now - (11 - i) * 30 * 86400000).toISOString().split('T')[0],
      spending: Math.floor(800000000 + Math.random() * 400000000),
      __typename: 'SpendingDataPoint',
    }));
    const optionsFlowData = Array.from({ length: 8 }, (_, i) => ({
      date: new Date(now - i * 86400000).toISOString().split('T')[0],
      callVolume: Math.floor(50000 + Math.random() * 100000),
      putVolume: Math.floor(20000 + Math.random() * 60000),
      callOI: Math.floor(200000 + Math.random() * 300000),
      putOI: Math.floor(100000 + Math.random() * 200000),
      unusualActivity: Math.random() > 0.6,
      __typename: 'OptionsFlowDataPoint',
    }));
    return {
      rustStockAnalysis: {
        symbol: 'NVDA',
        spendingData,
        optionsFlowData,
        signalContributions: [
          { signal: 'Momentum', contribution: 0.38, direction: 'bullish', __typename: 'SignalContribution' },
          { signal: 'Volume', contribution: 0.25, direction: 'bullish', __typename: 'SignalContribution' },
          { signal: 'Options Flow', contribution: 0.22, direction: 'bullish', __typename: 'SignalContribution' },
          { signal: 'Sentiment', contribution: 0.15, direction: 'neutral', __typename: 'SignalContribution' },
        ],
        shapValues: [
          { feature: 'RSI', value: 0.18, __typename: 'ShapValue' },
          { feature: 'MACD', value: 0.14, __typename: 'ShapValue' },
          { feature: 'Volume Surge', value: 0.22, __typename: 'ShapValue' },
          { feature: 'Options Gamma', value: 0.19, __typename: 'ShapValue' },
          { feature: 'News Sentiment', value: 0.12, __typename: 'ShapValue' },
        ],
        __typename: 'RustStockAnalysis',
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
  GetExecutionQualityTrends: {
    executionQualityTrends: {
      avgSlippagePct: 0.08,
      avgQualityScore: 87,
      chasedCount: 2,
      totalFills: 12,
      __typename: 'ExecutionQualityTrends',
    },
  },
  GetCreditScoreHistory: {
    creditScoreHistory: [
      { date: '2025-01-01', score: 710, factors: ['On-time payments', 'Low utilisation'] },
      { date: '2025-02-01', score: 718, factors: ['Credit age improving'] },
      { date: '2025-03-01', score: 725, factors: ['New account mix'] },
    ],
  },

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
