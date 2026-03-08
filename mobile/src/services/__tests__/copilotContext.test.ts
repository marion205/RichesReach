/**
 * Unit tests for Copilot context: getCopilotContext and serializeCopilotContextForPrompt.
 * Mocks portfolio, credit, and private markets services.
 */

const mockGetPortfolioData = jest.fn();
const mockGetScore = jest.fn();
const mockGetUtilization = jest.fn();
const mockGetSavedDealIds = jest.fn();
const mockGetDeals = jest.fn();

jest.mock('../../features/portfolio/services/RealTimePortfolioService', () => ({
  __esModule: true,
  default: { getPortfolioData: (...args: unknown[]) => mockGetPortfolioData(...args) },
}));

jest.mock('../../features/credit/services/CreditScoreService', () => ({
  creditScoreService: { getScore: (...args: unknown[]) => mockGetScore(...args) },
}));

jest.mock('../../features/credit/services/CreditUtilizationService', () => ({
  creditUtilizationService: { getUtilization: (...args: unknown[]) => mockGetUtilization(...args) },
}));

jest.mock('../../features/invest/services/privateMarketsService', () => ({
  getPrivateMarketsService: () => ({
    getSavedDealIds: (...args: unknown[]) => mockGetSavedDealIds(...args),
    getDeals: (...args: unknown[]) => mockGetDeals(...args),
  }),
}));

import {
  getCopilotContext,
  serializeCopilotContextForPrompt,
  type CopilotContext,
} from '../copilotContext';

describe('copilotContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetPortfolioData.mockResolvedValue(null);
    mockGetScore.mockResolvedValue(null);
    mockGetUtilization.mockResolvedValue(null);
    mockGetSavedDealIds.mockResolvedValue([]);
    mockGetDeals.mockResolvedValue([]);
  });

  describe('getCopilotContext', () => {
    it('returns builtAt and all sections null when all services fail or return empty', async () => {
      mockGetPortfolioData.mockRejectedValue(new Error('network'));
      mockGetScore.mockRejectedValue(new Error('network'));
      mockGetSavedDealIds.mockRejectedValue(new Error('storage'));

      const ctx = await getCopilotContext();

      expect(ctx.portfolio).toBeNull();
      expect(ctx.credit).toBeNull();
      expect(ctx.privateMarkets).toBeNull();
      expect(ctx.builtAt).toBeDefined();
      expect(new Date(ctx.builtAt).getTime()).toBeLessThanOrEqual(Date.now() + 1000);
    });

    it('populates portfolio when getPortfolioData returns holdings', async () => {
      mockGetPortfolioData.mockResolvedValue({
        totalValue: 100000,
        holdings: [
          { symbol: 'AAPL', totalValue: 60000 },
          { symbol: 'MSFT', totalValue: 40000 },
        ],
      });

      const ctx = await getCopilotContext();

      expect(ctx.portfolio).not.toBeNull();
      expect(ctx.portfolio!.totalValue).toBe(100000);
      expect(ctx.portfolio!.holdingCount).toBe(2);
      expect(ctx.portfolio!.topHoldings.map((h) => h.symbol)).toEqual(['AAPL', 'MSFT']);
      expect(ctx.portfolio!.topHoldings[0].pct).toBe(60);
      expect(ctx.portfolio!.topHoldings[1].pct).toBe(40);
    });

    it('returns portfolio null when getPortfolioData returns no holdings', async () => {
      mockGetPortfolioData.mockResolvedValue({ totalValue: 0, holdings: [] });

      const ctx = await getCopilotContext();

      expect(ctx.portfolio).toBeNull();
    });

    it('populates credit when score and utilization services resolve', async () => {
      mockGetScore.mockResolvedValue({ score: 720, scoreRange: 'Good' });
      mockGetUtilization.mockResolvedValue({
        currentUtilization: 0.25,
        totalLimit: 20000,
        totalBalance: 5000,
      });

      const ctx = await getCopilotContext();

      expect(ctx.credit).not.toBeNull();
      expect(ctx.credit!.score).toBe(720);
      expect(ctx.credit!.scoreRange).toBe('Good');
      expect(ctx.credit!.utilizationPct).toBe(0.25);
      expect(ctx.credit!.totalLimit).toBe(20000);
      expect(ctx.credit!.totalBalance).toBe(5000);
    });

    it('populates privateMarkets when saved deals exist', async () => {
      mockGetSavedDealIds.mockResolvedValue(['deal-1', 'deal-2']);
      mockGetDeals.mockResolvedValue([
        { id: 'deal-1', name: 'Fund A' },
        { id: 'deal-2', name: 'Fund B' },
        { id: 'deal-3', name: 'Other' },
      ]);

      const ctx = await getCopilotContext();

      expect(ctx.privateMarkets).not.toBeNull();
      expect(ctx.privateMarkets!.savedDealIds).toEqual(['deal-1', 'deal-2']);
      expect(ctx.privateMarkets!.savedDealNames).toEqual(['Fund A', 'Fund B']);
    });

    it('returns privateMarkets with empty arrays when no saved deals', async () => {
      mockGetSavedDealIds.mockResolvedValue([]);
      mockGetDeals.mockResolvedValue([{ id: 'x', name: 'X' }]);

      const ctx = await getCopilotContext();

      expect(ctx.privateMarkets).not.toBeNull();
      expect(ctx.privateMarkets!.savedDealIds).toEqual([]);
      expect(ctx.privateMarkets!.savedDealNames).toEqual([]);
    });
  });

  describe('serializeCopilotContextForPrompt', () => {
    it('returns fallback string when all sections are null', () => {
      const ctx: CopilotContext = {
        portfolio: null,
        credit: null,
        privateMarkets: null,
        builtAt: new Date().toISOString(),
      };
      const out = serializeCopilotContextForPrompt(ctx);
      expect(out).toContain('No portfolio');
      expect(out).toContain('credit');
      expect(out).toContain('private markets');
    });

    it('includes portfolio summary when present', () => {
      const ctx: CopilotContext = {
        portfolio: {
          totalValue: 150000,
          topHoldings: [
            { symbol: 'AAPL', value: 90000, pct: 60 },
            { symbol: 'MSFT', value: 60000, pct: 40 },
          ],
          holdingCount: 2,
        },
        credit: null,
        privateMarkets: null,
        builtAt: new Date().toISOString(),
      };
      const out = serializeCopilotContextForPrompt(ctx);
      expect(out).toContain('150,000');
      expect(out).toContain('2 holdings');
      expect(out).toContain('AAPL');
      expect(out).toContain('60%');
      expect(out).toContain('MSFT');
      expect(out).toContain('40%');
    });

    it('includes credit summary when present', () => {
      const ctx: CopilotContext = {
        portfolio: null,
        credit: {
          score: 720,
          scoreRange: 'Good',
          utilizationPct: 0.2,
          totalLimit: 10000,
          totalBalance: 2000,
        },
        privateMarkets: null,
        builtAt: new Date().toISOString(),
      };
      const out = serializeCopilotContextForPrompt(ctx);
      expect(out).toContain('720');
      expect(out).toContain('Good');
      expect(out).toContain('20%');
      expect(out).toContain('2,000');
      expect(out).toContain('10,000');
    });

    it('includes private markets saved deals when present', () => {
      const ctx: CopilotContext = {
        portfolio: null,
        credit: null,
        privateMarkets: {
          savedDealIds: ['a', 'b'],
          savedDealNames: ['Deal A', 'Deal B'],
        },
        builtAt: new Date().toISOString(),
      };
      const out = serializeCopilotContextForPrompt(ctx);
      expect(out).toContain('2 saved deal');
      expect(out).toContain('Deal A');
      expect(out).toContain('Deal B');
    });

    it('omits private markets when savedDealIds is empty', () => {
      const ctx: CopilotContext = {
        portfolio: null,
        credit: null,
        privateMarkets: { savedDealIds: [], savedDealNames: [] },
        builtAt: new Date().toISOString(),
      };
      const out = serializeCopilotContextForPrompt(ctx);
      expect(out).toContain('No portfolio');
    });

    it('joins all sections when multiple are present', () => {
      const ctx: CopilotContext = {
        portfolio: {
          totalValue: 50000,
          topHoldings: [{ symbol: 'SPY', value: 50000, pct: 100 }],
          holdingCount: 1,
        },
        credit: {
          score: 680,
          scoreRange: 'Fair',
          utilizationPct: 0.35,
          totalLimit: 5000,
          totalBalance: 1750,
        },
        privateMarkets: {
          savedDealIds: ['x'],
          savedDealNames: ['Growth Fund'],
        },
        builtAt: new Date().toISOString(),
      };
      const out = serializeCopilotContextForPrompt(ctx);
      expect(out).toContain('50,000');
      expect(out).toContain('SPY');
      expect(out).toContain('680');
      expect(out).toContain('35%');
      expect(out).toContain('Growth Fund');
    });
  });
});
