// Minimal setup for chart component tests only
// This avoids conflicts with other test setup files
// Using React.createElement instead of JSX to avoid Babel parsing issues

// Ensure React is available before any mocks
const React = require('react');

// Mock @shopify/react-native-skia
jest.mock('@shopify/react-native-skia', () => {
  const React = require('react');
  const { View } = require('react-native');
  
  // Create mock components using React.createElement (no JSX)
  const createMockComponent = (testID: string) => {
    return (props: any) => {
      return React.createElement(View, { ...props, testID });
    };
  };
  
  return {
    Canvas: createMockComponent('skia-canvas'),
    Path: createMockComponent('skia-path'),
    Rect: createMockComponent('skia-rect'),
    Circle: createMockComponent('skia-circle'),
    Line: createMockComponent('skia-line'),
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
  
  const createMockGesture = (name: string) => {
    return () => ({
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
    });
  };
  
  const GestureDetector = (props: any) => {
    return React.createElement(View, { ...props, testID: 'gesture-detector' });
  };
  
  return {
    Gesture: {
      Pan: createMockGesture('pan'),
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
    GestureDetector,
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

// Mock Dimensions and Platform
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Dimensions: {
      get: jest.fn(() => ({ width: 375, height: 812 })),
    },
    InteractionManager: {
      runAfterInteractions: jest.fn((callback) => {
        setTimeout(callback, 0);
        return { cancel: jest.fn() };
      }),
    },
    Platform: {
      OS: 'ios',
    },
    Alert: {
      alert: jest.fn(),
    },
  };
});

// Mock window for web event listeners
if (typeof window === 'undefined') {
  global.window = {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  } as any;
}

