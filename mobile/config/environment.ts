// Environment configuration for RichesReach
export const ENV = {
  // Development vs Production
  isDevelopment: __DEV__,
  isProduction: !__DEV__,
  
  // API URLs
  api: {
    development: {
      android: 'http://10.0.2.2:8000/graphql/',
      ios: 'http://localhost:8000/graphql/',
      web: 'http://localhost:8000/graphql/'
    },
    production: {
      // PRODUCTION BACKEND URL - Update this when you deploy your Django backend
      android: 'https://api.richesreach.com/graphql/',
      ios: 'https://api.richesreach.com/graphql/',
      web: 'https://api.richesreach.com/graphql/'
    }
  },
  
  // News API
  newsApi: {
    key: '94a335c7316145f79840edd62f77e11e',
    baseUrl: 'https://newsapi.org/v2'
  },
  
  // Feature flags
  features: {
    enableAnalytics: !__DEV__,
    enableCrashReporting: !__DEV__,
    enablePerformanceMonitoring: !__DEV__
  }
};

// Helper function to get API URL based on platform
export const getApiUrl = (platform: 'android' | 'ios' | 'web') => {
  if (ENV.isDevelopment) {
    return ENV.api.development[platform];
  }
  return ENV.api.production[platform];
};
