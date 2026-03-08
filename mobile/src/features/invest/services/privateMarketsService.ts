/**
 * Private Markets — service contract for real data.
 * Implement with demo data first; swap to API when compare workflow, data moat, and institutional diligence are live.
 *
 * Real-data capabilities:
 * - Compare workflow: getComparison(dealIds) returns DealComparison (benchmarked, consistent dimensions).
 * - Data moat: getDealDetail / getComparison expose dataProvenance (sources, refresh, gaps).
 * - Institutional diligence: getDiligence(dealId) returns InstitutionalDiligence (financials, cap table, terms, etc.).
 */

import type {
  Deal,
  DealDetail,
  DealComparison,
  CompareSession,
  InstitutionalDiligence,
  DealDataProvenance,
} from '../types/privateMarketsTypes';

export interface IPrivateMarketsService {
  /** List deals (with optional filters for segment, score range, etc.). */
  getDeals(filters?: { category?: string; minScore?: number; maxScore?: number }): Promise<Deal[]>;

  /** Full detail for one deal — includes score, fit, context, and when available diligence + provenance. */
  getDealDetail(dealId: string): Promise<DealDetail | null>;

  /**
   * Real compare workflow: compare N deals on consistent dimensions (scores, metrics, terms).
   * When real: uses same methodology and data moat as single-deal view; returns DealComparison.
   */
  getComparison(dealIds: string[]): Promise<DealComparison | null>;

  /**
   * Save or update a compare session (selected deal IDs) for persistence / "Saved comparisons".
   * When real: backend or local persistence.
   */
  saveCompareSession(session: CompareSession): Promise<void>;
  getCompareSessions(userId?: string): Promise<CompareSession[]>;

  /**
   * Institutional-grade diligence depth for a deal (financials, cap table, terms, legal, team, etc.).
   * When real: API returns full sections; demo returns null or stub.
   */
  getDiligence(dealId: string): Promise<InstitutionalDiligence | null>;

  /**
   * Data provenance for a deal (sources, last refresh, gaps) — data moat transparency.
   * When real: from API; demo can return stub or null.
   */
  getDataProvenance(dealId: string): Promise<DealDataProvenance | null>;
}

/** Default service instance. Swap demo for API-backed implementation when real data is live. */
let _instance: IPrivateMarketsService | null = null;

export function getPrivateMarketsService(): IPrivateMarketsService {
  if (_instance == null) {
    _instance = require('./demoPrivateMarketsService').demoPrivateMarketsService;
  }
  return _instance;
}

export function setPrivateMarketsService(service: IPrivateMarketsService): void {
  _instance = service;
}
