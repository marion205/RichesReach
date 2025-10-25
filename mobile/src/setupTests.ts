import 'react-native-gesture-handler/jestSetup';

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
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
  launchImageLibraryAsync: jest.fn(),
  MediaTypeOptions: {
    Images: 'Images',
    Videos: 'Videos',
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
  expoConfig: {
    extra: {
      eas: {
        projectId: 'test-project-id',
      },
    },
  },
}));

// Mock react-native-webrtc
jest.mock('react-native-webrtc', () => ({
  RTCIceCandidate: jest.fn(),
  RTCPeerConnection: jest.fn(),
  RTCSessionDescription: jest.fn(),
  RTCView: 'RTCView',
  MediaStream: {
    getUserMedia: jest.fn(),
  },
}));

// Mock socket.io-client
jest.mock('socket.io-client', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    emit: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    disconnect: jest.fn(),
    connected: true,
  })),
}));

// Mock react-native-gifted-chat
jest.mock('react-native-gifted-chat', () => ({
  GiftedChat: 'GiftedChat',
  IMessage: {},
}));

// Mock services
jest.mock('../services/WebRTCService', () => ({
  WebRTCService: jest.fn().mockImplementation(() => ({
    initialize: jest.fn(),
    setCallbacks: jest.fn(),
    startStream: jest.fn(),
    stopStream: jest.fn(),
    joinRoom: jest.fn(),
    leaveRoom: jest.fn(),
  })),
}));

jest.mock('../services/SocketChatService', () => ({
  SocketChatService: jest.fn().mockImplementation(() => ({
    initialize: jest.fn(),
    setCallbacks: jest.fn(),
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
    onMessage: jest.fn(),
  })),
}));

// Mock theme
jest.mock('../theme/PersonalizedThemes', () => ({
  useTheme: () => ({
    colors: {
      background: '#ffffff',
      surface: '#f5f5f5',
      text: '#000000',
      textSecondary: '#666666',
      primary: '#007AFF',
    },
  }),
}));

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
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');
