/**
 * Tests for SecureMarketDataService
 */

// Mock expo-constants and react-native before importing config
jest.mock('expo-constants', () => ({
  default: {
    expoConfig: {
      extra: {},
    },
  },
}));

jest.mock('react-native', () => ({
  Platform: {
    OS: 'ios',
  },
}));

// Mock API_BASE before importing the service
jest.mock('../../../../config/api', () => ({
  API_BASE: 'http://localhost:8000',
}));

import { SecureMarketDataService, Quote, Option } from '../SecureMarketDataService';

// Mock fetch globally
global.fetch = jest.fn();

// Mock console methods
const consoleLog = jest.spyOn(console, 'log').mockImplementation();
const consoleWarn = jest.spyOn(console, 'warn').mockImplementation();
const consoleError = jest.spyOn(console, 'error').mockImplementation();

describe('SecureMarketDataService', () => {
  let service: SecureMarketDataService;

  beforeEach(() => {
    jest.clearAllMocks();
    service = SecureMarketDataService.getInstance();
    service.clearCache();
  });

  afterEach(() => {
    service.clearCache();
  });

  describe('getInstance', () => {
    it('should return singleton instance', () => {
      const instance1 = SecureMarketDataService.getInstance();
      const instance2 = SecureMarketDataService.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('fetchQuotes', () => {
    const mockQuotes: Quote[] = [
      {
        symbol: 'AAPL',
        price: 180.00,
        change: 30.00,
        change_percent: 20.00,
        volume: 45000000,
        high: 182.50,
        low: 178.20,
        open: 179.00,
        previous_close: 150.00,
        updated: Date.now(),
        provider: 'test',
      },
      {
        symbol: 'MSFT',
        price: 320.00,
        change: 90.00,
        change_percent: 39.13,
        volume: 28000000,
        high: 322.50,
        low: 318.00,
        open: 319.00,
        previous_close: 230.00,
        updated: Date.now(),
        provider: 'test',
      },
    ];

    it('should fetch quotes from backend successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockQuotes),
      });

      const quotes = await service.fetchQuotes(['AAPL', 'MSFT']);
      
      expect(quotes).toHaveLength(2);
      expect(quotes[0].symbol).toBe('AAPL');
      expect(quotes[1].symbol).toBe('MSFT');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/market/quotes'),
        expect.objectContaining({
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });

    it('should return cached quotes if available', async () => {
      // First call - fetch from backend
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockQuotes.slice(0, 1)), // Only AAPL
      });

      await service.fetchQuotes(['AAPL']);
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Second call - should use cache
      const cachedQuotes = await service.fetchQuotes(['AAPL']);
      expect(global.fetch).toHaveBeenCalledTimes(1); // Still 1, not 2
      expect(cachedQuotes).toHaveLength(1);
      expect(cachedQuotes[0].symbol).toBe('AAPL');
    });

    it('should deduplicate in-flight requests', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          text: async () => JSON.stringify(mockQuotes.slice(0, 1)),
        }), 100))
      );

      const promise1 = service.fetchQuotes(['AAPL']);
      const promise2 = service.fetchQuotes(['AAPL']);

      const [result1, result2] = await Promise.all([promise1, promise2]);

      expect(result1).toBe(result2); // Same promise reference
      expect(global.fetch).toHaveBeenCalledTimes(1); // Only one network call
    });

    it('should handle array response format', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockQuotes),
      });

      const quotes = await service.fetchQuotes(['AAPL', 'MSFT']);
      expect(quotes).toHaveLength(2);
    });

    it('should handle object with quotes property', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify({ quotes: mockQuotes }),
      });

      const quotes = await service.fetchQuotes(['AAPL', 'MSFT']);
      expect(quotes).toHaveLength(2);
    });

    it('should return mock data on network error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network request failed')
      );

      const quotes = await service.fetchQuotes(['AAPL']);
      
      expect(quotes).toHaveLength(1);
      expect(quotes[0].symbol).toBe('AAPL');
      expect(quotes[0].provider).toBe('mock');
    });

    it('should return mock data on timeout', async () => {
      const abortController = new AbortController();
      (global.fetch as jest.Mock).mockImplementationOnce(() => {
        abortController.abort();
        return Promise.reject({ name: 'AbortError' });
      });

      const quotes = await service.fetchQuotes(['AAPL']);
      
      expect(quotes).toHaveLength(1);
      expect(quotes[0].symbol).toBe('AAPL');
      expect(quotes[0].provider).toBe('mock');
    });

    it('should use stale cache on network error if available', async () => {
      // First call - cache the data
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockQuotes.slice(0, 1)),
      });

      await service.fetchQuotes(['AAPL']);

      // Wait for cache to expire (simulate by manipulating time)
      jest.spyOn(Date, 'now').mockReturnValueOnce(Date.now() + 70000); // 70 seconds later

      // Second call - network fails, should use stale cache
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network request failed')
      );

      const quotes = await service.fetchQuotes(['AAPL']);
      expect(quotes).toHaveLength(1);
      expect(quotes[0].symbol).toBe('AAPL');
    });

    it('should handle rate limit errors gracefully with mock fallback', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests',
        json: async () => ({ message: 'Rate limit exceeded' }),
      });

      // Service should fall back to mock data instead of throwing
      const quotes = await service.fetchQuotes(['AAPL']);
      expect(quotes).toHaveLength(1);
      expect(quotes[0].symbol).toBe('AAPL');
      expect(quotes[0].provider).toBe('mock');
    });

    it('should handle invalid JSON response gracefully with mock fallback', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => 'invalid json',
      });

      // Service should fall back to mock data instead of throwing
      const quotes = await service.fetchQuotes(['AAPL']);
      expect(quotes).toHaveLength(1);
      expect(quotes[0].symbol).toBe('AAPL');
      expect(quotes[0].provider).toBe('mock');
    });

    it('should sort symbols in cache key', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockQuotes),
      });

      await service.fetchQuotes(['MSFT', 'AAPL']);

      // Should use same cache for different order
      const cached = await service.fetchQuotes(['AAPL', 'MSFT']);
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(cached).toHaveLength(2);
    });
  });

  describe('fetchOptions', () => {
    const mockOptions: Option[] = [
      {
        contract_type: 'call',
        strike_price: 180,
        expiration_date: '2024-12-20',
        ticker: 'AAPL241220C00180000',
        underlying_ticker: 'AAPL',
        provider: 'test',
      },
    ];

    it('should fetch options from backend successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockOptions),
      });

      const options = await service.fetchOptions('AAPL');
      
      expect(options).toHaveLength(1);
      expect(options[0].underlying_ticker).toBe('AAPL');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/market/options'),
        expect.any(Object)
      );
    });

    it('should include expiration in request if provided', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockOptions),
      });

      await service.fetchOptions('AAPL', '2024-12-20');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('expiration=2024-12-20'),
        expect.any(Object)
      );
    });

    it('should return cached options if available', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockOptions),
      });

      await service.fetchOptions('AAPL');
      expect(global.fetch).toHaveBeenCalledTimes(1);

      const cached = await service.fetchOptions('AAPL');
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(cached).toHaveLength(1);
    });

    it('should use stale cache on error if available', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify(mockOptions),
      });

      await service.fetchOptions('AAPL');

      // Simulate cache expiration
      jest.spyOn(Date, 'now').mockReturnValueOnce(Date.now() + 400000);

      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      const options = await service.fetchOptions('AAPL');
      expect(options).toHaveLength(1);
    });
  });

  describe('getServiceStatus', () => {
    it('should return service status successfully', async () => {
      const mockStatus = { service: 'market_data', status: 'online' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus,
      });

      const status = await service.getServiceStatus();
      expect(status).toEqual(mockStatus);
    });

    it('should return unavailable status on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      const status = await service.getServiceStatus();
      expect(status.status).toBe('unavailable');
      expect(status.error).toBeDefined();
    });
  });

  describe('clearCache', () => {
    it('should clear all caches', async () => {
      // Populate cache
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        text: async () => JSON.stringify([{
          symbol: 'AAPL',
          price: 180,
          change: 0,
          change_percent: 0,
          volume: 0,
          high: 0,
          low: 0,
          open: 0,
          previous_close: 0,
          updated: Date.now(),
        }]),
      });

      await service.fetchQuotes(['AAPL']);
      await service.fetchOptions('AAPL');

      const statsBefore = service.getCacheStats();
      expect(statsBefore.quotes.size).toBeGreaterThan(0);

      service.clearCache();

      const statsAfter = service.getCacheStats();
      expect(statsAfter.quotes.size).toBe(0);
      expect(statsAfter.options.size).toBe(0);
    });
  });

  describe('getCacheStats', () => {
    it('should return cache statistics', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        text: async () => JSON.stringify([{
          symbol: 'AAPL',
          price: 180,
          change: 0,
          change_percent: 0,
          volume: 0,
          high: 0,
          low: 0,
          open: 0,
          previous_close: 0,
          updated: Date.now(),
        }]),
      });

      await service.fetchQuotes(['AAPL']);

      const stats = service.getCacheStats();
      expect(stats).toHaveProperty('quotes');
      expect(stats).toHaveProperty('options');
      expect(stats.quotes.size).toBeGreaterThan(0);
    });
  });

  describe('mock data fallback', () => {
    it('should return mock quotes for known symbols', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      const quotes = await service.fetchQuotes(['AAPL', 'MSFT']);
      
      expect(quotes).toHaveLength(2);
      expect(quotes[0].symbol).toBe('AAPL');
      expect(quotes[0].provider).toBe('mock');
      expect(quotes[1].symbol).toBe('MSFT');
      expect(quotes[1].provider).toBe('mock');
    });

    it('should return default mock quote for unknown symbols', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      const quotes = await service.fetchQuotes(['UNKNOWN']);
      
      expect(quotes).toHaveLength(1);
      expect(quotes[0].symbol).toBe('UNKNOWN');
      expect(quotes[0].price).toBe(100.00);
      expect(quotes[0].provider).toBe('mock');
    });
  });
});

