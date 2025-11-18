/**
 * Trading Offline Cache Service
 * 
 * Provides persistent offline caching for trading screen data:
 * - Account data
 * - Positions
 * - Orders
 * - Quotes
 * - Market data
 * 
 * Uses AsyncStorage for persistence and provides cache-first strategy
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

const CACHE_KEYS = {
  ACCOUNT: 'trading_cache_account',
  POSITIONS: 'trading_cache_positions',
  ORDERS: 'trading_cache_orders',
  QUOTES: 'trading_cache_quotes',
  MARKET_DATA: 'trading_cache_market_data',
  LAST_SYNC: 'trading_cache_last_sync',
};

// Cache durations (in milliseconds)
const CACHE_DURATION = {
  ACCOUNT: 5 * 60 * 1000,      // 5 minutes
  POSITIONS: 2 * 60 * 1000,    // 2 minutes (more volatile)
  ORDERS: 1 * 60 * 1000,       // 1 minute (very volatile)
  QUOTES: 30 * 1000,            // 30 seconds (very volatile)
  MARKET_DATA: 5 * 60 * 1000,  // 5 minutes
};

interface CachedData<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface CacheStats {
  account: { size: number; age: number; valid: boolean };
  positions: { size: number; age: number; valid: boolean };
  orders: { size: number; age: number; valid: boolean };
  quotes: { size: number; age: number; valid: boolean };
  lastSync: number;
}

export class TradingOfflineCache {
  private static instance: TradingOfflineCache;
  private isOnline: boolean = true;

  private constructor() {
    // Monitor network status
    NetInfo.addEventListener(state => {
      this.isOnline = state.isConnected ?? false;
      if (__DEV__) {
        console.log(`📡 Network status: ${this.isOnline ? 'Online' : 'Offline'}`);
      }
    });
  }

  public static getInstance(): TradingOfflineCache {
    if (!TradingOfflineCache.instance) {
      TradingOfflineCache.instance = new TradingOfflineCache();
    }
    return TradingOfflineCache.instance;
  }

  /**
   * Check if device is online
   */
  public async isConnected(): Promise<boolean> {
    const state = await NetInfo.fetch();
    this.isOnline = state.isConnected ?? false;
    return this.isOnline;
  }

  /**
   * Cache account data
   */
  public async cacheAccount(account: any): Promise<void> {
    try {
      const cached: CachedData<any> = {
        data: account,
        timestamp: Date.now(),
        expiresAt: Date.now() + CACHE_DURATION.ACCOUNT,
      };
      await AsyncStorage.setItem(CACHE_KEYS.ACCOUNT, JSON.stringify(cached));
      await this.updateLastSync();
      if (__DEV__) {
        console.log('💾 Cached account data');
      }
    } catch (error) {
      console.error('❌ Failed to cache account:', error);
    }
  }

  /**
   * Get cached account data
   */
  public async getAccount(): Promise<any | null> {
    try {
      const cachedString = await AsyncStorage.getItem(CACHE_KEYS.ACCOUNT);
      if (!cachedString) return null;

      const cached: CachedData<any> = JSON.parse(cachedString);
      const now = Date.now();

      if (now > cached.expiresAt) {
        // Expired but return stale data if offline
        if (!(await this.isConnected())) {
          if (__DEV__) {
            console.log('📴 Using expired account cache (offline)');
          }
          return cached.data;
        }
        return null;
      }

      return cached.data;
    } catch (error) {
      console.error('❌ Failed to get cached account:', error);
      return null;
    }
  }

  /**
   * Cache positions
   */
  public async cachePositions(positions: any[]): Promise<void> {
    try {
      const cached: CachedData<any[]> = {
        data: positions,
        timestamp: Date.now(),
        expiresAt: Date.now() + CACHE_DURATION.POSITIONS,
      };
      await AsyncStorage.setItem(CACHE_KEYS.POSITIONS, JSON.stringify(cached));
      await this.updateLastSync();
      if (__DEV__) {
        console.log(`💾 Cached ${positions.length} positions`);
      }
    } catch (error) {
      console.error('❌ Failed to cache positions:', error);
    }
  }

  /**
   * Get cached positions
   */
  public async getPositions(): Promise<any[] | null> {
    try {
      const cachedString = await AsyncStorage.getItem(CACHE_KEYS.POSITIONS);
      if (!cachedString) return null;

      const cached: CachedData<any[]> = JSON.parse(cachedString);
      const now = Date.now();

      if (now > cached.expiresAt) {
        if (!(await this.isConnected())) {
          if (__DEV__) {
            console.log('📴 Using expired positions cache (offline)');
          }
          return cached.data;
        }
        return null;
      }

      return cached.data;
    } catch (error) {
      console.error('❌ Failed to get cached positions:', error);
      return null;
    }
  }

  /**
   * Cache orders
   */
  public async cacheOrders(orders: any[]): Promise<void> {
    try {
      const cached: CachedData<any[]> = {
        data: orders,
        timestamp: Date.now(),
        expiresAt: Date.now() + CACHE_DURATION.ORDERS,
      };
      await AsyncStorage.setItem(CACHE_KEYS.ORDERS, JSON.stringify(cached));
      await this.updateLastSync();
      if (__DEV__) {
        console.log(`💾 Cached ${orders.length} orders`);
      }
    } catch (error) {
      console.error('❌ Failed to cache orders:', error);
    }
  }

  /**
   * Get cached orders
   */
  public async getOrders(): Promise<any[] | null> {
    try {
      const cachedString = await AsyncStorage.getItem(CACHE_KEYS.ORDERS);
      if (!cachedString) return null;

      const cached: CachedData<any[]> = JSON.parse(cachedString);
      const now = Date.now();

      if (now > cached.expiresAt) {
        if (!(await this.isConnected())) {
          if (__DEV__) {
            console.log('📴 Using expired orders cache (offline)');
          }
          return cached.data;
        }
        return null;
      }

      return cached.data;
    } catch (error) {
      console.error('❌ Failed to get cached orders:', error);
      return null;
    }
  }

  /**
   * Cache quote for a symbol
   */
  public async cacheQuote(symbol: string, quote: any): Promise<void> {
    try {
      const key = `${CACHE_KEYS.QUOTES}_${symbol.toUpperCase()}`;
      const cached: CachedData<any> = {
        data: quote,
        timestamp: Date.now(),
        expiresAt: Date.now() + CACHE_DURATION.QUOTES,
      };
      await AsyncStorage.setItem(key, JSON.stringify(cached));
      if (__DEV__) {
        console.log(`💾 Cached quote for ${symbol}`);
      }
    } catch (error) {
      console.error(`❌ Failed to cache quote for ${symbol}:`, error);
    }
  }

  /**
   * Get cached quote for a symbol
   */
  public async getQuote(symbol: string): Promise<any | null> {
    try {
      const key = `${CACHE_KEYS.QUOTES}_${symbol.toUpperCase()}`;
      const cachedString = await AsyncStorage.getItem(key);
      if (!cachedString) return null;

      const cached: CachedData<any> = JSON.parse(cachedString);
      const now = Date.now();

      if (now > cached.expiresAt) {
        if (!(await this.isConnected())) {
          if (__DEV__) {
            console.log(`📴 Using expired quote cache for ${symbol} (offline)`);
          }
          return cached.data;
        }
        return null;
      }

      return cached.data;
    } catch (error) {
      console.error(`❌ Failed to get cached quote for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Update last sync timestamp
   */
  private async updateLastSync(): Promise<void> {
    try {
      await AsyncStorage.setItem(CACHE_KEYS.LAST_SYNC, Date.now().toString());
    } catch (error) {
      console.error('❌ Failed to update last sync:', error);
    }
  }

  /**
   * Get last sync timestamp
   */
  public async getLastSync(): Promise<number | null> {
    try {
      const timestamp = await AsyncStorage.getItem(CACHE_KEYS.LAST_SYNC);
      return timestamp ? parseInt(timestamp, 10) : null;
    } catch (error) {
      console.error('❌ Failed to get last sync:', error);
      return null;
    }
  }

  /**
   * Get cache statistics
   */
  public async getStats(): Promise<CacheStats> {
    const now = Date.now();
    const stats: CacheStats = {
      account: { size: 0, age: 0, valid: false },
      positions: { size: 0, age: 0, valid: false },
      orders: { size: 0, age: 0, valid: false },
      quotes: { size: 0, age: 0, valid: false },
      lastSync: 0,
    };

    try {
      // Account
      const accountString = await AsyncStorage.getItem(CACHE_KEYS.ACCOUNT);
      if (accountString) {
        const cached: CachedData<any> = JSON.parse(accountString);
        stats.account = {
          size: JSON.stringify(cached.data).length,
          age: now - cached.timestamp,
          valid: now <= cached.expiresAt,
        };
      }

      // Positions
      const positionsString = await AsyncStorage.getItem(CACHE_KEYS.POSITIONS);
      if (positionsString) {
        const cached: CachedData<any[]> = JSON.parse(positionsString);
        stats.positions = {
          size: JSON.stringify(cached.data).length,
          age: now - cached.timestamp,
          valid: now <= cached.expiresAt,
        };
      }

      // Orders
      const ordersString = await AsyncStorage.getItem(CACHE_KEYS.ORDERS);
      if (ordersString) {
        const cached: CachedData<any[]> = JSON.parse(ordersString);
        stats.orders = {
          size: JSON.stringify(cached.data).length,
          age: now - cached.timestamp,
          valid: now <= cached.expiresAt,
        };
      }

      // Last sync
      const lastSync = await this.getLastSync();
      stats.lastSync = lastSync || 0;
    } catch (error) {
      console.error('❌ Failed to get cache stats:', error);
    }

    return stats;
  }

  /**
   * Clear all trading cache
   */
  public async clearAll(): Promise<void> {
    try {
      await Promise.all([
        AsyncStorage.removeItem(CACHE_KEYS.ACCOUNT),
        AsyncStorage.removeItem(CACHE_KEYS.POSITIONS),
        AsyncStorage.removeItem(CACHE_KEYS.ORDERS),
        AsyncStorage.removeItem(CACHE_KEYS.LAST_SYNC),
      ]);

      // Clear all quote caches
      const keys = await AsyncStorage.getAllKeys();
      const quoteKeys = keys.filter(key => key.startsWith(CACHE_KEYS.QUOTES));
      await Promise.all(quoteKeys.map(key => AsyncStorage.removeItem(key)));

      if (__DEV__) {
        console.log('🧹 Cleared all trading cache');
      }
    } catch (error) {
      console.error('❌ Failed to clear cache:', error);
    }
  }
}

// Export singleton instance
export const tradingOfflineCache = TradingOfflineCache.getInstance();

