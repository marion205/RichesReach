import { gql } from '@apollo/client';

export const GET_PORTFOLIO_ANALYTICS = gql`
  query GetPortfolioAnalytics($portfolioName: String) {
    premiumPortfolioMetrics(portfolioName: $portfolioName) {
      totalValue
      totalCost
      totalReturn
      totalReturnPercent
      volatility
      sharpeRatio
      maxDrawdown
      beta
      alpha
      holdings {
        symbol
        shares
        costBasis
        currentValue
        return
        returnPercent
      }
      sectorAllocation
      riskMetrics
    }
  }
`;

export const GET_EXECUTION_QUALITY_TRENDS = gql`
  query GetExecutionQualityTrends($days: Int!) {
    executionQualityStats(signalType: "day_trading", days: $days) {
      avgSlippagePct
      avgQualityScore
      chasedCount
      totalFills
      improvementTips
      periodDays
    }
  }
`;

export const GET_CREDIT_SCORE_HISTORY = gql`
  query GetCreditScoreHistory($days: Int!) {
    creditScoreHistory(days: $days) {
      date
      score
      factors {
        utilization
        paymentHistory
        creditAge
        creditMix
        inquiries
      }
    }
  }
`;

