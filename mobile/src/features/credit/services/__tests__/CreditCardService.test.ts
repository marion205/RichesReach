/**
 * Unit Tests for CreditCardService
 */

import { creditCardService } from '../CreditCardService';
import { CreditCard, CreditCardRecommendation } from '../../types/CreditTypes';

// Mock fetch
global.fetch = jest.fn();

describe('CreditCardService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock AsyncStorage
    require('@react-native-async-storage/async-storage').default = {
      getItem: jest.fn().mockResolvedValue('test-token'),
    };
  });

  describe('getCards', () => {
    it('should fetch credit cards successfully', async () => {
      const mockCards: CreditCard[] = [
        {
          id: '1',
          name: 'Capital One Secured',
          limit: 200,
          balance: 50,
          utilization: 0.25,
          paymentDueDate: '2024-02-01',
          minimumPayment: 25,
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCards,
      });

      const result = await creditCardService.getCards();

      expect(result).toEqual(mockCards);
      expect(result.length).toBe(1);
    });

    it('should return empty array on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await creditCardService.getCards();

      expect(result).toEqual([]);
    });
  });

  describe('getRecommendations', () => {
    it('should fetch card recommendations successfully', async () => {
      const mockRecommendations: CreditCardRecommendation[] = [
        {
          id: 'capital_one_secured',
          name: 'Capital One Platinum Secured',
          type: 'secured',
          deposit: 49,
          annualFee: 0,
          apr: 26.99,
          description: 'Test description',
          benefits: ['No annual fee'],
          preQualified: true,
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecommendations,
      });

      const result = await creditCardService.getRecommendations();

      expect(result).toEqual(mockRecommendations);
      expect(result.length).toBeGreaterThan(0);
    });

    it('should return fallback recommendations on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await creditCardService.getRecommendations();

      expect(result.length).toBeGreaterThan(0);
      expect(result[0].type).toBe('secured');
    });
  });
});

