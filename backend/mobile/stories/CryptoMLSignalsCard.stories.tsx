import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { MockedProvider, MockedResponse } from '@apollo/client/testing';
import CryptoMLSignalsCard from '../components/crypto/CryptoMLSignalsCard';
import { GET_SUPPORTED_CURRENCIES, GET_CRYPTO_ML_SIGNAL } from '../graphql/cryptoQueries';

type Props = React.ComponentProps<typeof CryptoMLSignalsCard>;

const baseCurrencies: MockedResponse = {
  request: { query: GET_SUPPORTED_CURRENCIES },
  result: { data: { supportedCurrencies: [{ symbol: 'BTC' }, { symbol: 'ETH' }, { symbol: 'SOL' }] } },
};

const now = () => new Date().toISOString();
const plus6h = () => new Date(Date.now() + 6 * 3600_000).toISOString();

const bullishSignal: MockedResponse = {
  request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'BTC' } },
  result: {
    data: {
      cryptoMlSignal: {
        symbol: 'BTC',
        predictionType: 'BIG_UP_DAY',
        probability: 0.78,
        confidenceLevel: 'HIGH',
        sentiment: 'Bullish',
        sentimentDescription: 'Breadth, momentum, and funding trending positive.',
        featuresUsed: { rsi_14: 65.1, macd_signal: 0.42, volume_z: 1.3 },
        createdAt: now(),
        expiresAt: plus6h(),
        explanation: 'Price above MA200 with rising OBV; volatility contraction breakout.',
        __typename: 'CryptoMlSignal',
      },
    },
  },
};

const neutralSignal: MockedResponse = {
  request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'ETH' } },
  result: {
    data: {
      cryptoMlSignal: {
        symbol: 'ETH',
        predictionType: 'NEUTRAL',
        probability: 0.48,
        confidenceLevel: 'MEDIUM',
        sentiment: 'Neutral',
        sentimentDescription: 'Mixed signals; wait for confirmation.',
        featuresUsed: { rsi_14: 49.2, vol_10d: 0.032 },
        createdAt: now(),
        expiresAt: plus6h(),
        explanation: 'Range-bound regime; no strong catalyst.',
        __typename: 'CryptoMlSignal',
      },
    },
  },
};

const bearishSignal: MockedResponse = {
  request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'SOL' } },
  result: {
    data: {
      cryptoMlSignal: {
        symbol: 'SOL',
        predictionType: 'BIG_DOWN_DAY',
        probability: 0.65,
        confidenceLevel: 'MEDIUM',
        sentiment: 'Bearish',
        sentimentDescription: 'Weakness at key levels and declining momentum.',
        featuresUsed: { rsi_14: 35.2, macd_signal: -0.15, volume_z: 0.8 },
        createdAt: now(),
        expiresAt: plus6h(),
        explanation: 'Breakdown below support with increasing selling pressure.',
        __typename: 'CryptoMlSignal',
      },
    },
  },
};

const loadingMocks: MockedResponse[] = [
  baseCurrencies,
  {
    request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'BTC' } },
    result: new Promise<never>(() => {}), // keep loading
  },
];

const errorMocks: MockedResponse[] = [
  baseCurrencies,
  {
    request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'BTC' } },
    error: new Error('Network error') as any,
  },
];

const meta: Meta<Props> = {
  title: 'Crypto/CryptoMLSignalsCard',
  component: CryptoMLSignalsCard,
  decorators: [
    (Story: any) => (
      <MockedProvider addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
  argTypes: {
    pollInterval: { control: 'number' },
  },
  args: {
    pollInterval: undefined,
  },
};
export default meta;

type Story = StoryObj<Props>;

export const Bullish: Story = {
  decorators: [
    (Story: any) => (
      <MockedProvider mocks={[baseCurrencies, bullishSignal]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Neutral: Story = {
  decorators: [
    (Story: any) => (
      <MockedProvider mocks={[baseCurrencies, neutralSignal]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Bearish: Story = {
  decorators: [
    (Story: any) => (
      <MockedProvider mocks={[baseCurrencies, bearishSignal]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const WithAutoRefresh: Story = {
  args: { pollInterval: 30_000 },
  decorators: [
    (Story: any) => (
      <MockedProvider mocks={[baseCurrencies, bullishSignal]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Loading: Story = {
  decorators: [
    (Story: any) => (
      <MockedProvider mocks={loadingMocks} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Error: Story = {
  decorators: [
    (Story: any) => (
      <MockedProvider mocks={errorMocks} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};

export const Empty: Story = {
  decorators: [
    (Story: any) => (
      <MockedProvider mocks={[baseCurrencies]} addTypename={false}>
        <Story />
      </MockedProvider>
    ),
  ],
};