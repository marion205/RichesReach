/**
 * Production Error Service
 * Handles errors in production with proper logging, reporting, and user feedback
 */

import { Alert } from 'react-native';
import { PRODUCTION_CONFIG } from '../config/production';

export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION',
  VALIDATION = 'VALIDATION',
  API = 'API',
  DATABASE = 'DATABASE',
  UNKNOWN = 'UNKNOWN',
}

export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

interface ErrorInfo {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  screen?: string;
  action?: string;
  userId?: string;
  sessionId?: string;
}

class ProductionErrorService {
  private errorLog: ErrorInfo[] = [];
  private maxLogSize = PRODUCTION_CONFIG.LOGGING.MAX_LOG_SIZE;
  private errorCounts: Map<string, number> = new Map();

  /**
   * Handle and report errors in production
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
      userId?: string;
      sessionId?: string;
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
      userId,
      sessionId,
    } = options;

    // Create error info object
    const errorInfo: ErrorInfo = {
      code: error.code || error.name || 'UNKNOWN_ERROR',
      message: customMessage || error.message || 'An unexpected error occurred',
      details: this.sanitizeErrorDetails(error),
      timestamp: new Date(),
      screen,
      action,
      userId,
      sessionId,
    };

    // Log error
    this.logError(errorInfo);

    // Report to external service if enabled
    if (PRODUCTION_CONFIG.ERROR_REPORTING.ENABLED) {
      this.reportError(errorInfo);
    }

    // Show appropriate user feedback
    if (showAlert) {
      this.showErrorAlert(errorInfo, severity);
    } else if (showToast) {
      this.showErrorToast(errorInfo.message);
    }

    // Track error frequency
    this.trackErrorFrequency(errorInfo.code);
  }

  /**
   * Handle network errors specifically
   */
  public handleNetworkError(error: any, screen?: string, action?: string): void {
    this.handleError(error, {
      type: ErrorType.NETWORK,
      severity: ErrorSeverity.MEDIUM,
      customMessage: 'Network connection error. Please check your internet connection.',
      screen,
      action,
    });
  }

  /**
   * Handle authentication errors
   */
  public handleAuthError(error: any, screen?: string, action?: string): void {
    this.handleError(error, {
      type: ErrorType.AUTHENTICATION,
      severity: ErrorSeverity.HIGH,
      customMessage: 'Authentication failed. Please log in again.',
      screen,
      action,
    });
  }

  /**
   * Handle API errors
   */
  public handleApiError(error: any, screen?: string, action?: string): void {
    this.handleError(error, {
      type: ErrorType.API,
      severity: ErrorSeverity.MEDIUM,
      customMessage: 'Service temporarily unavailable. Please try again later.',
      screen,
      action,
    });
  }

  /**
   * Log error to local storage
   */
  private logError(errorInfo: ErrorInfo): void {
    this.errorLog.push(errorInfo);

    // Maintain log size limit
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(-this.maxLogSize);
    }

    // Log to console only in development
    if (__DEV__) {
      console.error('Production Error:', errorInfo);
    }
  }

  /**
   * Report error to external service (Sentry, etc.)
   */
  private reportError(errorInfo: ErrorInfo): void {
    try {
      // In a real implementation, this would send to Sentry or similar service
      if (PRODUCTION_CONFIG.ERROR_REPORTING.SENTRY_DSN) {
        // Sentry.captureException(errorInfo.details, {
        //   tags: {
        //     errorType: errorInfo.code,
        //     screen: errorInfo.screen,
        //     action: errorInfo.action,
        //   },
        //   user: {
        //     id: errorInfo.userId,
        //   },
        //   extra: {
        //     sessionId: errorInfo.sessionId,
        //     timestamp: errorInfo.timestamp,
        //   },
        // });
      }
    } catch (reportingError) {
      // Don't let error reporting break the app
      if (__DEV__) {
        console.error('Error reporting failed:', reportingError);
      }
    }
  }

  /**
   * Show error alert to user
   */
  private showErrorAlert(errorInfo: ErrorInfo, severity: ErrorSeverity): void {
    const title = this.getErrorTitle(severity);
    const message = this.getErrorMessage(errorInfo, severity);

    Alert.alert(
      title,
      message,
      [
        { text: 'OK', style: 'default' },
        ...(severity === ErrorSeverity.CRITICAL ? [
          { text: 'Report Issue', onPress: () => this.reportIssue(errorInfo) }
        ] : [])
      ]
    );
  }

  /**
   * Show error toast (if toast library is available)
   */
  private showErrorToast(message: string): void {
    // In a real implementation, this would use a toast library
    // Toast.show(message, { type: 'error' });
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
        return 'Important Error';
      case ErrorSeverity.CRITICAL:
        return 'Critical Error';
      default:
        return 'Error';
    }
  }

  /**
   * Get user-friendly error message
   */
  private getErrorMessage(errorInfo: ErrorInfo, severity: ErrorSeverity): string {
    // Return sanitized message for production
    return errorInfo.message;
  }

  /**
   * Sanitize error details to remove sensitive information
   */
  private sanitizeErrorDetails(error: any): any {
    if (!PRODUCTION_CONFIG.ERROR_REPORTING.FILTER_SENSITIVE_DATA) {
      return error;
    }

    // Remove sensitive information
    const sanitized = { ...error };
    
    // Remove common sensitive fields
    const sensitiveFields = ['password', 'token', 'key', 'secret', 'auth', 'credential'];
    sensitiveFields.forEach(field => {
      if (sanitized[field]) {
        sanitized[field] = '[REDACTED]';
      }
    });

    return sanitized;
  }

  /**
   * Track error frequency for monitoring
   */
  private trackErrorFrequency(errorCode: string): void {
    const count = this.errorCounts.get(errorCode) || 0;
    this.errorCounts.set(errorCode, count + 1);
  }

  /**
   * Report issue manually
   */
  private reportIssue(errorInfo: ErrorInfo): void {
    // In a real implementation, this would open a support form or email
    // with pre-filled error information
  }

  /**
   * Get error statistics
   */
  public getErrorStats(): {
    totalErrors: number;
    errorCounts: Map<string, number>;
    recentErrors: ErrorInfo[];
  } {
    return {
      totalErrors: this.errorLog.length,
      errorCounts: new Map(this.errorCounts),
      recentErrors: this.errorLog.slice(-10), // Last 10 errors
    };
  }

  /**
   * Clear error log
   */
  public clearErrorLog(): void {
    this.errorLog = [];
    this.errorCounts.clear();
  }
}

// Export singleton instance
export const productionErrorService = new ProductionErrorService();
export default productionErrorService;
