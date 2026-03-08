/**
 * Demo implementation of IPrivateMarketsService.
 * Uses demo deals and getDemoDealDetail; compare/diligence/provenance are stubbed for real-data contract.
 * Swap this for an API-backed implementation when compare workflow, data moat, and diligence are live.
 */

import type {
  Deal,
  DealDetail,
  DealComparison,
  CompareSession,
  CompareSummary,
  InstitutionalDiligence,
  DealDataProvenance,
  ComparisonDimensionId,
  DealConfidence,
} from '../types/privateMarketsTypes';
import type { IPrivateMarketsService } from './privateMarketsService';
import { DEMO_DEALS } from '../data/demoDeals';
import { getDemoDealDetail } from '../data/demoDealDetail';

const sessions = new Map<string, CompareSession>();

export const demoPrivateMarketsService: IPrivateMarketsService = {
  async getDeals(filters) {
    let list = [...DEMO_DEALS];
    if (filters?.category) {
      list = list.filter((d) => (d.category ?? '').toLowerCase() === filters.category!.toLowerCase());
    }
    if (filters?.minScore != null) list = list.filter((d) => d.score >= filters!.minScore!);
    if (filters?.maxScore != null) list = list.filter((d) => d.score <= filters!.maxScore!);
    return list;
  },

  async getDealDetail(dealId: string): Promise<DealDetail | null> {
    const deal = DEMO_DEALS.find((d) => d.id === dealId);
    if (!deal) return null;
    return getDemoDealDetail(deal);
  },

  async getComparison(dealIds: string[]): Promise<DealComparison | null> {
    if (dealIds.length === 0) return null;
    const deals = dealIds
      .map((id) => DEMO_DEALS.find((d) => d.id === id))
      .filter(Boolean) as Deal[];
    if (deals.length !== dealIds.length) return null;

    const diligenceByDeal: Record<string, InstitutionalDiligence | null> = {};
    await Promise.all(dealIds.map(async (id) => { diligenceByDeal[id] = await this.getDiligence(id); }));

    const toConfidence = (d: InstitutionalDiligence | null): DealConfidence => {
      if (!d?.overallCompleteness) return 'limited';
      if (d.overallCompleteness === 'full') return 'high';
      if (d.overallCompleteness === 'partial') return 'moderate';
      return 'limited';
    };

    const dimensionIds: ComparisonDimensionId[] = [
      'overall_score',
      'unit_economics',
      'team',
      'market_traction',
      'risk',
      'valuation',
      'stage',
      'sector',
      'liquidity_profile',
      'portfolio_fit',
      'diligence_completeness',
    ];
    const labels: Record<ComparisonDimensionId, string> = {
      overall_score: 'Overall score',
      unit_economics: 'Unit economics',
      team: 'Team',
      market_traction: 'Market & traction',
      risk: 'Risk & downside',
      valuation: 'Valuation',
      stage: 'Stage',
      sector: 'Sector',
      liquidity_profile: 'Liquidity profile',
      portfolio_fit: 'Portfolio fit',
      diligence_completeness: 'Diligence completeness',
    };
    const higherIsBetter = new Set<ComparisonDimensionId>(['overall_score', 'unit_economics', 'team', 'market_traction', 'diligence_completeness']);
    const diligenceRank = (v: string | number | null): number => {
      if (v === 'Full' || v === 'full') return 3;
      if (v === 'Partial' || v === 'partial') return 2;
      return 1;
    };
    const getComponentScore = (deal: Deal, dim: ComparisonDimensionId): number | string | null => {
      const detail = getDemoDealDetail(deal);
      if (dim === 'overall_score') return deal.score;
      const comp = detail.scoreBreakdown?.components.find((c) =>
        dim === 'unit_economics' ? c.label === 'Unit economics' : dim === 'team' ? c.label === 'Team' : dim === 'market_traction' ? c.label === 'Market & traction' : dim === 'risk' ? c.label === 'Risk & downside' : false
      );
      return comp?.score ?? null;
    };

    const rows = dimensionIds.map((dimId) => {
      const values: Record<string, number | string | null> = {};
      dealIds.forEach((id) => {
        const deal = deals.find((d) => d.id === id)!;
        if (dimId === 'overall_score') {
          values[id] = deal.score;
        } else if (dimId === 'stage' || dimId === 'sector') {
          values[id] = deal.category ?? deal.name.split('—')[0]?.trim() ?? '';
        } else if (dimId === 'valuation') {
          values[id] = deal.id === '1' ? '$42M' : deal.id === '2' ? '$8M' : '$18M';
        } else if (dimId === 'liquidity_profile') {
          values[id] = '5–8 yr hold';
        } else if (dimId === 'portfolio_fit') {
          values[id] = deal.category === 'fintech' ? 'Overlap' : 'Diversifies';
        } else if (dimId === 'diligence_completeness') {
          values[id] = deal.id === '1' ? 'Partial' : deal.id === '2' ? 'Limited' : 'Partial';
        } else {
          values[id] = getComponentScore(deal, dimId);
        }
      });

      let bestDealId: string | undefined;
      let worstDealId: string | undefined;
      if (dimId === 'portfolio_fit') {
        const diversifies = dealIds.filter((id) => values[id] === 'Diversifies');
        const overlap = dealIds.filter((id) => values[id] === 'Overlap');
        if (diversifies.length > 0) bestDealId = diversifies[0];
        if (overlap.length > 0) worstDealId = overlap[0];
      } else if (dimId === 'diligence_completeness') {
        let bestRank = 0, worstRank = 4;
        dealIds.forEach((id) => {
          const r = diligenceRank(values[id]);
          if (r > bestRank) { bestRank = r; bestDealId = id; }
          if (r < worstRank) { worstRank = r; worstDealId = id; }
        });
      } else if (dimId !== 'stage' && dimId !== 'sector' && dimId !== 'valuation' && dimId !== 'liquidity_profile') {
        const numeric = higherIsBetter.has(dimId);
        let bestVal: number | null = null, worstVal: number | null = null;
        dealIds.forEach((id) => {
          const v = values[id];
          const n = typeof v === 'number' ? v : null;
          if (n == null) return;
          if (numeric) {
            if (bestVal == null || n > bestVal) { bestVal = n; bestDealId = id; }
            if (worstVal == null || n < worstVal) { worstVal = n; worstDealId = id; }
          } else {
            if (bestVal == null || n < bestVal) { bestVal = n; bestDealId = id; }
            if (worstVal == null || n > worstVal) { worstVal = n; worstDealId = id; }
          }
        });
      }

      return {
        dimensionId: dimId,
        dimensionLabel: labels[dimId],
        values,
        bestDealId,
        worstDealId,
      };
    });

    const scoreRow = rows.find((r) => r.dimensionId === 'overall_score');
    const fitRow = rows.find((r) => r.dimensionId === 'portfolio_fit');
    const diligenceRow = rows.find((r) => r.dimensionId === 'diligence_completeness');
    const bestOverallDealId = scoreRow?.bestDealId;
    const bestDiversificationFitDealId = fitRow?.bestDealId;
    const highestDiligenceRiskDealId = diligenceRow?.worstDealId;
    const summary: CompareSummary = {
      bestOverallDealId,
      bestDiversificationFitDealId,
      highestDiligenceRiskDealId,
      lines: [
        bestOverallDealId && `Best overall: ${deals.find((d) => d.id === bestOverallDealId)?.name ?? ''}`,
        bestDiversificationFitDealId && `Best diversification fit: ${deals.find((d) => d.id === bestDiversificationFitDealId)?.name ?? ''}`,
        highestDiligenceRiskDealId && `Highest diligence risk: ${deals.find((d) => d.id === highestDiligenceRiskDealId)?.name ?? ''}`,
      ].filter(Boolean) as string[],
    };

    return {
      dealIds,
      deals: deals.map((d) => ({
        id: d.id,
        name: d.name,
        tagline: d.tagline,
        score: d.score,
        category: d.category,
        confidence: toConfidence(diligenceByDeal[d.id]),
      })),
      dimensions: dimensionIds.map((id) => ({ id, label: labels[id] })),
      rows,
      generatedAt: new Date().toISOString(),
      summary,
    };
  },

  async saveCompareSession(session: CompareSession): Promise<void> {
    sessions.set(session.id, { ...session, updatedAt: new Date().toISOString() });
  },

  async getCompareSessions(): Promise<CompareSession[]> {
    return Array.from(sessions.values());
  },

  async getDiligence(dealId: string): Promise<InstitutionalDiligence | null> {
    const deal = DEMO_DEALS.find((d) => d.id === dealId);
    if (!deal) return null;
    return {
      dealId,
      overallCompleteness: dealId === '1' ? 'partial' : 'limited',
      lastUpdated: new Date().toISOString(),
      sections: [
        {
          id: 'financials',
          label: 'Financials',
          summary: 'Revenue, burn, unit economics',
          completeness: 'partial',
          lastUpdated: new Date().toISOString(),
          items: [
            { label: 'ARR (trailing)', value: '$2.1M' },
            { label: 'Growth (YoY)', value: '120%' },
            { label: 'Gross margin', value: '74%', detail: 'Target 80% in 18mo' },
          ],
        },
        {
          id: 'terms',
          label: 'Terms',
          summary: 'Round terms and key rights',
          completeness: 'partial',
          items: [
            { label: 'Round', value: 'Series B' },
            { label: 'Valuation (pre)', value: '$42M' },
            { label: 'Liquidation pref', value: '1x non-participating' },
          ],
        },
        {
          id: 'market',
          label: 'Market',
          summary: 'TAM, SAM, competitive landscape',
          completeness: 'full',
          items: [
            { label: 'TAM', value: '$12B' },
            { label: 'SAM (addressable)', value: '$1.2B' },
            { label: 'Competitors', value: '3 direct', detail: 'Incumbents moving in' },
          ],
        },
        {
          id: 'team',
          label: 'Team',
          summary: 'Founders and key hires',
          completeness: 'partial',
          items: [
            { label: 'CEO', value: 'Prior exit (fintech)' },
            { label: 'CTO', value: 'Ex-FAANG' },
          ],
        },
        {
          id: 'legal',
          label: 'Legal',
          summary: 'Cap table, governance, docs',
          completeness: 'missing',
          items: [],
          documentRefs: [{ label: 'Data room', refId: 'room-1', type: 'link' }],
        },
        {
          id: 'governance',
          label: 'Governance',
          summary: 'Board, rights, reporting',
          completeness: 'partial',
          items: [
            { label: 'Board seats (investor)', value: '1' },
            { label: 'Reporting', value: 'Quarterly' },
          ],
        },
      ],
    };
  },

  async getDataProvenance(dealId: string): Promise<DealDataProvenance | null> {
    return {
      dealId,
      attributions: [
        { sourceId: 'demo', sourceName: 'Demo data', lastRefreshedAt: new Date().toISOString(), coverage: 'N/A' },
      ],
      lastFullRefresh: new Date().toISOString(),
      gaps: ['no_institutional_diligence', 'no_live_compare_data_moat'],
    };
  },
};
