/**
 * Simplified Unit Tests for InnovativeChartSkia Component
 * Tests basic rendering and functionality without complex mocking
 */

import React from 'react';
import { render } from '@testing-library/react-native';

// Mock Skia before imports
jest.mock('@shopify/react-native-skia', () => ({
  Canvas: 'Canvas',
  Path: 'Path',
  Rect: 'Rect',
  Circle: 'Circle',
  Line: 'Line',
  Skia: {
    Path: {
      Make: jest.fn(() => ({ moveTo: jest.fn(), lineTo: jest.fn() })),
    },
  },
  vec: jest.fn((x: number, y: number) => ({ x, y })),
}));

// Use existing mocks from setupTests.ts
describe('InnovativeChartSkia - Basic Tests', () => {
  it('should import without errors', () => {
    expect(() => {
      require('../InnovativeChartSkia');
    }).not.toThrow();
  });

  it('should handle empty data gracefully', () => {
    const InnovativeChart = require('../InnovativeChartSkia').default;
    const { getByText } = render(
      React.createElement(InnovativeChart, { series: [], height: 300 })
    );
    expect(getByText('No data')).toBeTruthy();
  });
});

