import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { MockedProvider, MockedResponse } from '@apollo/client/testing';
import CryptoTradingCard from '../components/crypto/CryptoTradingCard';
import { GET_SUPPORTED_CURRENCIES, GET_CRYPTO_PRICE } from '../graphql/cryptoQueries';

type Props = React.ComponentProps<typeof CryptoTradingCard>;

const baseCurrencies: MockedResponse = {
  request: { query: GET_SUPPORTED_CURRENCIES },
  result: { 
    data: { 
      supportedCurrencies: [
        { symbol: 'BTC', name: 'Bitcoin' },
        { symbol: 'ETH', name: 'Ethereum' },
        { symbol: 'SOL', name: 'Solana' },
        { symbol: 'ADA', name: 'Cardano' },
        { symbol: 'DOT', name: 'Polkadot' },
      ] 
    } 
  },
};

const btcPrice: MockedResponse = {
  request: { query: GET_CRYPTO_PRICE, variables: { symbol: 'BTC' } },
  result: {
    data: {
      cryptoPrice: {
        priceUsd: 67000.50,
        priceChangePercentage24h: 2.5,
        volume24h: 25000000000,
        marketCap: 1300000000000,
        __typename: 'CryptoPrice',
      },
    },
  },
};

const ethPrice: MockedResponse = {
  request: { query: GET_CRYPTO_PRICE, variables: { symbol: 'ETH' } },
  result: {
    data: {
      cryptoPrice: {
        priceUsd: 3400.25,
        priceChangePercentage24h: -1.2,
        volume24h: 15000000000,
        marketCap: 400000000000,
        __typename: 'CryptoPrice',
      },
    },
  },
};

const solPrice: MockedResponse = {
  request: { query: GET_CRYPTO_PRICE, variables: { symbol: 'SOL' } },
  result: {
    data: {
      cryptoPrice: {
        priceUsd: 150.75,
        priceChangePercentage24h: 5.8,
        volume24h: 3000000000,
        marketCap: 70000000000,
        __typename: 'CryptoPrice',
      },
    },
  },
};

const meta: Meta<Props> = {
  title: 'Crypto/CryptoTradingCard',
  component: CryptoTradingCard,
  decorators: [
    (Story) => (
      <MockedProvider addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
  argTypes: {
    usdAvailable: { control: 'number' },
  },
  args: {
    onTradeSuccess: () => console.log('Trade successful!'),
    usdAvailable: 10000,
  },
};
export default meta;

type Story = StoryObj<Props>;

export const Default: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[baseCurrencies, btcPrice]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const WithBalances: Story = {
  args: {
    balances: {
      BTC: 0.25,
      ETH: 2.0,
      SOL: 50.0,
    },
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[baseCurrencies, btcPrice]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Ethereum: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[baseCurrencies, ethPrice]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Solana: Story = {
  decorators: [
    (Story) => (
      <MockedProvider mocks={[baseCurrencies, solPrice]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const HighBalance: Story = {
  args: {
    balances: {
      BTC: 5.0,
      ETH: 100.0,
      SOL: 1000.0,
      ADA: 5000.0,
      DOT: 200.0,
    },
    usdAvailable: 500000,
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[baseCurrencies, btcPrice]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const LowBalance: Story = {
  args: {
    balances: {
      BTC: 0.001,
      ETH: 0.01,
      SOL: 0.1,
    },
    usdAvailable: 100,
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[baseCurrencies, btcPrice]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const NoBalance: Story = {
  args: {
    balances: {},
    usdAvailable: 0,
  },
  decorators: [
    (Story) => (
      <MockedProvider mocks={[baseCurrencies, btcPrice]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};
