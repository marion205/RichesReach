import { gql } from '@apollo/client';

// ============================================================================
// RAHA Strategy Queries
// ============================================================================

export const GET_STRATEGIES = gql`
  query GetStrategies($marketType: String, $category: String) {
    strategies(marketType: $marketType, category: $category) {
      id
      slug
      name
      category
      description
      marketType
      timeframeSupported
      influencerRef
      enabled
      defaultVersion {
        id
        version
        configSchema
        logicRef
      }
    }
  }
`;

export const GET_STRATEGY = gql`
  query GetStrategy($id: ID!) {
    strategy(id: $id) {
      id
      slug
      name
      category
      description
      marketType
      timeframeSupported
      influencerRef
      enabled
      versions {
        id
        version
        configSchema
        logicRef
        isDefault
        createdAt
      }
    }
  }
`;

export const GET_USER_STRATEGY_SETTINGS = gql`
  query GetUserStrategySettings {
    userStrategySettings {
      id
      strategyVersion {
        id
        version
        strategy {
          id
          name
          slug
          category
        }
      }
      parameters
      enabled
      autoTradeEnabled
      maxDailyLossPercent
      maxConcurrentPositions
      createdAt
      updatedAt
    }
  }
`;

// ============================================================================
// RAHA Signal Queries
// ============================================================================

export const GET_RAHA_SIGNALS = gql`
  query GetRAHASignals($symbol: String!, $timeframe: String!, $limit: Int) {
    rahaSignals(symbol: $symbol, timeframe: $timeframe, limit: $limit) {
      id
      symbol
      timestamp
      timeframe
      signalType
      price
      stopLoss
      takeProfit
      confidenceScore
      meta
      strategyVersion {
        id
        strategy {
          id
          name
          slug
        }
      }
    }
  }
`;

// ============================================================================
// Backtest Queries
// ============================================================================

export const GET_BACKTEST_RUN = gql`
  query GetBacktestRun($id: ID!) {
    backtestRun(id: $id) {
      id
      symbol
      timeframe
      startDate
      endDate
      status
      parameters
      metrics
      equityCurve {
        timestamp
        equity
      }
      tradeLog
      createdAt
      completedAt
      strategyVersion {
        id
        strategy {
          id
          name
        }
      }
    }
  }
`;

export const GET_USER_BACKTESTS = gql`
  query GetUserBacktests($limit: Int) {
    userBacktests(limit: $limit) {
      id
      symbol
      timeframe
      startDate
      endDate
      status
      metrics
      createdAt
      strategyVersion {
        id
        strategy {
          id
          name
        }
      }
    }
  }
`;

// ============================================================================
// RAHA Metrics Queries
// ============================================================================

export const GET_RAHA_METRICS = gql`
  query GetRAHAMetrics($strategyVersionId: ID, $days: Int) {
    rahaMetrics(strategyVersionId: $strategyVersionId, days: $days) {
      winRate
      expectancy
      sharpeRatio
      maxDrawdown
      totalTrades
      winningTrades
      losingTrades
      avgWin
      avgLoss
      profitFactor
      expectancyPerCandle
    }
  }
`;

// ============================================================================
// RAHA Mutations
// ============================================================================

export const ENABLE_STRATEGY = gql`
  mutation EnableStrategy($strategyVersionId: ID!, $parameters: JSONString!) {
    enableStrategy(strategyVersionId: $strategyVersionId, parameters: $parameters) {
      success
      message
      userStrategySettings {
        id
        enabled
        parameters
        autoTradeEnabled
      }
    }
  }
`;

export const DISABLE_STRATEGY = gql`
  mutation DisableStrategy($strategyVersionId: ID!) {
    disableStrategy(strategyVersionId: $strategyVersionId) {
      success
      message
      userStrategySettings {
        id
        enabled
      }
    }
  }
`;

export const RUN_BACKTEST = gql`
  mutation RunBacktest(
    $strategyVersionId: ID!
    $symbol: String!
    $timeframe: String!
    $startDate: Date!
    $endDate: Date!
    $parameters: JSONString
  ) {
    runBacktest(
      strategyVersionId: $strategyVersionId
      symbol: $symbol
      timeframe: $timeframe
      startDate: $startDate
      endDate: $endDate
      parameters: $parameters
    ) {
      success
      message
      backtestRun {
        id
        status
        createdAt
      }
    }
  }
`;

export const GENERATE_RAHA_SIGNALS = gql`
  mutation GenerateRAHASignals(
    $strategyVersionId: ID!
    $symbol: String!
    $timeframe: String!
    $lookbackCandles: Int
    $parameters: JSONString
  ) {
    generateRAHASignals(
      strategyVersionId: $strategyVersionId
      symbol: $symbol
      timeframe: $timeframe
      lookbackCandles: $lookbackCandles
      parameters: $parameters
    ) {
      success
      message
      signals {
        id
        symbol
        timestamp
        signalType
        price
        stopLoss
        takeProfit
        confidenceScore
        meta
      }
    }
  }
`;

