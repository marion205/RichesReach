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
      total_delta
      total_gamma
      total_theta
      total_vega
      portfolio_health_status
      repairs_available
      total_max_loss
    }
    positions(userId: $user_id, accountId: $account_id) {
      id
      ticker
      strategy_type
      entry_price
      current_price
      quantity
      unrealized_pnl
      days_to_expiration
      expiration_date
      greeks {
        delta
        gamma
        theta
        vega
        rho
      }
      max_loss
      probability_of_profit
      status
    }
    repair_plans: activeRepairPlans(userId: $user_id, accountId: $account_id) {
      position_id
      ticker
      original_strategy
      current_delta
      delta_drift_pct
      current_max_loss
      repair_type
      repair_strikes
      repair_credit
      new_max_loss
      new_break_even
      confidence_boost
      headline
      reason
      action_description
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
      strategy_type
      entry_price
      current_price
      quantity
      unrealized_pnl
      days_to_expiration
      greeks {
        delta
        gamma
        theta
        vega
        rho
      }
      max_loss
      probability_of_profit
    }
    repair_plan: repairPlan(positionId: $position_id) {
      position_id
      ticker
      original_strategy
      current_delta
      delta_drift_pct
      current_max_loss
      repair_type
      repair_strikes
      repair_credit
      new_max_loss
      new_break_even
      confidence_boost
      headline
      reason
      action_description
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
      position_id
      repair_type
      execution_price
      execution_credit
      estimated_fees
      execution_message
      new_position_status
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
      rejection_logged
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
      position_id
      ticker
      priority
      headline
      action_description
      repair_credit
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
      repair_type
      title
      description
      mathematical_explanation
      example_setup {
        ticker
        strikes
        expiration
      }
      historical_success_rate
      edge_percentage
      avg_credit_collected
      risk_metrics {
        max_loss
        break_even_points
        probability_of_profit
      }
      related_videos
      related_articles
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
      health_score
      last_check_timestamp
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
      repairs_needed
      estimated_improvement
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
      position_id
      ticker
      repair_type
      status
      accepted_at
      executed_at
      credit_collected
      result
      pnl_impact
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
      repairs_executed
      total_credit_collected
      execution_summary
      failures {
        position_id
        error
      }
    }
  }
`;
