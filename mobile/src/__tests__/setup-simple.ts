/**
 * Simple Jest setup file for React Native tests
 */

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/Feather', () => 'Icon');
jest.mock('react-native-vector-icons/Ionicons', () => 'Icon');
jest.mock('@expo/vector-icons', () => ({
  Feather: 'Icon',
  Ionicons: 'Icon',
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// Mock react-native-svg
jest.mock('react-native-svg', () => ({
  default: 'Svg',
  Circle: 'Circle',
  Path: 'Path',
  G: 'G',
  Text: 'SvgText',
  Line: 'SvgLine',
  Rect: 'SvgRect',
}));

// Mock react-native-chart-kit
jest.mock('react-native-chart-kit', () => ({
  LineChart: 'LineChart',
  BarChart: 'BarChart',
  PieChart: 'PieChart',
}));

// Mock expo modules
jest.mock('expo-linear-gradient', () => 'LinearGradient');
jest.mock('expo-image-picker', () => ({
  requestCameraPermissionsAsync: jest.fn(),
  requestMediaLibraryPermissionsAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  launchImageLibraryAsync: jest.fn(),
}));
jest.mock('expo-font', () => ({}));
jest.mock('expo-constants', () => ({
  expoConfig: {},
}));

// Mock Apollo Client
jest.mock('@apollo/client', () => ({
  useQuery: () => ({
    data: null,
    loading: false,
    error: null,
    refetch: jest.fn(),
  }),
  useMutation: () => [jest.fn(), { loading: false, error: null }],
  useApolloClient: () => ({
    cache: { reset: jest.fn() },
    refetchQueries: jest.fn(),
  }),
  gql: jest.fn(),
}));

// Global test timeout
jest.setTimeout(10000);
