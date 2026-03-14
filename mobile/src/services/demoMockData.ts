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
  regime: 'Expansion',
  narrative: 'Equities are in a risk-on phase driven by AI capex and better-than-expected earnings. Breadth remains healthy with 68% of S&P 500 names above their 200-day MA. Fed pivot expectations are supporting valuations and the labour market remains resilient.',
  top_bullish: [
    {
      ticker: 'NVDA',
      signal: 'Bullish',
      confidence: 'High',
      reasons: ['AI infrastructure demand accelerating', 'Blackwell GPU ramp ahead of schedule', 'Data-centre capex cycle intact'],
    },
    {
      ticker: 'MSFT',
      signal: 'Bullish',
      confidence: 'High',
      reasons: ['Cloud growth beating estimates', 'Copilot monetisation gaining traction'],
    },
    {
      ticker: 'AAPL',
      signal: 'Bullish',
      confidence: 'Medium',
      reasons: ['Services revenue expanding margins', 'iPhone upgrade cycle approaching'],
    },
  ],
  top_bearish: [
    {
      ticker: 'TSLA',
      signal: 'Bearish',
      confidence: 'High',
      reasons: ['Margin pressure from aggressive price cuts', 'EV demand softening in key markets'],
    },
    {
      ticker: 'COIN',
      signal: 'Bearish',
      confidence: 'Medium',
      reasons: ['Regulatory headwinds persist', 'Crypto volumes declining'],
    },
  ],
  generated_at: new Date().toISOString(),
  from_cache: false,
};

// ─── Daily Brief (REST /api/daily-brief/today) ───────────────────────────────
export const DEMO_DAILY_BRIEF = {
  id: 'demo-brief-001',
  date: new Date().toISOString().split('T')[0],
  market_summary: 'Markets opened higher today as strong jobs data calmed recession fears. The S&P 500 is up 0.8% led by technology and energy sectors.',
  personalized_action: 'Your NVDA position is up 4.2% this week — consider whether to take partial profits or hold through earnings next week.',
  action_type: 'review_portfolio',
  lesson_id: 'demo-lesson-001',
  lesson_title: 'Understanding P/E Ratios',
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
  regime: 'Expansion',          // matches regimeColour map: green #10B981
  gate_multiplier: 1.0,         // "Full" sizing gate — no restrictions
  sizing_down_pct: 0,
  narrative: 'Market regime confirmed Expansion — risk-on conditions intact. Your portfolio volatility (14.2%) is below the 90-day average (18.5%) and sector diversification is healthy across Technology, ETF, and Energy. Full position sizing is authorised.',
  risk_score: 38,               // low risk score (good for demo)
  max_drawdown_30d: -3.8,
  var_95: -287,
  sharpe_30d: 1.54,
  beta: 1.12,
});

// ─── Quant Terminal (Options tab — Portfolio risk / Vol surface / Edge decay / Regime / Portfolio DNA) ─
export const DEMO_QUANT_VOL_SURFACE = {
  symbol: 'AAPL',
  strikes: [160, 170, 180, 190, 200, 210],
  expirations: ['2025-04-18', '2025-05-16', '2025-06-20', '2025-07-18'],
  iv_matrix: [
    [0.28, 0.26, 0.24, 0.22, 0.23, 0.25],
    [0.26, 0.25, 0.23, 0.22, 0.23, 0.24],
    [0.24, 0.24, 0.23, 0.22, 0.23, 0.24],
    [0.23, 0.23, 0.22, 0.22, 0.23, 0.24],
  ],
  timestamp: new Date().toISOString(),
};

export const DEMO_QUANT_EDGE_DECAY = {
  strategy_name: 'long_call',
  symbol: 'AAPL',
  time_points: ['0', '7', '14', '21', '30', '45', '60'],
  edge_values: [0.42, 0.38, 0.32, 0.26, 0.20, 0.12, 0.06],
  confidence_values: [0.88, 0.82, 0.75, 0.68, 0.58, 0.45, 0.32],
  decay_rate: 0.08,
  half_life_days: 12,
  timestamp: new Date().toISOString(),
};

export const DEMO_QUANT_REGIME_TIMELINE = {
  start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  end_date: new Date().toISOString().split('T')[0],
  events: [
    { date: new Date().toISOString().split('T')[0], regime: 'Expansion', headline: 'Risk-on conditions intact', confidence: 0.85, market_impact: 0.02 },
    { date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], regime: 'Expansion', headline: 'Breadth improving', confidence: 0.78, market_impact: 0.01 },
  ],
  transitions: [
    { from: 'Contraction', to: 'Expansion', date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], duration_days: 5, volatility_spike: 1.2 },
  ],
  timestamp: new Date().toISOString(),
};

export const DEMO_QUANT_PORTFOLIO_DNA = {
  user_id: 'demo-user-1',
  fingerprint: {
    win_rate: 0.58,
    profit_factor: 1.52,
    avg_holding_period_days: 12,
    preferred_iv_regime: 'mid',
    preferred_dte_range: '21-45',
    risk_tolerance: 0.6,
    strategy_preferences: { long_call: 0.35, put_spread: 0.25, covered_call: 0.2, straddle: 0.2 },
    sharpe_ratio: 1.24,
    max_drawdown: -0.12,
    total_trades: 84,
    best_performing_strategy: 'long_call',
    worst_performing_strategy: 'naked_put',
  },
  archetype: 'Balanced growth',
  archetype_breakdown: { growth: 0.5, income: 0.3, speculation: 0.2 },
  strengths: ['Consistent with 21–45 DTE', 'Good win rate on defined-risk spreads', 'Disciplined position sizing'],
  weaknesses: ['Naked puts have drawn down in vol spikes', 'Holding period sometimes too short'],
  recommendations: ['Size down naked puts or replace with spreads', 'Consider 30–60 DTE for higher-probability names'],
  timestamp: new Date().toISOString(),
};

// ─── Demo options positions (Options tab — Portfolio Risk Management) ───────────
// OCC format: SYMBOL + YYMMDD + C/P + STRIKE (8 digits). Used when EXPO_PUBLIC_DEMO_MODE=true.
export const DEMO_OPTIONS_POSITIONS = [
  {
    symbol: 'AAPL250418C00190000',
    qty: 2,
    side: 'long' as const,
    marketValue: 840,
    avgEntryPrice: 3.80,
    currentPrice: 4.20,
    unrealizedPl: 80,
    unrealizedPL: 80,
    unrealized_pl: 80,
    unrealized_plpc: 0.105,
    avg_entry_price: 3.80,
    current_price: 4.20,
    market_value: 840,
    cost_basis: 760,
  },
  {
    symbol: 'MSFT250620C00420000',
    qty: 1,
    side: 'long' as const,
    marketValue: 325,
    avgEntryPrice: 2.90,
    currentPrice: 3.25,
    unrealizedPl: 35,
    unrealizedPL: 35,
    unrealized_pl: 35,
    unrealized_plpc: 0.121,
    avg_entry_price: 2.90,
    current_price: 3.25,
    market_value: 325,
    cost_basis: 290,
  },
  {
    symbol: 'NVDA250517P00850000',
    qty: 1,
    side: 'long' as const,
    marketValue: 420,
    avgEntryPrice: 5.10,
    currentPrice: 4.20,
    unrealizedPl: -90,
    unrealizedPL: -90,
    unrealized_pl: -90,
    unrealized_plpc: -0.176,
    avg_entry_price: 5.10,
    current_price: 4.20,
    market_value: 420,
    cost_basis: 510,
  },
];

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

// ─── Swing Trading Signals (schema matches GetSwingSignals query) ─────────────
const now = Date.now();
const demoCreatedBy = { id: 'demo-1', username: 'system', name: 'AI Signals', __typename: 'User' as const };

function demoTechnicalIndicatorsList(obj: Record<string, number | string>) {
  return Object.entries(obj).map(([name, value]) => ({
    name: name.toUpperCase(),
    value: typeof value === 'number' ? value : 0,
    signal: typeof value === 'string' ? value : 'neutral',
    strength: 'medium',
    description: `${name}: ${value}`,
    __typename: 'TechnicalIndicator' as const,
  }));
}

function demoPatternsList(names: string[], timeframe: string) {
  return names.map(name => ({
    name,
    confidence: 0.85,
    signal: 'bullish',
    description: `Pattern: ${name.replace(/_/g, ' ')}`,
    timeframe,
    __typename: 'PatternRecognition' as const,
  }));
}

export const DEMO_SWING_SIGNALS = [
  {
    id: 'sig-1',
    symbol: 'MSFT',
    companyName: 'Microsoft Corporation',
    timeframe: '2-4 weeks',
    triggeredAt: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString(),
    signalType: 'LONG',
    entryPrice: 415.00,
    stopPrice: 398.00,
    targetPrice: 455.00,
    mlScore: 0.87,
    thesis: 'Azure growth re-acceleration; AI Copilot uptake stronger than expected. Technical: consolidation above 20-week MA with rising volume.',
    riskRewardRatio: 2.35,
    daysSinceTriggered: 2,
    isLikedByUser: false,
    userLikeCount: 142,
    features: {},
    isActive: true,
    isValidated: true,
    validationPrice: 416.50,
    validationTimestamp: new Date(now - 1 * 24 * 60 * 60 * 1000).toISOString(),
    createdBy: demoCreatedBy,
    technicalIndicators: demoTechnicalIndicatorsList({ rsi: 58, macd: 'bullish_cross', bb_position: 'mid', adx: 32 }),
    patterns: demoPatternsList(['ascending_triangle', 'volume_accumulation'], '2-4 weeks'),
    __typename: 'SwingSignal' as const,
  },
  {
    id: 'sig-2',
    symbol: 'JPM',
    companyName: 'JPMorgan Chase',
    timeframe: '3-6 weeks',
    triggeredAt: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString(),
    signalType: 'LONG',
    entryPrice: 198.50,
    stopPrice: 190.00,
    targetPrice: 218.00,
    mlScore: 0.81,
    thesis: 'Net interest income still expanding; credit quality holding. Trading below historical P/B with 2.8% dividend yield as cushion.',
    riskRewardRatio: 2.24,
    daysSinceTriggered: 3,
    isLikedByUser: false,
    userLikeCount: 98,
    features: {},
    isActive: true,
    isValidated: true,
    validationPrice: 199.20,
    validationTimestamp: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString(),
    createdBy: demoCreatedBy,
    technicalIndicators: demoTechnicalIndicatorsList({ rsi: 52, macd: 'positive', bb_position: 'lower_mid', adx: 28 }),
    patterns: demoPatternsList(['bull_flag', 'support_hold'], '3-6 weeks'),
    __typename: 'SwingSignal' as const,
  },
  {
    id: 'sig-3',
    symbol: 'LLY',
    companyName: 'Eli Lilly',
    timeframe: '4-8 weeks',
    triggeredAt: new Date(now - 5 * 24 * 60 * 60 * 1000).toISOString(),
    signalType: 'LONG',
    entryPrice: 780.00,
    stopPrice: 748.00,
    targetPrice: 850.00,
    mlScore: 0.79,
    thesis: 'GLP-1 demand continues to outpace supply. Pipeline optionality in Alzheimer\'s space. Defensive growth in uncertain macro.',
    riskRewardRatio: 2.19,
    daysSinceTriggered: 5,
    isLikedByUser: false,
    userLikeCount: 203,
    features: {},
    isActive: true,
    isValidated: true,
    validationPrice: 782.00,
    validationTimestamp: new Date(now - 4 * 24 * 60 * 60 * 1000).toISOString(),
    createdBy: demoCreatedBy,
    technicalIndicators: demoTechnicalIndicatorsList({ rsi: 61, macd: 'bullish', bb_position: 'upper_mid', adx: 38 }),
    patterns: demoPatternsList(['cup_and_handle', 'breakout_pending'], '4-8 weeks'),
    __typename: 'SwingSignal' as const,
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

// ─── Oracle Insights (GetOracleInsights) ───────────────────────────────────────
export const DEMO_ORACLE_INSIGHTS = {
  id: 'oracle-demo-1',
  question: 'What is the outlook for tech stocks given current macro conditions?',
  answer: 'Tech remains supported by AI capex and resilient earnings. We maintain a neutral-to-positive bias with a preference for quality large caps (NVDA, MSFT) over speculative names. Key risks: rates staying higher for longer and multiple compression.',
  confidence: 0.82,
  sources: ['Macro regime model', 'Sector flow data', 'Earnings revisions'],
  timestamp: new Date().toISOString(),
  relatedInsights: [] as string[],
  __typename: 'OracleInsightType',
};

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

// ─── Transparency Dashboard ───────────────────────────────────────────────────
const transparencyBase = new Date();
const daysAgo = (d: number) => new Date(transparencyBase.getTime() - d * 86_400_000).toISOString();

export const DEMO_TRANSPARENCY_SIGNALS = [
  { id: 1, symbol: 'NVDA', action: 'BUY', confidence: 0.89, entryPrice: 820.00, entryTimestamp: daysAgo(18), exitPrice: 875.40, exitTimestamp: daysAgo(11), pnl: 554.00, pnlPercent: 0.0677, status: 'CLOSED', reasoning: 'Blackwell ramp confirmed; data-centre demand exceeding supply estimates.', tradingMode: 'PAPER', signalId: 'sig-001', __typename: 'SignalRecordType' },
  { id: 2, symbol: 'AAPL', action: 'BUY', confidence: 0.81, entryPrice: 172.00, entryTimestamp: daysAgo(15), exitPrice: 180.00, exitTimestamp: daysAgo(8), pnl: 80.00, pnlPercent: 0.0465, status: 'CLOSED', reasoning: 'Services revenue beat; Apple Intelligence upgrade cycle beginning.', tradingMode: 'PAPER', signalId: 'sig-002', __typename: 'SignalRecordType' },
  { id: 3, symbol: 'TSLA', action: 'SELL', confidence: 0.74, entryPrice: 210.00, entryTimestamp: daysAgo(12), exitPrice: 196.50, exitTimestamp: daysAgo(5), pnl: 135.00, pnlPercent: 0.0643, status: 'CLOSED', reasoning: 'Gross margin compression below 18%; BYD volume overtake confirmed.', tradingMode: 'PAPER', signalId: 'sig-003', __typename: 'SignalRecordType' },
  { id: 4, symbol: 'MSFT', action: 'BUY', confidence: 0.83, entryPrice: 410.00, entryTimestamp: daysAgo(9), exitPrice: null, exitTimestamp: null, pnl: null, pnlPercent: null, status: 'OPEN', reasoning: 'Azure re-acceleration; Copilot enterprise seats growing faster than consensus.', tradingMode: 'PAPER', signalId: 'sig-004', __typename: 'SignalRecordType' },
  { id: 5, symbol: 'META', action: 'BUY', confidence: 0.79, entryPrice: 495.00, entryTimestamp: daysAgo(22), exitPrice: 512.30, exitTimestamp: daysAgo(14), pnl: 173.00, pnlPercent: 0.0350, status: 'CLOSED', reasoning: 'Ad ROAS recovery; Llama inference cost cuts boosting margin outlook.', tradingMode: 'PAPER', signalId: 'sig-005', __typename: 'SignalRecordType' },
  { id: 6, symbol: 'COIN', action: 'ABSTAIN', confidence: 0.52, entryPrice: null, entryTimestamp: daysAgo(20), exitPrice: null, exitTimestamp: null, pnl: null, pnlPercent: null, status: 'ABSTAINED', reasoning: 'Regulatory uncertainty too high; risk/reward insufficient at current levels.', tradingMode: 'PAPER', signalId: 'sig-006', __typename: 'SignalRecordType' },
  { id: 7, symbol: 'LLY', action: 'BUY', confidence: 0.77, entryPrice: 750.00, entryTimestamp: daysAgo(30), exitPrice: 780.00, exitTimestamp: daysAgo(19), pnl: 300.00, pnlPercent: 0.0400, status: 'CLOSED', reasoning: 'GLP-1 prescription data accelerating; pipeline FDA catalyst upcoming.', tradingMode: 'PAPER', signalId: 'sig-007', __typename: 'SignalRecordType' },
  { id: 8, symbol: 'SPY', action: 'BUY', confidence: 0.71, entryPrice: 510.00, entryTimestamp: daysAgo(7), exitPrice: null, exitTimestamp: null, pnl: null, pnlPercent: null, status: 'OPEN', reasoning: 'Broad market breadth improving; 68% of S&P 500 above 200-day MA.', tradingMode: 'PAPER', signalId: 'sig-008', __typename: 'SignalRecordType' },
];

export const DEMO_TRANSPARENCY_STATISTICS = {
  totalSignals: 8,
  closedSignals: 5,
  openSignals: 2,
  abstainedSignals: 1,
  winRate: 1.0,
  totalWins: 5,
  totalLosses: 0,
  avgWin: 248.40,
  avgLoss: 0,
  totalPnl: 1242.00,
  profitFactor: null,
  lastUpdated: transparencyBase.toISOString(),
  __typename: 'TransparencyStatisticsType',
};

export const DEMO_TRANSPARENCY_DASHBOARD = {
  signals: DEMO_TRANSPARENCY_SIGNALS,
  statistics: DEMO_TRANSPARENCY_STATISTICS,
  __typename: 'TransparencyDashboardType',
};

export const DEMO_TRANSPARENCY_PERFORMANCE = {
  periodDays: 30,
  totalSignals: 8,
  winRate: 0.833,
  totalPnl: 1242.00,
  avgPnl: 248.40,
  sharpeRatio: 1.87,
  maxDrawdown: -0.042,
  __typename: 'PerformanceSummaryType',
};

// ─── Credit Snapshot (REST /api/credit/snapshot) ─────────────────────────────
export const DEMO_CREDIT_SNAPSHOT = {
  score: {
    score: 725,
    scoreRange: 'Good',
    lastUpdated: new Date().toISOString(),
    provider: 'self_reported',
  },
  cards: [
    {
      id: 'card-1',
      name: 'Chase Sapphire',
      balance: 1240,
      limit: 8000,
      utilization: 0.155,
      paymentDueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
      minimumPayment: 35,
      apr: 0.2199,
    },
    {
      id: 'card-2',
      name: 'Amex Gold',
      balance: 480,
      limit: 5000,
      utilization: 0.096,
      paymentDueDate: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString(),
      minimumPayment: 25,
      apr: 0.2699,
    },
  ],
  utilization: {
    totalLimit: 13000,
    totalBalance: 1720,
    currentUtilization: 0.132,
    optimalUtilization: 0.09,
    paydownSuggestion: 550,
    projectedScoreGain: 12,
  },
  projection: {
    scoreGain6m: 38,
    topAction: 'REDUCE_UTILIZATION',
    confidence: 0.78,
    factors: {
      payment_history: 0.35,
      utilization: 0.30,
      credit_age: 0.15,
      credit_mix: 0.10,
      inquiries: 0.10,
    },
  },
  actions: [
    {
      id: '1',
      type: 'UTILIZATION_REDUCED',
      title: 'Pay Down Chase Sapphire',
      description: 'Pay $550 to bring your utilization from 13.2% to under 9% — the sweet spot for maximum score impact.',
      completed: false,
      projectedScoreGain: 12,
      dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '2',
      type: 'AUTOPAY_SETUP',
      title: 'Set Up Autopay',
      description: 'Automate minimum payments on both cards to protect your perfect payment history (35% of your score).',
      completed: false,
      projectedScoreGain: 8,
      dueDate: null,
    },
    {
      id: '3',
      type: 'CREDIT_LIMIT_INCREASE',
      title: 'Request Credit Limit Increase',
      description: 'With 18 months of on-time payments, Chase may approve a limit increase — lowering utilization without paying down debt.',
      completed: false,
      projectedScoreGain: 15,
      dueDate: null,
    },
  ],
  shield: [],

  // Feature 2: Per-bureau scores for arbitrage (Equifax notably higher)
  bureauScores: {
    experian:   720,
    equifax:    763,   // +43 pts higher — arbitrage window is open
    transunion: 737,
    lastPulled: new Date().toISOString(),
  },

  // Feature 3: Unreported recurring payments
  unreportedPayments: [
    {
      type: 'rent',
      description: 'Monthly Rent',
      monthlyAmount: 1400,
      reportingService: 'Experian RentBureau',
      estimatedPointsGain: 22,
      estimatedTimeToImpact: '45 days',
    },
    {
      type: 'utility',
      description: 'Electric & Gas Bills',
      monthlyAmount: 185,
      reportingService: 'Experian Boost',
      estimatedPointsGain: 8,
      estimatedTimeToImpact: '2 weeks',
    },
    {
      type: 'subscription',
      description: 'Netflix, Spotify, Disney+',
      monthlyAmount: 47,
      reportingService: 'Experian Boost',
      estimatedPointsGain: 4,
      estimatedTimeToImpact: '2 weeks',
    },
  ],
};

// ─── Budget / Spending ────────────────────────────────────────────────────────
export const DEMO_BUDGET_DATA = {
  monthlyIncome: 8500,
  monthlyExpenses: 5200,
  savingsRate: 38.8,
  remaining: 3300,
  categories: [
    { name: 'Housing', budgeted: 2000, spent: 1950, percentage: 97.5, __typename: 'BudgetCategory' },
    { name: 'Food', budgeted: 700, spent: 820, percentage: 117.1, __typename: 'BudgetCategory' },
    { name: 'Transport', budgeted: 400, spent: 385, percentage: 96.3, __typename: 'BudgetCategory' },
    { name: 'Subscriptions', budgeted: 150, spent: 148, percentage: 98.7, __typename: 'BudgetCategory' },
    { name: 'Entertainment', budgeted: 300, spent: 270, percentage: 90, __typename: 'BudgetCategory' },
    { name: 'Investing', budgeted: 1500, spent: 1500, percentage: 100, __typename: 'BudgetCategory' },
  ],
  __typename: 'BudgetData',
};

// Spending analysis schema: categories use amount/percentage/transactions/trend (not budgeted/spent)
const _demoSpendingCategories = [
  { name: 'Housing', amount: 1950, percentage: 37.5, transactions: 3, trend: 'stable' as const, __typename: 'SpendingCategory' as const },
  { name: 'Food', amount: 820, percentage: 15.8, transactions: 42, trend: 'up' as const, __typename: 'SpendingCategory' as const },
  { name: 'Transport', amount: 385, percentage: 7.4, transactions: 18, trend: 'down' as const, __typename: 'SpendingCategory' as const },
  { name: 'Subscriptions', amount: 148, percentage: 2.8, transactions: 6, trend: 'stable' as const, __typename: 'SpendingCategory' as const },
  { name: 'Entertainment', amount: 270, percentage: 5.2, transactions: 12, trend: 'up' as const, __typename: 'SpendingCategory' as const },
  { name: 'Investing', amount: 1500, percentage: 28.8, transactions: 4, trend: 'stable' as const, __typename: 'SpendingCategory' as const },
];

export const DEMO_SPENDING_ANALYSIS = {
  totalSpent: 5200,
  categories: _demoSpendingCategories,
  topMerchants: [
    { name: 'Trader Joe\'s', amount: 420, category: 'Food', count: 14, __typename: 'MerchantSpend' as const },
    { name: 'Netflix', amount: 22, category: 'Subscriptions', count: 1, __typename: 'MerchantSpend' as const },
    { name: 'Shell', amount: 185, category: 'Transport', count: 8, __typename: 'MerchantSpend' as const },
  ],
  trends: [
    { period: 'Jan', amount: 5100, change: 0 },
    { period: 'Feb', amount: 5350, change: 4.9 },
    { period: 'Mar', amount: 5200, change: -2.8 },
  ],
  __typename: 'SpendingAnalysis' as const,
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
export interface DemoHoldingInsightShape {
  headline: string;
  drivers: string[];
  repairSuggestion?: string;
  whyRepair?: string;
  learnMoreTopic?: string;
}

export const DEMO_HOLDING_INSIGHTS: Record<string, DemoHoldingInsightShape> = {
  AAPL: { headline: 'Services revenue growing faster than hardware — margin expansion story intact', drivers: ['App Store record revenue', 'Apple Intelligence driving upgrades', 'Wearables stabilising'] },
  MSFT: { headline: 'Azure re-accelerating as AI workloads shift to cloud', drivers: ['Copilot enterprise adoption', 'OpenAI partnership monetisation', 'Gaming segment recovering'] },
  NVDA: { headline: 'Blackwell ramp confirms $100B revenue trajectory for FY2026', drivers: ['Data centre demand outpacing supply', 'Sovereign AI spending rising', 'Software / CUDA moat deepening'] },
  GOOGL: {
    headline: 'Search dominance intact; Gemini integration boosts monetisation',
    drivers: ['AI Overviews not cannibalising clicks', 'YouTube Shorts ad load increasing', 'Cloud margin expansion'],
    repairSuggestion: 'Consider a covered call to reduce your cost basis',
    whyRepair: 'Selling a call against your shares collects premium and can lower your effective purchase price. If the stock stays flat or dips, you keep the premium; if it rises past the strike, you may be called away at a profit.',
    learnMoreTopic: 'Covered calls and reducing cost basis',
  },
  AMZN: {
    headline: 'AWS growth re-accelerating; retail margin at multi-year high',
    drivers: ['Gen AI services on AWS growing 3×', 'Same-day delivery reducing fulfilment cost', 'Advertising becoming third major pillar'],
    repairSuggestion: 'Consider a covered call to reduce your cost basis',
    whyRepair: 'Your position is under pressure. A covered call lets you earn premium and lower your breakeven. You keep the shares if the stock stays below the strike, and the premium cushions further downside.',
    learnMoreTopic: 'Defensive strategies for down positions',
  },
  TSLA: {
    headline: 'Margin pressure continues as price competition intensifies',
    drivers: ['Gross margin fell to 17.4%', 'BYD overtook in volume globally', 'FSD timeline uncertainty remains'],
    repairSuggestion: 'Consider a covered call or selling cash-secured put to improve basis',
    whyRepair: 'IV expansion can work in your favor: selling options collects more premium. A covered call reduces risk and cost basis; a cash-secured put can let you add shares at a lower price if you’re bullish long term.',
    learnMoreTopic: 'Options when your stock is under pressure',
  },
  SPY: { headline: 'S&P 500 in a broadening bull — small/mid caps catching up to mega-cap', drivers: ['Earnings breadth improving', 'Rate cut expectations supportive', 'GDP growth above 2%'] },
  META: { headline: 'Ad platform firing on all cylinders; AI-driven targeting gains share', drivers: ['ROAS outperforming peers', 'Llama 3 reducing inference cost', 'Threads monetisation ahead of schedule'] },
  DEFAULT: {
    headline: 'AI insight ready — add to watchlist for personalised analysis',
    drivers: ['Market analysis updated daily', 'Powered by RichesReach AI'],
    repairSuggestion: 'Consider defensive strategies to reduce cost basis',
    whyRepair: 'When a position is down, covered calls can collect premium and lower your breakeven. Learn how in the lesson below.',
    learnMoreTopic: 'Defensive strategies for your portfolio',
  },
};

// Helper to get insight for any ticker
export function getDemoHoldingInsight(ticker: string): DemoHoldingInsightShape {
  return DEMO_HOLDING_INSIGHTS[ticker.toUpperCase()] ?? DEMO_HOLDING_INSIGHTS.DEFAULT;
}

// ─── Financial GPS: Leak Detector ──────────────────────────────────────────────
export const DEMO_FINANCIAL_LEAKS = {
  totalMonthlyLeak: 287,
  totalAnnualLeak: 3444,
  savingsImpact5yr: 19842,
  headlineSentence: 'You have 8 recurring subscriptions draining $287/month. Cancelling unused ones could grow to $19,842 in 5 years.',
  topLeak: {
    merchantName: 'Adobe Creative Cloud',
    normalizedName: 'Adobe Creative Cloud',
    cadence: 'monthly',
    confidence: 0.95,
    monthlyEquivalent: 79.99,
    category: 'Software/Tools',
    easyToForget: true,
    __typename: 'DetectedSubscription',
  },
  detectedSubscriptions: [
    { merchantName: 'Adobe Creative Cloud', normalizedName: 'Adobe Creative Cloud', cadence: 'monthly', confidence: 0.95, monthlyEquivalent: 79.99, annualEquivalent: 959.88, category: 'Software/Tools', easyToForget: true, occurrenceCount: 12, lastSeen: new Date(Date.now() - 5 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
    { merchantName: 'Netflix', normalizedName: 'Netflix', cadence: 'monthly', confidence: 0.98, monthlyEquivalent: 22.99, annualEquivalent: 275.88, category: 'Streaming', easyToForget: false, occurrenceCount: 12, lastSeen: new Date(Date.now() - 3 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
    { merchantName: 'Spotify', normalizedName: 'Spotify Premium', cadence: 'monthly', confidence: 0.97, monthlyEquivalent: 15.99, annualEquivalent: 191.88, category: 'Music', easyToForget: false, occurrenceCount: 12, lastSeen: new Date(Date.now() - 2 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
    { merchantName: 'iCloud Storage', normalizedName: 'iCloud+ 200GB', cadence: 'monthly', confidence: 0.92, monthlyEquivalent: 2.99, annualEquivalent: 35.88, category: 'Cloud Storage', easyToForget: true, occurrenceCount: 12, lastSeen: new Date(Date.now() - 8 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
    { merchantName: 'Headspace', normalizedName: 'Headspace', cadence: 'monthly', confidence: 0.88, monthlyEquivalent: 12.99, annualEquivalent: 155.88, category: 'Health/Fitness', easyToForget: true, occurrenceCount: 6, lastSeen: new Date(Date.now() - 10 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
    { merchantName: 'Amazon Prime', normalizedName: 'Amazon Prime', cadence: 'yearly', confidence: 0.99, monthlyEquivalent: 11.58, annualEquivalent: 139.00, category: 'Shopping/Prime', easyToForget: false, occurrenceCount: 1, lastSeen: new Date(Date.now() - 45 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
    { merchantName: 'HBO Max', normalizedName: 'HBO Max', cadence: 'monthly', confidence: 0.94, monthlyEquivalent: 15.99, annualEquivalent: 191.88, category: 'Streaming', easyToForget: true, occurrenceCount: 8, lastSeen: new Date(Date.now() - 12 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
    { merchantName: 'Hinge', normalizedName: 'Hinge Premium', cadence: 'monthly', confidence: 0.85, monthlyEquivalent: 29.99, annualEquivalent: 359.88, category: 'Dating', easyToForget: true, occurrenceCount: 4, lastSeen: new Date(Date.now() - 15 * 86400000).toISOString(), amountVariance: 0, __typename: 'DetectedSubscription' },
  ],
  __typename: 'FinancialLeaksType',
};

// ─── Financial GPS: Wealth Arrival ─────────────────────────────────────────────
export const DEMO_WEALTH_ARRIVAL = {
  userId: 1,
  currentNetWorth: 145000,
  estimatedMonthlyIncome: 8500,
  investableSurplusMonthly: 2200,
  annualContribution: 26400,
  savingsRatePct: 25.9,
  projectionYears: 30,
  riskTolerance: 'moderate',
  targetNetWorth: 1000000,
  currentAge: 32,
  headlineSentence: 'At your current pace, you could reach $1M in 18 years (age 50).',
  dataQuality: 'actual',
  primary: {
    scenario: 'moderate',
    annualReturn: 0.07,
    wealthArrivalYears: 18,
    finalNetWorth: 1024000,
    totalContributions: 475200,
    totalGrowth: 548800,
    milestones: [
      { targetAmount: 200000, yearsAway: 2, arrivalYear: 2028, alreadyAchieved: false, label: '$200K' },
      { targetAmount: 500000, yearsAway: 9, arrivalYear: 2035, alreadyAchieved: false, label: 'Half Million' },
      { targetAmount: 750000, yearsAway: 14, arrivalYear: 2040, alreadyAchieved: false, label: '$750K' },
      { targetAmount: 1000000, yearsAway: 18, arrivalYear: 2044, alreadyAchieved: false, label: 'Millionaire' },
    ],
    yearByYear: Array.from({ length: 30 }, (_, i) => ({
      year: 2026 + i,
      netWorth: Math.round(145000 * Math.pow(1.07, i) + 26400 * ((Math.pow(1.07, i) - 1) / 0.07)),
      portfolioValue: Math.round(120000 * Math.pow(1.07, i) + 26400 * ((Math.pow(1.07, i) - 1) / 0.07)),
      annualContribution: 26400,
    })),
    __typename: 'WealthArrivalScenario',
  },
  scenarios: [
    { scenario: 'conservative', annualReturn: 0.05, wealthArrivalYears: 22, finalNetWorth: 820000, yearByYear: [] },
    { scenario: 'moderate', annualReturn: 0.07, wealthArrivalYears: 18, finalNetWorth: 1024000, yearByYear: [] },
    { scenario: 'aggressive', annualReturn: 0.10, wealthArrivalYears: 14, finalNetWorth: 1380000, yearByYear: [] },
  ],
  __typename: 'WealthArrivalType',
};

// ─── Financial GPS: Net Worth History ──────────────────────────────────────────
export const DEMO_NET_WORTH_HISTORY = {
  userId: 'demo-user-1',
  currentNetWorth: 145000,
  currentPortfolioValue: 120000,
  currentSavingsBalance: 35000,
  currentDebt: 10000,
  change7d: 1250,
  change30d: 4800,
  change90d: 12500,
  change1yr: 32000,
  changePct30d: 3.4,
  allTimeHigh: 148000,
  allTimeHighDate: new Date(Date.now() - 7 * 86400000).toISOString(),
  allTimeLow: 98000,
  allTimeLowDate: new Date(Date.now() - 365 * 86400000).toISOString(),
  increaseStreakDays: 12,
  snapshotCapturedToday: true,
  headlineSentence: 'Your net worth grew $4,800 this month — up 3.4% and on a 12-day winning streak.',
  dataQuality: 'live',
  history: Array.from({ length: 90 }, (_, i) => {
    const capturedAt = new Date(Date.now() - (89 - i) * 86400000);
    const base = 130000 + i * 170;
    const noise = (Math.random() - 0.5) * 2000;
    return {
      capturedAt: capturedAt.toISOString(),
      netWorth: Math.round(base + noise),
      portfolioValue: Math.round((base + noise) * 0.83),
      savingsBalance: Math.round((base + noise) * 0.24),
      debt: 10000,
      __typename: 'NetWorthDataPoint',
    };
  }),
  breakdown: {
    portfolioValue: 120000,
    savingsBalance: 35000,
    realEstateEquity: 0,
    otherAssets: 0,
    totalDebt: 10000,
    __typename: 'NetWorthBreakdown',
  },
  __typename: 'NetWorthHistoryType',
};

// ─── Financial GPS: Financial Health Score ─────────────────────────────────────
export const DEMO_FINANCIAL_HEALTH = {
  userId: 'demo-user-1',
  score: 72,
  grade: 'B',
  headlineSentence: 'Your financial health is strong with room to optimize savings rate and debt payoff.',
  dataQuality: 'live',
  savingsRatePct: 26,
  monthlyIncome: 8500,
  monthlyDebtService: 1870,
  debtToIncomePct: 22,
  emergencyFundMonths: 4.1,
  creditUtilizationPct: 18,
  pillars: [
    { name: 'savings_rate', label: 'Savings Rate', score: 78, grade: 'B', value: 26, unit: '%', weight: 0.25, insight: 'Saving 26% of income — above the recommended 20%', action: 'Consider automating an extra $200/month to max out tax-advantaged accounts', __typename: 'FinancialHealthPillar' },
    { name: 'emergency_fund', label: 'Emergency Fund', score: 68, grade: 'C', value: 4.1, unit: 'months', weight: 0.25, insight: '4.1 months of expenses covered', action: 'Build to 6 months for full protection', __typename: 'FinancialHealthPillar' },
    { name: 'debt_ratio', label: 'Debt-to-Income', score: 62, grade: 'C', value: 22, unit: '%', weight: 0.25, insight: 'Debt-to-income ratio at 22%', action: 'Prioritize paying down high-interest credit card debt', __typename: 'FinancialHealthPillar' },
    { name: 'credit_utilization', label: 'Credit Utilization', score: 82, grade: 'B', value: 18, unit: '%', weight: 0.25, insight: 'Credit utilization at 18% — under the 30% threshold', action: 'Keep utilization below 10% for optimal credit score impact', __typename: 'FinancialHealthPillar' },
  ],
  __typename: 'FinancialHealthType',
};

// ─── Financial GPS: Income Intelligence ────────────────────────────────────────
export const DEMO_INCOME_INTELLIGENCE = {
  userId: 'demo-user-1',
  totalMonthlyIncome: 8500,
  totalAnnualIncome: 102000,
  primaryIncomeMonthly: 7200,
  secondaryIncomeMonthly: 1300,
  incomeDiversityScore: 68,
  streamCount: 4,
  lookbackDays: 90,
  headlineSentence: 'Your income is 85% salary-dependent. Consider building passive income streams.',
  dataQuality: 'live',
  streams: [
    { streamType: 'salary', label: 'Primary Salary', monthlyAmount: 7200, annualAmount: 86400, transactionCount: 3, topSources: ['Acme Corp'], pctOfTotal: 84.7, insight: 'Stable W-2 income — backbone of your finances', __typename: 'IncomeStream' },
    { streamType: 'side_hustle', label: 'Side Consulting', monthlyAmount: 800, annualAmount: 9600, transactionCount: 6, topSources: ['Freelance clients'], pctOfTotal: 9.4, insight: 'Variable 1099 income — consider raising rates', __typename: 'IncomeStream' },
    { streamType: 'passive', label: 'Dividend Income', monthlyAmount: 350, annualAmount: 4200, transactionCount: 12, topSources: ['SCHD', 'VYM', 'O'], pctOfTotal: 4.1, insight: 'Growing passive stream — reinvest for compounding', __typename: 'IncomeStream' },
    { streamType: 'passive', label: 'Interest Income', monthlyAmount: 150, annualAmount: 1800, transactionCount: 3, topSources: ['HYSA', 'Treasury Bills'], pctOfTotal: 1.8, insight: 'Safe yield from savings — consider I-bonds', __typename: 'IncomeStream' },
  ],
  __typename: 'IncomeIntelligenceType',
};

// ─── Financial GPS: Life Decision Simulator ────────────────────────────────────
export const DEMO_LIFE_DECISION = {
  userId: 1,
  currentNetWorth: 145000,
  monthlyIncome: 8500,
  monthlySurplus: 2200,
  dataQuality: 'actual',
  recentSimulations: [
    {
      id: 'sim-1',
      title: 'Buy a $60K car',
      category: 'purchase',
      upfrontCost: 60000,
      monthlyImpact: -850,
      opportunityCost10yr: 142000,
      wealthImpact10yr: -98000,
      verdict: 'significant_impact',
      summary: 'This purchase would delay your millionaire goal by 4.2 years.',
      alternatives: ['Consider a $35K car — saves $42K over 10 years', 'Lease for $450/month to preserve capital'],
      __typename: 'LifeDecisionSimulation',
    },
    {
      id: 'sim-2',
      title: 'Have a baby',
      category: 'life_event',
      upfrontCost: 15000,
      monthlyImpact: -1200,
      opportunityCost10yr: 185000,
      wealthImpact10yr: -142000,
      verdict: 'major_impact',
      summary: 'Adding a child reduces your savings rate significantly but builds invaluable life experiences.',
      alternatives: ['Start a 529 plan now to prepare', 'Build to 12-month emergency fund first'],
      __typename: 'LifeDecisionSimulation',
    },
  ],
  __typename: 'LifeDecisionType',
};

// ─── Money Reallocation Engine ─────────────────────────────────────────────────
export const DEMO_REALLOCATION_STRATEGIES = {
  userId: 1,
  monthlyAmount: 287,
  annualAmount: 3444,
  headlineSentence: 'Investing $287/month could grow to $271,000 in 30 years at 7% return.',
  currentPortfolioSummary: '45% tech, 30% ETF, 15% bonds, 10% cash',
  dataQuality: 'actual',
  strategies: [
    {
      id: 'growth_etf',
      name: 'Growth ETF Investing',
      tagline: 'Long-term capital appreciation via broad market exposure',
      icon: 'trending-up',
      color: '#3B82F6',
      riskLevel: 'moderate',
      timeHorizon: 'long',
      fitScore: 82,
      graphRationale: 'Growth ETFs align well with your moderate risk profile and long time horizon.',
      warning: null,
      examples: [
        { symbol: 'VTI', name: 'Vanguard Total Stock Market', description: 'Entire U.S. stock market in one ETF.', assetClass: 'etf', __typename: 'ExampleAsset' },
        { symbol: 'VOO', name: 'Vanguard S&P 500', description: 'Tracks the 500 largest U.S. companies.', assetClass: 'etf', __typename: 'ExampleAsset' },
        { symbol: 'QQQ', name: 'Invesco QQQ Trust', description: 'Nasdaq-100 for tech-heavy growth.', assetClass: 'etf', __typename: 'ExampleAsset' },
      ],
      projections: [
        { returnRate: 0.05, returnLabel: '5% (conservative)', value10yr: 44500, value20yr: 117500, value30yr: 237000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.07, returnLabel: '7% (moderate)', value10yr: 49700, value20yr: 149300, value30yr: 350000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.10, returnLabel: '10% (aggressive)', value10yr: 58600, value20yr: 212000, value30yr: 658000, __typename: 'ProjectedOutcome' },
      ],
      __typename: 'StrategyCategory',
    },
    {
      id: 'dividend_income',
      name: 'Dividend Income',
      tagline: 'Generate passive income through dividend-paying stocks',
      icon: 'dollar-sign',
      color: '#10B981',
      riskLevel: 'moderate',
      timeHorizon: 'medium',
      fitScore: 75,
      graphRationale: 'Dividend investing generates passive income while you wait for growth.',
      warning: null,
      examples: [
        { symbol: 'SCHD', name: 'Schwab U.S. Dividend Equity', description: 'Quality dividend growers, ~3.5% yield.', assetClass: 'etf', __typename: 'ExampleAsset' },
        { symbol: 'VYM', name: 'Vanguard High Dividend Yield', description: 'High-dividend stocks, ~3% yield.', assetClass: 'etf', __typename: 'ExampleAsset' },
        { symbol: 'O', name: 'Realty Income Corp', description: 'Monthly dividend REIT, ~5% yield.', assetClass: 'reit', __typename: 'ExampleAsset' },
      ],
      projections: [
        { returnRate: 0.05, returnLabel: '5% (conservative)', value10yr: 44500, value20yr: 117500, value30yr: 237000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.07, returnLabel: '7% (moderate)', value10yr: 49700, value20yr: 149300, value30yr: 350000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.10, returnLabel: '10% (aggressive)', value10yr: 58600, value20yr: 212000, value30yr: 658000, __typename: 'ProjectedOutcome' },
      ],
      __typename: 'StrategyCategory',
    },
    {
      id: 'ai_sector',
      name: 'AI & Tech Growth',
      tagline: 'Exposure to artificial intelligence and technology leaders',
      icon: 'cpu',
      color: '#7C3AED',
      riskLevel: 'high',
      timeHorizon: 'long',
      fitScore: 58,
      graphRationale: 'Your portfolio is already 45% in tech. Consider diversifying into other sectors.',
      warning: 'High concentration risk',
      examples: [
        { symbol: 'NVDA', name: 'NVIDIA Corporation', description: 'Leading AI chip maker.', assetClass: 'stock', __typename: 'ExampleAsset' },
        { symbol: 'MSFT', name: 'Microsoft Corporation', description: 'Cloud + AI integration (Azure, Copilot).', assetClass: 'stock', __typename: 'ExampleAsset' },
        { symbol: 'BOTZ', name: 'Global X Robotics & AI ETF', description: 'Basket of robotics and AI companies.', assetClass: 'etf', __typename: 'ExampleAsset' },
      ],
      projections: [
        { returnRate: 0.07, returnLabel: '7% (moderate)', value10yr: 49700, value20yr: 149300, value30yr: 350000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.10, returnLabel: '10% (aggressive)', value10yr: 58600, value20yr: 212000, value30yr: 658000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.12, returnLabel: '12% (optimistic)', value10yr: 64200, value20yr: 264000, value30yr: 1020000, __typename: 'ProjectedOutcome' },
      ],
      __typename: 'StrategyCategory',
    },
    {
      id: 'fixed_income',
      name: 'Fixed Income & Bonds',
      tagline: 'Stable, predictable returns with lower volatility',
      icon: 'shield',
      color: '#6366F1',
      riskLevel: 'low',
      timeHorizon: 'short',
      fitScore: 68,
      graphRationale: 'Fixed income provides stability and predictable returns.',
      warning: null,
      examples: [
        { symbol: 'BND', name: 'Vanguard Total Bond Market', description: 'Entire U.S. bond market. Low risk.', assetClass: 'etf', __typename: 'ExampleAsset' },
        { symbol: 'SGOV', name: 'iShares 0-3 Month Treasury', description: 'Ultra-short T-bills, ~5% yield.', assetClass: 'etf', __typename: 'ExampleAsset' },
        { symbol: 'TIP', name: 'iShares TIPS Bond ETF', description: 'Inflation-protected bonds.', assetClass: 'etf', __typename: 'ExampleAsset' },
      ],
      projections: [
        { returnRate: 0.04, returnLabel: '4% (low risk)', value10yr: 42000, value20yr: 103000, value30yr: 194000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.05, returnLabel: '5% (moderate)', value10yr: 44500, value20yr: 117500, value30yr: 237000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.06, returnLabel: '6% (optimistic)', value10yr: 47000, value20yr: 132000, value30yr: 287000, __typename: 'ProjectedOutcome' },
      ],
      __typename: 'StrategyCategory',
    },
    {
      id: 'real_estate',
      name: 'Real Estate (REITs)',
      tagline: 'Real estate exposure without buying property',
      icon: 'home',
      color: '#F59E0B',
      riskLevel: 'moderate',
      timeHorizon: 'medium',
      fitScore: 72,
      graphRationale: 'REITs add real estate exposure without the hassle of property management.',
      warning: null,
      examples: [
        { symbol: 'VNQ', name: 'Vanguard Real Estate ETF', description: 'Broad REIT exposure, ~4% yield.', assetClass: 'etf', __typename: 'ExampleAsset' },
        { symbol: 'STAG', name: 'STAG Industrial', description: 'Industrial warehouses, monthly dividend.', assetClass: 'reit', __typename: 'ExampleAsset' },
        { symbol: 'AMT', name: 'American Tower Corp', description: 'Cell tower infrastructure.', assetClass: 'reit', __typename: 'ExampleAsset' },
      ],
      projections: [
        { returnRate: 0.06, returnLabel: '6% (conservative)', value10yr: 47000, value20yr: 132000, value30yr: 287000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.08, returnLabel: '8% (moderate)', value10yr: 52400, value20yr: 168000, value30yr: 428000, __typename: 'ProjectedOutcome' },
        { returnRate: 0.10, returnLabel: '10% (optimistic)', value10yr: 58600, value20yr: 212000, value30yr: 658000, __typename: 'ProjectedOutcome' },
      ],
      __typename: 'StrategyCategory',
    },
  ],
  __typename: 'ReallocationSuggestion',
};

// ─── AI Portfolio Builder ──────────────────────────────────────────────────────
export const DEMO_BUILD_PORTFOLIO = {
  userId: 1,
  monthlyAmount: 287,
  annualAmount: 3444,
  riskProfile: 'moderate',
  riskRationale: 'A balanced approach suits your current situation with 4+ months emergency fund and stable income.',
  allocations: [
    { strategyId: 'growth_etf', strategyName: 'Growth ETF', percentage: 40, monthlyAmount: 114.80, annualAmount: 1377.60, color: '#3B82F6', icon: 'trending-up', primaryEtf: 'VTI', primaryEtfName: 'Vanguard Total Stock Market', rationale: 'Core holding for long-term wealth building', __typename: 'AllocationSlice' },
    { strategyId: 'dividend_income', strategyName: 'Dividend Income', percentage: 25, monthlyAmount: 71.75, annualAmount: 861.00, color: '#10B981', icon: 'dollar-sign', primaryEtf: 'SCHD', primaryEtfName: 'Schwab U.S. Dividend Equity', rationale: 'Balance growth with passive income', __typename: 'AllocationSlice' },
    { strategyId: 'fixed_income', strategyName: 'Fixed Income', percentage: 20, monthlyAmount: 57.40, annualAmount: 688.80, color: '#6366F1', icon: 'shield', primaryEtf: 'BND', primaryEtfName: 'Vanguard Total Bond Market', rationale: 'Stability during market volatility', __typename: 'AllocationSlice' },
    { strategyId: 'ai_sector', strategyName: 'AI & Tech Growth', percentage: 10, monthlyAmount: 28.70, annualAmount: 344.40, color: '#7C3AED', icon: 'cpu', primaryEtf: 'QQQ', primaryEtfName: 'Invesco QQQ Trust', rationale: 'Targeted exposure to technology growth', __typename: 'AllocationSlice' },
    { strategyId: 'real_estate', strategyName: 'Real Estate', percentage: 5, monthlyAmount: 14.35, annualAmount: 172.20, color: '#F59E0B', icon: 'home', primaryEtf: 'VNQ', primaryEtfName: 'Vanguard Real Estate ETF', rationale: 'Real asset diversification', __typename: 'AllocationSlice' },
  ],
  projected10yr: 49700,
  projected20yr: 149300,
  projected30yr: 350000,
  expectedReturnRate: 0.075,
  milestones: [
    { years: 3, value: 10000, label: 'First $10K milestone', __typename: 'ProjectedMilestone' },
    { years: 10, value: 50000, label: '$50K — Serious portfolio', __typename: 'ProjectedMilestone' },
    { years: 16, value: 100000, label: '$100K — The hardest milestone', __typename: 'ProjectedMilestone' },
    { years: 26, value: 250000, label: '$250K — Quarter millionaire', __typename: 'ProjectedMilestone' },
  ],
  headline: 'Investing $287/month with a moderate approach could grow to $350,000 in 30 years.',
  portfolioAdjustments: ['Reduced tech allocation (you already have 45% tech)'],
  warnings: [],
  dataQuality: 'actual',
  __typename: 'PortfolioBuilderResult',
};

// ─── Investor Profile & Behavioral Identity ──────────────────────────────────

export const DEMO_QUIZ_QUESTIONS = [
  {
    id: 'q1_market_drop',
    text: "A stock you own drops 15% in one week. What's your gut reaction?",
    subtext: 'Be honest — what would you actually do?',
    questionType: 'single_choice',
    options: [
      { id: 'a', text: 'Sell immediately to protect what\'s left', __typename: 'QuizOption' },
      { id: 'b', text: 'Do nothing and wait for recovery', __typename: 'QuizOption' },
      { id: 'c', text: 'Buy more at the "discount"', __typename: 'QuizOption' },
      { id: 'd', text: 'Research why it dropped before deciding', __typename: 'QuizOption' },
    ],
    __typename: 'QuizQuestion',
  },
  {
    id: 'q2_wealth_view',
    text: 'Which statement best describes your view on wealth?',
    questionType: 'single_choice',
    options: [
      { id: 'a', text: 'I want to ensure I never backslide into financial stress', __typename: 'QuizOption' },
      { id: 'b', text: 'I want my money to work as hard as I do', __typename: 'QuizOption' },
      { id: 'c', text: 'I want to find opportunities before others do', __typename: 'QuizOption' },
      { id: 'd', text: 'I just want simple, automatic growth', __typename: 'QuizOption' },
    ],
    __typename: 'QuizQuestion',
  },
  {
    id: 'q3_luck_vs_skill',
    text: 'How much of financial success is your decisions vs. luck?',
    subtext: 'Slide toward which factor you believe matters more.',
    questionType: 'slider',
    sliderMin: 0,
    sliderMax: 10,
    sliderLabels: ['Mostly Luck', '50/50', 'Mostly My Decisions'],
    __typename: 'QuizQuestion',
  },
];

export const DEMO_INVESTOR_PROFILE = {
  userId: 'demo-user-1',
  archetype: 'steady_builder',
  archetypeTitle: 'The Steady Builder',
  archetypeDescription: 'You believe in systems and automation. You trust the power of compounding and prefer a disciplined, low-maintenance approach to wealth building.',
  archetypeFocus: 'Efficiency, systems, and the math of time',
  dimensions: {
    riskTolerance: 65,
    locusOfControl: 70,
    lossAversion: 40,
    sophistication: 55,
    __typename: 'QuizDimensions',
  },
  maturityStage: 'builder',
  coachingTone: 'the_architect',
  defaultStrategy: 'simple_path_core',
  biasMatrix: {
    concentrationScore: 55,
    recencyScore: 25,
    lossAversionScore: 30,
    familiarityScore: 48,
    overconfidenceScore: 20,
    overallBiasScore: 38,
    activeBiases: [
      {
        biasType: 'concentration',
        score: 55,
        signalDescription: 'Top 3 holdings = 42% of portfolio. Tech sector = 45%',
        coachingMessage: "Your portfolio is showing concentration in a few names. The Simple Path suggests broad diversification — a small shift to VTI would optimize your system's resilience.",
        __typename: 'BiasScore',
      },
      {
        biasType: 'familiarity',
        score: 48,
        signalDescription: '52% of portfolio in well-known consumer/tech names',
        coachingMessage: 'You\'re invested in companies you know well — that\'s natural. Consider adding VTI to capture growth from companies you haven\'t discovered yet.',
        __typename: 'BiasScore',
      },
    ],
    __typename: 'BiasMatrix',
  },
  quizCompleted: true,
  __typename: 'InvestorProfile',
};

export const DEMO_NEXT_BEST_ACTIONS = [
  {
    id: 'leak_critical',
    actionType: 'cancel_leak',
    priority: 1,
    priorityScore: 95,
    headline: 'Stop $127/mo in leaks',
    description: 'We found 4 subscriptions draining your wealth.',
    impactText: 'Worth $63,450 in 20 years',
    monthlyAmount: 127,
    totalImpact: 63450,
    timeImpactDays: 142,
    actionLabel: 'Review Leaks',
    actionScreen: 'LeakDetector',
    reasoning: 'These recurring charges are the easiest money to redirect. Cancel what you don\'t use and watch your millionaire date move closer.',
    __typename: 'NextBestAction',
  },
  {
    id: 'emergency_fund',
    actionType: 'build_emergency_fund',
    priority: 2,
    priorityScore: 80,
    headline: 'Build your fortress to 3 months',
    description: 'You have 1.9 months of expenses saved. Target: 3-6 months.',
    impactText: 'Need $5,040 to hit 3-month target',
    monthlyAmount: 420,
    totalImpact: 5040,
    timeImpactDays: 0,
    actionLabel: 'Start Saving',
    actionScreen: 'FinancialHealth',
    reasoning: 'Before aggressive investing, you need a safety net. This protects you from having to sell investments at the worst time.',
    __typename: 'NextBestAction',
  },
  {
    id: 'capture_match',
    actionType: 'capture_match',
    priority: 3,
    priorityScore: 82,
    headline: 'Capture $1,300/year in free money',
    description: 'Your employer match is the best investment you\'ll ever make — instant 50-100% return.',
    impactText: '100% guaranteed return',
    monthlyAmount: 108,
    totalImpact: 26000,
    timeImpactDays: 89,
    actionLabel: 'Increase 401k',
    actionScreen: 'FinancialHealth',
    reasoning: 'Never leave free money on the table. Increase your 401k contribution to at least capture the full match.',
    __typename: 'NextBestAction',
  },
];

export const DEMO_LEAK_REDIRECT = {
  actionType: 'redirect_savings',
  headline: 'Redirect $127/mo to your Millionaire Path',
  description: 'This becomes $63,450 over 20 years.',
  impactText: 'Moves your goal 142 days closer',
  monthlyAmount: 127,
  totalImpact: 63450,
  timeImpactDays: 142,
  suggestedEtf: 'VTI',
  actionScreen: 'AIPortfolioBuilder',
  reasoning: 'Your foundation is solid. VTI is a low-cost way to capture broad market growth — the "Simple Path" to wealth.',
  __typename: 'LeakRedirectSuggestion',
};

// ══════════════════════════════════════════════════════════════════════════════
// WEEKLY WEALTH DIGEST
// ══════════════════════════════════════════════════════════════════════════════

export const DEMO_WEEKLY_DIGEST = {
  userId: 'demo-user',
  weekEnding: 'March 9, 2026',
  portfolioValue: 47832,
  portfolioChangeAmount: 1247,
  portfolioChangePercent: 2.68,
  daysCloserToGoal: 14,
  goalProgressPercent: 4.78,
  estimatedGoalDate: 'August 2041',
  leaksRedirectedAmount: 127,
  contributionsThisWeek: 287,
  contributionStreakDays: 23,
  sp500ChangePercent: 1.92,
  beatMarket: true,
  highlights: [
    {
      type: 'portfolio_growth',
      headline: 'Portfolio Growth',
      value: '+$1,247',
      subtext: '+2.68% this week',
      icon: 'trending-up',
      color: '#10B981',
      isPositive: true,
      __typename: 'DigestHighlight',
    },
    {
      type: 'leak_savings',
      headline: 'Leaks Redirected',
      value: '$127/mo',
      subtext: 'Worth $63,450 in 20 years',
      icon: 'shield',
      color: '#6366F1',
      isPositive: true,
      __typename: 'DigestHighlight',
    },
    {
      type: 'goal_acceleration',
      headline: 'Goal Acceleration',
      value: '14 days closer',
      subtext: 'To your millionaire date',
      icon: 'zap',
      color: '#10B981',
      isPositive: true,
      __typename: 'DigestHighlight',
    },
    {
      type: 'market_beat',
      headline: 'Beat the Market',
      value: '+0.76%',
      subtext: 'S&P 500 was +1.92%',
      icon: 'award',
      color: '#F59E0B',
      isPositive: true,
      __typename: 'DigestHighlight',
    },
  ],
  coachingHeadline: 'The System Is Working',
  coachingMessage: "+$1,247 this week — the math of compounding in action. You're now 14 days ahead of schedule. Plus, you redirected $127/mo in leaks — worth $63,450 long-term!",
  coachingTone: 'the_architect',
  nextActionHeadline: 'Review your portfolio allocation',
  nextActionScreen: 'AIPortfolioBuilder',
  __typename: 'WeeklyWealthDigest',
};

// ══════════════════════════════════════════════════════════════════════════════
// IDENTITY GAP DETECTION
// ══════════════════════════════════════════════════════════════════════════════

export const DEMO_IDENTITY_GAPS = [
  {
    gapType: 'anxiety_gap',
    severity: 'mild',
    statedBehavior: 'Loss aversion: 45/100 (quiz)',
    actualBehavior: 'Checking app 4.2x/day, 8 times during volatility',
    gapScore: 28,
    headline: 'System Check: Anxiety Detected',
    message: "Data shows 4.2 app opens per day — above your baseline. This pattern often indicates anxiety overriding your systematic approach. The math hasn't changed. Your 20-year projection is still on track.",
    suggestedAction: 'See your 20-year projection',
    actionScreen: 'WealthArrival',
    __typename: 'IdentityGap',
  },
];
