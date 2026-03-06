/**
 * Demo Mode Mock Data
 * Single source of truth for all fake data used in demo mode.
 * Covers every GraphQL query and REST endpoint the app makes.
 */

import { getMockPortfolioMetrics, getMockMyPortfolios } from './mockPortfolioData';

// ─── Re-export existing mock data ───────────────────────────────────────────
export const DEMO_PORTFOLIO_METRICS = getMockPortfolioMetrics();
export const DEMO_MY_PORTFOLIOS = getMockMyPortfolios();

// ─── Me / User ───────────────────────────────────────────────────────────────
export const DEMO_ME = {
  id: 'demo-user-1',
  email: 'demo@richesreach.com',
  username: 'demo',
  name: 'Alex Demo',
  hasPremiumAccess: true,
  subscriptionTier: 'premium',
  incomeProfile: {
    incomeBracket: '$75,000 - $100,000',
    age: 32,
    investmentGoals: ['Wealth Building', 'Retirement Savings'],
    riskTolerance: 'Moderate',
    investmentHorizon: '5-10 years',
    __typename: 'IncomeProfile',
  },
  __typename: 'UserType',
};

// ─── Market Brief (REST /api/market/brief/) ──────────────────────────────────
export const DEMO_MARKET_BRIEF = {
  regime: 'Bull Market — Momentum Phase',
  top_bullish: [
    { symbol: 'NVDA', signal: 'AI infrastructure demand accelerating', score: 0.91 },
    { symbol: 'MSFT', signal: 'Cloud growth beating estimates', score: 0.87 },
    { symbol: 'AAPL', signal: 'Services revenue expanding margins', score: 0.83 },
  ],
  top_bearish: [
    { symbol: 'TSLA', signal: 'Margin pressure from price cuts', score: -0.72 },
    { symbol: 'COIN', signal: 'Regulatory headwinds persist', score: -0.68 },
  ],
  market_summary: 'Equities are in a risk-on phase driven by AI capex and better-than-expected earnings. Breadth remains healthy with 68% of S&P 500 names above their 200-day MA.',
};

// ─── Daily Brief (REST /api/daily-brief/today) ───────────────────────────────
export const DEMO_DAILY_BRIEF = {
  id: 'demo-brief-001',
  date: new Date().toISOString().split('T')[0],
  market_summary: 'Markets opened higher today as strong jobs data calmed recession fears. The S&P 500 is up 0.8% led by technology and energy sectors.',
  personalized_action: 'Your NVDA position is up 4.2% this week — consider whether to take partial profits or hold through earnings next week.',
  lesson_topic: 'Understanding P/E ratios and why they matter for valuation',
  lesson_content: 'A Price-to-Earnings (P/E) ratio tells you how much investors are paying for each dollar of earnings. A high P/E suggests growth expectations; a low P/E may signal value or risk.',
  is_completed: false,
  sections_viewed: [],
  streak: 7,
  xp_available: 50,
  weekly_progress: { briefs_completed: 4, goal: 5, lessons_completed: 3 },
  confidence_score: 5,
};

// ─── Daily Brief Progress (REST /api/daily-brief/progress) ───────────────────
export const DEMO_BRIEF_PROGRESS = {
  streak: 7,
  longest_streak: 14,
  weekly_briefs_completed: 4,
  weekly_goal: 5,
  weekly_lessons_completed: 3,
  monthly_lessons_completed: 11,
  monthly_goal: 20,
  concepts_learned: 28,
  current_level: 'intermediate',
  confidence_score: 7,
  achievements: [
    { type: 'streak_7', earned_at: '2025-03-01T10:00:00Z' },
    { type: 'lessons_10', earned_at: '2025-02-15T10:00:00Z' },
  ],
};

// ─── Trade Debrief ────────────────────────────────────────────────────────────
export const DEMO_TRADE_DEBRIEF = {
  headline: 'Strong week — your tech entries timed the dip well',
  narrative: 'Over the last 30 days you executed 12 trades with a 67% win rate. Your best sector was Technology (+$842) and you showed discipline by cutting TSLA quickly when it violated your stop. Two patterns stand out: you tend to oversize entries on gap-ups — consider reducing position size by 20% on opens above 2%.',
  topInsight: 'Your average winner is 2.3× your average loser — that\'s a healthy reward/risk ratio. Keep it above 2×.',
  recommendations: [
    'Reduce position size on gap-up opens to manage risk',
    'Consider adding to MSFT on dips — your thesis is intact',
    'Set a weekly max-loss rule of $500 to prevent outlier down weeks',
  ],
  statsSummary: JSON.stringify({ avgWin: 187, avgLoss: 81, bestDay: 'Tuesday', worstDay: 'Friday' }),
  patternCodes: ['OVERSIZE_GAP_UP', 'GOOD_STOP_DISCIPLINE'],
  sectorStats: [
    { sector: 'Technology', trades: 7, wins: 5, losses: 2, totalPnl: 842, __typename: 'SectorStatType' },
    { sector: 'Consumer', trades: 3, wins: 2, losses: 1, totalPnl: 213, __typename: 'SectorStatType' },
    { sector: 'Energy', trades: 2, wins: 1, losses: 1, totalPnl: -45, __typename: 'SectorStatType' },
  ],
  patternFlags: [
    { code: 'OVERSIZE_GAP_UP', severity: 'medium', description: 'Entering full-size on gap-up opens increases drawdown risk', impactDollars: -180, __typename: 'PatternFlagType' },
    { code: 'GOOD_STOP_DISCIPLINE', severity: 'positive', description: 'Consistent stop-loss execution reduced max single-trade loss', impactDollars: 320, __typename: 'PatternFlagType' },
  ],
  dataSource: 'paper_trading',
  hasEnoughData: true,
  totalTrades: 12,
  winRatePct: 66.7,
  totalPnl: 1010,
  bestSector: 'Technology',
  worstSector: 'Energy',
  counterfactualExtraPnl: 245,
  lookbackDays: 30,
  generatedAt: new Date().toISOString(),
  __typename: 'TradeDebriefType',
};

// ─── Portfolio Metrics (GraphQL GetPortfolioMetrics) ─────────────────────────
export const DEMO_GQL_PORTFOLIO_METRICS = {
  totalValue: 14303.52,
  totalCost: 12158.00,
  totalReturn: 2145.53,
  totalReturnPercent: 17.65,
  holdings: DEMO_PORTFOLIO_METRICS.holdings.map(h => ({
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
};

// ─── Portfolio Risk Report ────────────────────────────────────────────────────
export const DEMO_PORTFOLIO_RISK_REPORT = JSON.stringify({
  regime: 'Bull',
  gate_multiplier: 1.0,
  narrative: 'Your portfolio is well-positioned for the current bull regime. Volatility is below your 90-day average and sector diversification looks healthy.',
  risk_score: 42,
  max_drawdown_30d: -3.8,
  var_95: -287,
});

// ─── AI Recommendations ──────────────────────────────────────────────────────
export const DEMO_AI_RECOMMENDATIONS = {
  buyRecommendations: [
    {
      symbol: 'NVDA',
      companyName: 'NVIDIA Corporation',
      currentPrice: 875.40,
      targetPrice: 1050.00,
      expectedReturn: 19.9,
      confidence: 0.88,
      recommendation: 'BUY',
      reasoning: 'AI data-center demand accelerating; Blackwell ramp ahead of schedule. Supply constraints easing into H2 which should drive margin expansion.',
      rationale: 'AI data-center demand accelerating; Blackwell ramp ahead of schedule',
      sector: 'Technology',
      riskLevel: 'medium',
      mlScore: 0.91,
      consumerStrengthScore: null,
      spendingGrowth: null,
      optionsFlowScore: 0.84,
      earningsScore: 0.92,
      insiderScore: 0.67,
      __typename: 'StockRecommendation',
    },
    {
      symbol: 'META',
      companyName: 'Meta Platforms',
      currentPrice: 512.30,
      targetPrice: 620.00,
      expectedReturn: 21.1,
      confidence: 0.82,
      recommendation: 'BUY',
      reasoning: 'Ad revenue recovery + Llama AI monetisation optionality. Reels engagement driving higher ROAS than peers; Threads monetisation ahead of schedule.',
      rationale: 'Ad revenue recovery + Llama AI monetisation optionality',
      sector: 'Technology',
      riskLevel: 'medium',
      mlScore: 0.85,
      consumerStrengthScore: 0.78,
      spendingGrowth: 0.12,
      optionsFlowScore: 0.79,
      earningsScore: 0.88,
      insiderScore: 0.72,
      __typename: 'StockRecommendation',
    },
    {
      symbol: 'XOM',
      companyName: 'Exxon Mobil',
      currentPrice: 118.60,
      targetPrice: 135.00,
      expectedReturn: 13.8,
      confidence: 0.74,
      recommendation: 'BUY',
      reasoning: 'Strong free cash flow; dividend growth likely. Low-beta defensive play adds balance to growth-heavy portfolio.',
      rationale: 'Strong free cash flow; dividend growth likely',
      sector: 'Energy',
      riskLevel: 'low',
      mlScore: 0.74,
      consumerStrengthScore: null,
      spendingGrowth: null,
      optionsFlowScore: 0.61,
      earningsScore: 0.76,
      insiderScore: 0.80,
      __typename: 'StockRecommendation',
    },
  ],
  sellRecommendations: [
    {
      symbol: 'TSLA',
      reasoning: 'Margin compression from price wars; competition intensifying. Gross margin at multi-year low and delivery growth slowing.',
      __typename: 'StockRecommendation',
    },
  ],
  rebalanceSuggestions: [
    {
      action: 'TRIM',
      currentAllocation: 45.2,
      suggestedAllocation: 38.0,
      reasoning: 'Technology overweight relative to your moderate risk profile — trim to reduce concentration risk.',
      priority: 'medium',
      __typename: 'RebalanceSuggestion',
    },
    {
      action: 'ADD',
      currentAllocation: 0,
      suggestedAllocation: 8.0,
      reasoning: 'Add defensive exposure (Healthcare or Utilities) to reduce portfolio beta toward 1.0.',
      priority: 'low',
      __typename: 'RebalanceSuggestion',
    },
  ],
  riskAssessment: {
    overallRisk: 'Moderate-High',
    volatilityEstimate: 18.5,
    recommendations: [
      'Portfolio beta 1.15 — slightly above market. Consider adding low-beta defensive names.',
      'Technology concentration at 45% increases drawdown risk in rate-sensitive environments.',
    ],
    __typename: 'RiskAssessment',
  },
  marketOutlook: {
    overallSentiment: 'Constructive',
    confidence: 0.74,
    keyFactors: [
      'Fed pivot expectations support equity valuations',
      'AI capex cycle driving tech earnings upgrades',
      'Watch for Q2 earnings revision trajectory',
    ],
    __typename: 'MarketOutlook',
  },
  spendingInsights: null,
  portfolioAnalysis: {
    totalValue: 14303.52,
    numHoldings: 5,
    sectorBreakdown: JSON.stringify({ Technology: 45.2, ETF: 44.1, Automotive: 5.5, 'Consumer Cyclical': 2.8, Other: 2.4 }),
    riskScore: 42,
    diversificationScore: 68,
    __typename: 'PortfolioAnalysis',
  },
  __typename: 'AIRecommendations',
};

// ─── Day Trading Picks ───────────────────────────────────────────────────────
export const DEMO_DAY_TRADING_PICKS = {
  asOf: new Date().toISOString(),
  mode: 'momentum',
  universeSize: 1200,
  picks: [
    {
      symbol: 'NVDA',
      side: 'LONG',
      score: 0.91,
      features: { momentum: 0.94, volume_surge: 1.8, gap_pct: 1.2 },
      risk: { stopLoss: 862.00, target: 905.00, maxLoss: 130 },
      notes: 'AI catalyst momentum; volume 1.8× average; clean breakout above 875',
      __typename: 'DayTradingPick',
    },
    {
      symbol: 'AAPL',
      side: 'LONG',
      score: 0.84,
      features: { momentum: 0.81, volume_surge: 1.3, gap_pct: 0.6 },
      risk: { stopLoss: 176.50, target: 184.00, maxLoss: 90 },
      notes: 'Holding key support; services revenue beat overnight',
      __typename: 'DayTradingPick',
    },
    {
      symbol: 'TSLA',
      side: 'SHORT',
      score: 0.77,
      features: { momentum: -0.72, volume_surge: 1.5, gap_pct: -1.4 },
      risk: { stopLoss: 202.00, target: 188.00, maxLoss: 110 },
      notes: 'Failed breakout below 200-day MA; elevated short interest',
      __typename: 'DayTradingPick',
    },
  ],
  __typename: 'DayTradingPicksResult',
};

// ─── Swing Trading Signals ───────────────────────────────────────────────────
export const DEMO_SWING_SIGNALS = [
  {
    id: 'sig-1',
    symbol: 'MSFT',
    companyName: 'Microsoft Corporation',
    side: 'LONG',
    mlScore: 0.87,
    thesis: 'Azure growth re-acceleration; AI Copilot uptake stronger than expected. Technical: consolidation above 20-week MA with rising volume.',
    entryPrice: 415.00,
    stopLoss: 398.00,
    targetPrice: 455.00,
    riskRewardRatio: 2.35,
    timeframe: '2-4 weeks',
    sector: 'Technology',
    technicalIndicators: { rsi: 58, macd: 'bullish_cross', bb_position: 'mid', adx: 32 },
    patterns: ['ascending_triangle', 'volume_accumulation'],
    catalysts: ['Earnings next week', 'Azure monthly metrics'],
    likes: 142,
    comments: 18,
    __typename: 'SwingSignal',
  },
  {
    id: 'sig-2',
    symbol: 'JPM',
    companyName: 'JPMorgan Chase',
    side: 'LONG',
    mlScore: 0.81,
    thesis: 'Net interest income still expanding; credit quality holding. Trading below historical P/B with 2.8% dividend yield as cushion.',
    entryPrice: 198.50,
    stopLoss: 190.00,
    targetPrice: 218.00,
    riskRewardRatio: 2.24,
    timeframe: '3-6 weeks',
    sector: 'Financials',
    technicalIndicators: { rsi: 52, macd: 'positive', bb_position: 'lower_mid', adx: 28 },
    patterns: ['bull_flag', 'support_hold'],
    catalysts: ['Fed minutes', 'Q2 bank earnings'],
    likes: 98,
    comments: 12,
    __typename: 'SwingSignal',
  },
  {
    id: 'sig-3',
    symbol: 'LLY',
    companyName: 'Eli Lilly',
    side: 'LONG',
    mlScore: 0.79,
    thesis: 'GLP-1 demand continues to outpace supply. Pipeline optionality in Alzheimer\'s space. Defensive growth in uncertain macro.',
    entryPrice: 780.00,
    stopLoss: 748.00,
    targetPrice: 850.00,
    riskRewardRatio: 2.19,
    timeframe: '4-8 weeks',
    sector: 'Healthcare',
    technicalIndicators: { rsi: 61, macd: 'bullish', bb_position: 'upper_mid', adx: 38 },
    patterns: ['cup_and_handle', 'breakout_pending'],
    catalysts: ['FDA decision', 'Mounjaro prescriptions data'],
    likes: 203,
    comments: 31,
    __typename: 'SwingSignal',
  },
];

// ─── Market Data (Swing Trading) ─────────────────────────────────────────────
export const DEMO_MARKET_DATA = [
  { symbol: 'SPY', price: 524.30, change: 4.20, changePercent: 0.81, volume: 82_000_000, __typename: 'MarketDataPoint' },
  { symbol: 'QQQ', price: 448.70, change: 5.10, changePercent: 1.15, volume: 48_000_000, __typename: 'MarketDataPoint' },
  { symbol: 'IWM', price: 208.40, change: 1.80, changePercent: 0.87, volume: 32_000_000, __typename: 'MarketDataPoint' },
  { symbol: 'VIX', price: 14.2, change: -0.8, changePercent: -5.3, volume: 0, __typename: 'MarketDataPoint' },
];

export const DEMO_SECTOR_DATA = [
  { name: 'Technology', symbol: 'XLK', change: 1.42, weight: 31.2, __typename: 'SectorDataPoint' },
  { name: 'Healthcare', symbol: 'XLV', change: 0.88, weight: 12.8, __typename: 'SectorDataPoint' },
  { name: 'Financials', symbol: 'XLF', change: 0.65, weight: 13.1, __typename: 'SectorDataPoint' },
  { name: 'Energy', symbol: 'XLE', change: -0.31, weight: 4.2, __typename: 'SectorDataPoint' },
  { name: 'Consumer Disc', symbol: 'XLY', change: 0.97, weight: 10.4, __typename: 'SectorDataPoint' },
];

export const DEMO_VOLATILITY_DATA = {
  vix: 14.2,
  vixChange: -5.3,
  fearGreedIndex: 62,
  putCallRatio: 0.82,
  __typename: 'VolatilityData',
};

export const DEMO_PERFORMANCE_METRICS = {
  totalTrades: 12,
  winRate: 66.7,
  sharpeRatio: 1.42,
  maxDrawdown: -8.2,
  profitFactor: 2.31,
  __typename: 'PerformanceMetrics',
};

export const DEMO_RECENT_TRADES = [
  { id: 't1', symbol: 'NVDA', side: 'LONG', entryPrice: 820.00, exitPrice: 875.40, pnl: 554, status: 'closed', __typename: 'RecentTrade' },
  { id: 't2', symbol: 'AAPL', side: 'LONG', entryPrice: 172.00, exitPrice: 180.00, pnl: 80, status: 'closed', __typename: 'RecentTrade' },
  { id: 't3', symbol: 'TSLA', side: 'SHORT', entryPrice: 210.00, exitPrice: 196.50, pnl: 135, status: 'closed', __typename: 'RecentTrade' },
  { id: 't4', symbol: 'MSFT', side: 'LONG', entryPrice: 410.00, exitPrice: 415.00, pnl: 50, status: 'open', __typename: 'RecentTrade' },
];

export const DEMO_MARKET_NEWS = [
  { id: 'n1', title: 'Fed signals rate cut timeline, markets rally', summary: 'Federal Reserve officials indicated potential cuts later this year as inflation cools toward target.', source: 'Reuters', impact: 'bullish', sentiment: 0.72, relatedSymbols: ['SPY', 'QQQ'], __typename: 'MarketNewsItem' },
  { id: 'n2', title: 'NVIDIA Blackwell demand exceeds supply guidance', summary: 'CEO Jensen Huang confirmed order backlog extends into 2026, raising revenue outlook.', source: 'Bloomberg', impact: 'bullish', sentiment: 0.91, relatedSymbols: ['NVDA'], __typename: 'MarketNewsItem' },
  { id: 'n3', title: 'Tesla price cuts weigh on margins', summary: 'Q2 gross margin fell 150bps as competition in EV market intensifies globally.', source: 'WSJ', impact: 'bearish', sentiment: -0.61, relatedSymbols: ['TSLA'], __typename: 'MarketNewsItem' },
];

export const DEMO_SENTIMENT_INDICATORS = [
  { name: 'Fear & Greed', value: 62, change: 5, signal: 'greed', level: 'moderate', __typename: 'SentimentIndicator' },
  { name: 'Put/Call Ratio', value: 0.82, change: -0.06, signal: 'bullish', level: 'normal', __typename: 'SentimentIndicator' },
  { name: 'AAII Bull %', value: 44.2, change: 3.1, signal: 'bullish', level: 'above_avg', __typename: 'SentimentIndicator' },
  { name: 'Insider Buying', value: 1.8, change: 0.3, signal: 'bullish', level: 'elevated', __typename: 'SentimentIndicator' },
];

// ─── RAHA Signals ─────────────────────────────────────────────────────────────
export const DEMO_RAHA_SIGNALS = [
  {
    id: 'raha-1',
    symbol: 'NVDA',
    timestamp: new Date().toISOString(),
    timeframe: '1D',
    signalType: 'BUY',
    price: 875.40,
    entryPrice: 875.40,
    stopLoss: 850.00,
    takeProfit: 940.00,
    targetPrice: 940.00,
    confidenceScore: 0.89,
    globalRegime: 'bull',
    regimeMultiplier: 1.15,
    regimeNarration: 'Bull market momentum phase — AI infrastructure spending driving tech outperformance.',
    localContext: 'NVDA breaking out above key resistance; Blackwell shipment data beat estimates.',
    meta: JSON.stringify({ sector: 'Technology', catalyst: 'Earnings', mlVersion: 'v3.2' }),
    strategyVersion: {
      id: 'sv-1',
      strategy: { id: 's-1', name: 'RAHA Momentum', slug: 'raha-momentum', __typename: 'Strategy' },
      __typename: 'StrategyVersion',
    },
    __typename: 'RAHASignal',
  },
  {
    id: 'raha-2',
    symbol: 'SPY',
    timestamp: new Date().toISOString(),
    timeframe: '1W',
    signalType: 'HOLD',
    price: 524.30,
    entryPrice: 524.30,
    stopLoss: 505.00,
    takeProfit: 545.00,
    targetPrice: 545.00,
    confidenceScore: 0.72,
    globalRegime: 'bull',
    regimeMultiplier: 1.05,
    regimeNarration: 'Broad market in consolidation after Q1 run — risk/reward balanced at current levels.',
    localContext: 'SPY holding 20-week MA; breadth metrics neutral. Watch Fed commentary.',
    meta: JSON.stringify({ sector: 'ETF', catalyst: 'Macro', mlVersion: 'v3.2' }),
    strategyVersion: {
      id: 'sv-1',
      strategy: { id: 's-1', name: 'RAHA Momentum', slug: 'raha-momentum', __typename: 'Strategy' },
      __typename: 'StrategyVersion',
    },
    __typename: 'RAHASignal',
  },
  {
    id: 'raha-3',
    symbol: 'MSFT',
    timestamp: new Date().toISOString(),
    timeframe: '1D',
    signalType: 'BUY',
    price: 415.20,
    entryPrice: 415.20,
    stopLoss: 398.00,
    takeProfit: 455.00,
    targetPrice: 455.00,
    confidenceScore: 0.81,
    globalRegime: 'bull',
    regimeMultiplier: 1.10,
    regimeNarration: 'Cloud and AI capex cycle supports large-cap tech premium valuations.',
    localContext: 'MSFT consolidating above 20-week MA; Copilot enterprise deals accelerating.',
    meta: JSON.stringify({ sector: 'Technology', catalyst: 'Earnings', mlVersion: 'v3.2' }),
    strategyVersion: {
      id: 'sv-1',
      strategy: { id: 's-1', name: 'RAHA Momentum', slug: 'raha-momentum', __typename: 'Strategy' },
      __typename: 'StrategyVersion',
    },
    __typename: 'RAHASignal',
  },
];

export const DEMO_RAHA_METRICS = {
  winRate: 68.4,
  expectancy: 1.87,
  sharpeRatio: 1.54,
  maxDrawdown: -7.2,
  __typename: 'RAHAMetrics',
};

// ─── Stocks list ──────────────────────────────────────────────────────────────
export const DEMO_STOCKS = [
  { symbol: 'AAPL', companyName: 'Apple Inc.', currentPrice: 180.00, changePercent: 0.82, volume: 55_000_000, marketCap: 2_800_000_000_000, sector: 'Technology', __typename: 'StockType' },
  { symbol: 'MSFT', companyName: 'Microsoft Corporation', currentPrice: 415.20, changePercent: 1.12, volume: 22_000_000, marketCap: 3_080_000_000_000, sector: 'Technology', __typename: 'StockType' },
  { symbol: 'NVDA', companyName: 'NVIDIA Corporation', currentPrice: 875.40, changePercent: 3.21, volume: 48_000_000, marketCap: 2_160_000_000_000, sector: 'Technology', __typename: 'StockType' },
  { symbol: 'GOOGL', companyName: 'Alphabet Inc.', currentPrice: 172.50, changePercent: 0.64, volume: 18_000_000, marketCap: 2_140_000_000_000, sector: 'Technology', __typename: 'StockType' },
  { symbol: 'AMZN', companyName: 'Amazon.com Inc.', currentPrice: 192.30, changePercent: 1.43, volume: 31_000_000, marketCap: 2_020_000_000_000, sector: 'Consumer Cyclical', __typename: 'StockType' },
  { symbol: 'TSLA', companyName: 'Tesla, Inc.', currentPrice: 196.50, changePercent: -1.21, volume: 95_000_000, marketCap: 625_000_000_000, sector: 'Automotive', __typename: 'StockType' },
  { symbol: 'META', companyName: 'Meta Platforms', currentPrice: 512.30, changePercent: 1.87, volume: 16_000_000, marketCap: 1_310_000_000_000, sector: 'Technology', __typename: 'StockType' },
  { symbol: 'JPM', companyName: 'JPMorgan Chase', currentPrice: 198.50, changePercent: 0.45, volume: 9_000_000, marketCap: 575_000_000_000, sector: 'Financials', __typename: 'StockType' },
  { symbol: 'LLY', companyName: 'Eli Lilly', currentPrice: 780.00, changePercent: 2.10, volume: 3_400_000, marketCap: 740_000_000_000, sector: 'Healthcare', __typename: 'StockType' },
  { symbol: 'SPY', companyName: 'SPDR S&P 500 ETF', currentPrice: 524.30, changePercent: 0.81, volume: 82_000_000, marketCap: 0, sector: 'ETF', __typename: 'StockType' },
];

// ─── Quant Screener ───────────────────────────────────────────────────────────
export const DEMO_QUANT_SCREENER = [
  { symbol: 'NVDA', companyName: 'NVIDIA Corporation', sector: 'Technology', marketCap: 2_160_000_000_000, peRatio: 62.4, beginnerFriendlyScore: 72, currentPrice: 875.40, mlScore: 0.92, riskLevel: 'medium', growthPotential: 0.91, score: 94, momentum: 0.92, value: 0.41, quality: 0.88, __typename: 'ScreenerResult' },
  { symbol: 'META', companyName: 'Meta Platforms', sector: 'Technology', marketCap: 1_310_000_000_000, peRatio: 28.1, beginnerFriendlyScore: 78, currentPrice: 512.30, mlScore: 0.85, riskLevel: 'medium', growthPotential: 0.84, score: 88, momentum: 0.85, value: 0.62, quality: 0.79, __typename: 'ScreenerResult' },
  { symbol: 'MSFT', companyName: 'Microsoft Corporation', sector: 'Technology', marketCap: 3_080_000_000_000, peRatio: 36.8, beginnerFriendlyScore: 88, currentPrice: 415.20, mlScore: 0.81, riskLevel: 'low', growthPotential: 0.79, score: 86, momentum: 0.81, value: 0.55, quality: 0.91, __typename: 'ScreenerResult' },
  { symbol: 'LLY',  companyName: 'Eli Lilly', sector: 'Healthcare', marketCap: 740_000_000_000, peRatio: 58.2, beginnerFriendlyScore: 65, currentPrice: 780.00, mlScore: 0.79, riskLevel: 'medium', growthPotential: 0.85, score: 83, momentum: 0.79, value: 0.38, quality: 0.84, __typename: 'ScreenerResult' },
  { symbol: 'AAPL', companyName: 'Apple Inc.', sector: 'Technology', marketCap: 2_800_000_000_000, peRatio: 29.4, beginnerFriendlyScore: 92, currentPrice: 180.00, mlScore: 0.76, riskLevel: 'low', growthPotential: 0.72, score: 80, momentum: 0.76, value: 0.60, quality: 0.88, __typename: 'ScreenerResult' },
  { symbol: 'XOM',  companyName: 'Exxon Mobil', sector: 'Energy', marketCap: 500_000_000_000, peRatio: 14.2, beginnerFriendlyScore: 82, currentPrice: 118.60, mlScore: 0.74, riskLevel: 'low', growthPotential: 0.61, score: 76, momentum: 0.62, value: 0.81, quality: 0.77, __typename: 'ScreenerResult' },
];

// ─── Budget / Spending ────────────────────────────────────────────────────────
export const DEMO_BUDGET_DATA = {
  monthlyIncome: 8500,
  monthlyExpenses: 5200,
  savingsRate: 38.8,
  categories: [
    { name: 'Housing', budgeted: 2000, spent: 1950, __typename: 'BudgetCategory' },
    { name: 'Food', budgeted: 700, spent: 820, __typename: 'BudgetCategory' },
    { name: 'Transport', budgeted: 400, spent: 385, __typename: 'BudgetCategory' },
    { name: 'Subscriptions', budgeted: 150, spent: 148, __typename: 'BudgetCategory' },
    { name: 'Entertainment', budgeted: 300, spent: 270, __typename: 'BudgetCategory' },
    { name: 'Investing', budgeted: 1500, spent: 1500, __typename: 'BudgetCategory' },
  ],
  __typename: 'BudgetData',
};

export const DEMO_SPENDING_ANALYSIS = {
  totalSpent: 5200,
  categories: DEMO_BUDGET_DATA.categories,
  topMerchants: [
    { name: 'Trader Joe\'s', amount: 420, category: 'Food', __typename: 'MerchantSpend' },
    { name: 'Netflix', amount: 22, category: 'Subscriptions', __typename: 'MerchantSpend' },
    { name: 'Shell', amount: 185, category: 'Transport', __typename: 'MerchantSpend' },
  ],
  trends: 'Spending is 3% under budget this month. Food category slightly over — consider meal planning.',
  __typename: 'SpendingAnalysis',
};

// ─── Futures (REST /api/futures/) ─────────────────────────────────────────────
export const DEMO_FUTURES = {
  recommendations: [
    { symbol: 'ES', name: 'S&P 500 Futures', side: 'LONG', entry: 5243.00, stop: 5200.00, target: 5320.00, confidence: 0.82 },
    { symbol: 'NQ', name: 'Nasdaq 100 Futures', side: 'LONG', entry: 18420.00, stop: 18200.00, target: 18900.00, confidence: 0.79 },
    { symbol: 'CL', name: 'Crude Oil Futures', side: 'SHORT', entry: 78.40, stop: 80.50, target: 74.00, confidence: 0.71 },
  ],
  positions: [],
  prices: {
    ES: { price: 5243.00, change: 18.50, changePercent: 0.35 },
    NQ: { price: 18420.00, change: 95.00, changePercent: 0.52 },
    CL: { price: 78.40, change: -0.80, changePercent: -1.01 },
  },
};

// ─── Holding Insight (REST /api/coach/holding-insight) ───────────────────────
export const DEMO_HOLDING_INSIGHTS: Record<string, { headline: string; drivers: string[] }> = {
  AAPL: { headline: 'Services revenue growing faster than hardware — margin expansion story intact', drivers: ['App Store record revenue', 'Apple Intelligence driving upgrades', 'Wearables stabilising'] },
  MSFT: { headline: 'Azure re-accelerating as AI workloads shift to cloud', drivers: ['Copilot enterprise adoption', 'OpenAI partnership monetisation', 'Gaming segment recovering'] },
  NVDA: { headline: 'Blackwell ramp confirms $100B revenue trajectory for FY2026', drivers: ['Data centre demand outpacing supply', 'Sovereign AI spending rising', 'Software / CUDA moat deepening'] },
  GOOGL: { headline: 'Search dominance intact; Gemini integration boosts monetisation', drivers: ['AI Overviews not cannibalising clicks', 'YouTube Shorts ad load increasing', 'Cloud margin expansion'] },
  AMZN: { headline: 'AWS growth re-accelerating; retail margin at multi-year high', drivers: ['Gen AI services on AWS growing 3×', 'Same-day delivery reducing fulfilment cost', 'Advertising becoming third major pillar'] },
  TSLA: { headline: 'Margin pressure continues as price competition intensifies', drivers: ['Gross margin fell to 17.4%', 'BYD overtook in volume globally', 'FSD timeline uncertainty remains'] },
  SPY: { headline: 'S&P 500 in a broadening bull — small/mid caps catching up to mega-cap', drivers: ['Earnings breadth improving', 'Rate cut expectations supportive', 'GDP growth above 2%'] },
  META: { headline: 'Ad platform firing on all cylinders; AI-driven targeting gains share', drivers: ['ROAS outperforming peers', 'Llama 3 reducing inference cost', 'Threads monetisation ahead of schedule'] },
  DEFAULT: { headline: 'AI insight ready — add to watchlist for personalised analysis', drivers: ['Market analysis updated daily', 'Powered by RichesReach AI'] },
};

// Helper to get insight for any ticker
export function getDemoHoldingInsight(ticker: string): { headline: string; drivers: string[] } {
  return DEMO_HOLDING_INSIGHTS[ticker.toUpperCase()] ?? DEMO_HOLDING_INSIGHTS.DEFAULT;
}
