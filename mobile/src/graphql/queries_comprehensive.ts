import { gql } from '@apollo/client';

// Single comprehensive query for all stock detail data
export const GET_STOCK_COMPREHENSIVE = gql`
  query GetStockComprehensive($symbol: String!, $timeframe: String = "1D") {
    stockComprehensive(symbol: $symbol, timeframe: $timeframe) {
      # Basic Info
      symbol
      companyName
      sector
      industry
      description
      website
      employees
      founded
      
      # Financial Metrics
      marketCap
      peRatio
      pegRatio
      priceToBook
      priceToSales
      dividendYield
      dividendRate
      exDividendDate
      payoutRatio
      
      # Price Data
      currentPrice
      previousClose
      dayHigh
      dayLow
      week52High
      week52Low
      volume
      avgVolume
      change
      changePercent
      
      # Chart Data (last 30 days)
      chartData {
        timestamp
        open
        high
        low
        close
        volume
      }
      
      # Trading Position (if user has position)
      position {
        quantity
        averageCost
        marketValue
        unrealizedPl
        unrealizedPlPercent
      }
      
      # Key Metrics
      keyMetrics {
        revenue
        revenueGrowth
        grossProfit
        operatingIncome
        netIncome
        eps
        epsGrowth
        roe
        roa
        debtToEquity
        currentRatio
        quickRatio
      }
      
      # Recent News (top 5)
      news {
        title
        summary
        url
        publishedAt
        source
        sentiment
      }
      
      # Analyst Data
      analystRatings {
        consensusRating
        averageTargetPrice
        numberOfAnalysts
        ratingsBreakdown {
          buy
          hold
          sell
        }
        recentRatings {
          analyst
          firm
          rating
          targetPrice
          date
        }
      }
      
      # Earnings
      earnings {
        nextEarningsDate
        lastEarningsDate
        lastEarnings {
          actualEps
          estimatedEps
          surprise
          surprisePercent
          revenue
          estimatedRevenue
        }
        nextEarnings {
          estimatedEps
          estimatedRevenue
          date
        }
      }
      
      # Insider Trading (recent)
      insiderTrades {
        insiderName
        transactionDate
        shares
        price
        type
        value
      }
      
      # Institutional Ownership
      institutionalOwnership {
        institutionName
        sharesHeld
        percentOfShares
        valueHeld
        changeFromPrevious
      }
      
      # Market Sentiment
      sentiment {
        overallScore
        positiveMentions
        negativeMentions
        neutralMentions
        recentPosts {
          content
          sentiment
          source
          timestamp
        }
      }
      
      # Technical Indicators
      technicals {
        rsi
        macd
        macdSignal
        macdHistogram
        sma20
        sma50
        sma200
        ema12
        ema26
        bollingerUpper
        bollingerLower
        bollingerMiddle
        supportLevel
        resistanceLevel
        impliedVolatility
      }
      
      # Peers
      peers {
        symbol
        companyName
        currentPrice
        changePercent
        marketCap
      }
    }
  }
`;

// Fallback query for when comprehensive isn't available
export const GET_STOCK_BASIC = gql`
  query GetStockBasic($symbol: String!) {
    stockDetail(symbol: $symbol) {
      symbol
      companyName
      sector
      marketCap
      peRatio
      dividendYield
      currentPrice
      changePercent
      description
    }
  }
`;
