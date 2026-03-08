/**
 * Demo opportunity catalog — curated across Real Estate, Alternatives, Fixed Income.
 * Used by demoOpportunityDiscoveryService.
 * Replace with API-backed data by swapping the service instance.
 */
import type { Opportunity } from '../types/opportunityTypes';

export const DEMO_OPPORTUNITIES: Opportunity[] = [
  // ── Fixed Income ──────────────────────────────────────────────────────────
  {
    id: 'fi_1',
    assetClass: 'fixed_income',
    name: '3-Month Treasury Bills',
    tagline: 'Risk-free short-term yield',
    score: 85,
    category: 'treasury',
    minimumInvestment: 100,
    expectedReturnRange: '4.5–5.5%',
    liquidity: 'daily',
    riskLevel: 'low',
    graphRationale:
      'A zero-risk position that pairs well with your emergency fund strategy — freed cash from debt payoff can go here first.',
    graphEdgeIds: ['emergency_fund_to_risk_capacity', 'credit_utilization_to_borrowing_power'],
  },
  {
    id: 'fi_2',
    assetClass: 'fixed_income',
    name: 'High-Yield CDs (18-Month)',
    tagline: 'FDIC-insured, above-market rate',
    score: 82,
    category: 'cd',
    minimumInvestment: 1000,
    expectedReturnRange: '4.8–5.3%',
    liquidity: 'illiquid',
    riskLevel: 'low',
    graphRationale:
      'With your emergency fund at 4+ months, locking up $1k+ for 18 months is safe — and FDIC-backed.',
    graphEdgeIds: ['emergency_fund_to_risk_capacity'],
  },
  {
    id: 'fi_3',
    assetClass: 'fixed_income',
    name: '5-Year Bond Ladder',
    tagline: 'Staggered maturities, predictable income',
    score: 80,
    category: 'bond_ladder',
    minimumInvestment: 5000,
    expectedReturnRange: '4–5%',
    liquidity: 'quarterly',
    riskLevel: 'low',
    graphRationale:
      'Your credit profile qualifies you to use these bonds as collateral for a securities-backed line of credit.',
    graphEdgeIds: ['credit_utilization_to_borrowing_power'],
  },
  {
    id: 'fi_4',
    assetClass: 'fixed_income',
    name: 'I-Bonds (Inflation-Linked)',
    tagline: 'Government-backed inflation protection',
    score: 77,
    category: 'treasury',
    minimumInvestment: 25,
    expectedReturnRange: '3.5–6%',
    liquidity: 'illiquid',
    riskLevel: 'low',
  },

  // ── Real Estate ───────────────────────────────────────────────────────────
  {
    id: 're_1',
    assetClass: 'real_estate',
    name: 'Vanguard Real Estate ETF (VNQ)',
    tagline: 'Broad REIT exposure, daily liquidity',
    score: 78,
    category: 'reit',
    minimumInvestment: 1,
    expectedReturnRange: '5–8%',
    liquidity: 'daily',
    riskLevel: 'moderate',
    graphRationale:
      'With $230/month in investable surplus, a liquid REIT lets you build real estate exposure incrementally — no lock-up.',
    graphEdgeIds: ['debt_to_investable_surplus'],
  },
  {
    id: 're_2',
    assetClass: 'real_estate',
    name: 'Fundrise eREIT',
    tagline: 'Private real estate, quarterly liquidity',
    score: 71,
    category: 'reit',
    minimumInvestment: 10,
    expectedReturnRange: '8–12%',
    liquidity: 'quarterly',
    riskLevel: 'moderate',
    graphRationale:
      'Your 4-month emergency fund supports the quarterly lock-up period. A $10 minimum makes this easy to start.',
    graphEdgeIds: ['emergency_fund_to_risk_capacity'],
  },
  {
    id: 're_3',
    assetClass: 'real_estate',
    name: 'Arrived Homes (Fractional Rental)',
    tagline: 'Single-family rental income from $100',
    score: 69,
    category: 'reit',
    minimumInvestment: 100,
    expectedReturnRange: '5–7%',
    liquidity: 'quarterly',
    riskLevel: 'moderate',
  },

  // ── Alternatives ──────────────────────────────────────────────────────────
  {
    id: 'alt_1',
    assetClass: 'alternatives',
    name: 'iShares Gold ETF (IAU)',
    tagline: 'Commodity hedge against inflation',
    score: 68,
    category: 'commodity',
    minimumInvestment: 1,
    expectedReturnRange: '0–6% (inflation hedge)',
    liquidity: 'daily',
    riskLevel: 'moderate',
    graphRationale:
      'At your $41k annual wealth velocity, adding a 3–5% gold allocation provides macro diversification at minimal cost.',
    graphEdgeIds: ['income_savings_wealth_velocity'],
  },
  {
    id: 'alt_2',
    assetClass: 'alternatives',
    name: 'Bloomberg Commodity ETF (PDBC)',
    tagline: 'Diversified commodity basket',
    score: 65,
    category: 'commodity',
    minimumInvestment: 1,
    expectedReturnRange: '2–8%',
    liquidity: 'daily',
    riskLevel: 'moderate',
  },
];
