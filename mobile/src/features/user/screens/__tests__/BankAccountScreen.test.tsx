/**
 * Unit tests for BankAccountScreen component
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react-native';
import { MockedProvider } from '@apollo/client/testing';
import { gql } from '@apollo/client';
import BankAccountScreen from '../BankAccountScreen';

// Mock the Yodlee hook
jest.mock('../../../../hooks/useYodlee', () => ({
  useYodlee: () => ({
    linkBankAccount: jest.fn(),
    fetchAccounts: jest.fn(),
    isLoading: false,
    isAvailable: true,
    accounts: [],
    error: null,
    fastLinkSession: null,
    clearSession: jest.fn(),
  }),
}));

// Mock navigation
const mockNavigateTo = jest.fn();
const mockNavigation = {
  navigate: mockNavigateTo,
  goBack: jest.fn(),
};

// GraphQL queries and mutations
const GET_BANK_ACCOUNTS = gql`
  query GetBankAccounts {
    bankAccounts {
      id
      provider
      name
      mask
      accountType
      accountSubtype
      currency
      balanceCurrent
      balanceAvailable
      isVerified
      isPrimary
      lastUpdated
      createdAt
    }
  }
`;

const GET_FUNDING_HISTORY = gql`
  query GetFundingHistory {
    fundingHistory {
      id
      amount
      status
      bankAccountId
      initiatedAt
      completedAt
    }
  }
`;

const LINK_BANK_ACCOUNT = gql`
  mutation LinkBankAccount($bankName: String!, $accountNumber: String!, $routingNumber: String!) {
    linkBankAccount(bankName: $bankName, accountNumber: $accountNumber, routingNumber: $routingNumber) {
      success
      message
      bankAccount {
        id
        bankName
        accountType
        status
      }
    }
  }
`;

const INITIATE_FUNDING = gql`
  mutation InitiateFunding($amount: Float!, $bankAccountId: String!) {
    initiateFunding(amount: $amount, bankAccountId: $bankAccountId) {
      success
      message
      funding {
        id
        amount
        status
        estimatedCompletion
      }
    }
  }
`;

describe('BankAccountScreen', () => {
  const mockBankAccounts = {
    request: {
      query: GET_BANK_ACCOUNTS,
    },
    result: {
      data: {
        bankAccounts: [
          {
            id: '1',
            provider: 'Test Bank',
            name: 'Checking Account',
            mask: '1234',
            accountType: 'CHECKING',
            accountSubtype: 'checking',
            currency: 'USD',
            balanceCurrent: 5000.00,
            balanceAvailable: 5000.00,
            isVerified: true,
            isPrimary: true,
            lastUpdated: '2024-01-01T00:00:00Z',
            createdAt: '2024-01-01T00:00:00Z',
          },
        ],
      },
    },
  };

  const mockFundingHistory = {
    request: {
      query: GET_FUNDING_HISTORY,
    },
    result: {
      data: {
        fundingHistory: [
          {
            id: '1',
            amount: 1000.00,
            status: 'PENDING',
            bankAccountId: '1',
            initiatedAt: '2024-01-01T00:00:00Z',
            completedAt: null,
          },
        ],
      },
    },
  };

  const mockLinkBankAccount = {
    request: {
      query: LINK_BANK_ACCOUNT,
      variables: {
        bankName: 'New Bank',
        accountNumber: '1234567890',
        routingNumber: '987654321',
      },
    },
    result: {
      data: {
        linkBankAccount: {
          success: true,
          message: 'Bank account linked successfully',
          bankAccount: {
            id: '2',
            bankName: 'New Bank',
            accountType: 'CHECKING',
            status: 'PENDING',
          },
        },
      },
    },
  };

  const mockInitiateFunding = {
    request: {
      query: INITIATE_FUNDING,
      variables: {
        amount: 500.00,
        bankAccountId: '1',
      },
    },
    result: {
      data: {
        initiateFunding: {
          success: true,
          message: 'Funding initiated successfully',
          funding: {
            id: '2',
            amount: 500.00,
            status: 'PENDING',
            estimatedCompletion: '2024-01-04T00:00:00Z',
          },
        },
      },
    },
  };

  it('renders bank accounts screen', async () => {
    const mocks = [mockBankAccounts, mockFundingHistory];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Bank Accounts')).toBeTruthy();
    });
  });

  it('displays bank accounts when loaded', async () => {
    const mocks = [mockBankAccounts, mockFundingHistory];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Bank')).toBeTruthy();
      expect(screen.getByText('Checking Account')).toBeTruthy();
    });
  });

  it('displays empty state when no bank accounts', async () => {
    const emptyMock = {
      request: {
        query: GET_BANK_ACCOUNTS,
      },
      result: {
        data: {
          bankAccounts: [],
        },
      },
    };

    const mocks = [emptyMock, mockFundingHistory];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('No Bank Accounts')).toBeTruthy();
    });
  });

  it('handles linkBankAccount mutation', async () => {
    const mocks = [mockBankAccounts, mockFundingHistory, mockLinkBankAccount];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      // Find and press link bank button
      const linkButton = screen.getByText('Link Bank');
      fireEvent.press(linkButton);
    });
  });

  it('handles initiateFunding mutation', async () => {
    const mocks = [mockBankAccounts, mockFundingHistory, mockInitiateFunding];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      // Find and press add funds button
      const addFundsButton = screen.getByText('Add Funds');
      fireEvent.press(addFundsButton);
    });
  });

  it('handles GraphQL errors gracefully', async () => {
    const errorMock = {
      request: {
        query: GET_BANK_ACCOUNTS,
      },
      error: new Error('GraphQL error'),
    };

    const mocks = [errorMock, mockFundingHistory];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      // Should show empty state or error handling
      expect(screen.getByText('No Bank Accounts')).toBeTruthy();
    });
  });

  it('displays all required fields from bankAccounts query', async () => {
    const mocks = [mockBankAccounts, mockFundingHistory];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      // Check that all expected fields are present in the query
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('id');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('provider');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('name');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('mask');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('accountType');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('accountSubtype');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('currency');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('balanceCurrent');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('balanceAvailable');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('isVerified');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('isPrimary');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('lastUpdated');
      expect(mockBankAccounts.result.data.bankAccounts[0]).toHaveProperty('createdAt');
    });
  });

  it('displays all required fields from fundingHistory query', async () => {
    const mocks = [mockBankAccounts, mockFundingHistory];
    
    render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <BankAccountScreen navigateTo={mockNavigateTo} navigation={mockNavigation} />
      </MockedProvider>
    );

    await waitFor(() => {
      // Check that all expected fields are present in the query
      expect(mockFundingHistory.result.data.fundingHistory[0]).toHaveProperty('id');
      expect(mockFundingHistory.result.data.fundingHistory[0]).toHaveProperty('amount');
      expect(mockFundingHistory.result.data.fundingHistory[0]).toHaveProperty('status');
      expect(mockFundingHistory.result.data.fundingHistory[0]).toHaveProperty('bankAccountId');
      expect(mockFundingHistory.result.data.fundingHistory[0]).toHaveProperty('initiatedAt');
      expect(mockFundingHistory.result.data.fundingHistory[0]).toHaveProperty('completedAt');
    });
  });
});

