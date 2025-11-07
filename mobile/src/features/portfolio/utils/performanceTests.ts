/**
 * Performance testing utilities for portfolio components
 * Phase 3: Measure render times, ensure SLOs met
 */

/**
 * Performance marker for measuring render times
 */
export function markPerformance(label: string): void {
  if (__DEV__ && typeof performance !== 'undefined' && performance.mark) {
    performance.mark(`${label}-start`);
  }
}

/**
 * Measure performance between two marks
 */
export function measurePerformance(label: string): number | null {
  // Check for web Performance API (not available in React Native)
  if (__DEV__ && typeof performance !== 'undefined' && performance.measure && performance.getEntriesByName) {
    try {
      performance.mark(`${label}-end`);
      performance.measure(label, `${label}-start`, `${label}-end`);
      
      const entries = performance.getEntriesByName(label);
      if (entries.length > 0) {
        const duration = entries[entries.length - 1].duration;
        console.log(`[Performance] ${label}: ${duration.toFixed(2)}ms`);
        return duration;
      }
    } catch (e) {
      // Silently fail in React Native - performance API not available
      if (typeof window !== 'undefined') {
        console.warn(`[Performance] Could not measure ${label}:`, e);
      }
    }
  }
  return null;
}

/**
 * Measure component render time
 * Usage: useEffect(() => { const end = measureRenderStart('PortfolioHoldings'); return () => end(); });
 */
export function measureRenderStart(componentName: string): () => void {
  markPerformance(`${componentName}-render`);
  return () => {
    measurePerformance(`${componentName}-render`);
  };
}

/**
 * SLO targets
 */
export const PERFORMANCE_SLOS = {
  PORTFOLIO_HOLDINGS_RENDER_MS: 120, // p95 target
  CHART_RENDER_MS: 200,
  SWIPE_ACTION_RESPONSE_MS: 50,
  DATA_LOADING_MS: 500,
};

/**
 * Check if performance meets SLO
 */
export function checkSLO(metric: keyof typeof PERFORMANCE_SLOS, actualMs: number): boolean {
  const target = PERFORMANCE_SLOS[metric];
  return actualMs <= target;
}

/**
 * Log SLO compliance
 */
export function logSLOCompliance(metric: keyof typeof PERFORMANCE_SLOS, actualMs: number): void {
  const compliant = checkSLO(metric, actualMs);
  const emoji = compliant ? '✅' : '⚠️';
  const status = compliant ? 'PASS' : 'FAIL';
  
  console.log(
    `${emoji} [SLO] ${metric}: ${actualMs.toFixed(2)}ms / ${PERFORMANCE_SLOS[metric]}ms target (${status})`
  );
}

