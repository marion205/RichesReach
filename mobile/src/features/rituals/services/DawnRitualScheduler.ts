/**
 * Dawn Ritual Scheduler
 * Schedules daily dawn ritual notifications
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';

const DAWN_RITUAL_STORAGE_KEY = 'dawn_ritual_preferences';
const DAWN_RITUAL_NOTIFICATION_ID = 'dawn_ritual_daily';

export interface DawnRitualPreferences {
  enabled: boolean;
  time: string; // HH:MM format, e.g., "07:00"
  lastPerformed?: string; // ISO timestamp
}

class DawnRitualScheduler {
  private static instance: DawnRitualScheduler;

  static getInstance(): DawnRitualScheduler {
    if (!DawnRitualScheduler.instance) {
      DawnRitualScheduler.instance = new DawnRitualScheduler();
    }
    return DawnRitualScheduler.instance;
  }

  /**
   * Schedule daily dawn ritual notification
   */
  async scheduleDailyRitual(preferences: DawnRitualPreferences): Promise<void> {
    try {
      // Cancel existing notification
      await Notifications.cancelScheduledNotificationAsync(DAWN_RITUAL_NOTIFICATION_ID);

      if (!preferences.enabled) {
        await AsyncStorage.setItem(DAWN_RITUAL_STORAGE_KEY, JSON.stringify(preferences));
        return;
      }

      // Parse time (HH:MM)
      const [hours, minutes] = preferences.time.split(':').map(Number);

      // Schedule daily notification
      await Notifications.scheduleNotificationAsync({
        identifier: DAWN_RITUAL_NOTIFICATION_ID,
        content: {
          title: 'Ritual Dawn',
          body: 'Your portfolio moved overnight. 60 seconds to clarity.',
          data: {
            type: 'dawn_ritual',
            action: 'open_ritual',
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
          channelId: 'dawn_ritual',
        }),
      });

      // Save preferences
      await AsyncStorage.setItem(DAWN_RITUAL_STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      logger.error('[DawnRitual] Failed to schedule ritual:', error);
    }
  }

  /**
   * Get current preferences
   */
  async getPreferences(): Promise<DawnRitualPreferences> {
    try {
      const stored = await AsyncStorage.getItem(DAWN_RITUAL_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
      // Default preferences
      return {
        enabled: true,
        time: '07:00', // 7 AM default
      };
    } catch (error) {
      logger.error('[DawnRitual] Failed to get preferences:', error);
      return {
        enabled: true,
        time: '07:00',
      };
    }
  }

  /**
   * Mark ritual as performed
   */
  async markPerformed(): Promise<void> {
    try {
      const preferences = await this.getPreferences();
      preferences.lastPerformed = new Date().toISOString();
      await AsyncStorage.setItem(DAWN_RITUAL_STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      logger.error('[DawnRitual] Failed to mark as performed:', error);
    }
  }

  /**
   * Check if ritual should be performed today
   */
  async shouldPerformToday(): Promise<boolean> {
    try {
      const preferences = await this.getPreferences();
      if (!preferences.enabled) {
        return false;
      }

      const lastPerformed = preferences.lastPerformed;
      if (!lastPerformed) {
        return true; // Never performed, should perform
      }

      const lastDate = new Date(lastPerformed);
      const today = new Date();
      
      // Check if last performed was today
      return (
        lastDate.getDate() !== today.getDate() ||
        lastDate.getMonth() !== today.getMonth() ||
        lastDate.getFullYear() !== today.getFullYear()
      );
    } catch (error) {
      logger.error('[DawnRitual] Failed to check if should perform:', error);
      return false;
    }
  }

  /**
   * Cancel scheduled ritual
   */
  async cancelScheduledRitual(): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(DAWN_RITUAL_NOTIFICATION_ID);
      const preferences = await this.getPreferences();
      preferences.enabled = false;
      await AsyncStorage.setItem(DAWN_RITUAL_STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      logger.error('[DawnRitual] Failed to cancel ritual:', error);
    }
  }
}

export const dawnRitualScheduler = DawnRitualScheduler.getInstance();

