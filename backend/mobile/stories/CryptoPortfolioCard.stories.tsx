import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import CryptoPortfolioCard from '../src/components/crypto/CryptoPortfolioCard';

type Props = React.ComponentProps<typeof CryptoPortfolioCard>;

const onRefresh = () => console.log('Refresh portfolio');
const onPressHolding = (symbol: string) => console.log(`Pressed ${symbol}`);
const onStartTrading = () => console.log('Start trading');

const mockPortfolio = {
  total_value_usd: 15000.5,
  total_pnl: 2500.75,
  total_pnl_percentage: 20.0,
  total_pnl_1d: 150.25,
  total_pnl_pct_1d: 1.0,
  total_pnl_1w: 800.5,
  total_pnl_pct_1w: 5.6,
  total_pnl_1m: 2000.25,
  total_pnl_pct_1m: 15.4,
  holdings: [
    { cryptocurrency: { symbol: 'BTC' }, quantity: 0.25, current_value: 11250.0, unrealized_pnl_percentage: 12.5 },
    { cryptocurrency: { symbol: 'ETH' }, quantity: 2.0, current_value: 6400.0, unrealized_pnl_percentage: 8.3 },
    { cryptocurrency: { symbol: 'SOL' }, quantity: 50.0, current_value: 7500.0, unrealized_pnl_percentage: -5.2 },
  ],
};

const mockAnalytics = {
  portfolio_volatility: 0.045,
  sharpe_ratio: 1.8,
  max_drawdown: 0.15,
  diversification_score: 75.0,
  sector_allocation: { LOW: 25.0, MEDIUM: 40.0, HIGH: 30.0, EXTREME: 5.0 },
  best_performer: { symbol: 'BTC', pnl_percentage: 12.5 },
  worst_performer: { symbol: 'SOL', pnl_percentage: -5.2 },
};

const meta: Meta<Props> = {
  title: 'Crypto/CryptoPortfolioCard',
  component: CryptoPortfolioCard,
  argTypes: {
    hideBalances: { control: 'boolean' },
    ltvState: { control: 'radio', options: ['SAFE', 'CAUTION', 'AT_RISK', 'DANGER', undefined] },
  },
  args: {
    portfolio: mockPortfolio,
    analytics: mockAnalytics,
    loading: false,
    hideBalances: false,
    ltvState: 'SAFE',
    onRefresh,
    onPressHolding,
    onStartTrading,
    onToggleHideBalances: undefined,
  },
};
export default meta;

type Story = StoryObj<Props>;

export const Default: Story = {};
export const WithMaskedBalances: Story = { args: { hideBalances: true } };
export const Loading: Story = { args: { loading: true } };
export const Empty: Story = { args: { portfolio: null as unknown as typeof mockPortfolio } };
export const WithoutAnalytics: Story = { args: { analytics: null as unknown as typeof mockAnalytics } };

export const LargePortfolio: Story = {
  args: {
    portfolio: {
      ...mockPortfolio,
      holdings: Array.from({ length: 20 }, (_, i) => ({
        cryptocurrency: { symbol: `COIN${i + 1}` },
        quantity: Math.random() * 100,
        current_value: Math.random() * 10000,
        unrealized_pnl_percentage: (Math.random() - 0.5) * 40,
      })),
    },
  },
};

export const NegativePerformance: Story = {
  args: {
    portfolio: {
      ...mockPortfolio,
      total_pnl: -1500.25,
      total_pnl_percentage: -10.0,
      total_pnl_1d: -50.75,
      total_pnl_pct_1d: -0.3,
      holdings: mockPortfolio.holdings.map(h => ({
        ...h,
        unrealized_pnl_percentage: -Math.abs(h.unrealized_pnl_percentage),
      })),
    },
  },
};

export const HighRiskPortfolio: Story = {
  args: {
    analytics: {
      ...mockAnalytics,
      portfolio_volatility: 0.12,
      sharpe_ratio: 0.8,
      max_drawdown: 0.35,
      diversification_score: 45.0,
      sector_allocation: { LOW: 5.0, MEDIUM: 15.0, HIGH: 50.0, EXTREME: 30.0 },
    },
    ltvState: 'AT_RISK',
  },
};

export const ConservativePortfolio: Story = {
  args: {
    analytics: {
      ...mockAnalytics,
      portfolio_volatility: 0.02,
      sharpe_ratio: 2.5,
      max_drawdown: 0.05,
      diversification_score: 90.0,
      sector_allocation: { LOW: 60.0, MEDIUM: 35.0, HIGH: 5.0, EXTREME: 0.0 },
    },
    ltvState: 'SAFE',
  },
};

export const Interactive: Story = {
  render: (args: any) => {
    const [hide, setHide] = React.useState<boolean>(!!args.hideBalances);
    return <CryptoPortfolioCard {...args} hideBalances={hide} onToggleHideBalances={setHide} />;
  },
};