import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { MockedProvider } from '@apollo/client/testing';
import CryptoMLSignalsCard from '../components/crypto/CryptoMLSignalsCard';
import { GET_SUPPORTED_CURRENCIES, GET_CRYPTO_ML_SIGNAL, GENERATE_ML_PREDICTION } from '../graphql/cryptoQueries';

const mocks = [
  {
    request: { query: GET_SUPPORTED_CURRENCIES },
    result: { data: { supportedCurrencies: [{ symbol: 'BTC' }, { symbol: 'ETH' }] } },
  },
  {
    request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'BTC' } },
    result: {
      data: {
        cryptoMlSignal: {
          predictionType: 'BIG_UP_DAY',
          probability: 0.74,
          confidenceLevel: 'HIGH',
          sentiment: 'Bullish',
          sentimentDescription: 'Momentum and breadth improving.',
          featuresUsed: { rsi_14: 62.3, vol_10d: 0.042 },
          createdAt: new Date('2025-01-01T00:00:00Z').toISOString(),
          expiresAt: new Date('2025-01-01T06:00:00Z').toISOString(),
          explanation: 'Breakout above MA with rising volume.',
          __typename: 'CryptoMlSignal'
        }
      }
    }
  },
];

describe('CryptoMLSignalsCard', () => {
  it('renders a signal and matches snapshot', async () => {
    const tree = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <CryptoMLSignalsCard />
      </MockedProvider>
    );

    // waits for probability text to appear
    const prob = await screen.findByText(/74.0%/);
    expect(prob).toBeTruthy();

    // sanity check of key labels
    expect(screen.getByText('AI Analysis')).toBeTruthy();
    expect(tree.toJSON()).toMatchSnapshot();
  });

  it('refresh button can be pressed', async () => {
    const { findByLabelText, findByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <CryptoMLSignalsCard />
      </MockedProvider>
    );
    await findByText(/Probability/);
    const refresh = await findByLabelText('Refresh');
    fireEvent.press(refresh);
  });

  it('renders with auto-refresh when pollInterval is provided', () => {
    const tree = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <CryptoMLSignalsCard pollInterval={30000} />
      </MockedProvider>
    );
    expect(tree.toJSON()).toBeTruthy();
  });

  it('handles missing signal data gracefully', async () => {
    const emptyMocks = [
      {
        request: { query: GET_SUPPORTED_CURRENCIES },
        result: { data: { supportedCurrencies: [{ symbol: 'BTC' }] } },
      },
      {
        request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'BTC' } },
        result: { data: { cryptoMlSignal: null } },
      },
    ];

    const tree = render(
      <MockedProvider mocks={emptyMocks} addTypename={false}>
        <CryptoMLSignalsCard />
      </MockedProvider>
    );

    // Should show empty state
    expect(screen.getByText('No Signal Yet')).toBeTruthy();
  });

  it('clamps probability values correctly', async () => {
    const invalidMocks = [
      {
        request: { query: GET_SUPPORTED_CURRENCIES },
        result: { data: { supportedCurrencies: [{ symbol: 'BTC' }] } },
      },
      {
        request: { query: GET_CRYPTO_ML_SIGNAL, variables: { symbol: 'BTC' } },
        result: {
          data: {
            cryptoMlSignal: {
              predictionType: 'BIG_UP_DAY',
              probability: 1.5, // Invalid > 1
              confidenceLevel: 'HIGH',
              sentiment: 'Bullish',
              sentimentDescription: 'Test description.',
              featuresUsed: {},
              createdAt: new Date().toISOString(),
              expiresAt: new Date(Date.now() + 6 * 3600_000).toISOString(),
              explanation: 'Test explanation.',
              __typename: 'CryptoMlSignal'
            }
          }
        }
      },
    ];

    render(
      <MockedProvider mocks={invalidMocks} addTypename={false}>
        <CryptoMLSignalsCard />
      </MockedProvider>
    );

    // Should clamp to 100%
    const prob = await screen.findByText(/100.0%/);
    expect(prob).toBeTruthy();
  });
});
