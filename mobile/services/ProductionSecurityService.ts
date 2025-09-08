/**
 * Production Security Service
 * Handles security measures for production environment
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { PRODUCTION_CONFIG } from '../config/production';

interface SecurityConfig {
  enableSSL: boolean;
  enableCertificatePinning: boolean;
  maxLoginAttempts: number;
  lockoutDuration: number;
  tokenRefreshInterval: number;
}

interface LoginAttempt {
  timestamp: Date;
  success: boolean;
  ipAddress?: string;
  userAgent?: string;
}

class ProductionSecurityService {
  private config: SecurityConfig;
  private loginAttempts: LoginAttempt[] = [];
  private isLockedOut = false;
  private lockoutEndTime: Date | null = null;

  constructor() {
    this.config = {
      enableSSL: PRODUCTION_CONFIG.SECURITY.ENABLE_SSL_PINNING,
      enableCertificatePinning: PRODUCTION_CONFIG.SECURITY.ENABLE_CERTIFICATE_PINNING,
      maxLoginAttempts: PRODUCTION_CONFIG.SECURITY.MAX_LOGIN_ATTEMPTS,
      lockoutDuration: PRODUCTION_CONFIG.SECURITY.LOCKOUT_DURATION,
      tokenRefreshInterval: PRODUCTION_CONFIG.SECURITY.TOKEN_REFRESH_INTERVAL,
    };
  }

  /**
   * Validate API request security
   */
  public validateApiRequest(url: string, headers: Record<string, string>): boolean {
    // Check if URL is HTTPS in production
    if (this.config.enableSSL && !url.startsWith('https://')) {
      return false;
    }

    // Validate required headers
    if (!headers['Content-Type'] && !headers['content-type']) {
      return false;
    }

    return true;
  }

  /**
   * Validate authentication token
   */
  public async validateToken(token: string): Promise<boolean> {
    try {
      // Check token format
      if (!token || typeof token !== 'string') {
        return false;
      }

      // Check token length (JWT tokens are typically longer)
      if (token.length < 20) {
        return false;
      }

      // Check if token is expired (basic check)
      const tokenParts = token.split('.');
      if (tokenParts.length === 3) {
        try {
          const payload = JSON.parse(atob(tokenParts[1]));
          const currentTime = Math.floor(Date.now() / 1000);
          
          if (payload.exp && payload.exp < currentTime) {
            return false;
          }
        } catch (error) {
          // If we can't parse the token, it's invalid
          return false;
        }
      }

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Record login attempt
   */
  public recordLoginAttempt(success: boolean, ipAddress?: string, userAgent?: string): void {
    const attempt: LoginAttempt = {
      timestamp: new Date(),
      success,
      ipAddress,
      userAgent,
    };

    this.loginAttempts.push(attempt);

    // Clean up old attempts (older than 1 hour)
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    this.loginAttempts = this.loginAttempts.filter(
      attempt => attempt.timestamp > oneHourAgo
    );

    // Check if user should be locked out
    this.checkLockout();
  }

  /**
   * Check if user is locked out
   */
  public isUserLockedOut(): boolean {
    if (this.isLockedOut && this.lockoutEndTime) {
      if (new Date() > this.lockoutEndTime) {
        this.isLockedOut = false;
        this.lockoutEndTime = null;
        return false;
      }
      return true;
    }
    return false;
  }

  /**
   * Check if user should be locked out based on failed attempts
   */
  private checkLockout(): void {
    const recentAttempts = this.loginAttempts.filter(
      attempt => attempt.timestamp > new Date(Date.now() - 15 * 60 * 1000) // Last 15 minutes
    );

    const failedAttempts = recentAttempts.filter(attempt => !attempt.success);

    if (failedAttempts.length >= this.config.maxLoginAttempts) {
      this.isLockedOut = true;
      this.lockoutEndTime = new Date(Date.now() + this.config.lockoutDuration);
    }
  }

  /**
   * Get remaining lockout time in seconds
   */
  public getRemainingLockoutTime(): number {
    if (!this.isLockedOut || !this.lockoutEndTime) {
      return 0;
    }

    const remaining = this.lockoutEndTime.getTime() - Date.now();
    return Math.max(0, Math.floor(remaining / 1000));
  }

  /**
   * Sanitize user input
   */
  public sanitizeInput(input: string): string {
    if (!input || typeof input !== 'string') {
      return '';
    }

    // Remove potentially dangerous characters
    return input
      .replace(/[<>]/g, '') // Remove HTML tags
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/on\w+=/gi, '') // Remove event handlers
      .trim();
  }

  /**
   * Validate email format
   */
  public validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate password strength
   */
  public validatePassword(password: string): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }

    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }

    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }

    if (!/\d/.test(password)) {
      errors.push('Password must contain at least one number');
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  /**
   * Encrypt sensitive data (basic implementation)
   */
  public async encryptData(data: string): Promise<string> {
    try {
      // In a real implementation, this would use proper encryption
      // For now, we'll use a simple base64 encoding
      return btoa(data);
    } catch (error) {
      throw new Error('Failed to encrypt data');
    }
  }

  /**
   * Decrypt sensitive data (basic implementation)
   */
  public async decryptData(encryptedData: string): Promise<string> {
    try {
      // In a real implementation, this would use proper decryption
      // For now, we'll use a simple base64 decoding
      return atob(encryptedData);
    } catch (error) {
      throw new Error('Failed to decrypt data');
    }
  }

  /**
   * Store secure data
   */
  public async storeSecureData(key: string, data: string): Promise<void> {
    try {
      const encryptedData = await this.encryptData(data);
      await AsyncStorage.setItem(key, encryptedData);
    } catch (error) {
      throw new Error('Failed to store secure data');
    }
  }

  /**
   * Retrieve secure data
   */
  public async getSecureData(key: string): Promise<string | null> {
    try {
      const encryptedData = await AsyncStorage.getItem(key);
      if (!encryptedData) {
        return null;
      }
      return await this.decryptData(encryptedData);
    } catch (error) {
      return null;
    }
  }

  /**
   * Clear secure data
   */
  public async clearSecureData(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      // Ignore errors when clearing data
    }
  }

  /**
   * Get security configuration
   */
  public getSecurityConfig(): SecurityConfig {
    return { ...this.config };
  }

  /**
   * Update security configuration
   */
  public updateSecurityConfig(newConfig: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get security statistics
   */
  public getSecurityStats(): {
    totalLoginAttempts: number;
    failedAttempts: number;
    isLockedOut: boolean;
    remainingLockoutTime: number;
  } {
    const failedAttempts = this.loginAttempts.filter(attempt => !attempt.success);

    return {
      totalLoginAttempts: this.loginAttempts.length,
      failedAttempts: failedAttempts.length,
      isLockedOut: this.isLockedOut,
      remainingLockoutTime: this.getRemainingLockoutTime(),
    };
  }
}

// Export singleton instance
export const productionSecurityService = new ProductionSecurityService();
export default productionSecurityService;
