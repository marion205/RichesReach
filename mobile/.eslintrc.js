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
    'no-console': 'off', // Allow console.log for debugging
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
