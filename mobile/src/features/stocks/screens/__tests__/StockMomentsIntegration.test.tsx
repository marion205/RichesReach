/**
 * Unit Tests for StockMomentsIntegration Component
 * Tests GraphQL integration, moment handling, and story mode
 */

// CRITICAL: Import React FIRST to ensure ReactCurrentOwner is initialized
import React from 'react';

// Ensure React is globally available before importing test libraries
if (typeof global !== 'undefined') {
  global.React = React;
}

// Load jest-native matchers if available (after PixelRatio mock is set up)
if (typeof global.loadJestNativeMatchers === 'function') {
  global.loadJestNativeMatchers();
}

// Now safe to import test libraries that depend on React internals
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { MockedProvider } from '@apollo/client/testing';
import { StockMomentsIntegration } from '../StockMomentsIntegration';
import { ChartPoint } from '../../../../components/charts/ChartWithMoments';
import { gql } from '@apollo/client';

// Mock components
jest.mock('../../../../components/charts/ChartWithMoments', () => {
  const React = require('react');
  const { View, Text } = require('react-native');
  return {
    __esModule: true,
    default: ({ onMomentLongPress, onMomentChange }: any) => (
      <View testID="chart">
        <Text onPress={() => onMomentChange?.({ id: '1' })}>Select Moment</Text>
        <Text onPress={() => onMomentLongPress?.({ id: '1' })}>Long Press</Text>
      </View>
    ),
    ChartPoint: {},
  };
});

jest.mock('../../../../components/charts/MomentStoryPlayer', () => {
  const React = require('react');
  const { View, Text } = require('react-native');
  return {
    __esModule: true,
    default: ({ visible, onClose }: any) => (
      visible ? (
        <View testID="story-player">
          <Text onPress={onClose}>Close</Text>
        </View>
      ) : null
    ),
  };
});

jest.mock('../../../../services/wealthOracleTTS', () => ({
  playWealthOracle: jest.fn(),
  stopWealthOracle: jest.fn(),
}));

const GET_STOCK_MOMENTS = gql`
  query GetStockMoments($symbol: String!, $range: ChartRangeEnum!) {
    stockMoments(symbol: $symbol, range: $range) {
      id
      symbol
      timestamp
      category
      title
      quickSummary
      deepSummary
    }
  }
`;

describe('StockMomentsIntegration', () => {
  const mockPriceSeries: ChartPoint[] = [
    { timestamp: '2024-01-01T00:00:00Z', price: 100 },
    { timestamp: '2024-01-02T00:00:00Z', price: 105 },
  ];

  const mockMomentsData = {
    stockMoments: [
      {
        id: '1',
        symbol: 'AAPL',
        timestamp: '2024-01-01T00:00:00Z',
        category: 'EARNINGS',
        title: 'Earnings Beat',
        quickSummary: 'Beat estimates',
        deepSummary: 'Detailed analysis',
      },
      {
        id: '2',
        symbol: 'AAPL',
        timestamp: '2024-01-02T00:00:00Z',
        category: 'NEWS',
        title: 'Product Launch',
        quickSummary: 'New product',
        deepSummary: 'Product details',
      },
    ],
  };

  const mocks = [
    {
      request: {
        query: GET_STOCK_MOMENTS,
        variables: {
          symbol: 'AAPL',
          range: 'ONE_MONTH',
        },
      },
      result: {
        data: mockMomentsData,
      },
    },
  ];

  it('renders loading state', () => {
    const { getByText } = render(
      <MockedProvider mocks={[]}>
        <StockMomentsIntegration
          symbol="AAPL"
          priceSeries={mockPriceSeries}
          chartRange="ONE_MONTH"
        />
      </MockedProvider>
    );

    expect(getByText('Loading key moments...')).toBeTruthy();
  });

  it('renders chart when moments are loaded', async () => {
    const { getByTestId } = render(
      <MockedProvider mocks={mocks}>
        <StockMomentsIntegration
          symbol="AAPL"
          priceSeries={mockPriceSeries}
          chartRange="ONE_MONTH"
        />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByTestId('chart')).toBeTruthy();
    });
  });

  it('opens story mode from button with intro', async () => {
    const { getByText, getByTestId } = render(
      <MockedProvider mocks={mocks}>
        <StockMomentsIntegration
          symbol="AAPL"
          priceSeries={mockPriceSeries}
          chartRange="ONE_MONTH"
        />
      </MockedProvider>
    );

    await waitFor(() => {
      const playButton = getByText('▶ Play Story');
      fireEvent.press(playButton);
    });

    await waitFor(() => {
      expect(getByTestId('story-player')).toBeTruthy();
    });
  });

  it('opens story mode from long-press without intro', async () => {
    const { getByText, getByTestId } = render(
      <MockedProvider mocks={mocks}>
        <StockMomentsIntegration
          symbol="AAPL"
          priceSeries={mockPriceSeries}
          chartRange="ONE_MONTH"
        />
      </MockedProvider>
    );

    await waitFor(() => {
      const longPressButton = getByText('Long Press');
      fireEvent.press(longPressButton);
    });

    await waitFor(() => {
      expect(getByTestId('story-player')).toBeTruthy();
    });
  });

  it('handles GraphQL errors gracefully', async () => {
    const errorMocks = [
      {
        request: {
          query: GET_STOCK_MOMENTS,
          variables: {
            symbol: 'AAPL',
            range: 'ONE_MONTH',
          },
        },
        error: new Error('GraphQL error'),
      },
    ];

    const { queryByTestId } = render(
      <MockedProvider mocks={errorMocks}>
        <StockMomentsIntegration
          symbol="AAPL"
          priceSeries={mockPriceSeries}
          chartRange="ONE_MONTH"
        />
      </MockedProvider>
    );

    await waitFor(() => {
      // Should not render chart on error
      expect(queryByTestId('chart')).toBeNull();
    });
  });

  it('does not render when no moments are returned', async () => {
    const emptyMocks = [
      {
        request: {
          query: GET_STOCK_MOMENTS,
          variables: {
            symbol: 'AAPL',
            range: 'ONE_MONTH',
          },
        },
        result: {
          data: {
            stockMoments: [],
          },
        },
      },
    ];

    const { queryByTestId } = render(
      <MockedProvider mocks={emptyMocks}>
        <StockMomentsIntegration
          symbol="AAPL"
          priceSeries={mockPriceSeries}
          chartRange="ONE_MONTH"
        />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(queryByTestId('chart')).toBeNull();
    });
  });

  it('calls analytics handler on story events', async () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

    const { getByText, getByTestId } = render(
      <MockedProvider mocks={mocks}>
        <StockMomentsIntegration
          symbol="AAPL"
          priceSeries={mockPriceSeries}
          chartRange="ONE_MONTH"
        />
      </MockedProvider>
    );

    await waitFor(() => {
      const playButton = getByText('▶ Play Story');
      fireEvent.press(playButton);
    });

    await waitFor(() => {
      const closeButton = getByText('Close');
      fireEvent.press(closeButton);
    });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[MomentAnalytics]'),
        expect.objectContaining({
          type: 'story_close',
        })
      );
    });

    consoleSpy.mockRestore();
  });
});

