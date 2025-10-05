/**
 * 🔥 Hedge Fund-Grade AI Market Scanning Types
 * Designed for institutional-grade AI scanning, auditing, and performance tracking
 */

// Branded types for type safety
export type UUID = string & { __brand: 'uuid' };
export type Bps = number & { __brand: 'bps' };           // basis points 0..10_000
export type Pct = number & { __brand: 'pct' };           // 0..1
export type UnixMs = number & { __brand: 'unixms' };

export interface ModelProvenance {
  modelFamily: 'router' | 'rules' | 'stat' | 'ml';
  modelName: string;                // e.g., "alpha-momentum-v3"
  modelVersion: string;             // semver
  trainingWindow?: { start: string; end: string }; // ISO 8601
  featureSchemaHash?: string;       // sha256
  codeCommit?: string;              // git sha
}

export interface ComplianceMetadata {
  classification: 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED';
  jurisdictionTags: string[];       // ['GDPR', 'SEC_17a4', ...]
  pii: boolean;
  retentionDays: number;            // policy-backed
  disclaimer?: string;
}

export interface ScanPerformance {
  wallMs: number;
  symbolsEvaluated: number;
  symbolsReturned: number;
  cacheHit: boolean;
}

export interface ExplainabilityVector {
  method: 'shap' | 'lime' | 'rules';
  topDrivers: Array<{ feature: string; contribution: number }>;
  globalConfidence: Pct;
}

export interface BacktestSummary {
  window: { start: string; end: string };
  totalRuns: number;
  hitRate: Pct;
  avgReturn: Pct;
  maxDrawdown: Pct;
  sharpe: number;
}

export interface RiskEnvelope {
  valueAtRisk1dPct?: Pct;
  beta?: number;
  maxPositionSizePct: Pct;          // 0..1
  stopLossPct?: Pct;
  timeStopDays?: number;
}

export interface AIScan {
  id: UUID;
  name: string;
  description: string;
  category: ScanCategory;
  riskLevel: RiskLevel;
  timeHorizon: TimeHorizon;
  isActive: boolean;
  lastRun?: string;                  // ISO for transport safety
  results?: ScanResult[];
  parameters: ScanParameters;
  playbook?: Playbook;
  performance?: ScanPerformance;
  provenance?: ModelProvenance;
  compliance?: ComplianceMetadata;
  backtest?: BacktestSummary;
  version?: string;                  // semver
}

/** Individual result from AI market scan */
export interface ScanResult {
  id: UUID;
  symbol: string;
  name: string;
  currentPrice: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  score: Pct;
  confidence: Pct;
  reasoning: string;
  riskFactors: string[];
  opportunityFactors: string[];
  technicalSignals: TechnicalSignal[];
  fundamentalMetrics: FundamentalMetric[];
  altDataSignals: AltDataSignal[];
  explainability?: ExplainabilityVector;
  riskEnvelope?: RiskEnvelope;
  provenance?: ModelProvenance;
  compliance?: ComplianceMetadata;
}

/** Core playbook definition for institutional strategies */
export interface Playbook {
  id: UUID;
  name: string;
  description: string;
  author: string;
  category: ScanCategory;
  riskLevel: RiskLevel;
  isPublic: boolean;
  isClonable: boolean;
  parameters: ScanParameters;
  explanation: PlaybookExplanation;
  performance: PlaybookPerformance;
  tags: string[];
  approval?: { status: 'draft'|'review'|'approved'|'retired'; approver?: string; at?: string };
  version?: string;
}

export interface PlaybookExplanation {
  whyThisSetup: string;
  riskBands: RiskBand[];
  altDataHooks: AltDataHook[];
  marketConditions: string[];
  expectedOutcomes: string[];
  modelRationale?: string;
}

/** Extended risk structure aligned with hedge-fund risk policy */
export interface RiskBand {
  level: RiskLevel;
  description: string;
  maxPositionSize: Pct;
  stopLossPercent: Pct;
  timeHorizon: TimeHorizon;
}

/** Data hook linking alternative data to alpha hypothesis */
export interface AltDataHook {
  name: string;
  description: string;
  weight: Pct;
  source: string;
  example: string;
}

/** Detailed signal explainability for compliance + audit */
export interface ExplainabilityVector {
  method: 'shap' | 'lime' | 'rules';
  topDrivers: Array<{ feature: string; contribution: number }>;
  globalConfidence: Pct;
}

/** Structured risk and opportunity factors for analysts */
export interface RiskFactor {
  name: string;
  description: string;
  severity: number;
  impact: number;
}

export interface OpportunityFactor {
  name: string;
  description: string;
  potentialGain: number;
  conviction: number;
}

export interface TechnicalSignal {
  indicator: string;
  value: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  strength: Pct;
  description: string;
}

export interface FundamentalMetric {
  metric: string;
  value: number;
  benchmark: number;
  signal: 'positive' | 'negative' | 'neutral';
  description?: string;
}

export interface AltDataSignal {
  source: string;
  signal: string;
  strength: Pct;
  description: string;
  timestamp: string;                // ISO
}

/** Parameters controlling the scan universe and logic */
export interface ScanParameters {
  universe: string[];
  minPrice: number;
  maxPrice: number;
  minVolume: number;
  minMarketCap: number;
  sectors: string[];
  technicalIndicators: string[];
  fundamentalFilters: string[];
  altDataSources: string[];
  riskTolerance: RiskLevel;
  timeHorizon: TimeHorizon;
  lookbackPeriod?: number;
  rebalanceFrequency?: string;
  signalThreshold?: number;
}

/** Performance analytics for scans or playbooks */
export interface PlaybookPerformance {
  totalRuns: number;
  successRate: Pct;
  averageReturn: Pct;
  maxDrawdown: Pct;
  sharpeRatio: number;
  winRate: Pct;
  avgHoldTime: number;
  lastUpdated: string;              // ISO
}

/** Backtesting and validation summary */
export interface BacktestSummary {
  window: { start: string; end: string };
  totalRuns: number;
  hitRate: Pct;
  avgReturn: Pct;
  maxDrawdown: Pct;
  sharpe: number;
}

/** Risk & compliance metadata */
export interface ComplianceMetadata {
  classification: 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED';
  jurisdictionTags: string[];       // ['GDPR', 'SEC_17a4', ...]
  pii: boolean;
  retentionDays: number;            // policy-backed
  disclaimer?: string;
}

/** Provenance for model tracking and reproducibility */
export interface ModelProvenance {
  modelFamily: 'router' | 'rules' | 'stat' | 'ml';
  modelName: string;                // e.g., "alpha-momentum-v3"
  modelVersion: string;             // semver
  trainingWindow?: { start: string; end: string }; // ISO 8601
  featureSchemaHash?: string;       // sha256
  codeCommit?: string;              // git sha
}

export interface ScanPerformance {
  wallMs: number;
  symbolsEvaluated: number;
  symbolsReturned: number;
  cacheHit: boolean;
}

export type ScanCategory =
  | 'momentum'
  | 'value'
  | 'growth'
  | 'dividend'
  | 'volatility'
  | 'earnings'
  | 'sector_rotation'
  | 'technical_breakout'
  | 'mean_reversion'
  | 'quant_factor'
  | 'macro_event'
  | 'custom';

export type RiskLevel = 'low' | 'medium' | 'high' | 'very_high';

export type TimeHorizon = 'intraday' | 'daily' | 'weekly' | 'monthly' | 'quarterly';

export type ScanStatus = 'draft' | 'active' | 'paused' | 'archived';

/** API request/response interfaces */
export interface AIScanFilters {
  category?: ScanCategory;
  riskLevel?: RiskLevel;
  timeHorizon?: TimeHorizon;
  isActive?: boolean;
  tags?: string[];
  minSharpe?: number;
  dateRange?: [Date, Date];
}

export interface CreateScanRequest {
  name: string;
  description: string;
  category: ScanCategory;
  parameters: ScanParameters;
  playbookId?: string;
}

export interface RunScanRequest {
  scanId: UUID;
  parameters?: Partial<ScanParameters>;
}

export interface ClonePlaybookRequest {
  playbookId: UUID;
  name: string;
  description: string;
  parameters?: Partial<ScanParameters>;
}