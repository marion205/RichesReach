/**
 * Simple component tests to verify Jest is working with React Native
 */

import React from 'react';
import { render, Text } from '@testing-library/react-native';

// Simple test component
const TestComponent = () => {
  return <Text>Hello World</Text>;
};

describe('Simple Component Tests', () => {
  it('should render a simple component', () => {
    const { getByText } = render(<TestComponent />);
    expect(getByText('Hello World')).toBeTruthy();
  });

  it('should handle basic interactions', () => {
    const { getByText } = render(<TestComponent />);
    const element = getByText('Hello World');
    expect(element).toBeDefined();
  });
});
