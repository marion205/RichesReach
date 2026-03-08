/**
 * Private Markets — domain types for scoring, portfolio fit, context, and trust.
 * Supports: proprietary scoring, portfolio-fit intelligence, decision infra, trust layer, better-than-market context.
 */

/** Base deal as used in list and detail */
export interface Deal {
  id: string;
  name: string;
  tagline: string;
  score: number;
  category?: string;
}

/** Single component of the overall score (explainable, consistent) */
export interface ScoreComponent {
  label: string;
  score: number;
  weight: string; // e.g. "25%"
  shortReason: string;
}

/** Benchmark context: how this deal compares to similar deals */
export interface ScoreBenchmark {
  percentileAmongPeers?: number; // e.g. 72 = top 28%
  peerCount?: number;
  segmentLabel?: string; // e.g. "Series B Fintech"
  trend?: 'above_peer' | 'in_line' | 'below_peer';
}

/** Full proprietary score: consistent, explainable, benchmarked */
export interface DealScore {
  overall: number;
  components: ScoreComponent[];
  benchmark?: ScoreBenchmark;
  methodologyId?: string; // link to trust layer
}

/** One portfolio-fit insight (overlap, diversification, liquidity) */
export type PortfolioFitKind = 'overlap' | 'diversification' | 'liquidity' | 'concentration' | 'alignment';

export interface PortfolioFitInsight {
  kind: PortfolioFitKind;
  headline: string;
  body: string;
  positive: boolean; // improves fit vs concern
}

/** Better-than-market context: what most platforms don't answer */
export interface DealContext {
  /** Is this deal actually attractive relative to similar ones? */
  relativeAttractiveness: string;
  /** What kind of investor is this fit for? */
  investorFit: string;
  /** Main hidden risk (clear risk framing) */
  mainHiddenRisk: string;
  /** How should this sit inside a real portfolio? */
  portfolioPlacement: string;
}

/** Transparent methodology (trust layer) */
export interface MethodologySummary {
  id: string;
  name: string;
  summary: string;
  pillars: string[]; // e.g. ["Unit economics", "Team", "Market", "Risk"]
  lastUpdated?: string;
}

/** Clear risk framing (trust layer) */
export interface RiskFraming {
  mainRisks: { label: string; description: string }[];
  concentrationNote?: string;
  liquidityNote?: string;
}

/** Decision infrastructure: compare, tradeoffs, sizing, concentration */
export interface DecisionSupport {
  suggestedPositionSize?: string; // e.g. "2–5% of alternatives sleeve"
  concentrationWarning?: string;
  tradeoffSummary?: string;
  compareDealIds?: string[];
}

/** What feeds the score — real inputs (unit economics, team, market, terms, signals) */
export interface ScoreInputCategory {
  id: string;
  label: string;
  items: { label: string; value: string | number; source?: string }[];
}

/** Full deal detail payload (for detail screen) */
export interface DealDetail extends Deal {
  scoreBreakdown?: DealScore;
  whyScore?: string[];
  riskFraming?: RiskFraming;
  portfolioFit?: PortfolioFitInsight[];
  context?: DealContext;
  methodology?: MethodologySummary;
  decisionSupport?: DecisionSupport;
  diligence?: InstitutionalDiligence;
  dataProvenance?: DealDataProvenance;
  /** Confidence in score and recommendation (from diligence + provenance) */
  confidence?: DealConfidence;
  /** Numeric confidence + factors (e.g. 68%, affected by missing legal) */
  confidenceDetail?: ConfidenceDetail;
  /** What feeds this score — real inputs for credibility */
  scoreInputs?: ScoreInputCategory[];
  /** What would change this score or confidence (actionable) */
  whatWouldChangeScore?: string[];
}

// ─── Compare workflow (real data) ───────────────────────────────────────────

/** Dimension to compare across deals (scores, metrics, terms) */
export type ComparisonDimensionId =
  | 'overall_score'
  | 'unit_economics'
  | 'team'
  | 'market_traction'
  | 'risk'
  | 'valuation'
  | 'stage'
  | 'sector'
  | 'liquidity_profile'
  | 'portfolio_fit'
  | 'diligence_completeness';

export interface ComparisonDimension {
  id: ComparisonDimensionId;
  label: string;
  format?: 'number' | 'percent' | 'text' | 'tier';
}

/** One row in a comparison: dimension + value per deal (by dealId) */
export interface ComparisonRow {
  dimensionId: ComparisonDimensionId;
  dimensionLabel: string;
  values: Record<string, number | string | null>; // dealId -> value
  /** Which deal is strongest on this dimension (for winner callout) */
  bestDealId?: string;
  /** Which deal is weakest or highest concern (for concern callout) */
  worstDealId?: string;
}

/** Result of comparing N deals — real data contract for compare workflow */
export interface DealComparison {
  dealIds: string[];
  deals: (Pick<Deal, 'id' | 'name' | 'tagline' | 'score' | 'category'> & { confidence?: DealConfidence })[];
  dimensions: ComparisonDimension[];
  rows: ComparisonRow[];
  generatedAt: string; // ISO
  dataProvenance?: DealDataProvenance;
  /** AI or rule-based summary for top of compare screen */
  summary?: CompareSummary;
}

/** Explicit data/score confidence — PE uncertainty should be visible */
export type DealConfidence = 'high' | 'moderate' | 'limited';

/** Numeric confidence + factors that affect it (actionable) */
export interface ConfidenceDetail {
  level: DealConfidence;
  /** 0–100, e.g. 68 for "Moderate (68%)" */
  percent?: number;
  /** What affects confidence: missing legal, incomplete cap table, etc. */
  factors?: string[];
}

/** Status for "What would change this score?" checklist — diligence workflow */
export type DiligenceItemStatus = 'not_started' | 'requested' | 'received' | 'reviewed';

/** Top-of-compare summary: best overall, best fit, highest diligence risk */
export interface CompareSummary {
  bestOverallDealId?: string;
  bestDiversificationFitDealId?: string;
  highestDiligenceRiskDealId?: string;
  /** Optional short lines for display, e.g. "Best overall: NovaGrid" */
  lines?: string[];
}

/** In-memory or persisted compare session (selected deal IDs + optional criteria) */
export interface CompareSession {
  id: string;
  dealIds: string[];
  userId?: string;
  createdAt: string;
  updatedAt: string;
}

// ─── Data moat (real data) ─────────────────────────────────────────────────

/** Single source that feeds our deal data (proprietary, partner, public) */
export type DataSourceKind = 'proprietary' | 'partner' | 'public' | 'user';

export interface DataSource {
  id: string;
  kind: DataSourceKind;
  name: string;
  description?: string;
  /** Whether we have exclusive or enhanced access (moat) */
  exclusiveOrEnhanced?: boolean;
}

/** Attribution for a piece of deal data: where it came from, when refreshed */
export interface DataAttribution {
  sourceId: string;
  sourceName: string;
  lastRefreshedAt: string; // ISO
  coverage?: string; // e.g. "financials, cap table"
}

/** Provenance for a deal or comparison — transparency and data moat */
export interface DealDataProvenance {
  dealId: string;
  attributions: DataAttribution[];
  lastFullRefresh: string; // ISO
  /** Gaps vs institutional-grade (e.g. "cap_table_partial") */
  gaps?: string[];
}

// ─── Institutional-grade diligence (real data) ──────────────────────────────

export type DiligenceSectionId =
  | 'financials'
  | 'cap_table'
  | 'terms'
  | 'legal'
  | 'team'
  | 'market'
  | 'competition'
  | 'governance'
  | 'documents';

export interface DiligenceSection {
  id: DiligenceSectionId;
  label: string;
  summary?: string;
  /** Structured content — real API fills these */
  items: { label: string; value: string | number; detail?: string }[];
  /** When we have document references */
  documentRefs?: { label: string; refId: string; type?: string }[];
  lastUpdated?: string;
  /** If section is partial or missing (vs institutional standard) */
  completeness?: 'full' | 'partial' | 'missing';
}

/** Institutional-grade diligence depth — real data contract */
export interface InstitutionalDiligence {
  dealId: string;
  sections: DiligenceSection[];
  /** Overall completeness vs institutional standard (for UI trust) */
  overallCompleteness?: 'full' | 'partial' | 'limited';
  lastUpdated: string;
}
