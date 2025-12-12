/**
 * RAHA Notification Service
 * Handles push token registration and notification handling for RAHA signals and backtests
 */
import * as Notifications from 'expo-notifications';
import logger from '../utils/logger';
import { Platform } from 'react-native';

class RAHANotificationService {
  private static instance: RAHANotificationService;
  private pushToken: string | null = null;
  private isInitialized = false;

  private constructor() {}

  static getInstance(): RAHANotificationService {
    if (!RAHANotificationService.instance) {
      RAHANotificationService.instance = new RAHANotificationService();
    }
    return RAHANotificationService.instance;
  }

  /**
   * Initialize and register push token with backend
   * @param updatePreferencesMutation - Apollo mutation function for updating preferences
   */
  async initialize(updatePreferencesMutation?: any): Promise<boolean> {
    if (this.isInitialized) {
      return true;
    }

    try {
      // Request permissions
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        logger.warn('⚠️  Push notification permissions not granted');
        return false;
      }

      // Get push token
      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID,
      });

      this.pushToken = tokenData.data;
      logger.info(`✅ Got push token: ${this.pushToken.substring(0, 20)}...`);

      // Register token with backend (if mutation provided)
      if (updatePreferencesMutation && this.pushToken) {
        try {
          await updatePreferencesMutation({
            variables: {
              pushToken: this.pushToken,
              pushEnabled: true,
            },
          });
          logger.info('✅ Push token registered with backend');
        } catch (error) {
          logger.error('❌ Failed to register push token:', error);
        }
      } else if (this.pushToken) {
        logger.info(
          '📝 Push token obtained, but no mutation provided. Will register when preferences screen opens.'
        );
      }

      // Set up notification handlers
      this.setupNotificationHandlers();

      this.isInitialized = true;
      return true;
    } catch (error) {
      logger.error('❌ Error initializing RAHA notifications:', error);
      return false;
    }
  }

  /**
   * Set up notification handlers for RAHA-specific notifications
   */
  private setupNotificationHandlers(): void {
    // Handle notifications received while app is in foreground
    Notifications.addNotificationReceivedListener(notification => {
      const data = notification.request.content.data;

      if (data?.type === 'raha_signal') {
        logger.info('📱 Received RAHA signal notification:', data.symbol);
        // You can emit an event here for the app to handle
        // e.g., navigate to The Whisper screen with the symbol
      } else if (data?.type === 'raha_backtest') {
        logger.info('📱 Received backtest completion notification:', data.backtest_id);
        // You can emit an event here for the app to handle
        // e.g., navigate to backtest results
      }
    });

    // Handle user interactions with notifications
    Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;

      if (data?.type === 'raha_signal') {
        logger.info('👆 User tapped RAHA signal notification:', data.symbol);
        // Navigate to The Whisper screen with the symbol
        const { DeviceEventEmitter } = require('react-native');
        DeviceEventEmitter.emit('navigateToWhisper', { symbol: data.symbol });
      } else if (data?.type === 'raha_backtest') {
        logger.info('👆 User tapped backtest notification:', data.backtest_id);
        // Navigate to backtest results
        const { DeviceEventEmitter } = require('react-native');
        DeviceEventEmitter.emit('navigateToBacktest', {
          backtestId: data.backtest_id,
        });
      }
    });
  }

  /**
   * Get the current push token
   */
  getPushToken(): string | null {
    return this.pushToken;
  }

  /**
   * Check if notifications are initialized
   */
  isReady(): boolean {
    return this.isInitialized && this.pushToken !== null;
  }
}

export default RAHANotificationService.getInstance();
