import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import CollateralHealthCard from '../components/crypto/CollateralHealthCard';

type Props = React.ComponentProps<typeof CollateralHealthCard>;

const mockLoans = [
  {
    id: 'loan_1',
    status: 'ACTIVE',
    collateralQuantity: '0.5',
    loanAmount: '15000',
    cryptocurrency: { symbol: 'BTC' },
  },
  {
    id: 'loan_2',
    status: 'ACTIVE',
    collateralQuantity: '10.0',
    loanAmount: '16000',
    cryptocurrency: { symbol: 'ETH' },
  },
  {
    id: 'loan_3',
    status: 'WARNING',
    collateralQuantity: '100.0',
    loanAmount: '8000',
    cryptocurrency: { symbol: 'SOL' },
  },
];

const priceMap = {
  BTC: 67000,
  ETH: 3400,
  SOL: 150,
};

const highRiskLoans = [
  {
    id: 'loan_4',
    status: 'WARNING',
    collateralQuantity: '0.1',
    loanAmount: '5500',
    cryptocurrency: { symbol: 'BTC' },
  },
  {
    id: 'loan_5',
    status: 'WARNING',
    collateralQuantity: '5.0',
    loanAmount: '12000',
    cryptocurrency: { symbol: 'ETH' },
  },
];

const emptyLoans: any[] = [];

const meta: Meta<Props> = {
  title: 'Crypto/CollateralHealthCard',
  component: CollateralHealthCard,
  argTypes: {
    showPerAsset: { control: 'boolean' },
  },
  args: {
    loans: mockLoans,
    priceMap,
    showPerAsset: true,
    onAssetPress: (symbol: string) => console.log(`Pressed ${symbol}`),
  },
};
export default meta;

type Story = StoryObj<Props>;

export const Default: Story = {};

export const HighRisk: Story = {
  args: {
    loans: highRiskLoans,
  },
};

export const Empty: Story = {
  args: {
    loans: emptyLoans,
  },
};

export const WithoutPerAsset: Story = {
  args: {
    showPerAsset: false,
  },
};

export const SingleAsset: Story = {
  args: {
    loans: [mockLoans[0]],
  },
};

export const ManyAssets: Story = {
  args: {
    loans: [
      ...mockLoans,
      {
        id: 'loan_6',
        status: 'ACTIVE',
        collateralQuantity: '50.0',
        loanAmount: '5000',
        cryptocurrency: { symbol: 'ADA' },
      },
      {
        id: 'loan_7',
        status: 'ACTIVE',
        collateralQuantity: '200.0',
        loanAmount: '3000',
        cryptocurrency: { symbol: 'DOT' },
      },
    ],
    priceMap: {
      ...priceMap,
      ADA: 0.5,
      DOT: 7.5,
    },
  },
};
