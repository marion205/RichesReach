import { gql } from '@apollo/client';

// ============================================================================
// Order Monitoring Dashboard Queries
// ============================================================================

export const GET_ORDER_DASHBOARD = gql`
  query GetOrderDashboard(
    $ordersLimit: Int
    $ordersOffset: Int
    $filledOrdersLimit: Int
    $filledOrdersOffset: Int
    $rahaOrdersLimit: Int
    $rahaOrdersOffset: Int
  ) {
    orderDashboard(
      ordersLimit: $ordersLimit
      ordersOffset: $ordersOffset
      filledOrdersLimit: $filledOrdersLimit
      filledOrdersOffset: $filledOrdersOffset
      rahaOrdersLimit: $rahaOrdersLimit
      rahaOrdersOffset: $rahaOrdersOffset
    ) {
      orders {
        id
        clientOrderId
        alpacaOrderId
        symbol
        side
        orderType
        timeInForce
        quantity
        notional
        limitPrice
        stopPrice
        status
        filledQty
        filledAvgPrice
        guardrailChecksPassed
        guardrailRejectReason
        rejectionReason
        source
        rahaSignal {
          id
          symbol
          signalType
          price
          stopLoss
          takeProfit
          confidenceScore
          strategyVersion {
            id
            strategy {
              id
              name
            }
          }
        }
        createdAt
        updatedAt
        submittedAt
        filledAt
      }
      ordersHasMore
      activeOrders {
        id
        symbol
        side
        orderType
        quantity
        status
        filledQty
        createdAt
      }
      filledOrders {
        id
        symbol
        side
        orderType
        quantity
        filledQty
        filledAvgPrice
        notional
        status
        source
        createdAt
        filledAt
      }
      filledOrdersHasMore
      positions {
        id
        symbol
        qty
        avgEntryPrice
        currentPrice
        marketValue
        costBasis
        unrealizedPl
        unrealizedPlpc
        lastSyncedAt
      }
      rahaOrders {
        id
        symbol
        side
        quantity
        status
        filledQty
        filledAvgPrice
        source
        rahaSignal {
          id
          symbol
          signalType
          confidenceScore
          strategyVersion {
            strategy {
              name
            }
          }
        }
        createdAt
        filledAt
      }
      rahaOrdersHasMore
      metrics {
        totalTrades
        winningTrades
        losingTrades
        winRate
        totalPnl
        totalPnlPercent
        avgWin
        avgLoss
        largestWin
        largestLoss
        profitFactor
      }
      riskStatus {
        dailyNotionalUsed
        dailyNotionalRemaining
        dailyNotionalLimit
        dailyLimitWarning
        activePositionsCount
        maxPositions
        positionLimitWarning
        totalPositionValue
        totalUnrealizedPnl
        positionSizePercent
        accountEquity
        tradingBlocked
        patternDayTrader
        dayTradeCount
      }
    }
  }
`;
