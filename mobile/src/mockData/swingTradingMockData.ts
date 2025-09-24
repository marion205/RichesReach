/**
 * Mock Data for Swing Trading UI Testing
 * Provides realistic data for testing UI components without backend
 */

export const mockSignals = [
  {
    id: '1',
    symbol: 'AAPL',
    timeframe: '1d',
    triggeredAt: new Date().toISOString(),
    signalType: 'rsi_rebound_long',
    entryPrice: 175.50,
    stopPrice: 170.00,
    targetPrice: 185.00,
    mlScore: 0.78,
    thesis: 'RSI oversold at 28.5 with strong volume confirmation. EMA crossover suggests bullish momentum.',
    riskRewardRatio: 2.1,
    daysSinceTriggered: 1,
    isLikedByUser: false,
    userLikeCount: 12,
    features: {
      rsi_14: 28.5,
      ema_12: 176.2,
      ema_26: 174.8,
      atr_14: 2.1,
      volume_surge: 1.8
    },
    isActive: true,
    isValidated: false,
    createdBy: {
      id: '1',
      username: 'ai_trader',
      name: 'AI Trading System'
    }
  },
  {
    id: '2',
    symbol: 'TSLA',
    timeframe: '1d',
    triggeredAt: new Date(Date.now() - 86400000).toISOString(),
    signalType: 'breakout_long',
    entryPrice: 245.30,
    stopPrice: 238.00,
    targetPrice: 260.00,
    mlScore: 0.82,
    thesis: 'Breakout above resistance with 2.3x volume. MACD bullish crossover confirms momentum.',
    riskRewardRatio: 1.8,
    daysSinceTriggered: 2,
    isLikedByUser: true,
    userLikeCount: 8,
    features: {
      rsi_14: 65.2,
      ema_12: 244.1,
      ema_26: 241.5,
      atr_14: 3.2,
      volume_surge: 2.3
    },
    isActive: true,
    isValidated: false,
    createdBy: {
      id: '2',
      username: 'swing_master',
      name: 'Swing Master'
    }
  },
  {
    id: '3',
    symbol: 'NVDA',
    timeframe: '1d',
    triggeredAt: new Date(Date.now() - 172800000).toISOString(),
    signalType: 'ema_crossover_long',
    entryPrice: 420.75,
    stopPrice: 410.00,
    targetPrice: 445.00,
    mlScore: 0.71,
    thesis: 'EMA 12/26 bullish crossover with RSI at 58. Strong institutional buying detected.',
    riskRewardRatio: 2.3,
    daysSinceTriggered: 3,
    isLikedByUser: false,
    userLikeCount: 15,
    features: {
      rsi_14: 58.0,
      ema_12: 421.2,
      ema_26: 418.9,
      atr_14: 4.1,
      volume_surge: 1.5
    },
    isActive: true,
    isValidated: true,
    validationPrice: 425.50,
    validationTimestamp: new Date(Date.now() - 86400000).toISOString(),
    createdBy: {
      id: '1',
      username: 'ai_trader',
      name: 'AI Trading System'
    }
  }
];

export const mockBacktestStrategies = [
  {
    id: '1',
    name: 'RSI Rebound Strategy',
    description: 'Buy when RSI < 30 and volume > 1.5x average. Exit at RSI > 70 or 5% profit.',
    strategyType: 'rsi_rebound',
    parameters: {
      rsi_oversold: 30,
      rsi_overbought: 70,
      volume_threshold: 1.5,
      profit_target: 0.05
    },
    totalReturn: 0.23,
    winRate: 0.68,
    maxDrawdown: -0.12,
    sharpeRatio: 1.45,
    totalTrades: 156,
    isPublic: true,
    likesCount: 24,
    sharesCount: 8,
    createdAt: new Date(Date.now() - 2592000000).toISOString(),
    user: {
      id: '1',
      username: 'strategy_guru',
      name: 'Strategy Guru'
    }
  },
  {
    id: '2',
    name: 'EMA Crossover Momentum',
    description: 'Long when EMA 12 > EMA 26 with volume confirmation. Stop at EMA 26.',
    strategyType: 'ema_crossover',
    parameters: {
      ema_fast: 12,
      ema_slow: 26,
      volume_threshold: 1.2
    },
    totalReturn: 0.31,
    winRate: 0.72,
    maxDrawdown: -0.08,
    sharpeRatio: 1.67,
    totalTrades: 89,
    isPublic: true,
    likesCount: 31,
    sharesCount: 12,
    createdAt: new Date(Date.now() - 1728000000).toISOString(),
    user: {
      id: '2',
      username: 'momentum_trader',
      name: 'Momentum Trader'
    }
  }
];

export const mockBacktestResults = [
  {
    id: '1',
    symbol: 'AAPL',
    timeframe: '1d',
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    initialCapital: 10000,
    finalCapital: 12300,
    totalReturn: 0.23,
    annualizedReturn: 0.23,
    maxDrawdown: -0.12,
    sharpeRatio: 1.45,
    sortinoRatio: 1.78,
    calmarRatio: 1.92,
    winRate: 0.68,
    profitFactor: 2.1,
    totalTrades: 156,
    winningTrades: 106,
    losingTrades: 50,
    avgWin: 0.045,
    avgLoss: -0.021,
    createdAt: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: '2',
    symbol: 'TSLA',
    timeframe: '1d',
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    initialCapital: 10000,
    finalCapital: 13100,
    totalReturn: 0.31,
    annualizedReturn: 0.31,
    maxDrawdown: -0.08,
    sharpeRatio: 1.67,
    sortinoRatio: 2.1,
    calmarRatio: 3.88,
    winRate: 0.72,
    profitFactor: 2.4,
    totalTrades: 89,
    winningTrades: 64,
    losingTrades: 25,
    avgWin: 0.052,
    avgLoss: -0.019,
    createdAt: new Date(Date.now() - 172800000).toISOString()
  }
];

export const mockDayTradingPicks = {
  as_of: new Date().toISOString(),
  mode: 'SAFE',
  picks: [
    {
      symbol: 'SPY',
      side: 'LONG',
      score: 2.1,
      features: {
        momentum_15m: 0.023,
        rvol_10m: 1.8,
        vwap_dist: 0.012,
        breakout_pct: 0.015,
        spread_bps: 2.1,
        catalyst_score: 0.75
      },
      risk: {
        atr_5m: 1.2,
        size_shares: 100,
        stop: 445.50,
        targets: [448.00, 450.50],
        time_stop_min: 45
      },
      notes: 'Strong momentum with low spread. Earnings catalyst in 2 days.'
    },
    {
      symbol: 'QQQ',
      side: 'SHORT',
      score: 1.8,
      features: {
        momentum_15m: -0.018,
        rvol_10m: 2.1,
        vwap_dist: -0.008,
        breakout_pct: -0.012,
        spread_bps: 1.8,
        catalyst_score: 0.65
      },
      risk: {
        atr_5m: 0.9,
        size_shares: 50,
        stop: 378.20,
        targets: [375.00, 372.50],
        time_stop_min: 30
      },
      notes: 'Bearish momentum with high relative volume. Tech sector weakness.'
    }
  ],
  universe_size: 500,
  quality_threshold: 1.5
};

export const mockRiskCalculation = {
  accountEquity: 25000,
  riskPerTrade: 0.02,
  entryPrice: 175.50,
  stopPrice: 170.00,
  positionSize: 100,
  dollarRisk: 550,
  positionValue: 17550,
  positionPct: 0.07,
  riskPerTradePct: 0.02,
  riskRewardRatio: 2.1
};
