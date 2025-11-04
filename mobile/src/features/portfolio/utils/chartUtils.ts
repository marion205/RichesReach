/**
 * Chart utility functions for portfolio performance
 * Fixes -100% ticks, scales y-axis properly, formats ticks
 */

type Point = { t: number; v: number }; // t=epoch ms, v=value OR return

const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));

/**
 * Compute sensible y-axis domain that prevents weird -100% ticks
 */
export function computeYDomain(points: Point[], isPercent: boolean): [number, number] {
  if (!points?.length) return [0, 1];

  const vals = points.map(p => p.v);
  let min = Math.min(...vals);
  let max = Math.max(...vals);

  if (isPercent) {
    // Prevent silly axes (e.g., -100% if one bad point)
    const band = Math.max(Math.abs(min), Math.abs(max));
    const pad = band * 0.15;
    
    // Clamp to reasonable bounds for percentage returns
    min = clamp(min - pad, -0.5, 0.5); // -50% to +50%
    max = clamp(max + pad, -0.5, 0.5);
    
    // If min and max are too close, center around zero
    if (max - min < 0.02) {
      const center = (min + max) / 2;
      min = clamp(center - 0.1, -0.5, 0.5);
      max = clamp(center + 0.1, -0.5, 0.5);
    }
  } else {
    // For dollar values, add 10% padding
    const pad = (max - min) * 0.1 || 1;
    min = Math.max(0, min - pad); // Don't go below 0 for dollar values
    max += pad;
  }

  return [min, max];
}

/**
 * Format tick labels appropriately
 */
export const tickFormat = (isPercent: boolean) => (d: number): string => {
  if (isPercent) {
    const pct = d * 100;
    return `${pct >= 0 ? '+' : ''}${pct.toFixed(Math.abs(pct) < 10 ? 1 : 0)}%`;
  } else {
    // Format dollar values
    if (d >= 1000000) {
      return `$${(d / 1000000).toFixed(1)}M`;
    } else if (d >= 1000) {
      return `$${(d / 1000).toFixed(1)}K`;
    } else {
      return `$${d.toFixed(0)}`;
    }
  }
};

/**
 * Calculate period return label (e.g., "+4.2% / 30D")
 */
export function getPeriodReturnLabel(
  startValue: number,
  endValue: number,
  periodDays: number
): string {
  if (!startValue || startValue === 0) return '0.00%';
  
  const returnPercent = ((endValue - startValue) / startValue) * 100;
  const sign = returnPercent >= 0 ? '+' : '';
  const periodLabel = periodDays === 1 ? '1D' : periodDays === 7 ? '1W' : 
                      periodDays === 30 ? '1M' : periodDays === 90 ? '3M' :
                      periodDays === 365 ? '1Y' : `${periodDays}D`;
  
  return `${sign}${returnPercent.toFixed(2)}% / ${periodLabel}`;
}

