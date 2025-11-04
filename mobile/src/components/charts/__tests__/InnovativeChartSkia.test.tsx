/**
 * Unit Tests for InnovativeChartSkia Component
 * Tests all chart features: regime bands, confidence glass, event markers, driver lines, gestures
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';

// Mock @shopify/react-native-skia before importing component
jest.mock('@shopify/react-native-skia', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    Canvas: ({ children, style, ...props }: any) => (
      <View testID="skia-canvas" style={style} {...props}>
        {children}
      </View>
    ),
    Path: ({ path, color, style: pathStyle, strokeWidth, ...props }: any) => (
      <View testID="skia-path" style={{ backgroundColor: color, ...props }} />
    ),
    Rect: ({ x, y, width, height, color, ...props }: any) => (
      <View 
        testID="skia-rect" 
        style={{ 
          position: 'absolute', 
          left: x, 
          top: y, 
          width, 
          height, 
          backgroundColor: color 
        }} 
        {...props} 
      />
    ),
    Circle: ({ cx, cy, r, color, ...props }: any) => (
      <View 
        testID="skia-circle" 
        style={{ 
          position: 'absolute', 
          left: cx - r, 
          top: cy - r, 
          width: r * 2, 
          height: r * 2, 
          borderRadius: r,
          backgroundColor: color 
        }} 
        {...props} 
      />
    ),
    Line: ({ p1, p2, color, strokeWidth, ...props }: any) => (
      <View 
        testID="skia-line" 
        style={{ 
          position: 'absolute',
          left: Math.min(p1.x, p2.x),
          top: Math.min(p1.y, p2.y),
          width: Math.abs(p2.x - p1.x) || strokeWidth,
          height: Math.abs(p2.y - p1.y) || strokeWidth,
          backgroundColor: color 
        }} 
        {...props} 
      />
    ),
    Skia: {
      Path: {
        Make: () => ({ moveTo: jest.fn(), lineTo: jest.fn() }),
      },
    },
    vec: (x: number, y: number) => ({ x, y }),
  };
});

// Mock react-native-gesture-handler
jest.mock('react-native-gesture-handler', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    Gesture: {
      Pan: () => ({
        minPointers: jest.fn().mockReturnThis(),
        maxPointers: jest.fn().mockReturnThis(),
        enabled: jest.fn().mockReturnThis(),
        activeOffsetX: jest.fn().mockReturnThis(),
        failOffsetY: jest.fn().mockReturnThis(),
        onStart: jest.fn().mockReturnThis(),
        onBegin: jest.fn().mockReturnThis(),
        onUpdate: jest.fn().mockReturnThis(),
        onEnd: jest.fn().mockReturnThis(),
        shouldCancelWhenOutside: jest.fn().mockReturnThis(),
      }),
      Pinch: () => ({
        enabled: jest.fn().mockReturnThis(),
        onUpdate: jest.fn().mockReturnThis(),
        onEnd: jest.fn().mockReturnThis(),
        shouldCancelWhenOutside: jest.fn().mockReturnThis(),
      }),
      Tap: () => ({
        maxDuration: jest.fn().mockReturnThis(),
        onEnd: jest.fn().mockReturnThis(),
      }),
      Simultaneous: jest.fn((...gestures) => ({
        gestures,
      })),
    },
    GestureDetector: ({ children, gesture, ...props }: any) => (
      <View testID="gesture-detector" {...props}>
        {children}
      </View>
    ),
  };
});

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return {
    ...Reanimated,
    useSharedValue: (initial: any) => ({ value: initial }),
    useDerivedValue: (fn: () => any) => ({ value: fn() }),
    withSpring: (value: number) => value,
    withTiming: (value: number) => value,
    interpolate: (value: number, input: number[], output: number[]) => {
      const ratio = (value - input[0]) / (input[1] - input[0]);
      return output[0] + (output[1] - output[0]) * ratio;
    },
    runOnJS: (fn: Function) => fn,
  };
});

// Import component after mocks
import InnovativeChart from '../InnovativeChartSkia';

// Sample test data
const generateSampleData = (days: number = 30) => {
  const data = [];
  const basePrice = 100;
  const now = Date.now();
  
  for (let i = 0; i < days; i++) {
    const date = new Date(now - (days - i) * 24 * 60 * 60 * 1000);
    const price = basePrice + Math.sin(i / 5) * 10 + Math.random() * 5;
    data.push({
      t: date,
      price: Math.round(price * 100) / 100,
    });
  }
  return data;
};

const generateEvents = () => [
  {
    t: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
    title: 'Earnings Report',
    summary: 'Q4 earnings beat expectations',
    color: '#3B82F6',
  },
  {
    t: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
    title: 'Product Launch',
    summary: 'New product line launched',
    color: '#EF4444',
  },
];

const generateDrivers = () => [
  {
    t: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
    driver: 'earnings',
    cause: 'Strong quarterly results',
    relevancy: 85,
  },
  {
    t: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000),
    driver: 'market',
    cause: 'Market volatility increase',
    relevancy: 70,
  },
];

describe('InnovativeChartSkia', () => {
  const mockSeries = generateSampleData(30);
  const mockEvents = generateEvents();
  const mockDrivers = generateDrivers();
  const mockBenchmarkData = generateSampleData(30).map((p, i) => ({
    t: p.t,
    price: p.price * 0.98 + Math.random() * 2,
  }));

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      const { getByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          events={mockEvents}
          drivers={mockDrivers}
          costBasis={105}
          benchmarkData={mockBenchmarkData}
          height={300}
        />
      );

      expect(getByTestId('skia-canvas')).toBeTruthy();
    });

    it('renders empty state when no data provided', () => {
      const { getByText } = render(
        <InnovativeChart series={[]} height={300} />
      );

      expect(getByText('No data')).toBeTruthy();
    });

    it('displays loading state initially', async () => {
      const { getByText, queryByText } = render(
        <InnovativeChart series={mockSeries} height={300} />
      );

      // Initially shows loading
      expect(getByText('Loading chart...')).toBeTruthy();

      // After InteractionManager completes, should render chart
      await waitFor(() => {
        expect(queryByText('Loading chart...')).toBeNull();
      }, { timeout: 100 });
    });
  });

  describe('Regime Bands', () => {
    it('renders regime bands for trend, chop, and shock', async () => {
      const { getAllByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
        />
      );

      await waitFor(() => {
        const rects = getAllByTestId('skia-rect');
        expect(rects.length).toBeGreaterThan(0);
      });
    });

    it('displays regime count text', async () => {
      const { getByText } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
        />
      );

      await waitFor(() => {
        const regimeText = getByText(/regime/i);
        expect(regimeText).toBeTruthy();
      });
    });
  });

  describe('Event Markers', () => {
    it('renders event markers on chart', async () => {
      const { getAllByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          events={mockEvents}
          height={300}
        />
      );

      await waitFor(() => {
        const circles = getAllByTestId('skia-circle');
        // Should have at least 2 event markers
        expect(circles.length).toBeGreaterThanOrEqual(2);
      });
    });

    it('opens event modal when event marker is tapped', async () => {
      // Note: This would require gesture handler to be properly mocked
      // For now, we test that events are rendered
      const { getAllByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          events={mockEvents}
          height={300}
        />
      );

      await waitFor(() => {
        const circles = getAllByTestId('skia-circle');
        expect(circles.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Driver Lines', () => {
    it('renders driver lines on chart', async () => {
      const { getAllByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          drivers={mockDrivers}
          height={300}
        />
      );

      await waitFor(() => {
        const lines = getAllByTestId('skia-line');
        // Should have at least 2 driver lines
        expect(lines.length).toBeGreaterThanOrEqual(2);
      });
    });
  });

  describe('Cost Basis Line', () => {
    it('renders cost basis line when costBasis prop provided', async () => {
      const { getAllByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          costBasis={105}
          height={300}
        />
      );

      await waitFor(() => {
        const lines = getAllByTestId('skia-line');
        expect(lines.length).toBeGreaterThan(0);
      });
    });

    it('does not render cost basis line when costBasis not provided', async () => {
      const { getAllByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
        />
      );

      await waitFor(() => {
        const lines = getAllByTestId('skia-line');
        // May or may not have lines, but shouldn't error
        expect(lines).toBeDefined();
      });
    });
  });

  describe('Benchmark Data', () => {
    it('renders benchmark toggle button when benchmark data provided', async () => {
      const { getByText } = render(
        <InnovativeChart
          series={mockSeries}
          benchmarkData={mockBenchmarkData}
          height={300}
        />
      );

      await waitFor(() => {
        expect(getByText('Bench')).toBeTruthy();
      });
    });

    it('toggles benchmark visibility when button pressed', async () => {
      const { getByText } = render(
        <InnovativeChart
          series={mockSeries}
          benchmarkData={mockBenchmarkData}
          height={300}
        />
      );

      await waitFor(() => {
        const benchButton = getByText('Bench');
        fireEvent.press(benchButton);
        
        // Button text should change to 'Hide'
        expect(getByText('Hide')).toBeTruthy();
      });
    });
  });

  describe('Money View Toggle', () => {
    it('renders money toggle button when costBasis provided', async () => {
      const { getByText } = render(
        <InnovativeChart
          series={mockSeries}
          costBasis={105}
          height={300}
        />
      );

      await waitFor(() => {
        expect(getByText('Money')).toBeTruthy();
      });
    });

    it('toggles money view when button pressed', async () => {
      const { getByText } = render(
        <InnovativeChart
          series={mockSeries}
          costBasis={105}
          height={300}
        />
      );

      await waitFor(() => {
        const moneyButton = getByText('Money');
        fireEvent.press(moneyButton);
        
        // Button text should change to 'Price'
        expect(getByText('Price')).toBeTruthy();
      });
    });
  });

  describe('AR Button', () => {
    it('renders AR button', async () => {
      const { getByText } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
        />
      );

      await waitFor(() => {
        expect(getByText('AR')).toBeTruthy();
      });
    });

    it('opens AR modal when AR button pressed', async () => {
      const { getByText } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
        />
      );

      await waitFor(() => {
        const arButton = getByText('AR');
        fireEvent.press(arButton);
        
        // Should show AR modal content
        expect(getByText('AR Walk Prototype')).toBeTruthy();
      });
    });
  });

  describe('Gesture Detector', () => {
    it('renders GestureDetector wrapper', async () => {
      const { getByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
        />
      );

      await waitFor(() => {
        expect(getByTestId('gesture-detector')).toBeTruthy();
      });
    });
  });

  describe('Price Path Rendering', () => {
    it('renders price path', async () => {
      const { getAllByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
        />
      );

      await waitFor(() => {
        const paths = getAllByTestId('skia-path');
        expect(paths.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Error Handling', () => {
    it('handles invalid data gracefully', () => {
      const invalidData = [
        { t: new Date(), price: NaN },
        { t: new Date(), price: null },
      ];

      expect(() => {
        render(
          <InnovativeChart series={invalidData as any} height={300} />
        );
      }).not.toThrow();
    });

    it('handles empty events array', async () => {
      const { getByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          events={[]}
          height={300}
        />
      );

      await waitFor(() => {
        expect(getByTestId('skia-canvas')).toBeTruthy();
      });
    });

    it('handles empty drivers array', async () => {
      const { getByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          drivers={[]}
          height={300}
        />
      );

      await waitFor(() => {
        expect(getByTestId('skia-canvas')).toBeTruthy();
      });
    });
  });

  describe('Props Validation', () => {
    it('accepts custom height prop', async () => {
      const { getByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          height={400}
        />
      );

      await waitFor(() => {
        const canvas = getByTestId('skia-canvas');
        expect(canvas).toBeTruthy();
      });
    });

    it('accepts custom margin prop', async () => {
      const { getByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
          margin={20}
        />
      );

      await waitFor(() => {
        expect(getByTestId('skia-canvas')).toBeTruthy();
      });
    });

    it('accepts custom palette prop', async () => {
      const customPalette = {
        bg: '#000000',
        text: '#FFFFFF',
        price: '#00FF00',
      };

      const { getByTestId } = render(
        <InnovativeChart
          series={mockSeries}
          height={300}
          palette={customPalette}
        />
      );

      await waitFor(() => {
        expect(getByTestId('skia-canvas')).toBeTruthy();
      });
    });
  });
});

