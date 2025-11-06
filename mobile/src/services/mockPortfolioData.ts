/**
 * Mock Portfolio Data Service
 * Provides demo portfolio data that matches chart values for demonstrations
 * 
 * Chart values:
 * - Total Value: $14,303.52
 * - Total Return: $2,145.53
 * - Total Return Percent: 17.65%
 */

export interface MockPortfolioHolding {
  symbol: string;
  companyName: string;
  shares: number;
  currentPrice: number;
  totalValue: number;
  costBasis: number;
  returnAmount: number;
  returnPercent: number;
  sector: string;
}

export interface MockPortfolioMetrics {
  totalValue: number;
  totalCost: number;
  totalReturn: number;
  totalReturnPercent: number;
  dayChange?: number;
  dayChangePercent?: number;
  volatility?: number;
  sharpeRatio?: number;
  maxDrawdown?: number;
  beta?: number;
  alpha?: number;
  sectorAllocation?: Record<string, number>;
  holdings: MockPortfolioHolding[];
}

export interface MockPortfolio {
  id: string;
  name: string;
  totalValue: number;
  holdingsCount: number;
  holdings: Array<{
    id: string;
    stock: {
      symbol: string;
      companyName?: string;
      currentPrice?: number;
    };
    shares: number;
    averagePrice: number;
    currentPrice: number;
    totalValue: number;
  }>;
}

export interface MockMyPortfolios {
  totalPortfolios: number;
  totalValue: number;
  portfolios: MockPortfolio[];
}

/**
 * Get mock portfolio metrics that match the chart data
 * Total: $14,303.52, Return: $2,145.53 (17.65%)
 */
export function getMockPortfolioMetrics(): MockPortfolioMetrics {
  const holdings: MockPortfolioHolding[] = [
    {
      symbol: 'AAPL',
      companyName: 'Apple Inc.',
      shares: 10,
      currentPrice: 180.00,
      totalValue: 1800.00,
      costBasis: 1500.00, // $150 per share average
      returnAmount: 300.00,
      returnPercent: 20.00,
      sector: 'Technology',
    },
    {
      symbol: 'MSFT',
      companyName: 'Microsoft Corporation',
      shares: 8,
      currentPrice: 320.00,
      totalValue: 2560.00,
      costBasis: 1840.00, // $230 per share average
      returnAmount: 720.00,
      returnPercent: 39.13,
      sector: 'Technology',
    },
    {
      symbol: 'SPY',
      companyName: 'SPDR S&P 500 ETF Trust',
      shares: 15,
      currentPrice: 420.00,
      totalValue: 6300.00,
      costBasis: 5700.00, // $380 per share average
      returnAmount: 600.00,
      returnPercent: 10.53,
      sector: 'ETF',
    },
    {
      symbol: 'GOOGL',
      companyName: 'Alphabet Inc.',
      shares: 5,
      currentPrice: 128.71,
      totalValue: 643.55,
      costBasis: 550.00, // $110 per share average
      returnAmount: 93.55,
      returnPercent: 17.01,
      sector: 'Technology',
    },
    {
      symbol: 'AMZN',
      companyName: 'Amazon.com Inc.',
      shares: 3,
      currentPrice: 132.00,
      totalValue: 396.00,
      costBasis: 300.00, // $100 per share average
      returnAmount: 96.00,
      returnPercent: 32.00,
      sector: 'Consumer Cyclical',
    },
    {
      symbol: 'NVDA',
      companyName: 'NVIDIA Corporation',
      shares: 2,
      currentPrice: 504.00,
      totalValue: 1008.00,
      costBasis: 800.00, // $400 per share average
      returnAmount: 208.00,
      returnPercent: 26.00,
      sector: 'Technology',
    },
    {
      symbol: 'TSLA',
      companyName: 'Tesla, Inc.',
      shares: 4,
      currentPrice: 196.50,
      totalValue: 786.00,
      costBasis: 700.00, // $175 per share average
      returnAmount: 86.00,
      returnPercent: 12.29,
      sector: 'Automotive',
    },
  ];

  // Calculate totals
  const totalValue = holdings.reduce((sum, h) => sum + h.totalValue, 0);
  const totalCost = holdings.reduce((sum, h) => sum + h.costBasis, 0);
  const totalReturn = totalValue - totalCost;
  const totalReturnPercent = totalCost > 0 ? (totalReturn / totalCost) * 100 : 0;

  // Calculate sector allocation
  const sectorAllocation: Record<string, number> = {};
  holdings.forEach(holding => {
    const sector = holding.sector;
    sectorAllocation[sector] = (sectorAllocation[sector] || 0) + holding.totalValue;
  });
  Object.keys(sectorAllocation).forEach(sector => {
    sectorAllocation[sector] = (sectorAllocation[sector] / totalValue) * 100;
  });

  return {
    totalValue: 14303.52, // Match chart value
    totalCost: 12158.00, // Matches totalValue - totalReturn
    totalReturn: 2145.53, // Match chart value
    totalReturnPercent: 17.65, // Match chart value
    dayChange: 45.23,
    dayChangePercent: 0.32,
    volatility: 18.5,
    sharpeRatio: 1.42,
    maxDrawdown: -8.2,
    beta: 1.15,
    alpha: 2.3,
    sectorAllocation,
    holdings,
  };
}

/**
 * Get mock myPortfolios data that matches chart values
 */
export function getMockMyPortfolios(): MockMyPortfolios {
  const holdings = [
    {
      id: 'h1',
      stock: {
        symbol: 'AAPL',
        companyName: 'Apple Inc.',
        currentPrice: 180.00,
      },
      shares: 10,
      averagePrice: 150.00,
      currentPrice: 180.00,
      totalValue: 1800.00,
    },
    {
      id: 'h2',
      stock: {
        symbol: 'MSFT',
        companyName: 'Microsoft Corporation',
        currentPrice: 320.00,
      },
      shares: 8,
      averagePrice: 230.00,
      currentPrice: 320.00,
      totalValue: 2560.00,
    },
    {
      id: 'h3',
      stock: {
        symbol: 'SPY',
        companyName: 'SPDR S&P 500 ETF Trust',
        currentPrice: 420.00,
      },
      shares: 15,
      averagePrice: 380.00,
      currentPrice: 420.00,
      totalValue: 6300.00,
    },
    {
      id: 'h4',
      stock: {
        symbol: 'GOOGL',
        companyName: 'Alphabet Inc.',
        currentPrice: 128.71,
      },
      shares: 5,
      averagePrice: 110.00,
      currentPrice: 128.71,
      totalValue: 643.55,
    },
    {
      id: 'h5',
      stock: {
        symbol: 'AMZN',
        companyName: 'Amazon.com Inc.',
        currentPrice: 132.00,
      },
      shares: 3,
      averagePrice: 100.00,
      currentPrice: 132.00,
      totalValue: 396.00,
    },
    {
      id: 'h6',
      stock: {
        symbol: 'NVDA',
        companyName: 'NVIDIA Corporation',
        currentPrice: 504.00,
      },
      shares: 2,
      averagePrice: 400.00,
      currentPrice: 504.00,
      totalValue: 1008.00,
    },
    {
      id: 'h7',
      stock: {
        symbol: 'TSLA',
        companyName: 'Tesla, Inc.',
        currentPrice: 196.50,
      },
      shares: 4,
      averagePrice: 175.00,
      currentPrice: 196.50,
      totalValue: 786.00,
    },
  ];

  const totalValue = holdings.reduce((sum, h) => sum + h.totalValue, 0);

  return {
    totalPortfolios: 1,
    totalValue: 14303.52, // Match chart value
    portfolios: [
      {
        id: 'p1',
        name: 'Main Portfolio',
        totalValue: 14303.52,
        holdingsCount: holdings.length,
        holdings,
      },
    ],
  };
}

/**
 * Get mock portfolio data for HomeScreen (matching chart values)
 */
export function getMockHomeScreenPortfolio() {
  const metrics = getMockPortfolioMetrics();
  
  return {
    portfolioMetrics: {
      totalValue: metrics.totalValue,
      totalCost: metrics.totalCost,
      totalReturn: metrics.totalReturn,
      totalReturnPercent: metrics.totalReturnPercent,
      holdings: metrics.holdings.map(h => ({
        symbol: h.symbol,
        companyName: h.companyName,
        shares: h.shares,
        currentPrice: h.currentPrice,
        totalValue: h.totalValue,
        costBasis: h.costBasis,
        returnAmount: h.returnAmount,
        returnPercent: h.returnPercent,
        sector: h.sector,
      })),
    },
  };
}

