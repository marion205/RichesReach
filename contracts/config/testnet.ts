/**
 * Testnet Configuration
 * Defines limits and constants for testnet operations
 */

/**
 * Maximum testnet MATIC that can be requested from Polygon Support
 * Polygon's limit: 100 MATIC per project every 90 days
 */
export const MAX_POLYGON_TESTNET_MATIC = 100;

/**
 * Minimum safe balance for deployment (in MATIC)
 * Deployment costs ~0.2 MATIC, so 0.5 is a safe minimum
 */
export const MIN_SAFE_BALANCE_MATIC = 0.5;

/**
 * Default request amount for testnet MATIC
 * Always clamped to MAX_POLYGON_TESTNET_MATIC
 */
export const DEFAULT_MATIC_REQUEST_AMOUNT = 100;

/**
 * Get the safe MATIC request amount
 * Clamps any input to the maximum allowed by Polygon
 * 
 * @param requestedAmount - Amount requested (from env or user input)
 * @returns Clamped amount that never exceeds MAX_POLYGON_TESTNET_MATIC
 */
export function getSafeMaticRequestAmount(requestedAmount?: number | string): number {
  const rawAmount = requestedAmount 
    ? Number(requestedAmount) 
    : DEFAULT_MATIC_REQUEST_AMOUNT;
  
  // Clamp to maximum allowed
  const clamped = Math.min(rawAmount, MAX_POLYGON_TESTNET_MATIC);
  
  // Ensure positive
  if (clamped <= 0) {
    throw new Error(`MATIC request amount must be > 0, got: ${rawAmount}`);
  }
  
  return clamped;
}

/**
 * Validate MATIC request amount
 * Throws if amount exceeds maximum
 */
export function validateMaticRequestAmount(amount: number | string): void {
  const numAmount = Number(amount);
  
  if (numAmount > MAX_POLYGON_TESTNET_MATIC) {
    throw new Error(
      `Requested amount (${numAmount}) exceeds Polygon's limit of ${MAX_POLYGON_TESTNET_MATIC} MATIC per 90 days. ` +
      `Please request ${MAX_POLYGON_TESTNET_MATIC} or less.`
    );
  }
  
  if (numAmount <= 0) {
    throw new Error(`Requested amount must be > 0, got: ${numAmount}`);
  }
}

