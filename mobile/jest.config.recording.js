module.exports = {
  preset: 'react-native',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  testMatch: [
    '**/__tests__/**/*.(ts|tsx|js)',
    '**/*.(test|spec).(ts|tsx|js)',
  ],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  testTimeout: 30000,
  verbose: true,
  // Integration with demo recording
  reporters: [
    'default',
    ['jest-html-reporters', {
      publicPath: './demo-recordings/test-reports',
      filename: 'test-report.html',
      expand: true,
    }],
  ],
  // Performance monitoring
  globalSetup: '<rootDir>/src/__tests__/setup-simple.ts',
  globalTeardown: '<rootDir>/src/__tests__/setup-simple.ts',
};
