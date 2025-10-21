/**
 * Simple Jest setup file for React Native tests
 */

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/Feather', () => 'Icon');
jest.mock('react-native-vector-icons/Ionicons', () => 'Icon');

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// Global test timeout
jest.setTimeout(10000);
