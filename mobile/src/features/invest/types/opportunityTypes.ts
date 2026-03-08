/**
 * Opportunity Discovery — TypeScript type definitions.
 * Covers all asset classes and the Financial Intelligence Graph.
 * Mirrors the Private Markets deal pattern with graph-aware fields added.
 */

// ── Asset class & category enums ────────────────────────────────────────────

export type AssetClass =
  | 'real_estate'
  | 'alternatives'
  | 'fixed_income'
  | 'private_markets';

export type OpportunityCategory =
  | 'reit'           // real_estate
  | 'direct'         // real_estate (direct property)
  | 'hedge_fund'     // alternatives
  | 'commodity'      // alternatives
  | 'treasury'       // fixed_income
  | 'bond_ladder'    // fixed_income
  | 'cd'             // fixed_income
  | 'venture'        // private_markets
  | 'buyout';        // private_markets

export type LiquidityProfile = 'daily' | 'quarterly' | 'illiquid';
export type RiskLevel = 'low' | 'moderate' | 'high';

// ── Core opportunity ─────────────────────────────────────────────────────────

/** A curated investment opportunity across any asset class. */
export interface Opportunity {
  id: string;
  assetClass: AssetClass;
  name: string;
  tagline: string;
  /** 0–100, same scale as Private Markets Deal.score */
  score: number;
  category: OpportunityCategory | string;

  // Graph-aware fields — populated when graph context is available
  graphRationale?: string;
  graphEdgeIds?: string[];

  // Display / filter metadata
  minimumInvestment?: number;
  expectedReturnRange?: string;   // e.g. "4–6%"
  liquidity?: LiquidityProfile;
  riskLevel?: RiskLevel;
}

// ── Financial Intelligence Graph ─────────────────────────────────────────────

/** A single cross-silo relationship edge. */
export interface FinancialGraphEdge {
  relationshipId: string;    // e.g. "debt_to_investable_surplus"
  sourceLabel: string;       // e.g. "Credit Card Debt"
  targetLabel: string;       // e.g. "Monthly Investable Surplus"
  explanation: string;       // Human-readable sentence shown in UI + Oracle
  numericImpact?: number;
  unit?: string;             // "$/month", "months covered", "% utilization", "$/year"
  direction: 'positive' | 'negative' | 'neutral';
  confidence: number;        // 0.0–1.0
}

/** Full financial intelligence graph for the current user. */
export interface FinancialGraph {
  userId: number;
  edges: FinancialGraphEdge[];
  /** One-sentence summary per edge — shown in banners and Oracle feeds. */
  summarySentences: string[];

  // Raw silo snapshots
  totalCcBalance?: number;
  totalCcMinPayments?: number;
  totalSavingsBalance?: number;
  emergencyFundMonths?: number;
  avgCreditUtilization?: number;   // 0.0–1.0
  bestCreditScore?: number;
  estimatedMonthlyIncome?: number;
  investableSurplusMonthly?: number;
  portfolioTotalValue?: number;
}
