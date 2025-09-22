/**
 * GraphQL queries for crypto functionality (Pro)
 * - Adds advanced order inputs for executeCryptoTrade
 * - Adds per-asset SBLOC query
 * - Uses fragments to keep things DRY
 */

import { gql } from '@apollo/client';

/* ========= Fragments ========= */

export const CURRENCY_FIELDS = gql`
  fragment CurrencyFields on Cryptocurrency {
    id
    symbol
    name
    coingeckoId
    isStakingAvailable
    minTradeAmount
    precision
    volatilityTier
    isSecCompliant
    regulatoryStatus
  }
`;

export const PRICE_FIELDS = gql`
  fragment PriceFields on CryptoPrice {
    id
    priceUsd
    priceBtc
    volume24h
    marketCap
    priceChange24h
    priceChangePercentage24h
    rsi14
    volatility7d
    volatility30d
    momentumScore
    sentimentScore
    timestamp
  }
`;

export const LOAN_FIELDS = gql`
  fragment LoanFields on CryptoSblocLoan {
    id
    collateralQuantity
    collateralValueAtLoan
    loanAmount
    interestRate
    maintenanceMargin
    liquidationThreshold
    status
    createdAt
    updatedAt
    cryptocurrency { id symbol name }
  }
`;

export const HOLDING_FIELDS = gql`
  fragment HoldingFields on CryptoHolding {
    id
    quantity
    averageCost
    currentPrice
    currentValue
    unrealizedPnl
    unrealizedPnlPercentage
    stakedQuantity
    stakingRewards
    stakingApy
    isCollateralized
    collateralValue
    loanAmount
    cryptocurrency { id symbol name volatilityTier }
  }
`;

/* ========= Queries ========= */

// Get supported cryptocurrencies
export const GET_SUPPORTED_CURRENCIES = gql`
  query GetSupportedCurrencies {
    supportedCurrencies {
      ...CurrencyFields
    }
  }
  ${CURRENCY_FIELDS}
`;

// Get crypto price
export const GET_CRYPTO_PRICE = gql`
  query GetCryptoPrice($symbol: String!) {
    cryptoPrice(symbol: $symbol) {
      ...PriceFields
    }
  }
  ${PRICE_FIELDS}
`;

// Get crypto portfolio
export const GET_CRYPTO_PORTFOLIO = gql`
  query GetCryptoPortfolio {
    cryptoPortfolio {
      id
      totalValueUsd
      totalCostBasis
      totalPnl
      totalPnlPercentage
      totalPnl1d
      totalPnlPct1d
      totalPnl1w
      totalPnlPct1w
      totalPnl1m
      totalPnlPct1m
      portfolioVolatility
      sharpeRatio
      maxDrawdown
      diversificationScore
      topHoldingPercentage
      createdAt
      updatedAt
      holdings {
        ...HoldingFields
      }
    }
  }
  ${HOLDING_FIELDS}
`;

// Get crypto analytics
export const GET_CRYPTO_ANALYTICS = gql`
  query GetCryptoAnalytics {
    cryptoAnalytics {
      totalValueUsd
      totalCostBasis
      totalPnl
      totalPnlPercentage
      portfolioVolatility
      sharpeRatio
      maxDrawdown
      diversificationScore
      topHoldingPercentage
      sectorAllocation
      bestPerformer { symbol pnlPercentage }
      worstPerformer { symbol pnlPercentage }
      lastUpdated
    }
  }
`;

// Get crypto trades
export const GET_CRYPTO_TRADES = gql`
  query GetCryptoTrades($symbol: String, $limit: Int) {
    cryptoTrades(symbol: $symbol, limit: $limit) {
      id
      tradeType
      quantity
      pricePerUnit
      totalAmount
      fees
      orderId
      status
      executionTime
      isSblocFunded
      sblocLoanId
      cryptocurrency { id symbol name }
    }
  }
`;

// Get crypto predictions
export const GET_CRYPTO_PREDICTIONS = gql`
  query GetCryptoPredictions($symbol: String!) {
    cryptoPredictions(symbol: $symbol) {
      id
      predictionType
      probability
      confidenceLevel
      featuresUsed
      modelVersion
      predictionHorizonHours
      createdAt
      expiresAt
      wasCorrect
      actualReturn
    }
  }
`;

// Get crypto ML signal
export const GET_CRYPTO_ML_SIGNAL = gql`
  query GetCryptoMLSignal($symbol: String!) {
    cryptoMlSignal(symbol: $symbol) {
      symbol
      probability
      confidenceLevel
      explanation
      features
      modelVersion
      timestamp
    }
  }
`;

// Get SBLOC loans (all)
export const GET_CRYPTO_SBLOC_LOANS = gql`
  query GetCryptoSBLOCLoans {
    cryptoSblocLoans {
      ...LoanFields
    }
  }
  ${LOAN_FIELDS}
`;

// Get SBLOC loans for a specific symbol (for your per-asset tap-through modal)
export const GET_CRYPTO_SBLOC_LOANS_BY_SYMBOL = gql`
  query GetCryptoSBLOCLoansBySymbol($symbol: String!) {
    cryptoSblocLoans(symbol: $symbol) {
      ...LoanFields
    }
  }
  ${LOAN_FIELDS}
`;

// Get education progress
export const GET_CRYPTO_EDUCATION_PROGRESS = gql`
  query GetCryptoEducationProgress {
    cryptoEducationProgress {
      id
      moduleName
      moduleType
      progressPercentage
      isCompleted
      completedAt
      quizAttempts
      bestQuizScore
      createdAt
      updatedAt
    }
  }
`;

/* ========= Mutations ========= */

/**
 * Advanced trade mutation to match the Trading Card (Pro++) UI
 * - orderType: MARKET | LIMIT | STOP_MARKET | STOP_LIMIT | TAKE_PROFIT_LIMIT
 * - timeInForce: GTC | IOC | FOK | DAY
 * - triggerPrice: required for STOP_* orders
 * - pricePerUnit: required for LIMIT / STOP_LIMIT / TAKE_PROFIT_LIMIT (ignored for MARKET/STOP_MARKET)
 * - clientOrderId: optional for idempotency
 */
export const EXECUTE_CRYPTO_TRADE = gql`
  mutation ExecuteCryptoTrade(
    $symbol: String!
    $tradeType: String!
    $quantity: Float!
    $orderType: OrderType!
    $timeInForce: TimeInForce!
    $pricePerUnit: Float
    $triggerPrice: Float
    $clientOrderId: String
  ) {
    executeCryptoTrade(
      symbol: $symbol
      tradeType: $tradeType
      quantity: $quantity
      orderType: $orderType
      timeInForce: $timeInForce
      pricePerUnit: $pricePerUnit
      triggerPrice: $triggerPrice
      clientOrderId: $clientOrderId
    ) {
      success
      tradeId
      orderId
      message
    }
  }
`;

export const CREATE_SBLOC_LOAN = gql`
  mutation CreateSBLOCLoan(
    $symbol: String!
    $collateralQuantity: Float!
    $loanAmount: Float!
  ) {
    createSblocLoan(
      symbol: $symbol
      collateralQuantity: $collateralQuantity
      loanAmount: $loanAmount
    ) {
      success
      loanId
      message
    }
  }
`;

export const GENERATE_ML_PREDICTION = gql`
  mutation GenerateMLPrediction($symbol: String!) {
    generateMlPrediction(symbol: $symbol) {
      success
      predictionId
      probability
      explanation
      message
    }
  }
`;

export const REPAY_SBLOC_LOAN = gql`
  mutation RepaySblocLoan($loanId: ID!, $amountUsd: Float!) {
    repaySblocLoan(loanId: $loanId, amountUsd: $amountUsd) {
      success
      message
      newOutstanding
      interestPaid
      principalPaid
      loan {
        id
        status
        loanAmount
        updatedAt
        cryptocurrency { symbol }
      }
    }
  }
`;

export const GET_CRYPTO_RECOMMENDATIONS = gql`
  query GetCryptoRecommendations($limit: Int, $symbols: [String!]) {
    cryptoRecommendations(limit: $limit, symbols: $symbols) {
      symbol
      score
      probability
      confidenceLevel
      priceUsd
      volatilityTier
      liquidity24hUsd
      rationale
      recommendation
      riskLevel
    }
  }
`;

/* ========= Phase 3 Queries ========= */

// Advanced chart data with technical indicators
export const GET_ADVANCED_CHART_DATA = gql`
  query GetAdvancedChartData(
    $symbol: String!
    $interval: String = "1D"
    $limit: Int = 180
    $indicators: [String!] = ["SMA20", "SMA50", "EMA12", "EMA26", "RSI", "MACD", "BB"]
  ) {
    stockChartData(
      symbol: $symbol
      timeframe: $interval
      interval: $interval
      limit: $limit
      indicators: $indicators
    ) {
      symbol
      interval
      limit
      currentPrice
      change
      changePercent
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
      indicators {
        SMA20
        SMA50
        EMA12
        EMA26
        BB_upper
        BB_middle
        BB_lower
        RSI14
        MACD
        MACD_signal
        MACD_hist
      }
    }
  }
`;

// Research hub comprehensive data
export const GET_RESEARCH_HUB = gql`
  query GetResearchHub($symbol: String!) {
    researchHub(symbol: $symbol) {
      symbol
      company {
        name
        sector
        marketCap
        country
        website
      }
      quote {
        currentPrice
        change
        changePercent
        high
        low
        volume
      }
      technicals {
        rsi
        macd
        macdhistogram
        movingAverage50
        movingAverage200
        supportLevel
        resistanceLevel
        impliedVolatility
      }
      sentiment {
        sentiment_label
        sentiment_score
        article_count
        confidence
      }
      macro {
        vix
        market_sentiment
        risk_appetite
      }
      marketRegime {
        market_regime
        confidence
        recommended_strategy
      }
      peers
      updatedAt
    }
  }
`;

// Options trading mutations
export const PLACE_OPTION_ORDER = gql`
  mutation PlaceOptionOrder($input: PlaceOptionOrderInput!) {
    placeOptionOrder(input: $input) {
      success
      cached
      order {
        id
        status
        symbol
        optionType
        strike
        expiration
        side
        orderType
        timeInForce
        limitPrice
        stopPrice
        quantity
        createdAt
      }
    }
  }
`;

export const CANCEL_ORDER = gql`
  mutation CancelOrder($orderId: String!) {
    cancelOrder(orderId: $orderId) {
      success
      orderId
    }
  }
`;

export const GET_ORDERS = gql`
  query GetOrders($status: String) {
    orders(status: $status) {
      id
      status
      symbol
      optionType
      strike
      expiration
      side
      orderType
      timeInForce
      limitPrice
      stopPrice
      quantity
      createdAt
    }
  }
`;

// Batch chart data for multiple symbols
export const GET_BATCH_CHART_DATA = gql`
  query GetBatchChartData(
    $symbols: [String!]!
    $timeframe: String = "1D"
    $indicators: [String!] = ["SMA20", "SMA50", "EMA12", "EMA26", "RSI", "MACD", "BB"]
  ) {
    batchStockChartData(
      symbols: $symbols
      timeframe: $timeframe
      indicators: $indicators
    ) {
      symbol
      timeframe
      currentPrice
      change
      changePercent
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
      indicators {
        SMA20
        SMA50
        EMA12
        EMA26
        BB_upper
        BB_middle
        BB_lower
        RSI14
        MACD
        MACD_signal
        MACD_hist
      }
    }
  }
`;