import { Alert, ToastAndroid, Platform } from 'react-native';

export interface ErrorInfo {
  code?: string;
  message: string;
  details?: any;
  timestamp: Date;
  userId?: string;
  screen?: string;
  action?: string;
}

export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION',
  VALIDATION = 'VALIDATION',
  PERMISSION = 'PERMISSION',
  API = 'API',
  UNKNOWN = 'UNKNOWN',
}

export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

class ErrorService {
  private errorLog: ErrorInfo[] = [];
  private maxLogSize = 100;

  /**
   * Handle and display errors to the user
   */
  public handleError(
    error: any,
    options: {
      type?: ErrorType;
      severity?: ErrorSeverity;
      showAlert?: boolean;
      showToast?: boolean;
      customMessage?: string;
      screen?: string;
      action?: string;
    } = {}
  ): void {
    const {
      type = ErrorType.UNKNOWN,
      severity = ErrorSeverity.MEDIUM,
      showAlert = true,
      showToast = false,
      customMessage,
      screen,
      action,
    } = options;

    // Create error info object
    const errorInfo: ErrorInfo = {
      code: error.code || error.name || 'UNKNOWN_ERROR',
      message: customMessage || error.message || 'An unexpected error occurred',
      details: error,
      timestamp: new Date(),
      screen,
      action,
    };

    // Log error
    this.logError(errorInfo);

    // Show appropriate user feedback
    if (showAlert) {
      this.showErrorAlert(errorInfo, severity);
    } else if (showToast) {
      this.showErrorToast(errorInfo.message);
    }

    // Log to console in development
    if (__DEV__) {
      console.error('Error handled:', errorInfo);
    }
  }

  /**
   * Handle network errors specifically
   */
  public handleNetworkError(error: any, screen?: string, action?: string): void {
    let message = 'Network connection error. Please check your internet connection.';
    
    if (error.message?.includes('timeout')) {
      message = 'Request timed out. Please try again.';
    } else if (error.message?.includes('Network request failed')) {
      message = 'Unable to connect to the server. Please check your internet connection.';
    } else if (error.status === 401) {
      message = 'Your session has expired. Please log in again.';
    } else if (error.status === 403) {
      message = 'You do not have permission to perform this action.';
    } else if (error.status === 404) {
      message = 'The requested resource was not found.';
    } else if (error.status >= 500) {
      message = 'Server error. Please try again later.';
    }

    this.handleError(error, {
      type: ErrorType.NETWORK,
      severity: ErrorSeverity.MEDIUM,
      customMessage: message,
      screen,
      action,
    });
  }

  /**
   * Handle authentication errors
   */
  public handleAuthError(error: any, screen?: string, action?: string): void {
    let message = 'Authentication failed. Please log in again.';
    
    if (error.message?.includes('Invalid credentials')) {
      message = 'Invalid email or password. Please try again.';
    } else if (error.message?.includes('Token expired')) {
      message = 'Your session has expired. Please log in again.';
    }

    this.handleError(error, {
      type: ErrorType.AUTHENTICATION,
      severity: ErrorSeverity.HIGH,
      customMessage: message,
      screen,
      action,
    });
  }

  /**
   * Handle validation errors
   */
  public handleValidationError(error: any, screen?: string, action?: string): void {
    this.handleError(error, {
      type: ErrorType.VALIDATION,
      severity: ErrorSeverity.LOW,
      customMessage: error.message || 'Please check your input and try again.',
      screen,
      action,
      showAlert: false,
      showToast: true,
    });
  }

  /**
   * Handle API errors
   */
  public handleApiError(error: any, screen?: string, action?: string): void {
    let message = 'An error occurred while processing your request.';
    
    if (error.message?.includes('GraphQL')) {
      message = 'Server error. Please try again later.';
    } else if (error.message?.includes('rate limit')) {
      message = 'Too many requests. Please wait a moment and try again.';
    }

    this.handleError(error, {
      type: ErrorType.API,
      severity: ErrorSeverity.MEDIUM,
      customMessage: message,
      screen,
      action,
    });
  }

  /**
   * Show error alert to user
   */
  private showErrorAlert(errorInfo: ErrorInfo, severity: ErrorSeverity): void {
    const title = this.getErrorTitle(severity);
    
    Alert.alert(
      title,
      errorInfo.message,
      [
        {
          text: 'OK',
          style: 'default',
        },
        ...(severity === ErrorSeverity.CRITICAL ? [{
          text: 'Report Issue',
          style: 'default',
          onPress: () => this.reportError(errorInfo),
        }] : []),
      ]
    );
  }

  /**
   * Show error toast (Android only)
   */
  private showErrorToast(message: string): void {
    if (Platform.OS === 'android') {
      ToastAndroid.show(message, ToastAndroid.SHORT);
    }
  }

  /**
   * Get error title based on severity
   */
  private getErrorTitle(severity: ErrorSeverity): string {
    switch (severity) {
      case ErrorSeverity.LOW:
        return 'Notice';
      case ErrorSeverity.MEDIUM:
        return 'Error';
      case ErrorSeverity.HIGH:
        return 'Important';
      case ErrorSeverity.CRITICAL:
        return 'Critical Error';
      default:
        return 'Error';
    }
  }

  /**
   * Log error to internal storage
   */
  private logError(errorInfo: ErrorInfo): void {
    this.errorLog.unshift(errorInfo);
    
    // Keep only the most recent errors
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize);
    }
  }

  /**
   * Get error log
   */
  public getErrorLog(): ErrorInfo[] {
    return [...this.errorLog];
  }

  /**
   * Clear error log
   */
  public clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * Report error (placeholder for crash reporting service)
   */
  private reportError(errorInfo: ErrorInfo): void {
    // Here you would integrate with a crash reporting service
    // like Crashlytics, Sentry, or Bugsnag
    console.log('Reporting error:', errorInfo);
    
    // For now, just show a confirmation
    Alert.alert(
      'Error Reported',
      'Thank you for reporting this issue. We will look into it.',
      [{ text: 'OK' }]
    );
  }

  /**
   * Handle GraphQL errors specifically
   */
  public handleGraphQLError(error: any, screen?: string, action?: string): void {
    let message = 'An error occurred while processing your request.';
    
    if (error.graphQLErrors && error.graphQLErrors.length > 0) {
      const graphQLError = error.graphQLErrors[0];
      message = graphQLError.message || message;
    } else if (error.networkError) {
      this.handleNetworkError(error.networkError, screen, action);
      return;
    }

    this.handleError(error, {
      type: ErrorType.API,
      severity: ErrorSeverity.MEDIUM,
      customMessage: message,
      screen,
      action,
    });
  }

  /**
   * Handle WebSocket errors
   */
  public handleWebSocketError(error: any, screen?: string, action?: string): void {
    this.handleError(error, {
      type: ErrorType.NETWORK,
      severity: ErrorSeverity.LOW,
      customMessage: 'Connection issue. Some features may not work properly.',
      screen,
      action,
      showAlert: false,
      showToast: true,
    });
  }
}

// Export singleton instance
export const errorService = new ErrorService();
export default errorService;
