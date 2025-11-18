/**
 * User-friendly error messages with actionable guidance
 */

export interface ErrorContext {
  operation?: string;
  errorType?: 'network' | 'validation' | 'account' | 'server' | 'unknown';
  details?: string;
}

/**
 * Get user-friendly error message based on error type
 */
export const getUserFriendlyError = (error: unknown, context?: ErrorContext): string => {
  const errorMessage = error instanceof Error ? error.message : String(error);
  const op = context?.operation || 'operation';
  const errorType = context?.errorType || detectErrorType(errorMessage);

  switch (errorType) {
    case 'network':
      return `Unable to connect. Please check your internet connection and try again.`;
    
    case 'validation':
      return context?.details || `Please check your input and try again.`;
    
    case 'account':
      if (errorMessage.includes('approved') || errorMessage.includes('KYC')) {
        return `Your account needs verification. Please complete the KYC process to continue.`;
      }
      if (errorMessage.includes('connect') || errorMessage.includes('linked')) {
        return `Please connect your Alpaca account to place orders.`;
      }
      return `Account issue: ${errorMessage}. Please contact support if this persists.`;
    
    case 'server':
      return `Server error occurred. Our team has been notified. Please try again in a few moments.`;
    
    default:
      // For unknown errors, provide a helpful message
      if (errorMessage.includes('timeout')) {
        return `Request timed out. Please try again.`;
      }
      if (errorMessage.includes('429') || errorMessage.includes('rate limit')) {
        return `Too many requests. Please wait a moment and try again.`;
      }
      return `Something went wrong with ${op}. Please try again.`;
  }
};

/**
 * Detect error type from error message
 */
const detectErrorType = (message: string): ErrorContext['errorType'] => {
  const lower = message.toLowerCase();
  
  if (lower.includes('network') || lower.includes('fetch') || lower.includes('connection')) {
    return 'network';
  }
  if (lower.includes('validation') || lower.includes('invalid') || lower.includes('required')) {
    return 'validation';
  }
  if (lower.includes('account') || lower.includes('auth') || lower.includes('unauthorized')) {
    return 'account';
  }
  if (lower.includes('500') || lower.includes('server error') || lower.includes('internal')) {
    return 'server';
  }
  
  return 'unknown';
};

/**
 * Get actionable next steps for error recovery
 */
export const getErrorRecoverySteps = (errorType: ErrorContext['errorType']): string[] => {
  switch (errorType) {
    case 'network':
      return [
        'Check your internet connection',
        'Try switching between WiFi and mobile data',
        'Restart the app if the issue persists',
      ];
    
    case 'validation':
      return [
        'Review the highlighted fields',
        'Ensure all required fields are filled',
        'Check that values are within acceptable ranges',
      ];
    
    case 'account':
      return [
        'Verify your account is connected',
        'Complete any pending verification steps',
        'Contact support if you need assistance',
      ];
    
    case 'server':
      return [
        'Wait a few moments and try again',
        'Check our status page for known issues',
        'Contact support if the problem continues',
      ];
    
    default:
      return [
        'Try again in a moment',
        'Check your connection',
        'Contact support if the issue persists',
      ];
  }
};

