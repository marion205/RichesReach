/**
 * Feature Flags for RichesReach Mobile App
 * Controls which features are enabled based on environment
 */

import { API_HTTP } from './index';

// Feature flag for AI-powered recommendations
export const FEATURE_FLAGS = {
  // AI Features
  AI_RECOMMENDATIONS_ENABLED: true, // Always enabled (falls back to mock)
  SHOW_AI_BADGE: false, // Show "AI Powered" badge in UI
  
  // Development Features
  SHOW_DEBUG_INFO: __DEV__,
  ENABLE_PERFORMANCE_MONITOR: __DEV__,
  
  // API Features
  USE_GRAPHQL_FALLBACK: true, // Fall back to REST if GraphQL fails
  ENABLE_REQUEST_RETRY: true,
  
  // UI Features
  ENABLE_ANIMATIONS: true,
  ENABLE_HAPTIC_FEEDBACK: true,
};

/**
 * Check if AI features are enabled
 * This can be controlled by server response or environment
 */
export const isAIEnabled = async (): Promise<boolean> => {
  try {
    // Check server status endpoint for AI availability
    const response = await fetch(`${API_HTTP}/api/ai-status`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.ai_enabled === true;
    }
  } catch (error) {
    console.log('Could not check AI status, defaulting to enabled with fallback');
  }
  
  // Default to enabled (with fallback)
  return FEATURE_FLAGS.AI_RECOMMENDATIONS_ENABLED;
};

/**
 * Get AI status badge text
 */
export const getAIStatusText = (isAIEnabled: boolean): string => {
  return isAIEnabled ? 'AI Powered' : 'Mock Data';
};

/**
 * Get AI status badge color
 */
export const getAIStatusColor = (isAIEnabled: boolean): string => {
  return isAIEnabled ? '#34C759' : '#FF9500'; // Green for AI, Orange for mock
};
