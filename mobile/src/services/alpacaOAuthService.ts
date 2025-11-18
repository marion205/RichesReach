/**
 * Alpaca OAuth Service
 * Handles OAuth flow for Alpaca Connect
 */
import { Linking, Alert } from 'react-native';
import { API_BASE } from '../config/api';
import { alpacaAnalytics } from './alpacaAnalyticsService';

const OAUTH_INITIATE_URL = `${API_BASE}/api/auth/alpaca/initiate`;

export interface OAuthResult {
  success: boolean;
  accountId?: string;
  error?: string;
  errorDescription?: string;
}

/**
 * Initiate Alpaca OAuth flow
 * Opens browser to Alpaca authorization page
 */
export const initiateAlpacaOAuth = async (redirectUri?: string): Promise<void> => {
  try {
    alpacaAnalytics.track('connect_oauth_started');
    
    // Build OAuth initiation URL
    const params = new URLSearchParams();
    if (redirectUri) {
      params.append('redirect_uri', redirectUri);
    }
    
    const url = `${OAUTH_INITIATE_URL}${params.toString() ? `?${params.toString()}` : ''}`;
    
    // Open in browser (will redirect to Alpaca)
    const canOpen = await Linking.canOpenURL(url);
    if (!canOpen) {
      throw new Error('Cannot open OAuth URL');
    }
    
    await Linking.openURL(url);
    
  } catch (error: any) {
    console.error('Failed to initiate OAuth flow:', error);
    alpacaAnalytics.track('connect_oauth_error', {
      error: 'initiation_failed',
      errorCode: 'INITIATION_ERROR',
      message: error?.message,
    });
    
    Alert.alert(
      'Connection Error',
      'Failed to start Alpaca connection. Please try again.',
      [{ text: 'OK' }]
    );
    
    throw error;
  }
};

/**
 * Handle OAuth callback from deep link
 * Parses URL parameters and returns result
 */
export const handleOAuthCallback = (url: string): OAuthResult => {
  try {
    // Parse URL (format: richesreach://auth/alpaca/callback?code=...&state=... or ?error=...)
    const urlObj = new URL(url);
    const params = new URLSearchParams(urlObj.search);
    
    // Check for errors
    const error = params.get('error');
    if (error) {
      const errorDescription = params.get('error_description') || 'OAuth authorization failed';
      
      alpacaAnalytics.track('connect_oauth_error', {
        error,
        errorCode: 'OAUTH_ERROR',
        errorDescription,
      });
      
      return {
        success: false,
        error,
        errorDescription,
      };
    }
    
    // Check for success
    const connected = params.get('connected');
    const accountId = params.get('account_id');
    
    if (connected === 'true' && accountId) {
      alpacaAnalytics.track('connect_oauth_success', { accountId });
      alpacaAnalytics.track('connect_account_linked', { accountId });
      
      return {
        success: true,
        accountId,
      };
    }
    
    // Unknown state
    return {
      success: false,
      error: 'unknown_state',
      errorDescription: 'OAuth callback in unknown state',
    };
    
  } catch (error: any) {
    console.error('Failed to handle OAuth callback:', error);
    
    alpacaAnalytics.track('connect_oauth_error', {
      error: 'callback_parse_failed',
      errorCode: 'CALLBACK_ERROR',
      message: error?.message,
    });
    
    return {
      success: false,
      error: 'callback_parse_failed',
      errorDescription: error?.message || 'Failed to parse OAuth callback',
    };
  }
};

/**
 * Check if URL is an OAuth callback
 */
export const isOAuthCallback = (url: string): boolean => {
  try {
    const urlObj = new URL(url);
    return urlObj.pathname.includes('/auth/alpaca/callback');
  } catch {
    return false;
  }
};

