/**
 * Mobile UI Types for RichesReach Edge Factory
 * 
 * This file defines the TypeScript interfaces that bridge the Python/Rust
 * backend with the React Native mobile app.
 */

// ============================================================================
// Greeks & Valuation
// ============================================================================

export interface Greeks {
  /** Delta: price sensitivity (-1 to 1) */
  delta: number;
  /** Gamma: delta sensitivity (convexity) */
  gamma: number;
  /** Theta: daily time decay */
  theta: number;
  /** Vega: IV sensitivity */
  vega: number;
  /** Rho: interest rate sensitivity */
  rho: number;
}

export interface OptionValuation {
  /** Underlying symbol (e.g., "AAPL") */
  symbol: string;
  /** Strike price */
  strike: number;
  /** Days to expiration */
  daysToExpiration: number;
  /** Implied volatility (0-1 scale) */
  impliedVolatility: number;
  /** Calculated Greeks */
  greeks: Greeks;
  /** Fair value estimate */
  fairValue: number;
  /** Bid-ask spread in dollars */
  spread: number;
}

// ============================================================================
// Positions & Portfolio
// ============================================================================

export interface OptionPosition {
  /** Unique position ID */
  id: string;
  /** Stock ticker */
  ticker: string;
  /** Strategy type (e.g., "BULL_PUT_SPREAD", "IRON_CONDOR") */
  strategyType: string;
  /** Entry price (credit/debit) */
  entryPrice: number;
  /** Current market price */
  currentPrice: number;
  /** Position Greeks */
  greeks: Greeks;
  /** Max profit in dollars */
  maxProfit: number;
  /** Max loss in dollars */
  maxLoss: number;
  /** Unrealized P&L */
  unrealizedPnL: number;
  /** Probability of profit (0-1) */
  probabilityOfProfit: number;
  /** Days to expiration */
  daysToExpiration: number;
  /** Status: "open" | "closed" | "exited" */
  status: "open" | "closed" | "exited";
  /** Timestamp when position was opened */
  openedAt: string;
}

export interface Portfolio {
  /** User ID */
  userId: number;
  /** Account equity */
  accountEquity: number;
  /** Total number of open positions */
  totalPositions: number;
  /** Aggregate portfolio Greeks */
  greeks: Greeks;
  /** Total risk (sum of max losses) */
  totalRisk: number;
  /** Win rate percentage */
  winRate: number;
}

// ============================================================================
// Health & Monitoring
// ============================================================================

export enum HealthStatus {
  GREEN = "GREEN",   // All systems healthy
  YELLOW = "YELLOW", // Caution warnings
  RED = "RED",       // Critical issues
}

export interface PositionHealth {
  /** Position ID */
  positionId: string;
  /** Overall health status */
  status: HealthStatus;
  /** Data freshness (GREEN/YELLOW/RED) */
  dataFreshness: "GREEN" | "YELLOW" | "RED";
  /** Logic confidence (0-1) */
  logicConfidence: number;
  /** Active alerts (if any) */
  activeAlerts: string[];
}

// ============================================================================
// Repair Plans & Defense
// ============================================================================

export interface RepairPlan {
  /** Position ID being repaired */
  positionId: string;
  /** Stock ticker */
  ticker: string;
  /** Original strategy type */
  originalStrategy: string;
  /** Current delta */
  currentDelta: number;
  /** Delta drift percentage (0-1) */
  deltaDriftPct: number;
  /** Current max loss */
  currentMaxLoss: number;
  /** Repair strategy (e.g., "BEAR_CALL_SPREAD") */
  repairType: string;
  /** Strikes to trade (e.g., "Sell 125C / Buy 130C") */
  repairStrikes: string;
  /** Credit to collect */
  repairCredit: number;
  /** New max loss after repair */
  newMaxLoss: number;
  /** New break-even price */
  newBreakEven: number;
  /** Confidence boost (0-1) */
  confidenceBoost: number;
  /** Priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" */
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  /** User-friendly headline */
  headline: string;
  /** Detailed reason */
  reason: string;
  /** Action description */
  actionDescription: string;
}

export interface RepairAction {
  /** Repair plan */
  plan: RepairPlan;
  /** Whether user accepted */
  accepted: boolean;
  /** Timestamp of decision */
  decidedAt: string;
  /** Result if executed */
  executionResult?: {
    status: "pending" | "executed" | "failed";
    orderId?: string;
    message?: string;
  };
}

// ============================================================================
// Market Regime & Strategy
// ============================================================================

export enum MarketRegime {
  CRASH_PANIC = "CRASH_PANIC",
  TREND_UP = "TREND_UP",
  TREND_DOWN = "TREND_DOWN",
  BREAKOUT_EXPANSION = "BREAKOUT_EXPANSION",
  MEAN_REVERSION = "MEAN_REVERSION",
  POST_EVENT_CRUSH = "POST_EVENT_CRUSH",
  NEUTRAL = "NEUTRAL",
}

export interface MarketAnalysis {
  /** Stock ticker */
  ticker: string;
  /** Current market regime */
  regime: MarketRegime;
  /** Confidence level: "HIGH" | "MEDIUM" | "LOW" | "CAUTION" */
  confidenceLevel: "HIGH" | "MEDIUM" | "LOW" | "CAUTION";
  /** Regime description */
  description: string;
  /** Top 3 recommended strategies */
  flightManuals: FlightManual[];
}

export interface FlightManual {
  /** Strategy name */
  strategy: string;
  /** Position type: "credit" | "debit" | "neutral" */
  positionType: "credit" | "debit" | "neutral";
  /** Recommended strike selection */
  strikes: {
    short: number;
    long?: number;
  };
  /** Days to expiration */
  daysToExpiration: number;
  /** Probability of profit */
  probabilityOfProfit: number;
  /** Max profit in dollars */
  maxProfit: number;
  /** Max loss in dollars */
  maxLoss: number;
  /** Recommended position size (contracts) */
  positionSize: number;
  /** User experience level this is suitable for */
  suitableFor: "basic" | "intermediate" | "pro";
  /** Human-readable summary */
  summary: string;
  /** Full action plan */
  action: string;
}

// ============================================================================
// Greeks Risk Dashboard
// ============================================================================

export interface RiskDashboard {
  /** Portfolio-level Greeks */
  portfolio: Greeks;
  /** Breakdown by Greek */
  breakdown: {
    /** Delta exposure (directional) */
    delta: {
      value: number;
      status: "neutral" | "bullish" | "bearish";
      exposure: "high" | "medium" | "low";
    };
    /** Gamma exposure (convexity) */
    gamma: {
      value: number;
      status: "positive" | "negative";
      exposure: "high" | "medium" | "low";
    };
    /** Theta exposure (time decay) */
    theta: {
      value: number;
      status: "positive" | "negative";
      exposure: "high" | "medium" | "low";
    };
    /** Vega exposure (volatility) */
    vega: {
      value: number;
      status: "long" | "short";
      exposure: "high" | "medium" | "low";
    };
  };
}

// ============================================================================
// GraphQL Response Wrappers
// ============================================================================

export interface OptionsAnalysisResponse {
  /** Analysis result */
  optionsAnalysis: {
    /** Market analysis */
    analysis: MarketAnalysis;
    /** Portfolio state */
    portfolio: Portfolio;
    /** Open positions */
    positions: OptionPosition[];
    /** Any warnings */
    warnings: string[];
  };
}

export interface PortfolioRepairCheckResponse {
  /** Repair analysis result */
  checkPortfolioRepairs: {
    /** User ID */
    userId: number;
    /** Repair plans */
    repairPlans: RepairPlan[];
    /** Number needing repair */
    repairsNeeded: number;
    /** Notifications sent */
    notificationsSent: number;
    /** Timestamp */
    timestamp: string;
  };
}

// ============================================================================
// UI Component Props
// ============================================================================

export interface PositionCardProps {
  position: OptionPosition;
  health: PositionHealth;
  repairPlan?: RepairPlan;
  onRepairClick?: (plan: RepairPlan) => void;
}

export interface GreeksRadarChartProps {
  greeks: Greeks;
  maxDelta?: number;
  maxTheta?: number;
  maxVega?: number;
  maxGamma?: number;
}

export interface ShieldStatusBarProps {
  status: HealthStatus;
  message?: string;
  onTap?: () => void;
}

export interface RepairModalProps {
  plan: RepairPlan;
  position: OptionPosition;
  onAccept: () => void;
  onReject: () => void;
  loading?: boolean;
}

// ============================================================================
// Mobile-specific Types
// ============================================================================

export interface MobileAnalysisRequest {
  userId: number;
  ticker: string;
  experienceLevel: "basic" | "intermediate" | "pro";
}

export interface MobilePortfolioRequest {
  userId: number;
}

export interface MobileRepairCheckRequest {
  userId: number;
}
