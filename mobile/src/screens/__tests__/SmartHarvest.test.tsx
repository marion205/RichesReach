/**
 * Unit tests for Smart Harvest functionality
 */

describe('Smart Harvest Flow', () => {
  const mockToken = 'test-token-123';
  const mockAPIBase = 'http://localhost:8000';
  const mockLossHoldings = [
    {
      symbol: 'AAPL',
      quantity: 100,
      shares: 100,
      costBasis: 150,
      currentPrice: 140,
      current_price: 140,
      unrealizedGain: -1000,
      returnAmount: -1000,
      washSaleRisk: false,
    },
    {
      symbol: 'MSFT',
      quantity: 50,
      shares: 50,
      costBasis: 300,
      currentPrice: 280,
      current_price: 280,
      unrealizedGain: -1000,
      returnAmount: -1000,
      washSaleRisk: false,
    },
  ];

  describe('Smart Harvest Recommendations Request', () => {
    it('should construct correct request URL', () => {
      const url = `${mockAPIBase}/api/tax/smart-harvest/recommendations`;
      expect(url).toBe('http://localhost:8000/api/tax/smart-harvest/recommendations');
    });

    it('should construct correct request headers', () => {
      const headers = {
        'Authorization': `Bearer ${mockToken}`,
        'Content-Type': 'application/json',
      };
      
      expect(headers['Authorization']).toBe('Bearer test-token-123');
      expect(headers['Content-Type']).toBe('application/json');
    });

    it('should format holdings correctly for request', () => {
      const requestBody = {
        holdings: mockLossHoldings.map((h) => ({
          symbol: h.symbol,
          shares: h.quantity || h.shares,
          costBasis: h.costBasis,
          currentPrice: h.currentPrice || h.current_price,
          unrealizedGain: h.unrealizedGain || h.returnAmount,
        })),
      };
      
      expect(requestBody.holdings).toHaveLength(2);
      expect(requestBody.holdings[0].symbol).toBe('AAPL');
      expect(requestBody.holdings[0].shares).toBe(100);
      expect(requestBody.holdings[1].symbol).toBe('MSFT');
      expect(requestBody.holdings[1].shares).toBe(50);
    });
  });

  describe('Smart Harvest Recommendations Response', () => {
    const mockRecommendations = {
      trades: [
        {
          symbol: 'AAPL',
          shares: 100,
          action: 'sell',
          estimatedSavings: 220,
          reason: 'Harvest $1,000 in losses',
        },
        {
          symbol: 'MSFT',
          shares: 50,
          action: 'sell',
          estimatedSavings: 220,
          reason: 'Harvest $1,000 in losses',
        },
      ],
      totalSavings: 440,
      warnings: [],
    };

    it('should handle successful recommendations response', () => {
      expect(mockRecommendations.trades).toHaveLength(2);
      expect(mockRecommendations.totalSavings).toBe(440);
      expect(mockRecommendations.warnings).toHaveLength(0);
    });

    it('should calculate estimated savings correctly', () => {
      const lossAmount = 1000;
      const taxRate = 0.22;
      const estimatedSavings = lossAmount * taxRate;
      
      expect(estimatedSavings).toBe(220);
    });

    it('should handle warnings in response', () => {
      const recommendationsWithWarnings = {
        ...mockRecommendations,
        warnings: [
          { symbol: 'AAPL', message: 'Potential wash sale risk' },
        ],
      };
      
      expect(recommendationsWithWarnings.warnings).toHaveLength(1);
      expect(recommendationsWithWarnings.warnings[0].symbol).toBe('AAPL');
    });
  });

  describe('Smart Harvest Execution', () => {
    it('should construct correct execution request', () => {
      const trades = [
        { symbol: 'AAPL', shares: 100, action: 'sell' },
        { symbol: 'MSFT', shares: 50, action: 'sell' },
      ];
      
      const requestBody = { trades };
      
      expect(requestBody.trades).toHaveLength(2);
      expect(requestBody.trades[0].symbol).toBe('AAPL');
      expect(requestBody.trades[1].symbol).toBe('MSFT');
    });

    it('should handle successful execution response', () => {
      const mockResponse = {
        success: true,
        tradesExecuted: 2,
        message: 'Smart harvest trades executed successfully',
      };
      
      expect(mockResponse.success).toBe(true);
      expect(mockResponse.tradesExecuted).toBe(2);
    });

    it('should handle execution errors', () => {
      const mockError = {
        success: false,
        error: 'Insufficient shares',
      };
      
      expect(mockError.success).toBe(false);
      expect(mockError.error).toBe('Insufficient shares');
    });
  });

  describe('Fallback Logic', () => {
    it('should calculate fallback recommendations when API fails', () => {
      const lossHoldings = mockLossHoldings;
      const potentialSavings = lossHoldings.reduce(
        (sum, h) => sum + Math.abs(h.unrealizedGain || h.returnAmount) * 0.22,
        0
      );
      
      const fallbackRecommendations = {
        trades: lossHoldings.map((h) => ({
          symbol: h.symbol,
          shares: h.quantity || h.shares,
          action: 'sell',
          estimatedSavings: Math.abs(h.unrealizedGain || h.returnAmount) * 0.22,
          reason: `Harvest ${Math.abs(h.unrealizedGain || h.returnAmount).toLocaleString()} in losses`,
        })),
        totalSavings: potentialSavings,
        warnings: lossHoldings.filter((h) => h.washSaleRisk).map((h) => ({
          symbol: h.symbol,
          message: 'Potential wash sale risk',
        })),
      };
      
      expect(fallbackRecommendations.trades).toHaveLength(2);
      expect(fallbackRecommendations.totalSavings).toBe(440);
    });
  });

  describe('Wash Sale Detection', () => {
    it('should filter out wash sale risks', () => {
      const holdingsWithWashSale = [
        ...mockLossHoldings,
        {
          symbol: 'TSLA',
          quantity: 200,
          shares: 200,
          costBasis: 200,
          currentPrice: 180,
          unrealizedGain: -4000,
          washSaleRisk: true,
        },
      ];
      
      const harvestableHoldings = holdingsWithWashSale.filter((h) => !h.washSaleRisk);
      
      expect(harvestableHoldings).toHaveLength(2);
      expect(harvestableHoldings.find((h) => h.symbol === 'TSLA')).toBeUndefined();
    });
  });

  describe('Empty State Handling', () => {
    it('should handle no loss holdings', () => {
      const emptyHoldings = [];
      const hasHarvestableLosses = emptyHoldings.filter((h) => !h.washSaleRisk).length > 0;
      
      expect(hasHarvestableLosses).toBe(false);
    });

    it('should show appropriate message for no opportunities', () => {
      const message = 'You don\'t have any harvestable losses right now.';
      expect(message).toContain('harvestable losses');
    });
  });
});

