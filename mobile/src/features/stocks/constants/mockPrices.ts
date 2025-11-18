/**
 * Mock stock prices for instant fallback display
 * Used when real-time quotes are unavailable or loading
 */

export const MOCK_PRICES: Record<string, number> = {
  AAPL: 190.12,
  MSFT: 375.00,
  GOOGL: 140.00,
  AMZN: 150.00,
  TSLA: 245.00,
  META: 490.00,
  NVDA: 125.00,
};

/**
 * Get mock price for a symbol, or return default
 */
export const getMockPrice = (symbol: string, defaultPrice: number = 150.00): number => {
  return MOCK_PRICES[symbol.toUpperCase()] || defaultPrice;
};

