import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { MockedProvider, MockedResponse } from '@apollo/client/testing';
import LoanManagementModal from '../components/crypto/LoanManagementModal';
import { GET_CRYPTO_SBLOC_LOANS_BY_SYMBOL } from '../graphql/cryptoQueries';

type Props = React.ComponentProps<typeof LoanManagementModal>;

const mockLoans: MockedResponse = {
  request: { query: GET_CRYPTO_SBLOC_LOANS_BY_SYMBOL, variables: { symbol: 'BTC' } },
  result: {
    data: {
      cryptoSblocLoans: [
        {
          id: 'loan_1',
          status: 'ACTIVE',
          collateralQuantity: '0.5',
          collateralValueAtLoan: 30000,
          loanAmount: 15000,
          interestRate: '0.08',
          maintenanceMargin: '0.4',
          liquidationThreshold: '0.5',
          createdAt: '2024-01-15T10:00:00Z',
          updatedAt: '2024-01-20T14:30:00Z',
          cryptocurrency: {
            id: 'btc',
            symbol: 'BTC',
            name: 'Bitcoin',
          },
        },
        {
          id: 'loan_2',
          status: 'WARNING',
          collateralQuantity: '0.1',
          collateralValueAtLoan: 6000,
          loanAmount: 5500,
          interestRate: '0.12',
          maintenanceMargin: '0.4',
          liquidationThreshold: '0.5',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-20T14:30:00Z',
          cryptocurrency: {
            id: 'btc',
            symbol: 'BTC',
            name: 'Bitcoin',
          },
        },
      ],
    },
  },
};

const emptyLoans: MockedResponse = {
  request: { query: GET_CRYPTO_SBLOC_LOANS_BY_SYMBOL, variables: { symbol: 'ETH' } },
  result: {
    data: {
      cryptoSblocLoans: [],
    },
  },
};

const meta: Meta<Props> = {
  title: 'Crypto/LoanManagementModal',
  component: LoanManagementModal,
  decorators: [
    (Story) => (
      <MockedProvider addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
  argTypes: {
    visible: { control: 'boolean' },
    symbol: { control: 'text' },
  },
  args: {
    visible: true,
    symbol: 'BTC',
    onClose: () => console.log('Modal closed'),
    onAddCollateral: (loanId: string, symbol: string) => console.log(`Add collateral for ${symbol} loan ${loanId}`),
    onRepayConfirm: (loanId: string, symbol: string, amountUsd: number) => console.log(`Repay ${amountUsd} USD for ${symbol} loan ${loanId}`),
    isRepaying: false,
  },
};
export default meta;

type Story = StoryObj<Props>;

export const Default: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[mockLoans]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Empty: Story = {
  args: {
    symbol: 'ETH',
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[emptyLoans]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Repaying: Story = {
  args: {
    isRepaying: true,
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[mockLoans]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Hidden: Story = {
  args: {
    visible: false,
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[mockLoans]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Ethereum: Story = {
  args: {
    symbol: 'ETH',
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[{
        request: { query: GET_CRYPTO_SBLOC_LOANS_BY_SYMBOL, variables: { symbol: 'ETH' } },
        result: {
          data: {
            cryptoSblocLoans: [
              {
                id: 'loan_3',
                status: 'ACTIVE',
                collateralQuantity: '10.0',
                collateralValueAtLoan: 32000,
                loanAmount: 16000,
                interestRate: '0.09',
                maintenanceMargin: '0.4',
                liquidationThreshold: '0.5',
                createdAt: '2024-01-10T09:00:00Z',
                updatedAt: '2024-01-20T14:30:00Z',
                cryptocurrency: {
                  id: 'eth',
                  symbol: 'ETH',
                  name: 'Ethereum',
                },
              },
            ],
          },
        },
      }]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};
