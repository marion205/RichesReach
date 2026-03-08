/**
 * Opportunity Discovery — service contract.
 * Demo implementation ships first; swap for a GraphQL-backed implementation
 * once opportunity_discovery_types.py is deployed.
 *
 * Usage:
 *   import { getOpportunityDiscoveryService } from './opportunityDiscoveryService';
 *   const service = getOpportunityDiscoveryService();
 *   const opps = await service.getOpportunities({ assetClass: 'fixed_income' });
 */

import type { Opportunity, FinancialGraph } from '../types/opportunityTypes';

export interface IOpportunityDiscoveryService {
  /**
   * List opportunities, optionally filtered by asset class.
   * Set includeGraphContext to true (default) to get graph-aware scoring & rationale.
   */
  getOpportunities(filters?: {
    assetClass?: string;
    minScore?: number;
    includeGraphContext?: boolean;
  }): Promise<Opportunity[]>;

  /** Full detail for one opportunity (score breakdown, risk framing, etc.). */
  getOpportunityDetail(opportunityId: string): Promise<Opportunity | null>;

  /** Financial Intelligence Graph for the current user. */
  getFinancialGraph(): Promise<FinancialGraph | null>;

  /** IDs of opportunities the user has saved (watchlist). */
  getSavedOpportunityIds(): Promise<string[]>;
  saveOpportunity(opportunityId: string): Promise<void>;
  unsaveOpportunity(opportunityId: string): Promise<void>;
}

/** Default service instance — swappable at runtime. */
let _instance: IOpportunityDiscoveryService | null = null;

export function getOpportunityDiscoveryService(): IOpportunityDiscoveryService {
  if (_instance == null) {
    _instance =
      require('./demoOpportunityDiscoveryService').demoOpportunityDiscoveryService;
  }
  return _instance;
}

export function setOpportunityDiscoveryService(
  service: IOpportunityDiscoveryService,
): void {
  _instance = service;
}
