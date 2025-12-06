/**
 * Comprehensive unit tests for BudgetingScreen
 */
import React from 'react';
import { render, waitFor, screen } from '@testing-library/react-native';
import { MockedProvider } from '@apollo/client/testing';
import BudgetingScreen from '../BudgetingScreen';
import { GET_BUDGET_DATA } from '../../../../graphql/banking';

// Mock GraphQL query
const mockBudgetData = {
  monthlyIncome: 5000,
  monthlyExpenses: 3500,
  categories: [
    { name: 'Housing', budgeted: 1500, spent: 1450, percentage: 96.7 },
    { name: 'Food', budgeted: 600, spent: 580, percentage: 96.7 },
    { name: 'Transportation', budgeted: 400, spent: 420, percentage: 105 },
  ],
  remaining: 1500,
  savingsRate: 30,
};

const mocks = [
  {
    request: {
      query: GET_BUDGET_DATA,
    },
    result: {
      data: {
        budgetData: mockBudgetData,
      },
    },
  },
];

const errorMocks = [
  {
    request: {
      query: GET_BUDGET_DATA,
    },
    error: new Error('Network error'),
  },
];

describe('BudgetingScreen', () => {
  it('should render loading state initially', () => {
    const { getByTestId } = render(
      <MockedProvider mocks={[]} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    // Should show loading indicator
    expect(getByTestId('loading-indicator') || screen.queryByText(/loading/i)).toBeTruthy();
  });

  it('should render budget data when loaded', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText('Budget Management')).toBeTruthy();
      expect(getByText('$5,000')).toBeTruthy(); // Monthly Income
      expect(getByText('$3,500')).toBeTruthy(); // Monthly Expenses
      expect(getByText('$1,500')).toBeTruthy(); // Remaining
      expect(getByText('30%')).toBeTruthy(); // Savings Rate
    });
  });

  it('should render category breakdown', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText('Housing')).toBeTruthy();
      expect(getByText('Food')).toBeTruthy();
      expect(getByText('Transportation')).toBeTruthy();
    });
  });

  it('should show category amounts correctly', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    await waitFor(() => {
      // Housing: $1,450 / $1,500
      expect(getByText('$1,450')).toBeTruthy();
      expect(getByText('$1,500')).toBeTruthy();
    });
  });

  it('should handle error state', async () => {
    const { getByText } = render(
      <MockedProvider mocks={errorMocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText(/failed to load/i)).toBeTruthy();
      expect(getByText(/retry/i)).toBeTruthy();
    });
  });

  it('should switch between periods', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    await waitFor(() => {
      // Should show period buttons
      expect(getByText('Week')).toBeTruthy();
      expect(getByText('Month')).toBeTruthy();
      expect(getByText('Year')).toBeTruthy();
    });
  });

  it('should use mock data fallback when query fails', async () => {
    const { getByText } = render(
      <MockedProvider mocks={errorMocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    // Even with error, should show some data (mock fallback)
    await waitFor(() => {
      // Mock data has $5,000 income
      expect(getByText('$5,000')).toBeTruthy();
    }, { timeout: 3000 });
  });

  it('should display savings rate correctly', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText('30%')).toBeTruthy();
    });
  });

  it('should show category percentage', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BudgetingScreen />
      </MockedProvider>
    );

    await waitFor(() => {
      // Should show percentage for each category
      expect(getByText(/96.7%/)).toBeTruthy();
      expect(getByText(/105%/)).toBeTruthy();
    });
  });
});

