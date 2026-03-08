/**
 * Demo Financial Intelligence Graph data.
 * Used by demoOpportunityDiscoveryService when the backend is not connected.
 * Reflects a realistic mid-career user scenario.
 */
import type { FinancialGraph } from '../types/opportunityTypes';

export const DEMO_FINANCIAL_GRAPH: FinancialGraph = {
  userId: 0,
  edges: [
    {
      relationshipId: 'debt_to_investable_surplus',
      sourceLabel: 'Credit Card Debt',
      targetLabel: 'Monthly Investable Surplus',
      explanation:
        'Eliminating your $320/month in minimum payments would free that amount to invest each month.',
      numericImpact: 320,
      unit: '$/month',
      direction: 'positive',
      confidence: 0.9,
    },
    {
      relationshipId: 'emergency_fund_to_risk_capacity',
      sourceLabel: 'Emergency Fund',
      targetLabel: 'Investment Risk Capacity',
      explanation:
        'Your $15,000 emergency fund covers 4.2 months of expenses — enough to support moderate-to-high risk positions.',
      numericImpact: 4.2,
      unit: 'months covered',
      direction: 'positive',
      confidence: 0.85,
    },
    {
      relationshipId: 'credit_utilization_to_borrowing_power',
      sourceLabel: 'Credit Utilization',
      targetLabel: 'Borrowing Power',
      explanation:
        'Your 22% credit utilization is good. Reducing it below 10% would unlock better rates and SBLOC access.',
      numericImpact: 22,
      unit: '% utilization',
      direction: 'positive',
      confidence: 0.8,
    },
    {
      relationshipId: 'income_savings_wealth_velocity',
      sourceLabel: 'Monthly Income',
      targetLabel: 'Annual Wealth Velocity',
      explanation:
        'At a 15% savings rate ($450/month), your estimated annual wealth velocity is $41,450 (portfolio growth + contributions).',
      numericImpact: 41450,
      unit: '$/year',
      direction: 'positive',
      confidence: 0.75,
    },
  ],
  summarySentences: [
    'Paying off your credit cards frees $320/month to invest.',
    'Your 4.2-month emergency fund supports moderate-to-high risk positions.',
    'Your 22% utilization qualifies you for competitive borrowing rates.',
    'Your annual wealth velocity is approximately $41,450.',
  ],
  totalCcBalance: 8400,
  totalCcMinPayments: 320,
  totalSavingsBalance: 15000,
  emergencyFundMonths: 4.2,
  avgCreditUtilization: 0.22,
  bestCreditScore: 718,
  estimatedMonthlyIncome: 3000,
  investableSurplusMonthly: 230,
  portfolioTotalValue: 28500,
};
