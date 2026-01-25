/**
 * Daily Brief Notification Scheduler
 * Schedules daily morning reminders for Daily Brief
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';

const DAILY_BRIEF_STORAGE_KEY = 'daily_brief_notification_preferences';
const DAILY_BRIEF_NOTIFICATION_ID = 'daily_brief_morning_reminder';

export interface DailyBriefNotificationPreferences {
  enabled: boolean;
  time: string; // HH:MM format, e.g., "08:00"
}

class DailyBriefNotificationScheduler {
  private static instance: DailyBriefNotificationScheduler;

  static getInstance(): DailyBriefNotificationScheduler {
    if (!DailyBriefNotificationScheduler.instance) {
      DailyBriefNotificationScheduler.instance = new DailyBriefNotificationScheduler();
    }
    return DailyBriefNotificationScheduler.instance;
  }

  /**
   * Schedule daily morning reminder for Daily Brief
   */
  async scheduleDailyReminder(preferences: DailyBriefNotificationPreferences): Promise<void> {
    try {
      // Cancel existing notification
      await Notifications.cancelScheduledNotificationAsync(DAILY_BRIEF_NOTIFICATION_ID);

      if (!preferences.enabled) {
        await AsyncStorage.setItem(DAILY_BRIEF_STORAGE_KEY, JSON.stringify(preferences));
        return;
      }

      // Request permissions
      const { status } = await Notifications.getPermissionsAsync();
      if (status !== 'granted') {
        const { status: newStatus } = await Notifications.requestPermissionsAsync();
        if (newStatus !== 'granted') {
          logger.warn('[DailyBrief] Notification permission not granted');
          return;
        }
      }

      // Parse time (HH:MM)
      const [hours, minutes] = preferences.time.split(':').map(Number);

      // Schedule daily notification
      await Notifications.scheduleNotificationAsync({
        identifier: DAILY_BRIEF_NOTIFICATION_ID,
        content: {
          title: '📚 Your Daily Brief is ready',
          body: 'Time for your 2-minute investing guide!',
          data: {
            type: 'daily_brief_reminder',
            screen: 'daily-brief',
          },
          sound: true,
        },
        trigger: {
          type: 'calendar',
          hour: hours,
          minute: minutes,
          repeats: true,
        } as Notifications.CalendarTriggerInput,
        ...(Platform.OS === 'android' && {
          channelId: 'daily_brief',
        }),
      });

      // Save preferences
      await AsyncStorage.setItem(DAILY_BRIEF_STORAGE_KEY, JSON.stringify(preferences));

      // Scheduled successfully - no need to log
    } catch (error) {
      logger.error('[DailyBrief] Failed to schedule reminder:', error);
    }
  }

  /**
   * Get current preferences
   */
  async getPreferences(): Promise<DailyBriefNotificationPreferences> {
    try {
      const stored = await AsyncStorage.getItem(DAILY_BRIEF_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      logger.error('[DailyBrief] Error loading preferences:', error);
    }
    
    // Default preferences
    return {
      enabled: true,
      time: '08:00', // 8 AM default
    };
  }

  /**
   * Cancel all Daily Brief notifications
   */
  async cancelAll(): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(DAILY_BRIEF_NOTIFICATION_ID);
      await AsyncStorage.removeItem(DAILY_BRIEF_STORAGE_KEY);
      // Cancelled successfully - no need to log
    } catch (error) {
      logger.error('[DailyBrief] Error cancelling notifications:', error);
    }
  }
}

export const dailyBriefNotificationScheduler = DailyBriefNotificationScheduler.getInstance();

