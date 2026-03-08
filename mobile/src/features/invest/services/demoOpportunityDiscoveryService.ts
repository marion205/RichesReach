/**
 * Demo implementation of IOpportunityDiscoveryService.
 * Reads from static DEMO_OPPORTUNITIES and DEMO_FINANCIAL_GRAPH.
 * Uses AsyncStorage for saved opportunity IDs.
 * Swap this for a GraphQL-backed implementation via setOpportunityDiscoveryService().
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Opportunity, FinancialGraph } from '../types/opportunityTypes';
import type { IOpportunityDiscoveryService } from './opportunityDiscoveryService';
import { DEMO_OPPORTUNITIES } from '../data/demoOpportunities';
import { DEMO_FINANCIAL_GRAPH } from '../data/demoFinancialGraph';

const SAVED_IDS_KEY = 'opportunityDiscovery_savedIds_v1';

export const demoOpportunityDiscoveryService: IOpportunityDiscoveryService = {
  async getOpportunities(filters) {
    let list = [...DEMO_OPPORTUNITIES];

    if (filters?.assetClass) {
      list = list.filter((o) => o.assetClass === filters.assetClass);
    }
    if (filters?.minScore != null) {
      list = list.filter((o) => o.score >= (filters.minScore ?? 0));
    }

    // Sort by score descending
    return list.sort((a, b) => b.score - a.score);
  },

  async getOpportunityDetail(opportunityId) {
    const found = DEMO_OPPORTUNITIES.find((o) => o.id === opportunityId);
    return found ? { ...found } : null;
  },

  async getFinancialGraph(): Promise<FinancialGraph | null> {
    return DEMO_FINANCIAL_GRAPH;
  },

  async getSavedOpportunityIds(): Promise<string[]> {
    try {
      const raw = await AsyncStorage.getItem(SAVED_IDS_KEY);
      if (!raw) return [];
      return JSON.parse(raw) as string[];
    } catch {
      return [];
    }
  },

  async saveOpportunity(opportunityId: string): Promise<void> {
    const ids = await demoOpportunityDiscoveryService.getSavedOpportunityIds();
    if (!ids.includes(opportunityId)) {
      await AsyncStorage.setItem(
        SAVED_IDS_KEY,
        JSON.stringify([...ids, opportunityId]),
      );
    }
  },

  async unsaveOpportunity(opportunityId: string): Promise<void> {
    const ids = await demoOpportunityDiscoveryService.getSavedOpportunityIds();
    await AsyncStorage.setItem(
      SAVED_IDS_KEY,
      JSON.stringify(ids.filter((id) => id !== opportunityId)),
    );
  },
};
