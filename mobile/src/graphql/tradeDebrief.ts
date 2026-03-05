import { gql } from '@apollo/client';

export const GET_TRADE_DEBRIEF = gql`
  query GetTradeDebrief($lookbackDays: Int) {
    tradeDebrief(lookbackDays: $lookbackDays) {
      headline
      narrative
      topInsight
      recommendations
      statsSummary
      patternCodes
      sectorStats {
        sector
        tradeCount
        winRate
        totalPnl
      }
      patternFlags {
        code
        severity
        description
        impactDollars
      }
      dataSource
      hasEnoughData
      totalTrades
      winRatePct
      totalPnl
      bestSector
      worstSector
      counterfactualExtraPnl
      lookbackDays
      generatedAt
    }
  }
`;
