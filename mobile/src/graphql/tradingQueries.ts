import { gql } from '@apollo/client';

/* ------------------------------- Trading Account ------------------------------- */

export const GET_TRADING_ACCOUNT = gql`
  query GetTradingAccount {
    tradingAccount {
      id
      buyingPower
      cash
      equity
      portfolioValue: equity
      dayTradeCount
      patternDayTrader
      tradingBlocked
      dayTradingBuyingPower
      status
      accountStatus: status
      kycStatus
      createdAt
    }
  }
`;

/* ------------------------------- Trading Positions ------------------------------- */

export const GET_TRADING_POSITIONS = gql`
  query GetTradingPositions {
    tradingPositions {
      id
      symbol
      qty
      quantity: qty
      marketValue
      costBasis
      unrealizedPl
      unrealizedPlpc
      unrealizedPLPercent: unrealizedPlpc
      currentPrice
    }
  }
`;

/* ------------------------------- Trading Orders ------------------------------- */

export const GET_TRADING_ORDERS = gql`
  query GetTradingOrders($status: String, $limit: Int) {
    tradingOrders(status: $status, limit: $limit) {
      id
      symbol
      side
      orderType
      quantity
      limitPrice
      price: limitPrice
      stopPrice
      status
      createdAt
      filledAt
      filledQty
      filledQuantity: filledQty
      filledAvgPrice
      averageFillPrice: filledAvgPrice
    }
  }
`;

/* ------------------------------- Trading Quote ------------------------------- */

/* ------------------------------- Trading Quote ------------------------------- */

export const GET_TRADING_QUOTE = gql`
  query GetTradingQuote($symbol: String!) {
    tradingQuote(symbol: $symbol) {
      symbol
      bid
      ask
      bidSize
      askSize
      timestamp
    }
  }
`;

// Note: The GraphQL field name is `tradingQuote` (camelCase) which maps to `trading_quote` (snake_case) in the schema

/* ------------------------------- Stock Chart Data ------------------------------- */

export const GET_STOCK_CHART_DATA = gql`
  query GetStockChartData($symbol: String!, $timeframe: String!) {
    stockChartData(symbol: $symbol, timeframe: $timeframe) {
      symbol
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
    }
  }
`;

/* ------------------------------- Place Stock Order ------------------------------- */

export const PLACE_STOCK_ORDER = gql`
  mutation PlaceStockOrder($symbol: String!, $side: String!, $quantity: Int!, $orderType: String!, $limitPrice: Float, $timeInForce: String) {
    placeStockOrder(symbol: $symbol, side: $side, quantity: $quantity, orderType: $orderType, limitPrice: $limitPrice, timeInForce: $timeInForce) {
      success
      message
      orderId
    }
  }
`;

/* ------------------------------- Alpaca Account ------------------------------- */

export const CREATE_ALPACA_ACCOUNT = gql`
  mutation CreateAlpacaAccount(
    $firstName: String!
    $lastName: String!
    $email: String!
    $dateOfBirth: Date!
    $streetAddress: String!
    $city: String!
    $state: String!
    $postalCode: String!
    $phone: String
    $ssn: String
    $country: String
    $employmentStatus: String
    $annualIncome: Float
    $netWorth: Float
    $riskTolerance: String
    $investmentExperience: String
  ) {
    createAlpacaAccount(
      firstName: $firstName
      lastName: $lastName
      email: $email
      dateOfBirth: $dateOfBirth
      streetAddress: $streetAddress
      city: $city
      state: $state
      postalCode: $postalCode
      phone: $phone
      ssn: $ssn
      country: $country
      employmentStatus: $employmentStatus
      annualIncome: $annualIncome
      netWorth: $netWorth
      riskTolerance: $riskTolerance
      investmentExperience: $investmentExperience
    ) {
      success
      message
      alpacaAccountId
      account {
        id
        status
        createdAt
        approvedAt
      }
    }
  }
`;

export const GET_ALPACA_ACCOUNT = gql`
  query GetAlpacaAccount($userId: Int!) {
    alpacaAccount(userId: $userId) {
      id
      status
      alpacaAccountId
      approvedAt
      buyingPower
      cash
      equity
      portfolioValue: equity
      createdAt
    }
  }
`;

export const GET_ALPACA_ORDERS = gql`
  query GetAlpacaOrders($accountId: Int!, $status: String) {
    alpacaOrders(accountId: $accountId, status: $status) {
      id
      symbol
      qty
      side
      type
      timeInForce
      limitPrice
      stopPrice
      status
      filledAvgPrice
      filledQty
      createdAt
      submittedAt
      filledAt
    }
  }
`;

export const GET_ALPACA_POSITIONS = gql`
  query GetAlpacaPositions($accountId: Int!) {
    alpacaPositions(accountId: $accountId) {
      id
      symbol
      qty
      avgEntryPrice
      marketValue
      costBasis
      unrealizedPl
      unrealizedPlPc
      currentPrice
      lastDayPrice
      changeToday
      updatedAt
    }
  }
`;

export const GET_OPTIONS_FLOW = gql`
  query GetOptionsFlow($symbol: String!) {
    optionsFlow(symbol: $symbol) {
      symbol
      timestamp
      unusualActivity {
        contractSymbol
        strike
        expiration
        optionType
        volume
        openInterest
        volumeVsOI
        lastPrice
        bid
        ask
        impliedVolatility
        unusualVolumePercent
        sweepCount
        blockSize
        isDarkPool
      }
      putCallRatio
      totalCallVolume
      totalPutVolume
      largestTrades {
        contractSymbol
        size
        price
        time
        isCall
        isSweep
        isBlock
      }
    }
  }
`;

export const CANCEL_ORDER = gql`
  mutation CancelOrder($orderId: String!) {
    cancelOrder(orderId: $orderId) { 
      success 
      message 
    }
  }
`;

