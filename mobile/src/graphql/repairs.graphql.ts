import { gql } from '@apollo/client';

/**
 * GraphQL Query: Get Portfolio with Active Repairs
 * 
 * Returns:
 * - Portfolio summary (total Greeks, health status)
 * - All open positions with Greeks
 * - Active repair plans with priority
 */
export const GET_PORTFOLIO_WITH_REPAIRS = gql`
  query GetPortfolioWithRepairs($user_id: String!, $account_id: String!) {
    portfolio(userId: $user_id, accountId: $account_id) {
      totalDelta
      totalGamma
      totalTheta
      totalVega
      portfolioHealthStatus
      repairsAvailable
      totalMaxLoss
    }
    positions(userId: $user_id, accountId: $account_id) {
      id
      ticker
      strategyType
      entryPrice
      currentPrice
      quantity
      unrealizedPnl
      daysToExpiration
      expirationDate
      greeks {
        delta
        gamma
        theta
        vega
        rho
      }
      maxLoss
      probabilityOfProfit
      status
    }
    repair_plans: activeRepairPlans(userId: $user_id, accountId: $account_id) {
      positionId
      ticker
      originalStrategy
      currentDelta
      deltaDriftPct
      currentMaxLoss
      repairType
      repairStrikes
      repairCredit
      newMaxLoss
      newBreakEven
      confidenceBoost
      headline
      reason
      actionDescription
      priority
    }
  }
`;

/**
 * GraphQL Query: Get Single Position with Repair Details
 */
export const GET_POSITION_WITH_REPAIR = gql`
  query GetPositionWithRepair($position_id: String!, $user_id: String!) {
    position(positionId: $position_id, userId: $user_id) {
      id
      ticker
      strategyType
      entryPrice
      currentPrice
      quantity
      unrealizedPnl
      daysToExpiration
      greeks {
        delta
        gamma
        theta
        vega
        rho
      }
      maxLoss
      probabilityOfProfit
    }
    repair_plan: repairPlan(positionId: $position_id) {
      positionId
      ticker
      originalStrategy
      currentDelta
      deltaDriftPct
      currentMaxLoss
      repairType
      repairStrikes
      repairCredit
      newMaxLoss
      newBreakEven
      confidenceBoost
      headline
      reason
      actionDescription
      priority
    }
  }
`;

/**
 * GraphQL Mutation: Accept and Deploy Repair Plan
 * 
 * This mutation:
 * 1. Validates the repair plan
 * 2. Calculates optimal execution (best bid/ask)
 * 3. Submits to broker
 * 4. Logs to database
 * 5. Updates position status
 * 6. Returns execution details
 */
export const ACCEPT_REPAIR_PLAN = gql`
  mutation AcceptRepairPlan(
    $position_id: String!
    $repair_plan_id: String!
    $user_id: String!
  ) {
    acceptRepairPlan(
      positionId: $position_id
      repairPlanId: $repair_plan_id
      userId: $user_id
    ) {
      success
      positionId
      repairType
      executionPrice
      executionCredit
      estimatedFees
      executionMessage
      newPositionStatus
      timestamp
    }
  }
`;

/**
 * GraphQL Mutation: Reject Repair Plan
 * 
 * Records rejection for analytics and removes from active queue
 */
export const REJECT_REPAIR_PLAN = gql`
  mutation RejectRepairPlan(
    $position_id: String!
    $user_id: String!
    $reason: String
  ) {
    rejectRepairPlan(
      positionId: $position_id
      userId: $user_id
      reason: $reason
    ) {
      success
      rejectionLogged: rejection_logged
      timestamp
    }
  }
`;

/**
 * GraphQL Subscription: Real-time Repair Plan Updates
 * 
 * Streams new repair plans to mobile app as they become available
 */
export const REPAIR_PLAN_UPDATES = gql`
  subscription RepairPlanUpdates($user_id: String!) {
    repairPlanUpdate(userId: $user_id) {
      positionId
      ticker
      priority
      headline
      actionDescription
      repairCredit
    }
  }
`;

/**
 * GraphQL Query: Get Flight Manual for Repair Type
 * 
 * Returns educational content explaining:
 * - Why this repair is recommended
 * - How the math works
 * - Historical success rate
 * - Example trades
 */
export const GET_FLIGHT_MANUAL_FOR_REPAIR = gql`
  query GetFlightManualForRepair($repair_type: String!) {
    flight_manual: flightManualByRepairType(repairType: $repair_type) {
      id
      repairType
      title
      description
      mathematicalExplanation
      exampleSetup {
        ticker
        strikes
        expiration
      }
      historicalSuccessRate
      edgePercentage
      avgCreditCollected
      riskMetrics {
        max_loss
        break_even_points
        probability_of_profit
      }
      relatedVideos
      relatedArticles
    }
  }
`;

/**
 * GraphQL Query: Portfolio Health Summary
 * 
 * Real-time snapshot of portfolio health
 */
export const GET_PORTFOLIO_HEALTH = gql`
  query GetPortfolioHealth($user_id: String!, $account_id: String!) {
    portfolio_health: portfolioHealth(userId: $user_id, accountId: $account_id) {
      status
      healthScore
      lastCheckTimestamp
      checks {
        name
        status
        message
      }
      alerts {
        type
        severity
        message
      }
      repairsNeeded
      estimatedImprovement
    }
  }
`;

/**
 * GraphQL Query: Repair History
 * 
 * Historical view of accepted/rejected repairs
 */
export const GET_REPAIR_HISTORY = gql`
  query GetRepairHistory($user_id: String!, $limit: Int, $offset: Int) {
    repair_history: repairHistory(userId: $user_id, limit: $limit, offset: $offset) {
      id
      positionId
      ticker
      repairType
      status
      acceptedAt
      executedAt
      creditCollected
      result
      pnlImpact
    }
  }
`;

/**
 * GraphQL Mutation: Execute Bulk Repairs
 * 
 * Deploy multiple repair plans at once
 */
export const EXECUTE_BULK_REPAIRS = gql`
  mutation ExecuteBulkRepairs(
    $user_id: String!
    $position_ids: [String!]!
  ) {
    executeBulkRepairs(userId: $user_id, positionIds: $position_ids) {
      success
      repairsExecuted
      totalCreditCollected
      executionSummary
      failures {
        positionId
        error
      }
    }
  }
`;
