// Dedicated Jest config for chart component tests
// This avoids conflicts with other test setup

module.exports = {
  preset: 'react-native',
  setupFiles: [
    '<rootDir>/src/components/charts/__tests__/setup-window-fix.js',
  ],
  setupFilesAfterEnv: [
    '<rootDir>/src/components/charts/__tests__/chart-test-setup.ts',
  ],
  testMatch: [
    '**/charts/**/__tests__/**/*.(ts|tsx|js)',
    '**/charts/**/*.(test|spec).(ts|tsx|js)',
  ],
  transform: {
    '^.+\\.(ts|tsx|js|jsx)$': 'babel-jest',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|@react-native|@expo|expo|@react-navigation|react-native-webrtc|react-native-gifted-chat|socket.io-client|@shopify)/)',
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@features/(.*)$': '<rootDir>/src/features/$1',
    '^@theme/(.*)$': '<rootDir>/src/theme/$1',
  },
  testEnvironment: 'node',
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
};

