// Stream.io and Agora Configuration
// Replace these with your actual API keys and tokens

export const STREAM_CONFIG = {
  // Get your API key from https://getstream.io/dashboard/
  API_KEY: '4866mbx8b4jv',
  
  // Generate user tokens server-side for security
  // For development, you can use a test token from Stream dashboard
  USER_TOKEN: 'YOUR_STREAM_USER_TOKEN',
  
  // Stream.io region (optional, defaults to us-east-1)
  REGION: 'us-east-1',
};

export const AGORA_CONFIG = {
  // Get your App ID from https://console.agora.io/
  APP_ID: '2d220d40a19d4fea955d4aac662b24d1',
  
  // Agora token (optional for testing, required for production)
  // Generate server-side for security
  TOKEN: null,
};

// Environment-specific configuration
export const getStreamConfig = () => {
  const isDevelopment = __DEV__;
  
  if (isDevelopment) {
    return {
      ...STREAM_CONFIG,
      // Use test credentials for development
      API_KEY: process.env.EXPO_PUBLIC_STREAM_API_KEY || STREAM_CONFIG.API_KEY,
      USER_TOKEN: process.env.EXPO_PUBLIC_STREAM_USER_TOKEN || STREAM_CONFIG.USER_TOKEN,
    };
  }
  
  return STREAM_CONFIG;
};

export const getAgoraConfig = () => {
  const isDevelopment = __DEV__;
  
  if (isDevelopment) {
    return {
      ...AGORA_CONFIG,
      // Use test credentials for development
      APP_ID: process.env.EXPO_PUBLIC_AGORA_APP_ID || AGORA_CONFIG.APP_ID,
      TOKEN: process.env.EXPO_PUBLIC_AGORA_TOKEN || AGORA_CONFIG.TOKEN,
    };
  }
  
  return AGORA_CONFIG;
};

// Helper function to generate Stream user token (should be done server-side)
export const generateStreamUserToken = async (userId: string): Promise<string> => {
  // This should be implemented on your backend
  // For now, return a placeholder
  console.warn('generateStreamUserToken should be implemented server-side');
  return 'placeholder_token';
};

// Helper function to generate Agora token (should be done server-side)
export const generateAgoraToken = async (channelName: string, userId: string): Promise<string> => {
  // This should be implemented on your backend
  // For now, return null (Agora allows null tokens for testing)
  console.warn('generateAgoraToken should be implemented server-side');
  return null;
};
