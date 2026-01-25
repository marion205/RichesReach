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
      regimeMultiplier
      regimeNarration
      globalRegime
      localContext
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

export const CREATE_CUSTOM_STRATEGY = gql`
  mutation CreateCustomStrategy(
    $name: String!
    $description: String!
    $category: String!
    $marketType: String!
    $timeframeSupported: [String!]!
    $customLogic: JSONString!
    $configSchema: JSONString
  ) {
    createCustomStrategy(
      name: $name
      description: $description
      category: $category
      marketType: $marketType
      timeframeSupported: $timeframeSupported
      customLogic: $customLogic
      configSchema: $configSchema
    ) {
      success
      message
      strategy {
        id
        name
        slug
        category
        description
      }
    }
  }
`;

// ============================================================================
// ML Model Training
// ============================================================================

export const GET_ML_MODELS = gql`
  query GetMLModels {
    mlModels {
      id
      strategyVersionId
      strategyName
      symbol
      modelType
      lookbackDays
      trainingSamples
      metrics
      isActive
      createdAt
      trainedAt
    }
  }
`;

export const TRAIN_ML_MODEL = gql`
  mutation TrainMLModel(
    $strategyVersionId: ID
    $symbol: String
    $lookbackDays: Int!
    $modelType: String!
  ) {
    trainMlModel(
      strategyVersionId: $strategyVersionId
      symbol: $symbol
      lookbackDays: $lookbackDays
      modelType: $modelType
    ) {
      success
      message
      trainingSamples
      metrics {
        accuracy
        precision
        recall
        f1Score
        rocAuc
        mse
        mae
        rmse
      }
      modelType
      trainedAt
    }
  }
`;

// ============================================================================
// Strategy Blend Queries and Mutations
// ============================================================================

export const GET_STRATEGY_BLENDS = gql`
  query GetStrategyBlends {
    strategyBlends {
      id
      name
      description
      components {
        strategyVersionId
        weight
        strategyName
      }
      isActive
      isDefault
      createdAt
      updatedAt
    }
  }
`;

export const CREATE_STRATEGY_BLEND = gql`
  mutation CreateStrategyBlend(
    $name: String!
    $description: String
    $components: [StrategyBlendComponentInput!]!
    $isDefault: Boolean
  ) {
    createStrategyBlend(
      name: $name
      description: $description
      components: $components
      isDefault: $isDefault
    ) {
      success
      message
      strategyBlend {
        id
        name
        description
        components {
          strategyVersionId
          weight
          strategyName
        }
        isActive
        isDefault
        createdAt
        updatedAt
      }
    }
  }
`;

export const UPDATE_STRATEGY_BLEND = gql`
  mutation UpdateStrategyBlend(
    $id: ID!
    $name: String
    $description: String
    $components: [StrategyBlendComponentInput!]
    $isActive: Boolean
    $isDefault: Boolean
  ) {
    updateStrategyBlend(
      id: $id
      name: $name
      description: $description
      components: $components
      isActive: $isActive
      isDefault: $isDefault
    ) {
      success
      message
      strategyBlend {
        id
        name
        description
        components {
          strategyVersionId
          weight
          strategyName
        }
        isActive
        isDefault
        createdAt
        updatedAt
      }
    }
  }
`;

export const DELETE_STRATEGY_BLEND = gql`
  mutation DeleteStrategyBlend($id: ID!) {
    deleteStrategyBlend(id: $id) {
      success
      message
    }
  }
`;

