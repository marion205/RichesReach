/**
 * Mobile Optimization Configuration
 * Centralized settings for battery and data usage optimization
 */

export interface MobileOptimizationConfig {
  // Network optimization
  network: {
    fastPolling: number;      // WiFi polling interval (ms)
    normalPolling: number;    // Cellular polling interval (ms)
    slowPolling: number;      // Background polling interval (ms)
    offlinePolling: number;   // Offline retry interval (ms)
    maxDataUsagePerHour: number; // MB per hour
    enableDataSaver: boolean;
  };
  
  // Battery optimization
  battery: {
    enableBatteryOptimization: boolean;
    lowBatteryThreshold: number; // Percentage
    criticalBatteryThreshold: number; // Percentage
    enableBackgroundSync: boolean;
  };
  
  // Caching
  cache: {
    ttl: number; // Time to live in milliseconds
    maxSize: number; // Maximum cache size in MB
    compressionEnabled: boolean;
    enablePersistentCache: boolean;
  };
  
  // UI optimization
  ui: {
    enableLazyLoading: boolean;
    enableImageOptimization: boolean;
    enableVirtualization: boolean;
    maxRenderedItems: number;
  };
  
  // Performance
  performance: {
    enableMemoryOptimization: boolean;
    enableRenderOptimization: boolean;
    maxConcurrentRequests: number;
    requestTimeout: number; // ms
  };
}

export const DEFAULT_MOBILE_CONFIG: MobileOptimizationConfig = {
  network: {
    fastPolling: 10000,      // 10 seconds on WiFi
    normalPolling: 30000,    // 30 seconds on cellular
    slowPolling: 300000,     // 5 minutes in background
    offlinePolling: 60000,   // 1 minute when offline
    maxDataUsagePerHour: 50, // 50MB per hour
    enableDataSaver: true,
  },
  
  battery: {
    enableBatteryOptimization: true,
    lowBatteryThreshold: 20, // 20%
    criticalBatteryThreshold: 10, // 10%
    enableBackgroundSync: true,
  },
  
  cache: {
    ttl: 300000, // 5 minutes
    maxSize: 50, // 50MB
    compressionEnabled: true,
    enablePersistentCache: true,
  },
  
  ui: {
    enableLazyLoading: true,
    enableImageOptimization: true,
    enableVirtualization: true,
    maxRenderedItems: 50,
  },
  
  performance: {
    enableMemoryOptimization: true,
    enableRenderOptimization: true,
    maxConcurrentRequests: 3,
    requestTimeout: 10000, // 10 seconds
  },
};

// Production configuration (more aggressive optimization)
export const PRODUCTION_MOBILE_CONFIG: MobileOptimizationConfig = {
  network: {
    fastPolling: 15000,      // 15 seconds on WiFi
    normalPolling: 60000,    // 1 minute on cellular
    slowPolling: 600000,     // 10 minutes in background
    offlinePolling: 120000,  // 2 minutes when offline
    maxDataUsagePerHour: 25, // 25MB per hour
    enableDataSaver: true,
  },
  
  battery: {
    enableBatteryOptimization: true,
    lowBatteryThreshold: 25, // 25%
    criticalBatteryThreshold: 15, // 15%
    enableBackgroundSync: false, // Disable in production for battery
  },
  
  cache: {
    ttl: 600000, // 10 minutes
    maxSize: 25, // 25MB
    compressionEnabled: true,
    enablePersistentCache: true,
  },
  
  ui: {
    enableLazyLoading: true,
    enableImageOptimization: true,
    enableVirtualization: true,
    maxRenderedItems: 25,
  },
  
  performance: {
    enableMemoryOptimization: true,
    enableRenderOptimization: true,
    maxConcurrentRequests: 2,
    requestTimeout: 15000, // 15 seconds
  },
};

// Development configuration (less aggressive for testing)
export const DEVELOPMENT_MOBILE_CONFIG: MobileOptimizationConfig = {
  network: {
    fastPolling: 5000,       // 5 seconds on WiFi
    normalPolling: 15000,    // 15 seconds on cellular
    slowPolling: 120000,     // 2 minutes in background
    offlinePolling: 30000,   // 30 seconds when offline
    maxDataUsagePerHour: 100, // 100MB per hour
    enableDataSaver: false,
  },
  
  battery: {
    enableBatteryOptimization: false,
    lowBatteryThreshold: 20,
    criticalBatteryThreshold: 10,
    enableBackgroundSync: true,
  },
  
  cache: {
    ttl: 60000, // 1 minute
    maxSize: 100, // 100MB
    compressionEnabled: false,
    enablePersistentCache: true,
  },
  
  ui: {
    enableLazyLoading: false,
    enableImageOptimization: false,
    enableVirtualization: false,
    maxRenderedItems: 100,
  },
  
  performance: {
    enableMemoryOptimization: false,
    enableRenderOptimization: false,
    maxConcurrentRequests: 5,
    requestTimeout: 5000, // 5 seconds
  },
};

// Get configuration based on environment
export const getMobileOptimizationConfig = (): MobileOptimizationConfig => {
  const isDevelopment = __DEV__;
  const isProduction = !isDevelopment;
  
  if (isProduction) {
    return PRODUCTION_MOBILE_CONFIG;
  } else {
    return DEVELOPMENT_MOBILE_CONFIG;
  }
};
