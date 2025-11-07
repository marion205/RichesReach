/**
 * Unit Tests for CreditUtilizationService
 */

import { creditUtilizationService } from '../CreditUtilizationService';
import { CreditUtilization } from '../../types/CreditTypes';

// Mock fetch
global.fetch = jest.fn();

describe('CreditUtilizationService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock AsyncStorage
    require('@react-native-async-storage/async-storage').default = {
      getItem: jest.fn().mockResolvedValue('test-token'),
    };
  });

  describe('getUtilization', () => {
    it('should fetch utilization data successfully', async () => {
      const mockUtilization = {
        totalLimit: 1000,
        totalBalance: 450,
        currentUtilization: 0.45,
        optimalUtilization: 0.3,
        paydownSuggestion: 150,
        projectedScoreGain: 8,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUtilization,
      });

      const result = await creditUtilizationService.getUtilization();

      expect(result).toEqual(mockUtilization);
      expect(result.currentUtilization).toBe(0.45);
      expect(result.paydownSuggestion).toBe(150);
    });

    it('should return fallback utilization on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await creditUtilizationService.getUtilization();

      expect(result.totalLimit).toBe(1000);
      expect(result.currentUtilization).toBe(0.45);
      expect(result.optimalUtilization).toBe(0.3);
    });

    it('should handle missing data gracefully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      const result = await creditUtilizationService.getUtilization();

      expect(result.totalLimit).toBe(0);
      expect(result.currentUtilization).toBe(0);
    });
  });

  describe('getOptimalPaydown', () => {
    it('should return optimal paydown suggestion', async () => {
      const mockUtilization = {
        totalLimit: 1000,
        totalBalance: 450,
        currentUtilization: 0.45,
        optimalUtilization: 0.3,
        paydownSuggestion: 150,
        projectedScoreGain: 8,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUtilization,
      });

      const result = await creditUtilizationService.getOptimalPaydown();

      expect(result.amount).toBe(150);
      expect(result.projectedGain).toBe(8);
    });
  });
});

