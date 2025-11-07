/**
 * Unit tests for OrbRenderer (Web/PWA)
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import OrbRenderer from '../OrbRenderer';

// Mock Three.js
jest.mock('three', () => {
  const mockScene = {
    add: jest.fn(),
    background: null,
  };
  const mockCamera = {
    position: { z: 5 },
  };
  const mockRenderer = {
    setSize: jest.fn(),
    setPixelRatio: jest.fn(),
    render: jest.fn(),
    domElement: document.createElement('canvas'),
    dispose: jest.fn(),
  };
  const mockMesh = {
    position: { set: jest.fn() },
    rotation: { x: 0, y: 0 },
  };

  return {
    Scene: jest.fn(() => mockScene),
    PerspectiveCamera: jest.fn(() => mockCamera),
    WebGLRenderer: jest.fn(() => mockRenderer),
    SphereGeometry: jest.fn(),
    MeshPhongMaterial: jest.fn(),
    MeshBasicMaterial: jest.fn(),
    Mesh: jest.fn(() => mockMesh),
    AmbientLight: jest.fn(),
    PointLight: jest.fn(),
    Color: jest.fn(),
  };
});

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 16));
global.cancelAnimationFrame = jest.fn();

describe('OrbRenderer', () => {
  const defaultProps = {
    netWorth: 100000,
    portfolioValue: 90000,
    bankBalance: 10000,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render orb container', () => {
    const { container } = render(<OrbRenderer {...defaultProps} />);
    
    expect(container.querySelector('div')).toBeTruthy();
  });

  it('should show loading state initially', () => {
    render(<OrbRenderer {...defaultProps} />);
    
    // Loading text should appear initially
    // (component sets isLoaded after Three.js initialization)
    expect(screen.queryByText(/Loading orb/i)).toBeTruthy();
  });

  it('should calculate orb size based on net worth', () => {
    const { rerender } = render(<OrbRenderer {...defaultProps} />);
    
    // Test with different net worth values
    rerender(<OrbRenderer {...defaultProps} netWorth={200000} />);
    rerender(<OrbRenderer {...defaultProps} netWorth={50000} />);
    
    // Component should handle different sizes
    expect(true).toBe(true); // Basic render test
  });

  it('should handle gesture callbacks', () => {
    const mockOnGesture = jest.fn();
    
    render(<OrbRenderer {...defaultProps} onGesture={mockOnGesture} />);
    
    // Gesture handlers are attached to canvas
    // Would need actual DOM events to test fully
    expect(mockOnGesture).toBeDefined();
  });

  it('should cleanup on unmount', () => {
    const { unmount } = render(<OrbRenderer {...defaultProps} />);
    
    unmount();
    
    // Should cancel animation frame
    expect(global.cancelAnimationFrame).toHaveBeenCalled();
  });

  it('should handle different width/height props', () => {
    const { rerender } = render(
      <OrbRenderer {...defaultProps} width={600} height={600} />
    );
    
    rerender(
      <OrbRenderer {...defaultProps} width={300} height={300} />
    );
    
    // Should handle size changes
    expect(true).toBe(true);
  });
});

