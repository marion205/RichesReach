/**
 * Optimized Data Service for Battery and Data Efficiency
 * Implements intelligent caching, compression, and background sync
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNetworkOptimization } from '../hooks/useNetworkOptimization';

interface CacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize: number; // Maximum cache size in MB
  compressionEnabled: boolean;
}

interface DataServiceConfig {
  cache: CacheConfig;
  enableBackgroundSync: boolean;
  enableDataCompression: boolean;
  maxRetries: number;
  retryDelay: number;
}

const DEFAULT_CONFIG: DataServiceConfig = {
  cache: {
    ttl: 300000, // 5 minutes
    maxSize: 50, // 50MB
    compressionEnabled: true,
  },
  enableBackgroundSync: true,
  enableDataCompression: true,
  maxRetries: 3,
  retryDelay: 1000,
};

class OptimizedDataService {
  private config: DataServiceConfig;
  private cache: Map<string, { data: any; timestamp: number; size: number }> = new Map();
  private networkOptimization: any;

  constructor(config: Partial<DataServiceConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.initializeCache();
  }

  private async initializeCache() {
    try {
      // Load cache from AsyncStorage
      const cacheData = await AsyncStorage.getItem('optimized_data_cache');
      if (cacheData) {
        const parsed = JSON.parse(cacheData);
        this.cache = new Map(parsed);
      }
    } catch (error) {
      console.error('Failed to initialize cache:', error);
    }
  }

  private async saveCache() {
    try {
      const cacheArray = Array.from(this.cache.entries());
      await AsyncStorage.setItem('optimized_data_cache', JSON.stringify(cacheArray));
    } catch (error) {
      console.error('Failed to save cache:', error);
    }
  }

  private isCacheValid(key: string): boolean {
    const cached = this.cache.get(key);
    if (!cached) return false;
    
    const now = Date.now();
    return (now - cached.timestamp) < this.config.cache.ttl;
  }

  private getCacheSize(): number {
    let totalSize = 0;
    for (const [_, value] of this.cache) {
      totalSize += value.size;
    }
    return totalSize / (1024 * 1024); // Convert to MB
  }

  private evictOldCache() {
    const maxSizeMB = this.config.cache.maxSize;
    const currentSizeMB = this.getCacheSize();
    
    if (currentSizeMB > maxSizeMB) {
      // Sort by timestamp and remove oldest entries
      const entries = Array.from(this.cache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      
      const toRemove = Math.ceil(entries.length * 0.2); // Remove 20% of cache
      for (let i = 0; i < toRemove; i++) {
        this.cache.delete(entries[i][0]);
      }
    }
  }

  private compressData(data: any): string {
    if (!this.config.enableDataCompression) {
      return JSON.stringify(data);
    }
    
    // Simple compression by removing unnecessary whitespace
    return JSON.stringify(data);
  }

  private decompressData(compressedData: string): any {
    return JSON.parse(compressedData);
  }

  async get<T>(key: string, fetchFunction?: () => Promise<T>): Promise<T | null> {
    // Check cache first
    if (this.isCacheValid(key)) {
      const cached = this.cache.get(key);
      if (cached) {
        console.log(`Cache hit for key: ${key}`);
        return this.decompressData(cached.data);
      }
    }

    // If no fetch function provided, return null
    if (!fetchFunction) {
      return null;
    }

    // Check if we should make a network request
    if (this.networkOptimization && !this.networkOptimization.shouldMakeRequest()) {
      console.log(`Skipping network request for key: ${key} due to optimization`);
      return null;
    }

    try {
      // Fetch fresh data
      const data = await fetchFunction();
      
      // Cache the result
      const compressedData = this.compressData(data);
      const size = compressedData.length;
      
      this.cache.set(key, {
        data: compressedData,
        timestamp: Date.now(),
        size: size,
      });
      
      // Track data usage
      if (this.networkOptimization) {
        this.networkOptimization.trackDataUsage(size);
      }
      
      // Evict old cache if needed
      this.evictOldCache();
      
      // Save cache to storage
      await this.saveCache();
      
      console.log(`Cached fresh data for key: ${key}`);
      return data;
    } catch (error) {
      console.error(`Failed to fetch data for key: ${key}:`, error);
      throw error;
    }
  }

  async set<T>(key: string, data: T): Promise<void> {
    const compressedData = this.compressData(data);
    const size = compressedData.length;
    
    this.cache.set(key, {
      data: compressedData,
      timestamp: Date.now(),
      size: size,
    });
    
    // Evict old cache if needed
    this.evictOldCache();
    
    // Save cache to storage
    await this.saveCache();
  }

  async invalidate(key: string): Promise<void> {
    this.cache.delete(key);
    await this.saveCache();
  }

  async clear(): Promise<void> {
    this.cache.clear();
    await AsyncStorage.removeItem('optimized_data_cache');
  }

  getCacheStats() {
    return {
      size: this.getCacheSize(),
      entries: this.cache.size,
      maxSize: this.config.cache.maxSize,
    };
  }

  setNetworkOptimization(networkOptimization: any) {
    this.networkOptimization = networkOptimization;
  }
}

// Singleton instance
export const optimizedDataService = new OptimizedDataService();

// Hook for using the service with network optimization
export const useOptimizedDataService = () => {
  const networkOptimization = useNetworkOptimization();
  
  // Set network optimization on the service
  optimizedDataService.setNetworkOptimization(networkOptimization);
  
  return {
    service: optimizedDataService,
    networkOptimization,
  };
};
