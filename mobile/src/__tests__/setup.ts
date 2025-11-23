/**
 * Jest setup file for React Native tests
 * Configures mocks and global test utilities
 */

// CRITICAL: Ensure React is available globally
// setupTests.ts should have already imported React, but ensure it's here too
if (typeof global !== 'undefined' && !global.React) {
  const React = require('react');
  global.React = React;
}

// CRITICAL: Re-assert PixelRatio mock here to ensure it's available when setup.ts runs
// Even though it's in setupTests.ts, we need it here too for when jest-native loads
jest.mock('react-native/Libraries/Utilities/PixelRatio', () => ({
  get: () => 2,
  getFontScale: () => 1,
  isFontScaleAtLeast: () => true,
  roundToNearestPixel: (size) => Math.round(size * 2) / 2,
  getPixelSizeForLayoutSize: (size) => size * 2,
  startDetecting: () => {},
}));

// CRITICAL: Mock StyleSheet to prevent it from loading PixelRatio
// This must be before any react-native mocks that use requireActual
jest.mock('react-native/Libraries/StyleSheet/StyleSheet', () => {
  return {
    create: (styles: any) => styles,
    flatten: (style: any) => style,
    compose: (style1: any, style2: any) => [style1, style2],
    hairlineWidth: 0.5,
    absoluteFill: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0 },
    absoluteFillObject: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0 },
    setStyleAttributePreprocessor: jest.fn(),
  };
});

// NOTE: PixelRatio mock is also in setupTests.ts (setupFiles) to ensure it loads before StyleSheet

// Mock TurboModuleRegistry to prevent DevMenu errors
jest.mock('react-native/Libraries/TurboModule/TurboModuleRegistry', () => ({
  getEnforcing: jest.fn(() => ({
    show: jest.fn(),
    getConstants: jest.fn(() => ({})),
  })),
  get: jest.fn(() => ({
    show: jest.fn(),
    getConstants: jest.fn(() => ({})),
  })),
}));

// Mock Dimensions to prevent native module errors
jest.mock('react-native/Libraries/Utilities/Dimensions', () => ({
  get: jest.fn(() => ({
    window: { width: 375, height: 812, scale: 2, fontScale: 1 },
    screen: { width: 375, height: 812, scale: 2, fontScale: 1 },
  })),
}));

// Mock Platform - must export both default and named exports
jest.mock('react-native/Libraries/Utilities/Platform', () => {
  const platform = {
    OS: 'ios',
    Version: 17,
    select: jest.fn((obj) => obj.ios || obj.default),
    constants: {
      isTesting: true,
    },
  };
  // Export as both default and named
  platform.default = platform;
  return platform;
});

// Mock PanResponder (for chart interactions)
jest.mock('react-native/Libraries/Interaction/PanResponder', () => ({
  create: jest.fn(() => ({
    panHandlers: {},
  })),
}));

// Mock react-native-svg (if using SVG in charts)
jest.mock('react-native-svg', () => ({
  Svg: 'SvgMock',
  Polyline: 'PolylineMock',
  Circle: 'CircleMock',
  Line: 'LineMock',
  Path: 'PathMock',
  G: 'GMock',
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(() => Promise.resolve([])),
}));

// Extend Jest matchers from @testing-library/jest-native
// Lazy import to prevent StyleSheet from loading before PixelRatio mock
// This is loaded conditionally to avoid the PixelRatio loading order issue
let jestNativeLoaded = false;
const loadJestNative = () => {
  if (!jestNativeLoaded) {
    try {
      require('@testing-library/jest-native/extend-expect');
      jestNativeLoaded = true;
    } catch (e) {
      console.warn('Failed to load @testing-library/jest-native:', e.message);
    }
  }
};

// Export function for test files to call if needed
global.loadJestNativeMatchers = loadJestNative;

// Don't auto-load - let test files call loadJestNativeMatchers() if they need it
// This prevents StyleSheet from loading before PixelRatio mock is ready
// Test files that need jest-native matchers should call: global.loadJestNativeMatchers()

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/Feather', () => 'Icon');
jest.mock('react-native-vector-icons/Ionicons', () => 'Icon');

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Modal mock is in setupTests.ts to avoid circular dependencies

// Mock react-native-gesture-handler
jest.mock('react-native-gesture-handler', () => {
  const View = require('react-native/Libraries/Components/View/View');
  return {
    Swipeable: View,
    DrawerLayout: View,
    State: {},
    ScrollView: View,
    Slider: View,
    Switch: View,
    TextInput: View,
    ToolbarAndroid: View,
    ViewPagerAndroid: View,
    DrawerLayoutAndroid: View,
    WebView: View,
    NativeViewGestureHandler: View,
    TapGestureHandler: View,
    FlingGestureHandler: View,
    ForceTouchGestureHandler: View,
    LongPressGestureHandler: View,
    PanGestureHandler: View,
    PinchGestureHandler: View,
    RotationGestureHandler: View,
    RawButton: View,
    BaseButton: View,
    RectButton: View,
    BorderlessButton: View,
    FlatList: View,
    gestureHandlerRootHOC: jest.fn(),
    Directions: {},
  };
});

// Mock expo modules
jest.mock('expo-linear-gradient', () => ({
  LinearGradient: 'LinearGradient',
}));

jest.mock('expo-speech', () => ({
  speak: jest.fn(),
  stop: jest.fn(),
  isSpeaking: jest.fn(() => Promise.resolve(false)),
}));

jest.mock('expo-notifications', () => ({
  scheduleNotificationAsync: jest.fn(),
  cancelAllScheduledNotificationsAsync: jest.fn(),
  getPermissionsAsync: jest.fn(() => Promise.resolve({ status: 'granted' })),
  requestPermissionsAsync: jest.fn(() => Promise.resolve({ status: 'granted' })),
}));

// Mock react-native-svg-charts (must be before @testing-library/jest-native)
jest.doMock('react-native-svg-charts', () => ({
  LineChart: 'LineChart',
  BarChart: 'BarChart',
  PieChart: 'PieChart',
}));

// Mock d3-shape
jest.mock('d3-shape', () => ({
  shape: {
    curveMonotoneX: 'curveMonotoneX',
  },
}));

// Mock react-native-confetti-cannon
jest.mock('react-native-confetti-cannon', () => 'ConfettiCannon');

// Mock Vibration
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Vibration: {
      vibrate: jest.fn(),
    },
  };
});

// Global test utilities
global.mockNavigateTo = jest.fn();
global.mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  reset: jest.fn(),
  setParams: jest.fn(),
  dispatch: jest.fn(),
  canGoBack: jest.fn(() => true),
  isFocused: jest.fn(() => true),
  addListener: jest.fn(),
  removeListener: jest.fn(),
};

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(),
  fetch: jest.fn(() => Promise.resolve({ isConnected: true })),
}));

// Suppress console warnings in tests
const originalWarn = console.warn;
const originalError = console.error;

beforeAll(() => {
  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is deprecated')
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };

  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning:') || args[0].includes('Error: Rendered fewer hooks'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.warn = originalWarn;
  console.error = originalError;
});

// Global test timeout
jest.setTimeout(10000);
