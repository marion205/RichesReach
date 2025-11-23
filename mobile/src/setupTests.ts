/**
 * Early setup file - runs BEFORE test environment is initialized
 * This is where we must mock PixelRatio before StyleSheet loads
 */

// CRITICAL: Import React FIRST to initialize ReactCurrentOwner
// This must be before any other imports to ensure React internals are set up
import React from 'react';

// Ensure React is available globally before any test libraries load
// This initializes ReactCurrentOwner and other React internals
if (typeof global !== 'undefined') {
  global.React = React;
}

// Force React internals to initialize by accessing them
// This ensures ReactCurrentOwner is set up before test libraries try to use it
if (React.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED) {
  // React internals are available - good
}

// CRITICAL: Mock react-test-renderer to prevent ReactCurrentOwner errors
// This must be before @testing-library/react-native tries to import it
jest.mock('react-test-renderer', () => {
  const React = require('react');
  // Ensure React is initialized before creating renderer
  if (typeof global !== 'undefined') {
    global.React = React;
  }
  
  // Return a mock renderer that doesn't access ReactCurrentOwner prematurely
  return {
    create: jest.fn((element) => ({
      toJSON: () => ({ type: 'MockedComponent' }),
      root: { findAllByType: jest.fn(), findByType: jest.fn() },
      update: jest.fn(),
      unmount: jest.fn(),
    })),
    act: (callback) => callback(),
  };
});

// CRITICAL: Mock PixelRatio FIRST - before ANY other React Native imports
// This ensures the mock is in place before any React Native modules load
// Using factory function to avoid evaluation issues
jest.mock('react-native/Libraries/Utilities/PixelRatio', () => {
  // Return plain object - jest.fn will be available when this runs
  return {
    get: () => 2,
    getFontScale: () => 1,
    isFontScaleAtLeast: () => true,
    roundToNearestPixel: (size) => Math.round(size * 2) / 2,
    getPixelSizeForLayoutSize: (size) => size * 2,
    startDetecting: () => {},
  };
});

import 'react-native-gesture-handler/jestSetup';

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Mock VirtualizedList internals comprehensively to prevent native module errors
jest.mock('react-native/node_modules/@react-native/virtualized-lists/Lists/VirtualizedListCellRenderer', () => {
  const React = require('react');
  return {
    default: {
      create: jest.fn(() => ({
        render: jest.fn(() => React.createElement('View')),
      })),
    },
  };
});

jest.mock('react-native/node_modules/@react-native/virtualized-lists/Lists/VirtualizedList', () => {
  const React = require('react');
  return {
    default: React.forwardRef((props: any, ref: any) => {
      const { data = [], renderItem } = props;
      return React.createElement(
        'View',
        { testID: props.testID || 'virtualized-list', ref, ...props },
        data.map((item: any, index: number) => {
          const element = renderItem?.({ item, index, separators: {} });
          return React.createElement('View', { key: item?.id || index }, element);
        })
      );
    }),
  };
});

// Mock FlatList/VirtualizedList early to prevent native module errors
jest.mock('react-native/Libraries/Lists/FlatList', () => {
  const React = require('react');
  return React.forwardRef((props: any, ref: any) => {
    const { data = [], renderItem } = props;
    return React.createElement(
      'View',
      { testID: props.testID || 'flatlist', ref, ...props },
      data.map((item: any, index: number) => {
        const element = renderItem?.({ item, index, separators: {} });
        return React.createElement('View', { key: item?.id || index }, element);
      })
    );
  });
});

// Mock Modal early to prevent native module errors
// Use a simple mock that doesn't require React Native components to avoid circular deps
jest.mock('react-native/Libraries/Modal/Modal', () => {
  const React = require('react');
  // Return a simple component that doesn't require View
  return React.forwardRef((props: any, ref: any) => {
    return React.createElement('div', { ...props, ref, 'data-testid': 'modal' });
  });
});

// Mock react-native-screens
jest.mock('react-native-screens', () => ({
  enableScreens: jest.fn(),
}));

// Mock @react-native-async-storage/async-storage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(),
  multiGet: jest.fn(),
  multiSet: jest.fn(),
  multiRemove: jest.fn(),
}));

// Mock expo modules
jest.mock('expo-av', () => ({
  Audio: {
    requestPermissionsAsync: jest.fn(),
    setAudioModeAsync: jest.fn(),
    Recording: jest.fn(),
  },
  Video: 'Video',
}));

jest.mock('expo-image-picker', () => ({
  requestMediaLibraryPermissionsAsync: jest.fn(),
  requestCameraPermissionsAsync: jest.fn(),
  launchImageLibraryAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  MediaType: {
    Images: 'Images',
    Videos: 'Videos',
    All: 'All',
  },
  // Keep MediaTypeOptions for backward compatibility in tests
  MediaTypeOptions: {
    Images: 'Images',
    Videos: 'Videos',
    All: 'All',
  },
}));

jest.mock('expo-notifications', () => ({
  setNotificationHandler: jest.fn(),
  requestPermissionsAsync: jest.fn(),
  getExpoPushTokenAsync: jest.fn(),
  addNotificationReceivedListener: jest.fn(),
  addNotificationResponseReceivedListener: jest.fn(),
}));

jest.mock('expo-device', () => ({
  isDevice: true,
}));

jest.mock('expo-constants', () => ({
  default: {
    expoConfig: {
      extra: {
        eas: {
          projectId: 'test-project-id',
        },
      },
    },
  },
  expoConfig: {
    extra: {
      eas: {
        projectId: 'test-project-id',
      },
    },
  },
}));

// Note: react-native-webrtc and socket.io-client mocks removed
// Individual test files should mock these locally if needed
// This avoids module resolution issues in the global setup

// Note: Optional mocks for react-native-gifted-chat and services
// have been removed. Add them back if needed for your specific tests.

// Mock theme (commented out - individual test files can mock this locally if needed)
// jest.mock('../theme/PersonalizedThemes', () => ({
//   useTheme: () => ({
//     colors: {
//       background: '#ffffff',
//       surface: '#f5f5f5',
//       text: '#000000',
//       textSecondary: '#666666',
//       primary: '#007AFF',
//     },
//   }),
// }));

// Mock navigation
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
    setOptions: jest.fn(),
  }),
  useRoute: () => ({
    params: {},
  }),
}));

// Mock fetch
global.fetch = jest.fn();

// Mock FormData
global.FormData = jest.fn(() => ({
  append: jest.fn(),
}));

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Mock Alert
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
    },
  };
});

// Silence the warning: Animated: `useNativeDriver` is not supported
// Mock NativeAnimatedHelper (commented out - may cause module resolution issues)
// jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');
