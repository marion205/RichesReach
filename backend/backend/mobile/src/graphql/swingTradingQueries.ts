/**
 * Swing Trading GraphQL Queries
 * Provides real-time swing trading data from the backend
 */

import { gql } from '@apollo/client';

// Types
export interface MarketDataPoint {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: string;
  timestamp: string;
}

export interface SectorDataPoint {
  name: string;
  symbol: string;
  change: number;
  changePercent: number;
  weight: number;
}

export interface VolatilityData {
  vix: number;
  vixChange: number;
  fearGreedIndex: number;
  putCallRatio: number;
}

export interface TechnicalIndicator {
  name: string;
  value: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  description: string;
}

export interface PatternRecognition {
  name: string;
  confidence: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  description: string;
  timeframe: string;
}

export interface SwingSignal {
  id: string;
  symbol: string;
  timeframe: string;
  triggeredAt: string;
  signalType: string;
  entryPrice: number;
  stopPrice?: number;
  targetPrice?: number;
  mlScore: number;
  thesis: string;
  riskRewardRatio?: number;
  daysSinceTriggered: number;
  isLikedByUser: boolean;
  userLikeCount: number;
  features: any;
  isActive: boolean;
  isValidated: boolean;
  validationPrice?: number;
  validationTimestamp?: string;
  createdBy: {
    id: string;
    username: string;
    name: string;
  };
  technicalIndicators: TechnicalIndicator[];
  patterns: PatternRecognition[];
}

export interface PerformanceMetrics {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  avgHoldingPeriod: number;
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  entryPrice: number;
  exitPrice?: number;
  quantity: number;
  entryDate: string;
  exitDate?: string;
  pnl: number;
  pnlPercent: number;
  holdingPeriod: number;
  status: 'open' | 'closed';
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timestamp: string;
  impact: 'high' | 'medium' | 'low';
  sentiment: 'bullish' | 'bearish' | 'neutral';
  relatedSymbols: string[];
  category: string;
}

export interface SentimentIndicator {
  name: string;
  value: number;
  change: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  level: 'high' | 'medium' | 'low';
}

// GraphQL Queries
export const GET_MARKET_DATA = gql`
  query GetMarketData($symbols: [String]) {
    marketData(symbols: $symbols) {
      symbol
      name
      price
      change
      changePercent
      volume
      marketCap
      timestamp
    }
  }
`;

export const GET_SECTOR_DATA = gql`
  query GetSectorData {
    sectorData {
      name
      symbol
      change
      changePercent
      weight
    }
  }
`;

export const GET_VOLATILITY_DATA = gql`
  query GetVolatilityData {
    volatilityData {
      vix
      vixChange
      fearGreedIndex
      putCallRatio
    }
  }
`;

export const GET_TECHNICAL_INDICATORS = gql`
  query GetTechnicalIndicators($symbol: String!, $timeframe: String) {
    technicalIndicators(symbol: $symbol, timeframe: $timeframe) {
      name
      value
      signal
      strength
      description
    }
  }
`;

export const GET_PATTERN_RECOGNITION = gql`
  query GetPatternRecognition($symbol: String!, $timeframe: String) {
    patternRecognition(symbol: $symbol, timeframe: $timeframe) {
      name
      confidence
      signal
      description
      timeframe
    }
  }
`;

export const GET_SWING_SIGNALS = gql`
  query GetSwingSignals(
    $symbol: String
    $signalType: String
    $minMlScore: Float
    $isActive: Boolean
    $limit: Int
  ) {
    swingSignals(
      symbol: $symbol
      signalType: $signalType
      minMlScore: $minMlScore
      isActive: $isActive
      limit: $limit
    ) {
      id
      symbol
      timeframe
      triggeredAt
      signalType
      entryPrice
      stopPrice
      targetPrice
      mlScore
      thesis
      riskRewardRatio
      daysSinceTriggered
      isLikedByUser
      userLikeCount
      features
      isActive
      isValidated
      validationPrice
      validationTimestamp
      createdBy {
        id
        username
        name
      }
      technicalIndicators {
        name
        value
        signal
        strength
        description
      }
      patterns {
        name
        confidence
        signal
        description
        timeframe
      }
    }
  }
`;

export const GET_PERFORMANCE_METRICS = gql`
  query GetPerformanceMetrics($timeframe: String) {
    performanceMetrics(timeframe: $timeframe) {
      totalTrades
      winningTrades
      losingTrades
      winRate
      avgWin
      avgLoss
      profitFactor
      totalReturn
      maxDrawdown
      sharpeRatio
      avgHoldingPeriod
    }
  }
`;

export const GET_RECENT_TRADES = gql`
  query GetRecentTrades($limit: Int) {
    recentTrades(limit: $limit) {
      id
      symbol
      side
      entryPrice
      exitPrice
      quantity
      entryDate
      exitDate
      pnl
      pnlPercent
      holdingPeriod
      status
    }
  }
`;

export const GET_MARKET_NEWS = gql`
  query GetMarketNews($limit: Int) {
    marketNews(limit: $limit) {
      id
      title
      summary
      source
      timestamp
      impact
      sentiment
      relatedSymbols
      category
    }
  }
`;

export const GET_SENTIMENT_INDICATORS = gql`
  query GetSentimentIndicators {
    sentimentIndicators {
      name
      value
      change
      signal
      level
    }
  }
`;

// Mutations
export const LIKE_SIGNAL = gql`
  mutation LikeSignal($signalId: ID!) {
    likeSignal(signalId: $signalId) {
      success
      isLiked
      likeCount
      errors
    }
  }
`;

export const COMMENT_SIGNAL = gql`
  mutation CommentSignal($signalId: ID!, $content: String!) {
    commentSignal(signalId: $signalId, content: $content) {
      success
      comment {
        id
        content
        createdAt
        user {
          id
          username
          name
        }
      }
      errors
    }
  }
`;

// Utility functions
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const formatPercentage = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
};

export const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US').format(value);
};

export const formatCompactNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

export const getSignalColor = (signal: string): string => {
  switch (signal) {
    case 'bullish':
      return '#10B981'; // green
    case 'bearish':
      return '#EF4444'; // red
    default:
      return '#6B7280'; // gray
  }
};

export const getImpactColor = (impact: string): string => {
  switch (impact) {
    case 'high':
      return '#EF4444'; // red
    case 'medium':
      return '#F59E0B'; // yellow
    case 'low':
      return '#10B981'; // green
    default:
      return '#6B7280'; // gray
  }
};

export const getSentimentColor = (sentiment: string): string => {
  switch (sentiment) {
    case 'bullish':
      return '#10B981'; // green
    case 'bearish':
      return '#EF4444'; // red
    case 'neutral':
      return '#6B7280'; // gray
    default:
      return '#6B7280'; // gray
  }
};

export const getTimeAgo = (timestamp: string): string => {
  const now = new Date();
  const date = new Date(timestamp);
  const diff = Math.max(0, now.getTime() - date.getTime());
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
};

export const calculateRiskReward = (entryPrice: number, stopPrice: number, targetPrice: number): number => {
  if (!entryPrice || !stopPrice || !targetPrice) return 0;
  
  const risk = Math.abs(entryPrice - stopPrice);
  const reward = Math.abs(targetPrice - entryPrice);
  
  if (risk === 0) return 0;
  return reward / risk;
};

export const getMLScoreColor = (score: number): string => {
  if (score >= 0.8) return '#10B981'; // green - high confidence
  if (score >= 0.6) return '#F59E0B'; // yellow - medium confidence
  return '#EF4444'; // red - low confidence
};

export const getMLScoreLabel = (score: number): string => {
  if (score >= 0.8) return 'High';
  if (score >= 0.6) return 'Medium';
  return 'Low';
};
