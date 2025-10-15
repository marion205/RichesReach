// Input validation schemas for crypto operations
import { z } from 'zod';

// Symbol validation (uppercase, 2-10 chars, alphanumeric)
export const symbolSchema = z.string()
  .regex(/^[A-Z0-9]{2,10}$/, 'Invalid symbol format')
  .min(2, 'Symbol too short')
  .max(10, 'Symbol too long');

// Trade type validation
export const tradeTypeSchema = z.enum(['BUY', 'SELL'], {
  errorMap: () => ({ message: 'Trade type must be BUY or SELL' })
});

// Order type validation
export const orderTypeSchema = z.enum(['MARKET', 'LIMIT', 'STOP_MARKET', 'STOP_LIMIT', 'TAKE_PROFIT_LIMIT'], {
  errorMap: () => ({ message: 'Invalid order type' })
});

// Time in force validation
export const timeInForceSchema = z.enum(['GTC', 'IOC', 'FOK', 'DAY'], {
  errorMap: () => ({ message: 'Invalid time in force' })
});

// Quantity validation (positive, reasonable range)
export const quantitySchema = z.number()
  .positive('Quantity must be positive')
  .max(1000000, 'Quantity too large')
  .refine(val => Number.isFinite(val), 'Quantity must be a valid number');

// Price validation (positive, reasonable range)
export const priceSchema = z.number()
  .positive('Price must be positive')
  .max(1000000, 'Price too large')
  .refine(val => Number.isFinite(val), 'Price must be a valid number');

// Trade execution schema
export const executeTradeSchema = z.object({
  symbol: symbolSchema,
  tradeType: tradeTypeSchema,
  quantity: quantitySchema,
  orderType: orderTypeSchema,
  timeInForce: timeInForceSchema,
  pricePerUnit: priceSchema.optional(),
  triggerPrice: priceSchema.optional(),
  clientOrderId: z.string().optional(),
}).refine(
  (data) => {
    // LIMIT orders require pricePerUnit
    if (data.orderType === 'LIMIT' && !data.pricePerUnit) {
      return false;
    }
    // STOP orders require triggerPrice
    if (data.orderType.startsWith('STOP') && !data.triggerPrice) {
      return false;
    }
    return true;
  },
  {
    message: 'Order type requirements not met',
    path: ['orderType']
  }
);

// SBLOC loan creation schema
export const createSblocLoanSchema = z.object({
  symbol: symbolSchema,
  collateralQuantity: quantitySchema,
  loanAmount: z.number()
    .positive('Loan amount must be positive')
    .max(10000000, 'Loan amount too large'),
});

// SBLOC loan repayment schema
export const repaySblocLoanSchema = z.object({
  loanId: z.string().min(1, 'Loan ID required'),
  amountUsd: z.number()
    .positive('Amount must be positive')
    .max(10000000, 'Amount too large'),
});

// Portfolio query schema
export const portfolioQuerySchema = z.object({
  includeRisk: z.boolean().optional().default(true),
  includeHoldings: z.boolean().optional().default(true),
  includeAnalytics: z.boolean().optional().default(true),
});

// ML prediction schema
export const mlPredictionSchema = z.object({
  symbol: symbolSchema,
  horizon: z.enum(['1h', '4h', '1d', '1w']).optional().default('1d'),
  features: z.array(z.string()).optional(),
});

// Validation helper functions
export function validateTradeInput(input: unknown) {
  return executeTradeSchema.safeParse(input);
}

export function validateSblocLoanInput(input: unknown) {
  return createSblocLoanSchema.safeParse(input);
}

export function validateRepayInput(input: unknown) {
  return repaySblocLoanSchema.safeParse(input);
}

// Error formatting
export function formatValidationError(error: z.ZodError): string {
  return error.errors
    .map(err => `${err.path.join('.')}: ${err.message}`)
    .join(', ');
}

// Type exports for use in components
export type ExecuteTradeInput = z.infer<typeof executeTradeSchema>;
export type CreateSblocLoanInput = z.infer<typeof createSblocLoanSchema>;
export type RepaySblocLoanInput = z.infer<typeof repaySblocLoanSchema>;
export type PortfolioQueryInput = z.infer<typeof portfolioQuerySchema>;
export type MLPredictionInput = z.infer<typeof mlPredictionSchema>;
