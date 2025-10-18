/**
 * Performance Testing Utilities
 * Measures GraphQL call speeds and login performance
 */

export interface PerformanceMetrics {
  operation: string;
  startTime: number;
  endTime: number;
  duration: number;
  success: boolean;
  error?: string;
  cacheHit?: boolean;
}

class PerformanceTracker {
  private metrics: PerformanceMetrics[] = [];
  private activeTimers: Map<string, number> = new Map();

  startTimer(operation: string): void {
    const startTime = performance.now();
    this.activeTimers.set(operation, startTime);
    console.log(`🚀 [PERF] Starting: ${operation}`);
  }

  endTimer(operation: string, success: boolean = true, error?: string, cacheHit?: boolean): PerformanceMetrics {
    const startTime = this.activeTimers.get(operation);
    if (!startTime) {
      console.warn(`⚠️ [PERF] No start time found for: ${operation}`);
      return {
        operation,
        startTime: 0,
        endTime: 0,
        duration: 0,
        success: false,
        error: 'No start time found'
      };
    }

    const endTime = performance.now();
    const duration = endTime - startTime;
    
    const metric: PerformanceMetrics = {
      operation,
      startTime,
      endTime,
      duration,
      success,
      error,
      cacheHit
    };

    this.metrics.push(metric);
    this.activeTimers.delete(operation);

    const status = success ? '✅' : '❌';
    const cache = cacheHit ? ' (CACHE)' : '';
    console.log(`${status} [PERF] ${operation}: ${duration.toFixed(2)}ms${cache}`);
    
    if (error) {
      console.error(`❌ [PERF] Error in ${operation}:`, error);
    }

    return metric;
  }

  getMetrics(): PerformanceMetrics[] {
    return [...this.metrics];
  }

  getAverageTime(operationPrefix?: string): number {
    const filtered = operationPrefix 
      ? this.metrics.filter(m => m.operation.startsWith(operationPrefix))
      : this.metrics;
    
    if (filtered.length === 0) return 0;
    
    const total = filtered.reduce((sum, m) => sum + m.duration, 0);
    return total / filtered.length;
  }

  getSuccessRate(operationPrefix?: string): number {
    const filtered = operationPrefix 
      ? this.metrics.filter(m => m.operation.startsWith(operationPrefix))
      : this.metrics;
    
    if (filtered.length === 0) return 0;
    
    const successful = filtered.filter(m => m.success).length;
    return (successful / filtered.length) * 100;
  }

  printSummary(): void {
    console.log('\n📊 [PERF] Performance Summary:');
    console.log('================================');
    
    const totalOps = this.metrics.length;
    const successfulOps = this.metrics.filter(m => m.success).length;
    const avgTime = this.getAverageTime();
    const successRate = this.getSuccessRate();
    
    console.log(`Total Operations: ${totalOps}`);
    console.log(`Successful: ${successfulOps} (${successRate.toFixed(1)}%)`);
    console.log(`Average Time: ${avgTime.toFixed(2)}ms`);
    
    // Group by operation type
    const groups = this.metrics.reduce((acc, metric) => {
      const prefix = metric.operation.split(' ')[0];
      if (!acc[prefix]) acc[prefix] = [];
      acc[prefix].push(metric);
      return acc;
    }, {} as Record<string, PerformanceMetrics[]>);

    console.log('\n📈 [PERF] By Operation Type:');
    Object.entries(groups).forEach(([type, metrics]) => {
      const avg = metrics.reduce((sum, m) => sum + m.duration, 0) / metrics.length;
      const success = metrics.filter(m => m.success).length;
      const cacheHits = metrics.filter(m => m.cacheHit).length;
      
      console.log(`${type}: ${avg.toFixed(2)}ms avg (${success}/${metrics.length} success, ${cacheHits} cache hits)`);
    });

    // Show slowest operations
    const slowest = [...this.metrics]
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 5);
    
    console.log('\n🐌 [PERF] Slowest Operations:');
    slowest.forEach((metric, i) => {
      console.log(`${i + 1}. ${metric.operation}: ${metric.duration.toFixed(2)}ms`);
    });

    // Show fastest operations
    const fastest = [...this.metrics]
      .filter(m => m.success)
      .sort((a, b) => a.duration - b.duration)
      .slice(0, 5);
    
    console.log('\n⚡ [PERF] Fastest Operations:');
    fastest.forEach((metric, i) => {
      console.log(`${i + 1}. ${metric.operation}: ${metric.duration.toFixed(2)}ms`);
    });
  }

  clear(): void {
    this.metrics = [];
    this.activeTimers.clear();
    console.log('🧹 [PERF] Performance metrics cleared');
  }
}

// Global performance tracker instance
export const perfTracker = new PerformanceTracker();

// Apollo Client performance link
export const createPerformanceLink = () => {
  return {
    request: (operation: any, forward: any) => {
      const operationName = operation.operationName || 'Unknown';
      perfTracker.startTimer(`GraphQL ${operationName}`);
      
      return forward(operation).map((result: any) => {
        const success = !result.errors || result.errors.length === 0;
        const error = result.errors?.[0]?.message;
        const cacheHit = result.data && !result.loading;
        
        perfTracker.endTimer(`GraphQL ${operationName}`, success, error, cacheHit);
        return result;
      });
    }
  };
};

// Login performance test
export const testLoginPerformance = async (loginFunction: () => Promise<any>) => {
  console.log('🔐 [PERF] Testing login performance...');
  perfTracker.startTimer('Login Flow');
  
  try {
    const result = await loginFunction();
    perfTracker.endTimer('Login Flow', true);
    return result;
  } catch (error) {
    perfTracker.endTimer('Login Flow', false, error instanceof Error ? error.message : 'Unknown error');
    throw error;
  }
};

// Tab switch performance test
export const testTabSwitchPerformance = (tabName: string, switchFunction: () => void) => {
  console.log(`📱 [PERF] Testing ${tabName} tab switch...`);
  perfTracker.startTimer(`Tab Switch ${tabName}`);
  
  try {
    switchFunction();
    // Use setTimeout to measure the time until the tab is fully rendered
    setTimeout(() => {
      perfTracker.endTimer(`Tab Switch ${tabName}`, true);
    }, 100); // Small delay to allow rendering
  } catch (error) {
    perfTracker.endTimer(`Tab Switch ${tabName}`, false, error instanceof Error ? error.message : 'Unknown error');
  }
};

// GraphQL query performance test
export const testQueryPerformance = async <T>(
  queryName: string, 
  queryFunction: () => Promise<T>
): Promise<T> => {
  console.log(`🔍 [PERF] Testing ${queryName} query...`);
  perfTracker.startTimer(`Query ${queryName}`);
  
  try {
    const result = await queryFunction();
    perfTracker.endTimer(`Query ${queryName}`, true);
    return result;
  } catch (error) {
    perfTracker.endTimer(`Query ${queryName}`, false, error instanceof Error ? error.message : 'Unknown error');
    throw error;
  }
};

export default perfTracker;
