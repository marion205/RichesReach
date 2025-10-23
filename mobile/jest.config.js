module.exports = {
  preset: 'react-native',
  setupFilesAfterEnv: ['<rootDir>/src/__tests__/setup-simple.ts'],
  testMatch: [
    '<rootDir>/src/__tests__/**/*.test.tsx',
    '<rootDir>/src/__tests__/**/*.test.ts'
  ],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/__tests__/**',
    '!src/**/*.stories.{ts,tsx}'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@features/(.*)$': '<rootDir>/src/features/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1'
  },
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|@react-native|@expo|expo|@react-navigation|react-native-vector-icons|react-native-svg|react-native-reanimated|react-native-gesture-handler|react-native-svg-charts|d3-shape|expo-font|expo-constants|expo-linear-gradient|expo-image-picker)/)'
  ],
  testEnvironment: 'node',
  verbose: true,
  clearMocks: true,
  restoreMocks: true
};
