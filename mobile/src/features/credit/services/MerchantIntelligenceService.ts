/**
 * Merchant Intelligence Service
 * Provides 0% APR financing alternatives and merchant-specific deals
 */

import { MerchantDeal } from '../types/CreditTypes';

// Merchant Intelligence Database (2026 Data)
const MERCHANT_DEALS: Record<string, MerchantDeal> = {
  apple: {
    name: 'Apple Store',
    option: 'Apple Card Monthly Installments',
    benefit: '0% APR for 24 months on purchases $499+',
    impact: 'Zero Interest Leak',
    apr: 0,
    termMonths: 24,
    eligibility: 'Apple Card holders',
  },
  amazon: {
    name: 'Amazon',
    option: 'Affirm / Amazon Store Card',
    benefit: '0% APR for 6-12 months on select purchases',
    impact: 'Protected Score',
    apr: 0,
    termMonths: 12,
    eligibility: 'Qualified buyers',
  },
  bestbuy: {
    name: 'Best Buy',
    option: 'My Best Buy Credit Card',
    benefit: '0% APR for 12-24 months on purchases $299+',
    impact: 'Zero Interest Leak',
    apr: 0,
    termMonths: 18,
    eligibility: 'Best Buy cardholders',
  },
  target: {
    name: 'Target',
    option: 'Target RedCard',
    benefit: '5% discount + 0% APR for 6 months',
    impact: 'Protected Score + Savings',
    apr: 0,
    termMonths: 6,
    eligibility: 'Target RedCard holders',
  },
  home: {
    name: 'Home Depot / Lowe\'s',
    option: 'Store Credit Card',
    benefit: '0% APR for 6-24 months on purchases $299+',
    impact: 'Zero Interest Leak',
    apr: 0,
    termMonths: 12,
    eligibility: 'Store cardholders',
  },
  furniture: {
    name: 'Furniture Stores',
    option: 'Store Financing Programs',
    benefit: '0% APR for 12-48 months on purchases $500+',
    impact: 'Zero Interest Leak',
    apr: 0,
    termMonths: 24,
    eligibility: 'Qualified buyers',
  },
};

/**
 * Get merchant intelligence for a given merchant name or category
 */
export const getMerchantIntelligence = (merchantInput: string): MerchantDeal | null => {
  if (!merchantInput) return null;
  
  const normalized = merchantInput.toLowerCase().trim();
  
  // Direct match
  if (MERCHANT_DEALS[normalized]) {
    return MERCHANT_DEALS[normalized];
  }
  
  // Partial match
  for (const [key, deal] of Object.entries(MERCHANT_DEALS)) {
    if (normalized.includes(key) || deal.name.toLowerCase().includes(normalized)) {
      return deal;
    }
  }
  
  // Category matching
  if (normalized.includes('furniture') || normalized.includes('sofa') || normalized.includes('mattress')) {
    return MERCHANT_DEALS.furniture;
  }
  
  if (normalized.includes('home') || normalized.includes('depot') || normalized.includes('lowe')) {
    return MERCHANT_DEALS.home;
  }
  
  return null;
};

/**
 * Get all available merchant deals
 */
export const getAllMerchantDeals = (): MerchantDeal[] => {
  return Object.values(MERCHANT_DEALS);
};

/**
 * Check if a purchase amount qualifies for 0% financing
 */
export const qualifiesForZeroAPR = (merchant: string, amount: number): boolean => {
  const deal = getMerchantIntelligence(merchant);
  if (!deal) return false;
  
  // Minimum purchase thresholds
  const thresholds: Record<string, number> = {
    apple: 499,
    amazon: 100,
    bestbuy: 299,
    target: 0,
    home: 299,
    furniture: 500,
  };
  
  const key = Object.keys(MERCHANT_DEALS).find(k => 
    MERCHANT_DEALS[k].name.toLowerCase().includes(merchant.toLowerCase())
  );
  
  const threshold = key ? thresholds[key] || 0 : 0;
  return amount >= threshold;
};

