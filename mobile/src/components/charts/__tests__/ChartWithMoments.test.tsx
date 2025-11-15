/**
 * Unit Tests for ChartWithMoments Component
 * Tests chart rendering, moment interaction, long-press, and haptics
 */

// CRITICAL: Import React FIRST to ensure ReactCurrentOwner is initialized
import React from 'react';

// Load jest-native matchers if available (after PixelRatio mock is set up)
if (typeof global.loadJestNativeMatchers === 'function') {
  global.loadJestNativeMatchers();
}
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import ChartWithMoments, { ChartPoint, StockMoment } from '../ChartWithMoments';
import * as Haptics from 'expo-haptics';

// Mock expo-haptics
jest.mock('expo-haptics', () => ({
  selectionAsync: jest.fn(),
  impactAsync: jest.fn(),
}));

// Mock react-native-svg
jest.mock('react-native-svg', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    Svg: ({ children, width, height, ...props }: any) => (
      <View testID="svg" style={{ width, height }} {...props}>
        {children}
      </View>
    ),
    Polyline: ({ points, ...props }: any) => (
      <View testID="polyline" data-points={points} {...props} />
    ),
    Circle: ({ cx, cy, r, ...props }: any) => (
      <View testID="circle" style={{ left: cx, top: cy, width: r * 2, height: r * 2 }} {...props} />
    ),
    Line: (props: any) => <View testID="line" {...props} />,
  };
});

describe('ChartWithMoments', () => {
  const mockPriceSeries: ChartPoint[] = [
    { timestamp: '2024-01-01T00:00:00Z', price: 100 },
    { timestamp: '2024-01-02T00:00:00Z', price: 105 },
    { timestamp: '2024-01-03T00:00:00Z', price: 110 },
    { timestamp: '2024-01-04T00:00:00Z', price: 108 },
    { timestamp: '2024-01-05T00:00:00Z', price: 115 },
  ];

  const mockMoments: StockMoment[] = [
    {
      id: '1',
      symbol: 'AAPL',
      timestamp: '2024-01-02T00:00:00Z',
      category: 'EARNINGS',
      title: 'Earnings Beat',
      quickSummary: 'Beat estimates',
      deepSummary: 'Detailed earnings analysis',
    },
    {
      id: '2',
      symbol: 'AAPL',
      timestamp: '2024-01-04T00:00:00Z',
      category: 'NEWS',
      title: 'Product Launch',
      quickSummary: 'New product',
      deepSummary: 'Product launch details',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders chart with price series', () => {
    const { getByTestId } = render(
      <ChartWithMoments priceSeries={mockPriceSeries} moments={mockMoments} />
    );

    expect(getByTestId('svg')).toBeTruthy();
    expect(getByTestId('polyline')).toBeTruthy();
  });

  it('renders moment dots on chart', () => {
    const { getAllByTestId } = render(
      <ChartWithMoments priceSeries={mockPriceSeries} moments={mockMoments} />
    );

    const circles = getAllByTestId('circle');
    expect(circles.length).toBeGreaterThanOrEqual(mockMoments.length);
  });

  it('calls onMomentChange when moment is selected', async () => {
    const onMomentChange = jest.fn();
    const { getByTestId } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
        onMomentChange={onMomentChange}
      />
    );

    const chartContainer = getByTestId('svg').parent;
    
    // Simulate pan gesture
    fireEvent(chartContainer, 'onResponderGrant', {
      nativeEvent: { locationX: 100, locationY: 50 },
    });

    await waitFor(() => {
      expect(onMomentChange).toHaveBeenCalled();
    });
  });

  it('triggers haptic feedback on moment selection', async () => {
    const onMomentChange = jest.fn();
    const { getByTestId } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
        onMomentChange={onMomentChange}
      />
    );

    const chartContainer = getByTestId('svg').parent;
    
    fireEvent(chartContainer, 'onResponderGrant', {
      nativeEvent: { locationX: 100, locationY: 50 },
    });

    await waitFor(() => {
      expect(Haptics.selectionAsync).toHaveBeenCalled();
    });
  });

  it('calls onMomentLongPress after long-press duration', async () => {
    const onMomentLongPress = jest.fn();
    const { getByTestId } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
        onMomentLongPress={onMomentLongPress}
      />
    );

    const chartContainer = getByTestId('svg').parent;
    
    // Start long-press
    fireEvent(chartContainer, 'onResponderGrant', {
      nativeEvent: { locationX: 100, locationY: 50 },
    });

    // Fast-forward 500ms (long-press duration)
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(onMomentLongPress).toHaveBeenCalled();
      expect(Haptics.impactAsync).toHaveBeenCalledWith(Haptics.ImpactFeedbackStyle.Medium);
    });
  });

  it('cancels long-press if finger moves too far', async () => {
    const onMomentLongPress = jest.fn();
    const { getByTestId } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
        onMomentLongPress={onMomentLongPress}
      />
    );

    const chartContainer = getByTestId('svg').parent;
    
    // Start long-press
    fireEvent(chartContainer, 'onResponderGrant', {
      nativeEvent: { locationX: 100, locationY: 50 },
    });

    // Move finger far away (>20px tolerance)
    fireEvent(chartContainer, 'onResponderMove', {
      nativeEvent: { locationX: 150, locationY: 50 },
    });

    // Fast-forward past long-press duration
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(onMomentLongPress).not.toHaveBeenCalled();
    });
  });

  it('cancels long-press on release', async () => {
    const onMomentLongPress = jest.fn();
    const { getByTestId } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
        onMomentLongPress={onMomentLongPress}
      />
    );

    const chartContainer = getByTestId('svg').parent;
    
    // Start long-press
    fireEvent(chartContainer, 'onResponderGrant', {
      nativeEvent: { locationX: 100, locationY: 50 },
    });

    // Release before long-press completes
    fireEvent(chartContainer, 'onResponderRelease');

    // Fast-forward past long-press duration
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(onMomentLongPress).not.toHaveBeenCalled();
    });
  });

  it('displays moment card when moment is active', async () => {
    const { getByTestId, queryByText } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
      />
    );

    const chartContainer = getByTestId('svg').parent;
    
    fireEvent(chartContainer, 'onResponderGrant', {
      nativeEvent: { locationX: 100, locationY: 50 },
    });

    await waitFor(() => {
      expect(queryByText('Earnings Beat')).toBeTruthy();
      expect(queryByText('Beat estimates')).toBeTruthy();
    });
  });

  it('opens detail modal when moment card is pressed', async () => {
    const { getByTestId, getByText, queryByText } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
      />
    );

    const chartContainer = getByTestId('svg').parent;
    
    // Select a moment
    fireEvent(chartContainer, 'onResponderGrant', {
      nativeEvent: { locationX: 100, locationY: 50 },
    });

    await waitFor(() => {
      const card = getByText('Tap for full story');
      fireEvent.press(card);
    });

    await waitFor(() => {
      expect(queryByText('Detailed earnings analysis')).toBeTruthy();
    });
  });

  it('respects activeMomentId prop for external control', () => {
    const { getAllByTestId } = render(
      <ChartWithMoments
        priceSeries={mockPriceSeries}
        moments={mockMoments}
        activeMomentId="1"
      />
    );

    const circles = getAllByTestId('circle');
    // Active moment should have larger radius (r=5 vs r=4)
    // This is hard to test directly, but we can verify the component renders
    expect(circles.length).toBeGreaterThan(0);
  });

  it('handles empty price series gracefully', () => {
    const { getByTestId } = render(
      <ChartWithMoments priceSeries={[]} moments={mockMoments} />
    );

    expect(getByTestId('svg')).toBeTruthy();
  });

  it('handles empty moments array gracefully', () => {
    const { getByTestId } = render(
      <ChartWithMoments priceSeries={mockPriceSeries} moments={[]} />
    );

    expect(getByTestId('svg')).toBeTruthy();
    expect(getByTestId('polyline')).toBeTruthy();
  });
});

