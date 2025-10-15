/**
 * Health Service
 * Checks the health of various backend services
 */

import { API_BASE } from '../config/api';

export interface HealthStatus {
  isHealthy: boolean;
  responseTime?: number;
  error?: string;
  timestamp: number;
}

export interface MarketDataHealthStatus extends HealthStatus {
  providers?: {
    finnhub: boolean;
    polygon: boolean;
    alpha_vantage: boolean;
  };
  cacheEnabled?: boolean;
}

/**
 * Check if the market data service is healthy
 */
export async function isMarketDataHealthy(apiBase: string = API_BASE): Promise<MarketDataHealthStatus> {
  const startTime = Date.now();
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const response = await fetch(`${apiBase}/health/marketdata`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    const responseTime = Date.now() - startTime;
    
    if (!response.ok) {
      return {
        isHealthy: false,
        responseTime,
        error: `HTTP ${response.status}: ${response.statusText}`,
        timestamp: Date.now(),
      };
    }
    
    const data = await response.json();
    
    return {
      isHealthy: true,
      responseTime,
      providers: {
        finnhub: data.providers?.finnhub?.configured || false,
        polygon: data.providers?.polygon?.configured || false,
        alpha_vantage: data.providers?.alpha_vantage?.configured || false,
      },
      cacheEnabled: data.cache_enabled || false,
      timestamp: Date.now(),
    };
    
  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      isHealthy: false,
      responseTime,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: Date.now(),
    };
  }
}

/**
 * Check if the main backend is healthy
 */
export async function isBackendHealthy(apiBase: string = API_BASE): Promise<HealthStatus> {
  const startTime = Date.now();
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${apiBase}/health`, {
      method: 'GET',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    const responseTime = Date.now() - startTime;
    
    if (!response.ok) {
      return {
        isHealthy: false,
        responseTime,
        error: `HTTP ${response.status}: ${response.statusText}`,
        timestamp: Date.now(),
      };
    }
    
    return {
      isHealthy: true,
      responseTime,
      timestamp: Date.now(),
    };
    
  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      isHealthy: false,
      responseTime,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: Date.now(),
    };
  }
}

/**
 * Check if GraphQL endpoint is healthy
 */
export async function isGraphQLHealthy(apiBase: string = API_BASE): Promise<HealthStatus> {
  const startTime = Date.now();
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${apiBase}/graphql`, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: '{ __typename }',
      }),
    });
    
    clearTimeout(timeoutId);
    const responseTime = Date.now() - startTime;
    
    if (!response.ok) {
      return {
        isHealthy: false,
        responseTime,
        error: `HTTP ${response.status}: ${response.statusText}`,
        timestamp: Date.now(),
      };
    }
    
    const data = await response.json();
    
    if (data.errors) {
      return {
        isHealthy: false,
        responseTime,
        error: `GraphQL errors: ${data.errors.map((e: any) => e.message).join(', ')}`,
        timestamp: Date.now(),
      };
    }
    
    return {
      isHealthy: true,
      responseTime,
      timestamp: Date.now(),
    };
    
  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      isHealthy: false,
      responseTime,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: Date.now(),
    };
  }
}

/**
 * Get comprehensive health status of all services
 */
export async function getComprehensiveHealthStatus(apiBase: string = API_BASE) {
  const [backend, graphql, marketData] = await Promise.allSettled([
    isBackendHealthy(apiBase),
    isGraphQLHealthy(apiBase),
    isMarketDataHealthy(apiBase),
  ]);
  
  return {
    backend: backend.status === 'fulfilled' ? backend.value : { isHealthy: false, error: 'Failed to check' },
    graphql: graphql.status === 'fulfilled' ? graphql.value : { isHealthy: false, error: 'Failed to check' },
    marketData: marketData.status === 'fulfilled' ? marketData.value : { isHealthy: false, error: 'Failed to check' },
    timestamp: Date.now(),
  };
}
