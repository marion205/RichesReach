/**
 * BiasDetectionService
 * ====================
 * Analyzes real portfolio data to detect behavioral biases.
 * This is the "Pompian Layer" that connects quiz-based profiles
 * to actual investment behavior.
 */

import realTimePortfolioService, {
  PortfolioMetrics,
  PortfolioHolding,
} from '../../portfolio/services/RealTimePortfolioService';

export interface BiasAnalysis {
  concentrationBias: {
    score: number; // 0-100
    isActive: boolean;
    topHoldingsPercent: number;
    topSectorPercent: number;
    largestHolding: { symbol: string; percent: number } | null;
    description: string;
    coaching: string;
  };
  familiarityBias: {
    score: number;
    isActive: boolean;
    knownBrandsPercent: number;
    description: string;
    coaching: string;
  };
  recencyBias: {
    score: number;
    isActive: boolean;
    recentWinnersPercent: number;
    description: string;
    coaching: string;
  };
  lossAversion: {
    score: number;
    isActive: boolean;
    holdingLosersCount: number;
    totalLosersPercent: number;
    description: string;
    coaching: string;
  };
  overallBiasScore: number;
  activeBiasCount: number;
}

const WELL_KNOWN_BRANDS = [
  'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA',
  'NFLX', 'DIS', 'NKE', 'SBUX', 'MCD', 'KO', 'PEP', 'WMT', 'COST',
  'HD', 'TGT', 'PYPL', 'SQ', 'V', 'MA', 'JPM', 'BAC', 'GS',
  'UBER', 'LYFT', 'ABNB', 'SNAP', 'PINS', 'SPOT', 'ROKU', 'ZOOM',
];

class BiasDetectionService {
  private biasThreshold = 40; // Score above this = active bias

  /**
   * Analyze portfolio for behavioral biases.
   */
  async analyzePortfolio(): Promise<BiasAnalysis> {
    const portfolio = await realTimePortfolioService.getPortfolioData();
    
    if (!portfolio || !portfolio.holdings || portfolio.holdings.length === 0) {
      return this.getEmptyAnalysis();
    }

    const concentrationBias = this.analyzeConcentration(portfolio);
    const familiarityBias = this.analyzeFamiliarity(portfolio);
    const recencyBias = this.analyzeRecency(portfolio);
    const lossAversion = this.analyzeLossAversion(portfolio);

    const scores = [
      concentrationBias.score,
      familiarityBias.score,
      recencyBias.score,
      lossAversion.score,
    ];
    
    const overallBiasScore = Math.round(
      scores.reduce((a, b) => a + b, 0) / scores.length
    );

    const activeBiasCount = [
      concentrationBias.isActive,
      familiarityBias.isActive,
      recencyBias.isActive,
      lossAversion.isActive,
    ].filter(Boolean).length;

    return {
      concentrationBias,
      familiarityBias,
      recencyBias,
      lossAversion,
      overallBiasScore,
      activeBiasCount,
    };
  }

  private analyzeConcentration(portfolio: PortfolioMetrics): BiasAnalysis['concentrationBias'] {
    const holdings = portfolio.holdings;
    const totalValue = portfolio.totalValue;

    if (totalValue === 0) {
      return {
        score: 0,
        isActive: false,
        topHoldingsPercent: 0,
        topSectorPercent: 0,
        largestHolding: null,
        description: 'No holdings to analyze',
        coaching: '',
      };
    }

    // Sort by value and get top 3
    const sorted = [...holdings].sort((a, b) => b.totalValue - a.totalValue);
    const top3 = sorted.slice(0, 3);
    const top3Value = top3.reduce((sum, h) => sum + h.totalValue, 0);
    const topHoldingsPercent = (top3Value / totalValue) * 100;

    // Calculate sector concentration
    const sectorValues: Record<string, number> = {};
    holdings.forEach(h => {
      const sector = h.sector || 'Unknown';
      sectorValues[sector] = (sectorValues[sector] || 0) + h.totalValue;
    });
    const topSectorValue = Math.max(...Object.values(sectorValues));
    const topSectorPercent = (topSectorValue / totalValue) * 100;

    // Largest holding
    const largest = sorted[0];
    const largestPercent = largest ? (largest.totalValue / totalValue) * 100 : 0;

    // Score: higher concentration = higher score
    // Ideal: top 3 < 30%, any single < 10%
    const score = Math.min(100, Math.round(
      (topHoldingsPercent / 30 * 50) + // top 3 contribution
      (largestPercent / 10 * 30) +      // single stock contribution  
      (topSectorPercent / 35 * 20)      // sector contribution
    ));

    const isActive = score >= this.biasThreshold;

    return {
      score,
      isActive,
      topHoldingsPercent: Math.round(topHoldingsPercent),
      topSectorPercent: Math.round(topSectorPercent),
      largestHolding: largest ? {
        symbol: largest.symbol,
        percent: Math.round(largestPercent),
      } : null,
      description: isActive
        ? `Top 3 holdings = ${Math.round(topHoldingsPercent)}% of portfolio`
        : 'Portfolio concentration is healthy',
      coaching: isActive
        ? `Your portfolio is showing concentration in a few names. Consider directing future contributions to a broad ETF like VTI to reduce single-stock risk.`
        : `Good diversification! Your holdings are well-distributed.`,
    };
  }

  private analyzeFamiliarity(portfolio: PortfolioMetrics): BiasAnalysis['familiarityBias'] {
    const holdings = portfolio.holdings;
    const totalValue = portfolio.totalValue;

    if (totalValue === 0) {
      return {
        score: 0,
        isActive: false,
        knownBrandsPercent: 0,
        description: 'No holdings to analyze',
        coaching: '',
      };
    }

    // Calculate value in well-known brands
    const knownBrandsValue = holdings
      .filter(h => WELL_KNOWN_BRANDS.includes(h.symbol.toUpperCase()))
      .reduce((sum, h) => sum + h.totalValue, 0);
    
    const knownBrandsPercent = (knownBrandsValue / totalValue) * 100;

    // Score: higher familiarity = higher score
    // Having some known brands is fine, but > 60% is a bias signal
    const score = Math.min(100, Math.round(
      knownBrandsPercent > 60
        ? 50 + ((knownBrandsPercent - 60) / 40 * 50)
        : knownBrandsPercent * 0.5
    ));

    const isActive = score >= this.biasThreshold;

    return {
      score,
      isActive,
      knownBrandsPercent: Math.round(knownBrandsPercent),
      description: isActive
        ? `${Math.round(knownBrandsPercent)}% invested in familiar consumer brands`
        : 'Good mix of familiar and unfamiliar names',
      coaching: isActive
        ? `You're invested in companies you know well — that's natural. Consider adding VTI to capture growth from companies you haven't discovered yet.`
        : `Nice balance! You're not over-weighting familiar names.`,
    };
  }

  private analyzeRecency(portfolio: PortfolioMetrics): BiasAnalysis['recencyBias'] {
    const holdings = portfolio.holdings;
    const totalValue = portfolio.totalValue;

    if (totalValue === 0) {
      return {
        score: 0,
        isActive: false,
        recentWinnersPercent: 0,
        description: 'No holdings to analyze',
        coaching: '',
      };
    }

    // Holdings with >20% gain (recent winners)
    const recentWinnersValue = holdings
      .filter(h => h.returnPercent > 20)
      .reduce((sum, h) => sum + h.totalValue, 0);
    
    const recentWinnersPercent = (recentWinnersValue / totalValue) * 100;

    // Score based on recent winner concentration
    // Some winners is good, but > 50% suggests chasing performance
    const score = Math.min(100, Math.round(
      recentWinnersPercent > 50
        ? 50 + ((recentWinnersPercent - 50) / 50 * 50)
        : recentWinnersPercent * 0.6
    ));

    const isActive = score >= this.biasThreshold;

    return {
      score,
      isActive,
      recentWinnersPercent: Math.round(recentWinnersPercent),
      description: isActive
        ? `${Math.round(recentWinnersPercent)}% in recent high-performers`
        : 'Not chasing recent winners',
      coaching: isActive
        ? `You're heavily weighted toward recent winners. Past performance doesn't guarantee future results. Consider rebalancing to lock in gains.`
        : `Balanced approach to performance — not chasing hot stocks.`,
    };
  }

  private analyzeLossAversion(portfolio: PortfolioMetrics): BiasAnalysis['lossAversion'] {
    const holdings = portfolio.holdings;
    const totalValue = portfolio.totalValue;

    if (totalValue === 0) {
      return {
        score: 0,
        isActive: false,
        holdingLosersCount: 0,
        totalLosersPercent: 0,
        description: 'No holdings to analyze',
        coaching: '',
      };
    }

    // Holdings with >20% loss that are still being held
    const losers = holdings.filter(h => h.returnPercent < -20);
    const holdingLosersCount = losers.length;
    const losersValue = losers.reduce((sum, h) => sum + h.totalValue, 0);
    const totalLosersPercent = (losersValue / totalValue) * 100;

    // Score based on holding losers
    // Having some losers is normal, but many large losers = loss aversion
    const score = Math.min(100, Math.round(
      holdingLosersCount * 15 + totalLosersPercent * 1.5
    ));

    const isActive = score >= this.biasThreshold;

    return {
      score,
      isActive,
      holdingLosersCount,
      totalLosersPercent: Math.round(totalLosersPercent),
      description: isActive
        ? `Holding ${holdingLosersCount} positions down >20%`
        : 'Not holding excessive losers',
      coaching: isActive
        ? `You may be holding onto losers hoping they'll recover. Consider whether the thesis for these investments still holds, or if the capital could work harder elsewhere.`
        : `Healthy relationship with losses — not holding dead weight.`,
    };
  }

  private getEmptyAnalysis(): BiasAnalysis {
    return {
      concentrationBias: {
        score: 0,
        isActive: false,
        topHoldingsPercent: 0,
        topSectorPercent: 0,
        largestHolding: null,
        description: 'Add holdings to analyze',
        coaching: '',
      },
      familiarityBias: {
        score: 0,
        isActive: false,
        knownBrandsPercent: 0,
        description: 'Add holdings to analyze',
        coaching: '',
      },
      recencyBias: {
        score: 0,
        isActive: false,
        recentWinnersPercent: 0,
        description: 'Add holdings to analyze',
        coaching: '',
      },
      lossAversion: {
        score: 0,
        isActive: false,
        holdingLosersCount: 0,
        totalLosersPercent: 0,
        description: 'Add holdings to analyze',
        coaching: '',
      },
      overallBiasScore: 0,
      activeBiasCount: 0,
    };
  }
}

export default new BiasDetectionService();
