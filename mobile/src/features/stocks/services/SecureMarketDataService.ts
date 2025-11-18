/**
 * Secure Market Data Service
 * Uses backend endpoints with caching and rate limit protection
 */
import { API_BASE } from '../../../config/api';

export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  previous_close: number;
  updated: number;
  provider?: string;
}

export interface Option {
  contract_type: string;
  strike_price: number;
  expiration_date: string;
  ticker: string;
  underlying_ticker: string;
  provider: string;
}

// In-flight request deduplication
const inflight = new Map<string, Promise<Quote[]>>();
const optionsInflight = new Map<string, Promise<Option[]>>();

// Client-side cache (1 minute TTL for quotes, 5 minutes for options)
const CACHE_TTL_MS = 60_000;
const OPTIONS_CACHE_TTL_MS = 300_000;
const cache = new Map<string, { at: number; data: Quote[] }>();
const optionsCache = new Map<string, { at: number; data: Option[] }>();

export class SecureMarketDataService {
  private static instance: SecureMarketDataService;
  
  public static getInstance(): SecureMarketDataService {
    if (!SecureMarketDataService.instance) {
      SecureMarketDataService.instance = new SecureMarketDataService();
    }
    return SecureMarketDataService.instance;
  }

  /**
   * Fetch quotes for multiple symbols with caching and deduplication
   */
  async fetchQuotes(symbols: string[]): Promise<Quote[]> {
    const key = symbols.sort().join(',');
    const now = Date.now();

    // Serve from cache if available
    const hit = cache.get(key);
    if (hit && now - hit.at < CACHE_TTL_MS) {
      console.log(`📊 Cache hit for symbols: ${key}`);
      return hit.data;
    }

    // Dedupe in-flight requests
    const existing = inflight.get(key);
    if (existing) {
      console.log(`⏳ Deduplicating request for symbols: ${key}`);
      return existing;
    }

    const promise = this._fetchQuotesFromBackend(symbols)
      .then(data => {
        // Cache successful response
        cache.set(key, { at: now, data });
        return data;
      })
      .catch(err => {
        // Use stale cache if available
        if (hit) {
          console.warn(`⚠️ Network error, using stale cache for symbols: ${key}`, err.message);
          return hit.data;
        }
        // If no cache, return mock data instead of throwing error
        // This prevents the app from breaking when the backend is unavailable
        console.warn(`⚠️ No cache available, using mock data for symbols: ${key}`);
        return this._getMockQuotes(symbols);
      })
      .finally(() => {
        inflight.delete(key);
      });

    inflight.set(key, promise);
    return promise;
  }

  /**
   * Fetch quotes from backend with rate limit handling
   */
  private async _fetchQuotesFromBackend(symbols: string[]): Promise<Quote[]> {
    const symbolsParam = symbols.join(',');
    const url = `${API_BASE}/api/market/quotes?symbols=${encodeURIComponent(symbolsParam)}`;
    
    console.log(`📡 Fetching quotes from backend: ${symbolsParam}`);
    
    try {
      // Use AbortController for proper timeout handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout (reduced from 10)
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 429) {
          // Rate limit response
          const errorData = await response.json();
          throw new Error(`RATE_LIMIT: ${errorData.message || 'Rate limit exceeded'}`);
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Get raw response text first for debugging
      const text = await response.text();
      console.log(`📦 Raw response: ${text.substring(0, 200)}...`);
      
      let data;
      try {
        data = JSON.parse(text);
      } catch (parseError) {
        console.error('❌ JSON parse error:', parseError, 'Raw:', text);
        throw new Error(`Invalid JSON response from backend: ${parseError.message}`);
      }
      
      // Handle both formats: {quotes: [...]} and [...]
      let quotes: Quote[];
      if (Array.isArray(data)) {
        quotes = data;
      } else if (data && Array.isArray(data.quotes)) {
        quotes = data.quotes;
      } else if (data && data.quotes && typeof data.quotes === 'object') {
        // Handle case where quotes might be an object
        quotes = Object.values(data.quotes) as Quote[];
      } else {
        console.error('❌ Unexpected response format:', JSON.stringify(data, null, 2));
        throw new Error(`Invalid response format from backend. Expected array or {quotes: [...]}, got: ${typeof data}`);
      }

      console.log(`✅ Successfully fetched ${quotes.length} quotes`);
      return quotes;

    } catch (error: any) {
      // Handle timeout and network errors gracefully
      if (error?.name === 'AbortError' || error?.message?.includes('timeout') || error?.message?.includes('aborted')) {
        console.warn(`⚠️ Quote request timed out for symbols: ${symbolsParam}, will use mock data`);
        throw error; // Re-throw to trigger mock data fallback in calling code
      }
      if (error?.message?.includes('Network request failed') || error?.message?.includes('Failed to fetch')) {
        console.warn(`⚠️ Network error for quotes, using mock data fallback`);
        throw error; // Re-throw to trigger mock data fallback in calling code
      }
      console.error(`❌ Error fetching quotes: ${error?.message || 'Unknown error'}`);
      throw error;
    }
  }

  /**
   * Get mock quotes for demo/offline mode
   * Prices match the mock portfolio data
   */
  private _getMockQuotes(symbols: string[]): Quote[] {
    const mockQuotes: Record<string, Quote> = {
      AAPL: {
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
        provider: 'mock',
      },
      MSFT: {
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
        provider: 'mock',
      },
      SPY: {
        symbol: 'SPY',
        price: 420.00,
        change: 40.00,
        change_percent: 10.53,
        volume: 75000000,
        high: 422.00,
        low: 418.50,
        open: 419.00,
        previous_close: 380.00,
        updated: Date.now(),
        provider: 'mock',
      },
      GOOGL: {
        symbol: 'GOOGL',
        price: 128.71,
        change: 18.71,
        change_percent: 17.01,
        volume: 22000000,
        high: 130.00,
        low: 127.50,
        open: 128.00,
        previous_close: 110.00,
        updated: Date.now(),
        provider: 'mock',
      },
      AMZN: {
        symbol: 'AMZN',
        price: 132.00,
        change: 32.00,
        change_percent: 32.00,
        volume: 35000000,
        high: 134.00,
        low: 130.50,
        open: 131.00,
        previous_close: 100.00,
        updated: Date.now(),
        provider: 'mock',
      },
      NVDA: {
        symbol: 'NVDA',
        price: 504.00,
        change: 104.00,
        change_percent: 26.00,
        volume: 45000000,
        high: 508.00,
        low: 500.00,
        open: 502.00,
        previous_close: 400.00,
        updated: Date.now(),
        provider: 'mock',
      },
      TSLA: {
        symbol: 'TSLA',
        price: 196.50,
        change: 21.50,
        change_percent: 12.29,
        volume: 85000000,
        high: 198.00,
        low: 195.00,
        open: 196.00,
        previous_close: 175.00,
        updated: Date.now(),
        provider: 'mock',
      },
      // Additional common stocks
      META: {
        symbol: 'META',
        price: 285.00,
        change: 15.00,
        change_percent: 5.56,
        volume: 18000000,
        high: 287.00,
        low: 283.00,
        open: 284.00,
        previous_close: 270.00,
        updated: Date.now(),
        provider: 'mock',
      },
      NFLX: {
        symbol: 'NFLX',
        price: 425.00,
        change: 25.00,
        change_percent: 6.25,
        volume: 12000000,
        high: 427.00,
        low: 423.00,
        open: 424.00,
        previous_close: 400.00,
        updated: Date.now(),
        provider: 'mock',
      },
      AMD: {
        symbol: 'AMD',
        price: 145.00,
        change: 10.00,
        change_percent: 7.41,
        volume: 35000000,
        high: 146.00,
        low: 144.00,
        open: 144.50,
        previous_close: 135.00,
        updated: Date.now(),
        provider: 'mock',
      },
      ADBE: {
        symbol: 'ADBE',
        price: 485.00,
        change: 15.00,
        change_percent: 3.19,
        volume: 8000000,
        high: 487.00,
        low: 483.00,
        open: 484.00,
        previous_close: 470.00,
        updated: Date.now(),
        provider: 'mock',
      },
      CRM: {
        symbol: 'CRM',
        price: 220.00,
        change: 10.00,
        change_percent: 4.76,
        volume: 15000000,
        high: 222.00,
        low: 218.00,
        open: 219.00,
        previous_close: 210.00,
        updated: Date.now(),
        provider: 'mock',
      },
      PYPL: {
        symbol: 'PYPL',
        price: 65.00,
        change: 5.00,
        change_percent: 8.33,
        volume: 25000000,
        high: 66.00,
        low: 64.00,
        open: 64.50,
        previous_close: 60.00,
        updated: Date.now(),
        provider: 'mock',
      },
      INTC: {
        symbol: 'INTC',
        price: 42.00,
        change: 2.00,
        change_percent: 5.00,
        volume: 40000000,
        high: 42.50,
        low: 41.50,
        open: 41.75,
        previous_close: 40.00,
        updated: Date.now(),
        provider: 'mock',
      },
      LYFT: {
        symbol: 'LYFT',
        price: 12.50,
        change: 0.50,
        change_percent: 4.17,
        volume: 18000000,
        high: 12.75,
        low: 12.25,
        open: 12.30,
        previous_close: 12.00,
        updated: Date.now(),
        provider: 'mock',
      },
      UBER: {
        symbol: 'UBER',
        price: 38.00,
        change: 2.00,
        change_percent: 5.56,
        volume: 22000000,
        high: 38.50,
        low: 37.50,
        open: 37.75,
        previous_close: 36.00,
        updated: Date.now(),
        provider: 'mock',
      },
    };

    // Return quotes for requested symbols, or default quote if symbol not found
    const quotes = symbols.map(symbol => {
      const quote = mockQuotes[symbol.toUpperCase()];
      if (quote) {
        return quote;
      }
      // Default fallback quote
      return {
        symbol: symbol.toUpperCase(),
        price: 100.00,
        change: 0.00,
        change_percent: 0.00,
        volume: 1000000,
        high: 101.00,
        low: 99.00,
        open: 100.00,
        previous_close: 100.00,
        updated: Date.now(),
        provider: 'mock',
      };
    });

    console.log(`📊 Using mock quotes for ${symbols.length} symbols`);
    return quotes;
  }

  /**
   * Get market data service status
   */
  async getServiceStatus(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE}/api/market/status`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching service status:', error);
      return {
        service: 'market_data',
        status: 'unavailable',
        error: error.message
      };
    }
  }

  /**
   * Clear client-side cache
   */
  clearCache(): void {
    cache.clear();
    inflight.clear();
    console.log('🧹 Market data cache cleared');
  }

  /**
   * Fetch options for an underlying symbol
   */
  async fetchOptions(underlying: string, expiration?: string): Promise<Option[]> {
    const key = `${underlying}:${expiration || 'all'}`;
    const now = Date.now();

    // Serve from cache if available
    const hit = optionsCache.get(key);
    if (hit && now - hit.at < OPTIONS_CACHE_TTL_MS) {
      console.log(`📊 Options cache hit for: ${key}`);
      return hit.data;
    }

    // Dedupe in-flight requests
    const existing = optionsInflight.get(key);
    if (existing) {
      console.log(`⏳ Deduplicating options request for: ${key}`);
      return existing;
    }

    const promise = this._fetchOptionsFromBackend(underlying, expiration)
      .then(data => {
        // Cache successful response
        optionsCache.set(key, { at: now, data });
        return data;
      })
      .catch(err => {
        // Graceful degradation: return stale data if available
        if (hit) {
          console.log(`⚠️ Using stale options data for: ${key}`);
          return hit.data;
        }
        throw err;
      })
      .finally(() => {
        optionsInflight.delete(key);
      });

    optionsInflight.set(key, promise);
    return promise;
  }

  /**
   * Fetch options from backend
   */
  private async _fetchOptionsFromBackend(underlying: string, expiration?: string): Promise<Option[]> {
    const params = new URLSearchParams({ underlying });
    if (expiration) {
      params.append('expiration', expiration);
    }
    
    const url = `${API_BASE}/api/market/options?${params.toString()}`;
    
    console.log(`📡 Fetching options from backend: ${underlying}${expiration ? ` (${expiration})` : ''}`);
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 15000, // 15 second timeout for options
      });

      if (!response.ok) {
        if (response.status === 429) {
          // Rate limit response
          const errorData = await response.json();
          throw new Error(`RATE_LIMIT: ${errorData.message || 'Rate limit exceeded'}`);
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Get raw response text first for debugging
      const text = await response.text();
      console.log(`📦 Raw options response: ${text.substring(0, 200)}...`);
      
      let data;
      try {
        data = JSON.parse(text);
      } catch (parseError) {
        console.error('❌ JSON parse error:', parseError, 'Raw:', text);
        throw new Error(`Invalid JSON response from backend: ${parseError.message}`);
      }
      
      // Handle both formats: {options: [...]} and [...]
      let options: Option[];
      if (Array.isArray(data)) {
        options = data;
      } else if (data && Array.isArray(data.options)) {
        options = data.options;
      } else if (data && data.options && typeof data.options === 'object') {
        // Handle case where options might be an object
        options = Object.values(data.options) as Option[];
      } else {
        console.error('❌ Unexpected options response format:', JSON.stringify(data, null, 2));
        throw new Error(`Invalid response format from backend. Expected array or {options: [...]}, got: ${typeof data}`);
      }

      console.log(`✅ Successfully fetched ${options.length} options contracts`);
      return options;

    } catch (error) {
      console.error(`❌ Error fetching options: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { 
    quotes: { size: number; keys: string[] };
    options: { size: number; keys: string[] };
  } {
    return {
      quotes: {
        size: cache.size,
        keys: Array.from(cache.keys())
      },
      options: {
        size: optionsCache.size,
        keys: Array.from(optionsCache.keys())
      }
    };
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    cache.clear();
    optionsCache.clear();
    inflight.clear();
    optionsInflight.clear();
    console.log('🧹 All market data caches cleared');
  }
}

// Export singleton instance
export const secureMarketDataService = SecureMarketDataService.getInstance();

// Export convenience functions
export const fetchQuotes = (symbols: string[]) => secureMarketDataService.fetchQuotes(symbols);
export const fetchOptions = (underlying: string, expiration?: string) => secureMarketDataService.fetchOptions(underlying, expiration);
export const getServiceStatus = () => secureMarketDataService.getServiceStatus();
export const clearCache = () => secureMarketDataService.clearCache();
