import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { MockedProvider, MockedResponse } from '@apollo/client/testing';
import CryptoSBLOCCard from '../components/crypto/CryptoSBLOCCard';
import { GET_CRYPTO_SBLOC_LOANS, GET_CRYPTO_HOLDINGS } from '../graphql/cryptoQueries';

type Props = React.ComponentProps<typeof CryptoSBLOCCard>;

const mockLoans: MockedResponse = {
  request: { query: GET_CRYPTO_SBLOC_LOANS },
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
};

const mockHoldings: MockedResponse = {
  request: { query: GET_CRYPTO_HOLDINGS },
  result: {
    data: {
      cryptoPortfolio: {
        holdings: [
          {
            cryptocurrency: { symbol: 'BTC' },
            quantity: 1.5,
          },
          {
            cryptocurrency: { symbol: 'ETH' },
            quantity: 25.0,
          },
          {
            cryptocurrency: { symbol: 'SOL' },
            quantity: 100.0,
          },
        ],
      },
    },
  },
};

const highRiskLoans: MockedResponse = {
  request: { query: GET_CRYPTO_SBLOC_LOANS },
  result: {
    data: {
      cryptoSblocLoans: [
        {
          id: 'loan_3',
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
  request: { query: GET_CRYPTO_SBLOC_LOANS },
  result: {
    data: {
      cryptoSblocLoans: [],
    },
  },
};

const meta: Meta<Props> = {
  title: 'Crypto/CryptoSBLOCCard',
  component: CryptoSBLOCCard,
  decorators: [
    (Story) => (
      <MockedProvider addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
  argTypes: {
    targetLtv: { control: { type: 'range', min: 0, max: 50, step: 5 } },
  },
  args: {
    onTopUpCollateral: () => console.log('Top up collateral'),
    onStartLoan: () => console.log('Start new loan'),
  },
};
export default meta;

type Story = StoryObj<Props>;

export const Default: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[mockLoans, mockHoldings]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const HighRisk: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[highRiskLoans, mockHoldings]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Empty: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[emptyLoans, mockHoldings]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const NoHoldings: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[mockLoans, { request: { query: GET_CRYPTO_HOLDINGS }, result: { data: { cryptoPortfolio: { holdings: [] } } } }]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const ConservativeTarget: Story = {
  args: { targetLtv: 25 },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[mockLoans, mockHoldings]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const AggressiveTarget: Story = {
  args: { targetLtv: 45 },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[mockLoans, mockHoldings]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};
