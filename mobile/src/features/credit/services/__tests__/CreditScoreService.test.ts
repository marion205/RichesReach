/**
 * Unit Tests for CreditScoreService
 */

import { creditScoreService } from '../CreditScoreService';
import { CreditScore, CreditProjection } from '../../types/CreditTypes';

// Mock fetch
global.fetch = jest.fn();

describe('CreditScoreService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock AsyncStorage
    require('@react-native-async-storage/async-storage').default = {
      getItem: jest.fn().mockResolvedValue('test-token'),
    };
  });

  describe('getScore', () => {
    it('should fetch credit score successfully', async () => {
      const mockScore: CreditScore = {
        score: 580,
        scoreRange: 'Fair',
        lastUpdated: '2024-01-15T00:00:00Z',
        provider: 'self_reported',
        factors: {
          paymentHistory: 35,
          utilization: 30,
          creditAge: 15,
        },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockScore,
      });

      const result = await creditScoreService.getScore();

      expect(result).toEqual(mockScore);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/credit/score'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });

    it('should return fallback score on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await creditScoreService.getScore();

      expect(result.score).toBe(580);
      expect(result.scoreRange).toBe('Fair');
      expect(result.provider).toBe('self_reported');
    });

    it('should handle HTTP errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const result = await creditScoreService.getScore();

      expect(result.score).toBe(580); // Fallback
    });
  });

  describe('refreshScore', () => {
    it('should refresh credit score successfully', async () => {
      const mockScore: CreditScore = {
        score: 600,
        scoreRange: 'Fair',
        lastUpdated: '2024-01-15T00:00:00Z',
        provider: 'self_reported',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockScore,
      });

      const result = await creditScoreService.refreshScore(600, 'self_reported');

      expect(result.score).toBe(600);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/credit/score/refresh'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ score: 600, provider: 'self_reported' }),
        })
      );
    });
  });

  describe('getProjection', () => {
    it('should fetch credit projection successfully', async () => {
      const mockProjection: CreditProjection = {
        scoreGain6m: 42,
        topAction: 'SET_UP_AUTOPAY',
        confidence: 0.71,
        factors: {
          paymentHistory: '+15 points',
          utilization: '+12 points',
        },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjection,
      });

      const result = await creditScoreService.getProjection();

      expect(result).toEqual(mockProjection);
    });

    it('should return fallback projection on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await creditScoreService.getProjection();

      expect(result.scoreGain6m).toBe(42);
      expect(result.topAction).toBe('SET_UP_AUTOPAY');
      expect(result.confidence).toBe(0.71);
    });
  });

  describe('getSnapshot', () => {
    it('should fetch complete credit snapshot', async () => {
      const mockSnapshot = {
        score: {
          score: 580,
          scoreRange: 'Fair',
          lastUpdated: '2024-01-15T00:00:00Z',
          provider: 'self_reported',
        },
        cards: [],
        utilization: {
          totalLimit: 1000,
          totalBalance: 450,
          currentUtilization: 0.45,
          optimalUtilization: 0.3,
          paydownSuggestion: 150,
          projectedScoreGain: 8,
        },
        projection: {
          scoreGain6m: 42,
          topAction: 'SET_UP_AUTOPAY',
          confidence: 0.71,
        },
        actions: [],
        shield: null,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const result = await creditScoreService.getSnapshot();

      expect(result).toEqual(mockSnapshot);
    });
  });
});

