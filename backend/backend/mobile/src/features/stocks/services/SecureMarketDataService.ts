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
        // Graceful degradation: return stale data if available
        if (hit) {
          console.log(`⚠️ Using stale data for symbols: ${key}`);
          return hit.data;
        }
        throw err;
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
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 10000, // 10 second timeout
      });

      if (!response.ok) {
        if (response.status === 429) {
          // Rate limit response
          const errorData = await response.json();
          throw new Error(`RATE_LIMIT: ${errorData.message || 'Rate limit exceeded'}`);
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Validate response format
      if (!Array.isArray(data)) {
        throw new Error('Invalid response format from backend');
      }

      console.log(`✅ Successfully fetched ${data.length} quotes`);
      return data as Quote[];

    } catch (error) {
      console.error(`❌ Error fetching quotes: ${error.message}`);
      throw error;
    }
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

      const data = await response.json();
      
      // Validate response format
      if (!Array.isArray(data)) {
        throw new Error('Invalid response format from backend');
      }

      console.log(`✅ Successfully fetched ${data.length} options contracts`);
      return data as Option[];

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
