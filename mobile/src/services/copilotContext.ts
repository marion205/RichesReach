/**
 * Copilot context: summary of user's portfolio, credit, and private markets for the Ask/Copilot.
 * Sent with each assistant query so answers are grounded in real data.
 */

import RealTimePortfolioService from '../features/portfolio/services/RealTimePortfolioService';
import { creditScoreService } from '../features/credit/services/CreditScoreService';
import { creditUtilizationService } from '../features/credit/services/CreditUtilizationService';
import { getPrivateMarketsService } from '../features/invest/services/privateMarketsService';

export interface CopilotPortfolioContext {
  totalValue: number;
  topHoldings: { symbol: string; value: number; pct: number }[];
  holdingCount: number;
}

export interface CopilotCreditContext {
  score: number;
  scoreRange: string;
  utilizationPct: number;
  totalLimit: number;
  totalBalance: number;
}

export interface CopilotPrivateMarketsContext {
  savedDealIds: string[];
  savedDealNames: string[];
}

export interface CopilotContext {
  portfolio: CopilotPortfolioContext | null;
  credit: CopilotCreditContext | null;
  privateMarkets: CopilotPrivateMarketsContext | null;
  /** ISO timestamp when context was built */
  builtAt: string;
}

/**
 * Build a compact context object for the Copilot from live services.
 * Each section is best-effort; missing data is omitted.
 */
export async function getCopilotContext(): Promise<CopilotContext> {
  const builtAt = new Date().toISOString();
  let portfolio: CopilotPortfolioContext | null = null;
  let credit: CopilotCreditContext | null = null;
  let privateMarkets: CopilotPrivateMarketsContext | null = null;

  try {
    const portfolioData = await RealTimePortfolioService.getPortfolioData();
    if (portfolioData && portfolioData.holdings?.length) {
      const total = portfolioData.totalValue || portfolioData.holdings.reduce((s, h) => s + (h.totalValue || 0), 0);
      const top = portfolioData.holdings
        .slice()
        .sort((a, b) => (b.totalValue || 0) - (a.totalValue || 0))
        .slice(0, 10)
        .map((h) => ({
          symbol: h.symbol,
          value: h.totalValue || 0,
          pct: total ? Math.round((100 * (h.totalValue || 0)) / total) : 0,
        }));
      portfolio = {
        totalValue: total,
        topHoldings: top,
        holdingCount: portfolioData.holdings.length,
      };
    }
  } catch (_) {
    // ignore
  }

  try {
    const [scoreData, utilData] = await Promise.all([
      creditScoreService.getScore(),
      creditUtilizationService.getUtilization(),
    ]);
    credit = {
      score: scoreData?.score ?? 0,
      scoreRange: scoreData?.scoreRange ?? 'Unknown',
      utilizationPct: utilData?.currentUtilization ?? 0,
      totalLimit: utilData?.totalLimit ?? 0,
      totalBalance: utilData?.totalBalance ?? 0,
    };
  } catch (_) {
    // ignore
  }

  try {
    const svc = getPrivateMarketsService();
    const savedIds = await svc.getSavedDealIds();
    const allDeals = await svc.getDeals();
    const savedDealNames = savedIds
      .map((id) => allDeals.find((d) => d.id === id)?.name)
      .filter(Boolean) as string[];
    privateMarkets = {
      savedDealIds: savedIds,
      savedDealNames,
    };
  } catch (_) {
    // ignore
  }

  return {
    portfolio,
    credit,
    privateMarkets,
    builtAt,
  };
}

/**
 * Serialize context for the assistant API (compact string for prompt).
 */
export function serializeCopilotContextForPrompt(ctx: CopilotContext): string {
  const parts: string[] = [];
  if (ctx.portfolio) {
    parts.push(
      `Portfolio: total value $${ctx.portfolio.totalValue.toLocaleString('en-US', { maximumFractionDigits: 0 })}; ${ctx.portfolio.holdingCount} holdings. Top: ${ctx.portfolio.topHoldings.map((h) => `${h.symbol} ${h.pct}%`).join(', ')}.`
    );
  }
  if (ctx.credit) {
    parts.push(
      `Credit: score ${ctx.credit.score} (${ctx.credit.scoreRange}); utilization ${Math.round(ctx.credit.utilizationPct * 100)}%; balance $${ctx.credit.totalBalance.toLocaleString()} of $${ctx.credit.totalLimit.toLocaleString()} limit.`
    );
  }
  if (ctx.privateMarkets && ctx.privateMarkets.savedDealIds.length) {
    parts.push(
      `Private markets: ${ctx.privateMarkets.savedDealIds.length} saved deal(s): ${ctx.privateMarkets.savedDealNames.join(', ') || 'unnamed'}.`
    );
  }
  if (parts.length === 0) return 'No portfolio, credit, or private markets data available.';
  return parts.join(' ');
}
