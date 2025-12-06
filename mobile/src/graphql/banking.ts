import { gql } from '@apollo/client';

export const GET_BUDGET_DATA = gql`
  query GetBudgetData {
    budgetData {
      monthlyIncome
      monthlyExpenses
      categories {
        name
        budgeted
        spent
        percentage
      }
      remaining
      savingsRate
    }
  }
`;

export const GET_SPENDING_ANALYSIS = gql`
  query GetSpendingAnalysis($period: String!) {
    spendingAnalysis(period: $period) {
      totalSpent
      categories {
        name
        amount
        percentage
        transactions
        trend
      }
      topMerchants {
        name
        amount
        count
      }
      trends {
        period
        amount
        change
      }
    }
  }
`;

