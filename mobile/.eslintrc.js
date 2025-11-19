module.exports = {
  root: true,
  extends: [
    '@react-native-community',
    'plugin:react-hooks/recommended',
  ],
  plugins: ['react-hooks'],
  rules: {
    // ✅ Enforce React hooks rules
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // Additional helpful rules
    'no-unused-vars': 'warn',
    
    // ✅ Prevent console.log/warn/debug in production code
    // Use logger utility instead (logger.log, logger.warn, logger.error)
    // console.error is allowed for critical errors that should always be logged
    'no-console': ['error', { 
      allow: ['error'] // Only allow console.error for critical errors
    }],
    
    // TypeScript-specific rules
    '@typescript-eslint/no-explicit-any': 'warn', // Warn on explicit any usage
  },
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
