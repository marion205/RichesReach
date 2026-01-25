/**
 * Image caching utility for quotes, portfolio data, and other images
 * Uses AsyncStorage for persistent caching
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Image } from 'react-native';
import logger from './logger';

interface CacheEntry {
  uri: string;
  timestamp: number;
  data?: any; // For non-image data (quotes, portfolio metrics)
}

const CACHE_PREFIX = '@richesreach_cache_';
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes for quotes/portfolio
const IMAGE_CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours for images

class ImageCache {
  private memoryCache: Map<string, CacheEntry> = new Map();
  private maxMemorySize = 50; // Max entries in memory cache

  /**
   * Preload and cache an image
   */
  async preloadImage(uri: string): Promise<void> {
    try {
      const cacheKey = this.getCacheKey(uri);
      
      // Check memory cache first
      if (this.memoryCache.has(cacheKey)) {
        return;
      }

      // Check persistent cache
      const cached = await AsyncStorage.getItem(cacheKey);
      if (cached) {
        const entry: CacheEntry = JSON.parse(cached);
        if (this.isValid(entry, IMAGE_CACHE_EXPIRY)) {
          this.memoryCache.set(cacheKey, entry);
          return;
        }
      }

      // Preload image
      await Image.prefetch(uri);
      
      // Cache it
      const entry: CacheEntry = {
        uri,
        timestamp: Date.now(),
      };
      
      this.memoryCache.set(cacheKey, entry);
      await AsyncStorage.setItem(cacheKey, JSON.stringify(entry));
      
      // Cleanup if cache is too large
      this.cleanupMemoryCache();
    } catch (error) {
      logger.warn('Failed to preload image:', uri, error);
    }
  }

  /**
   * Cache data (quotes, portfolio metrics, etc.)
   */
  async cacheData(key: string, data: any, expiry: number = CACHE_EXPIRY): Promise<void> {
    try {
      const cacheKey = this.getCacheKey(key);
      const entry: CacheEntry = {
        uri: key,
        timestamp: Date.now(),
        data,
      };
      
      this.memoryCache.set(cacheKey, entry);
      await AsyncStorage.setItem(cacheKey, JSON.stringify(entry));
      
      this.cleanupMemoryCache();
    } catch (error) {
      logger.warn('Failed to cache data:', key, error);
    }
  }

  /**
   * Get cached data
   */
  async getCachedData<T>(key: string, expiry: number = CACHE_EXPIRY): Promise<T | null> {
    try {
      const cacheKey = this.getCacheKey(key);
      
      // Check memory cache first
      const memoryEntry = this.memoryCache.get(cacheKey);
      if (memoryEntry && this.isValid(memoryEntry, expiry)) {
        return memoryEntry.data as T;
      }

      // Check persistent cache
      const cached = await AsyncStorage.getItem(cacheKey);
      if (cached) {
        const entry: CacheEntry = JSON.parse(cached);
        if (this.isValid(entry, expiry)) {
          this.memoryCache.set(cacheKey, entry);
          return entry.data as T;
        } else {
          // Expired, remove it
          await AsyncStorage.removeItem(cacheKey);
        }
      }

      return null;
    } catch (error) {
      logger.warn('Failed to get cached data:', key, error);
      return null;
    }
  }

  /**
   * Clear cache for a specific key
   */
  async clearCache(key: string): Promise<void> {
    try {
      const cacheKey = this.getCacheKey(key);
      this.memoryCache.delete(cacheKey);
      await AsyncStorage.removeItem(cacheKey);
    } catch (error) {
      logger.warn('Failed to clear cache:', key, error);
    }
  }

  /**
   * Clear all cache
   */
  async clearAllCache(): Promise<void> {
    try {
      this.memoryCache.clear();
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(CACHE_PREFIX));
      await AsyncStorage.multiRemove(cacheKeys);
    } catch (error) {
      logger.warn('Failed to clear all cache:', error);
    }
  }

  /**
   * Get cache key with prefix
   */
  private getCacheKey(key: string): string {
    return `${CACHE_PREFIX}${key}`;
  }

  /**
   * Check if cache entry is still valid
   */
  private isValid(entry: CacheEntry, expiry: number): boolean {
    return Date.now() - entry.timestamp < expiry;
  }

  /**
   * Cleanup memory cache if it gets too large
   */
  private cleanupMemoryCache(): void {
    if (this.memoryCache.size > this.maxMemorySize) {
      // Remove oldest entries
      const entries = Array.from(this.memoryCache.entries())
        .sort((a, b) => a[1].timestamp - b[1].timestamp);
      
      const toRemove = entries.slice(0, this.memoryCache.size - this.maxMemorySize);
      toRemove.forEach(([key]) => this.memoryCache.delete(key));
    }
  }
}

// Singleton instance
export const imageCache = new ImageCache();

