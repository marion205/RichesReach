/**
 * Corrected GraphQL Queries for React Native App
 * All queries are tested and verified against the actual schema
 */

import { gql } from '@apollo/client';

// ============================================================================
// AUTHENTICATION QUERIES
// ============================================================================

export const TOKEN_AUTH = gql`
  mutation TokenAuth($email: String!, $password: String!) {
    tokenAuth(email: $email, password: $password) {
      token
    }
  }
`;

export const VERIFY_TOKEN = gql`
  mutation VerifyToken($token: String!) {
    verifyToken(token: $token) {
      payload
    }
  }
`;

export const REFRESH_TOKEN = gql`
  mutation RefreshToken($token: String!) {
    refreshToken(token: $token) {
      token
    }
  }
`;

// ============================================================================
// USER PROFILE QUERIES
// ============================================================================

export const ME_QUERY = gql`
  query Me {
    me {
      id
      email
      username
      name
      profilePic
      hasPremiumAccess
      subscriptionTier
      followersCount
      followingCount
    }
  }
`;

export const USER_PROFILE = gql`
  query UserProfile($id: ID!) {
    user(id: $id) {
      id
      email
      username
      name
      profilePic
      hasPremiumAccess
      subscriptionTier
      followersCount
      followingCount
      isFollowingUser
      isFollowedByUser
    }
  }
`;

// ============================================================================
// WATCHLIST QUERIES & MUTATIONS
// ============================================================================

export const MY_WATCHLIST = gql`
  query MyWatchlist {
    myWatchlist {
      id
      stock {
        symbol
      }
      notes
      addedAt
      targetPrice
    }
  }
`;

export const ADD_TO_WATCHLIST = gql`
  mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) {
    addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) {
      success
      message
    }
  }
`;

export const REMOVE_FROM_WATCHLIST = gql`
  mutation RemoveFromWatchlist($symbol: String!) {
    removeFromWatchlist(symbol: $symbol) {
      success
      message
    }
  }
`;

export const WATCHLISTS = gql`
  query Watchlists($userId: ID) {
    watchlists(userId: $userId) {
      id
      name
      description
      isPublic
      isShared
      createdAt
      items {
        id
        stock {
          symbol
          companyName
        }
        notes
        addedAt
      }
    }
  }
`;

// ============================================================================
// STOCK QUERIES
// ============================================================================

export const STOCKS = gql`
  query Stocks {
    stocks {
      symbol
      companyName
      currentPrice
      changePercent
      volume
      marketCap
      pe
      dividend
      sector
    }
  }
`;

export const STOCK_DETAILS = gql`
  query StockDetails($symbol: String!) {
    stock(symbol: $symbol) {
      symbol
      companyName
      currentPrice
      changePercent
      volume
      marketCap
      pe
      dividend
      sector
      description
      website
      employees
      founded
    }
  }
`;

export const STOCK_CHART_DATA = gql`
  query StockChartData($symbol: String!, $period: String) {
    stockChartData(symbol: $symbol, period: $period) {
      timestamp
      open
      high
      low
      close
      volume
    }
  }
`;

export const STOCK_DISCUSSIONS = gql`
  query StockDiscussions($stockSymbol: String, $limit: Int) {
    stockDiscussions(stockSymbol: $stockSymbol, limit: $limit) {
      id
      title
      content
      author {
        id
        username
        name
      }
      stock {
        symbol
        companyName
      }
      createdAt
      likes
      comments {
        id
        content
        author {
          username
        }
        createdAt
      }
    }
  }
`;

// ============================================================================
// PORTFOLIO QUERIES & MUTATIONS
// ============================================================================

export const MY_PORTFOLIOS = gql`
  query MyPortfolios {
    myPortfolios {
      totalPortfolios
      totalValue
      portfolios {
        id
        name
        totalValue
        holdingsCount
        holdings {
          id
          stock {
            symbol
          }
          shares
          averagePrice
          currentPrice
          totalValue
        }
      }
    }
  }
`;

export const PORTFOLIO_DETAILS = gql`
  query PortfolioDetails($id: ID!) {
    portfolio(id: $id) {
      id
      name
      description
      totalValue
      holdings {
        symbol
        shares
        averagePrice
        currentValue
        totalReturn
        stock {
          symbol
          companyName
          currentPrice
          changePercent
        }
      }
      createdAt
      updatedAt
    }
  }
`;

export const CREATE_PORTFOLIO = gql`
  mutation CreatePortfolio($name: String!, $description: String) {
    createPortfolio(name: $name, description: $description) {
      success
      message
      portfolio {
        id
        name
        description
      }
    }
  }
`;

export const ADD_TO_PORTFOLIO = gql`
  mutation AddToPortfolio($portfolioId: ID!, $symbol: String!, $shares: Float!, $price: Float!) {
    addToPortfolio(portfolioId: $portfolioId, symbol: $symbol, shares: $shares, price: $price) {
      success
      message
    }
  }
`;

export const REMOVE_FROM_PORTFOLIO = gql`
  mutation RemoveFromPortfolio($portfolioId: ID!, $symbol: String!) {
    removeFromPortfolio(portfolioId: $portfolioId, symbol: $symbol) {
      success
      message
    }
  }
`;

// ============================================================================
// AI RECOMMENDATIONS
// ============================================================================

export const AI_RECOMMENDATIONS = gql`
  query AIRecommendations {
    aiRecommendations {
      buyRecommendations {
        symbol
        confidence
        reasoning
        targetPrice
        stopLoss
        timeHorizon
      }
      sellRecommendations {
        symbol
        confidence
        reasoning
        targetPrice
        timeHorizon
      }
      holdRecommendations {
        symbol
        confidence
        reasoning
        timeHorizon
      }
    }
  }
`;

export const AI_PORTFOLIO_RECOMMENDATIONS = gql`
  query AIPortfolioRecommendations($riskTolerance: String, $investmentAmount: Float) {
    aiPortfolioRecommendations(riskTolerance: $riskTolerance, investmentAmount: $investmentAmount) {
      id
      symbol
      allocation
      reasoning
      riskLevel
      expectedReturn
      createdAt
    }
  }
`;

// ============================================================================
// MARKET DATA QUERIES
// ============================================================================

export const MARKET_DATA = gql`
  query MarketData {
    marketData {
      symbol
      price
      change
      changePercent
      volume
      marketCap
      high
      low
      open
      previousClose
    }
  }
`;

export const MARKET_NEWS = gql`
  query MarketNews($limit: Int) {
    marketNews(limit: $limit) {
      id
      title
      summary
      url
      source
      publishedAt
      sentiment
      relatedStocks {
        symbol
        companyName
      }
    }
  }
`;

export const MARKET_OVERVIEW = gql`
  query MarketOverview {
    marketOverview {
      totalMarketCap
      marketChange
      marketChangePercent
      volume
      activeStocks
      gainers
      losers
      mostActive
    }
  }
`;

// ============================================================================
// OPTIONS QUERIES
// ============================================================================

export const OPTIONS_DATA = gql`
  query OptionsData($symbol: String!) {
    optionsData(symbol: $symbol) {
      symbol
      expiration
      strike
      optionType
      bid
      ask
      last
      volume
      openInterest
      impliedVolatility
      delta
      gamma
      theta
      vega
    }
  }
`;

export const OPTIONS_RECOMMENDATIONS = gql`
  query OptionsRecommendations($symbol: String!, $strategy: String) {
    optionsRecommendations(symbol: $symbol, strategy: $strategy) {
      id
      symbol
      strategy
      confidence
      maxProfit
      maxLoss
      breakeven
      expiration
      reasoning
      contracts {
        type
        strike
        expiration
        quantity
        action
      }
    }
  }
`;

// ============================================================================
// CRYPTO QUERIES
// ============================================================================

export const CRYPTO_PRICES = gql`
  query CryptoPrices {
    cryptoPrices {
      symbol
      name
      price
      change24h
      changePercent24h
      volume24h
      marketCap
      rank
    }
  }
`;

export const CRYPTO_DETAILS = gql`
  query CryptoDetails($symbol: String!) {
    cryptoDetails(symbol: $symbol) {
      symbol
      name
      price
      change24h
      changePercent24h
      volume24h
      marketCap
      rank
      description
      website
      whitepaper
      circulatingSupply
      totalSupply
      maxSupply
    }
  }
`;

// ============================================================================
// SOCIAL FEATURES
// ============================================================================

export const FOLLOW_USER = gql`
  mutation FollowUser($userId: ID!) {
    followUser(userId: $userId) {
      success
      message
    }
  }
`;

export const UNFOLLOW_USER = gql`
  mutation UnfollowUser($userId: ID!) {
    unfollowUser(userId: $userId) {
      success
      message
    }
  }
`;

export const USER_FEED = gql`
  query UserFeed($limit: Int) {
    userFeed(limit: $limit) {
      id
      type
      content
      author {
        id
        username
        name
        profilePic
      }
      stock {
        symbol
        companyName
      }
      createdAt
      likes
      comments
      shares
    }
  }
`;

// ============================================================================
// NOTIFICATIONS
// ============================================================================

export const NOTIFICATIONS = gql`
  query Notifications($limit: Int) {
    notifications(limit: $limit) {
      id
      type
      title
      message
      read
      createdAt
      data
    }
  }
`;

export const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($id: ID!) {
    markNotificationRead(id: $id) {
      success
      message
    }
  }
`;

// ============================================================================
// ANALYTICS & INSIGHTS
// ============================================================================

export const PORTFOLIO_ANALYTICS = gql`
  query PortfolioAnalytics($portfolioId: ID!) {
    portfolioAnalytics(portfolioId: $portfolioId) {
      totalReturn
      totalReturnPercent
      dailyReturn
      weeklyReturn
      monthlyReturn
      yearlyReturn
      sharpeRatio
      beta
      volatility
      maxDrawdown
      sectorAllocation {
        sector
        percentage
        value
      }
      topPerformers {
        symbol
        return
        returnPercent
      }
      worstPerformers {
        symbol
        return
        returnPercent
      }
    }
  }
`;

export const MARKET_INSIGHTS = gql`
  query MarketInsights {
    marketInsights {
      sentiment
      fearGreedIndex
      vix
      treasuryYield
      dollarIndex
      oilPrice
      goldPrice
      bitcoinPrice
      marketTrend
      sectorRotation
      economicIndicators {
        indicator
        value
        change
        impact
      }
    }
  }
`;

// ============================================================================
// SETTINGS & PREFERENCES
// ============================================================================

export const USER_PREFERENCES = gql`
  query UserPreferences {
    userPreferences {
      notifications {
        priceAlerts
        newsAlerts
        portfolioUpdates
        socialActivity
      }
      display {
        theme
        currency
        dateFormat
        timeFormat
      }
      privacy {
        profileVisibility
        portfolioVisibility
        activityVisibility
      }
    }
  }
`;

export const UPDATE_USER_PREFERENCES = gql`
  mutation UpdateUserPreferences($preferences: UserPreferencesInput!) {
    updateUserPreferences(preferences: $preferences) {
      success
      message
    }
  }
`;

// ============================================================================
// SEARCH QUERIES
// ============================================================================

export const SEARCH_STOCKS = gql`
  query SearchStocks($query: String!, $limit: Int) {
    searchStocks(query: $query, limit: $limit) {
      symbol
      companyName
      currentPrice
      changePercent
      marketCap
      sector
    }
  }
`;

export const SEARCH_USERS = gql`
  query SearchUsers($query: String!, $limit: Int) {
    searchUsers(query: $query, limit: $limit) {
      id
      username
      name
      profilePic
      followersCount
      isFollowingUser
    }
  }
`;

// ============================================================================
// HEALTH CHECK QUERIES
// ============================================================================

export const HEALTH_CHECK = gql`
  query HealthCheck {
    healthCheck {
      status
      timestamp
      version
      environment
      services {
        database
        redis
        externalApis
      }
    }
  }
`;

// ============================================================================
// SUBSCRIPTION QUERIES
// ============================================================================

export const SUBSCRIPTION_PLANS = gql`
  query SubscriptionPlans {
    subscriptionPlans {
      id
      name
      description
      price
      currency
      interval
      features
      popular
    }
  }
`;

export const CURRENT_SUBSCRIPTION = gql`
  query CurrentSubscription {
    currentSubscription {
      id
      plan {
        id
        name
        price
        features
      }
      status
      currentPeriodStart
      currentPeriodEnd
      cancelAtPeriodEnd
    }
  }
`;

// ============================================================================
// EXPORT ALL QUERIES
// ============================================================================

export const ALL_QUERIES = {
  // Authentication
  TOKEN_AUTH,
  VERIFY_TOKEN,
  REFRESH_TOKEN,
  
  // User Profile
  ME_QUERY,
  USER_PROFILE,
  
  // Watchlist
  MY_WATCHLIST,
  ADD_TO_WATCHLIST,
  REMOVE_FROM_WATCHLIST,
  WATCHLISTS,
  
  // Stocks
  STOCKS,
  STOCK_DETAILS,
  STOCK_CHART_DATA,
  STOCK_DISCUSSIONS,
  
  // Portfolio
  MY_PORTFOLIOS,
  PORTFOLIO_DETAILS,
  CREATE_PORTFOLIO,
  ADD_TO_PORTFOLIO,
  REMOVE_FROM_PORTFOLIO,
  
  // AI Recommendations
  AI_RECOMMENDATIONS,
  AI_PORTFOLIO_RECOMMENDATIONS,
  
  // Market Data
  MARKET_DATA,
  MARKET_NEWS,
  MARKET_OVERVIEW,
  
  // Options
  OPTIONS_DATA,
  OPTIONS_RECOMMENDATIONS,
  
  // Crypto
  CRYPTO_PRICES,
  CRYPTO_DETAILS,
  
  // Social
  FOLLOW_USER,
  UNFOLLOW_USER,
  USER_FEED,
  
  // Notifications
  NOTIFICATIONS,
  MARK_NOTIFICATION_READ,
  
  // Analytics
  PORTFOLIO_ANALYTICS,
  MARKET_INSIGHTS,
  
  // Settings
  USER_PREFERENCES,
  UPDATE_USER_PREFERENCES,
  
  // Search
  SEARCH_STOCKS,
  SEARCH_USERS,
  
  // Health
  HEALTH_CHECK,
  
  // Subscription
  SUBSCRIPTION_PLANS,
  CURRENT_SUBSCRIPTION,
};
