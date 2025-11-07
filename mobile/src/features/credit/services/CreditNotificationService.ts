/**
 * Credit Notification Service
 * Handles payment reminders and credit score change notifications
 */

import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

const CREDIT_NOTIFICATION_STORAGE_KEY = 'credit_notification_preferences';

export interface CreditNotificationPreferences {
  paymentReminders: boolean;
  scoreChangeAlerts: boolean;
  utilizationAlerts: boolean;
  daysBeforePayment: number; // e.g., 3 days before payment due
}

class CreditNotificationService {
  private static instance: CreditNotificationService;

  private constructor() {
    // Ensure notification handler is set up
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
  }

  static getInstance(): CreditNotificationService {
    if (!CreditNotificationService.instance) {
      CreditNotificationService.instance = new CreditNotificationService();
    }
    return CreditNotificationService.instance;
  }

  async getPreferences(): Promise<CreditNotificationPreferences> {
    try {
      const stored = await AsyncStorage.getItem(CREDIT_NOTIFICATION_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Error loading credit notification preferences:', error);
    }
    // Default preferences
    return {
      paymentReminders: true,
      scoreChangeAlerts: true,
      utilizationAlerts: true,
      daysBeforePayment: 3,
    };
  }

  async savePreferences(preferences: CreditNotificationPreferences): Promise<void> {
    try {
      await AsyncStorage.setItem(CREDIT_NOTIFICATION_STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      console.error('Error saving credit notification preferences:', error);
    }
  }

  async schedulePaymentReminder(
    cardName: string,
    dueDate: Date,
    daysBefore: number = 3
  ): Promise<string | null> {
    try {
      const preferences = await this.getPreferences();
      if (!preferences.paymentReminders) {
        return null;
      }

      const { status } = await Notifications.getPermissionsAsync();
      if (status !== 'granted') {
        const { status: newStatus } = await Notifications.requestPermissionsAsync();
        if (newStatus !== 'granted') {
          console.warn('Permission to send notifications not granted for payment reminders.');
          return null;
        }
      }

      const reminderDate = new Date(dueDate);
      reminderDate.setDate(reminderDate.getDate() - daysBefore);

      // Only schedule if reminder date is in the future
      if (reminderDate <= new Date()) {
        return null;
      }

      const trigger: Notifications.DateTriggerInput = {
        date: reminderDate,
      };

      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title: `💳 Payment Reminder: ${cardName}`,
          body: `Your payment is due in ${daysBefore} days. Pay on time to boost your credit score!`,
          data: { type: 'credit_payment_reminder', cardName, dueDate: dueDate.toISOString() },
          sound: 'default',
        },
        trigger,
      });

      return notificationId;
    } catch (error) {
      console.error('Error scheduling payment reminder:', error);
      return null;
    }
  }

  async scheduleUtilizationAlert(
    cardName: string,
    currentUtilization: number
  ): Promise<string | null> {
    try {
      const preferences = await this.getPreferences();
      if (!preferences.utilizationAlerts || currentUtilization <= 0.5) {
        return null;
      }

      const { status } = await Notifications.getPermissionsAsync();
      if (status !== 'granted') {
        return null;
      }

      const trigger: Notifications.TimeIntervalTriggerInput = {
        seconds: 60, // Show immediately
      };

      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title: `⚠️ High Credit Utilization`,
          body: `${cardName} utilization is ${Math.round(currentUtilization * 100)}%. Aim for under 30% to improve your score.`,
          data: { type: 'credit_utilization_alert', cardName, utilization: currentUtilization },
          sound: 'default',
        },
        trigger,
      });

      return notificationId;
    } catch (error) {
      console.error('Error scheduling utilization alert:', error);
      return null;
    }
  }

  async scheduleScoreChangeAlert(
    oldScore: number,
    newScore: number
  ): Promise<string | null> {
    try {
      const preferences = await this.getPreferences();
      if (!preferences.scoreChangeAlerts) {
        return null;
      }

      const { status } = await Notifications.getPermissionsAsync();
      if (status !== 'granted') {
        return null;
      }

      const change = newScore - oldScore;
      const changeText = change > 0 ? `+${change}` : `${change}`;
      const emoji = change > 0 ? '📈' : change < 0 ? '📉' : '➡️';

      const trigger: Notifications.TimeIntervalTriggerInput = {
        seconds: 60,
      };

      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title: `${emoji} Credit Score Update`,
          body: `Your credit score changed: ${oldScore} → ${newScore} (${changeText} points)`,
          data: { type: 'credit_score_change', oldScore, newScore, change },
          sound: 'default',
        },
        trigger,
      });

      return notificationId;
    } catch (error) {
      console.error('Error scheduling score change alert:', error);
      return null;
    }
  }

  async cancelAllCreditNotifications(): Promise<void> {
    try {
      const allNotifications = await Notifications.getAllScheduledNotificationsAsync();
      const creditNotifications = allNotifications.filter(
        notif => notif.content.data?.type?.startsWith('credit_')
      );
      
      for (const notif of creditNotifications) {
        await Notifications.cancelScheduledNotificationAsync(notif.identifier);
      }
    } catch (error) {
      console.error('Error canceling credit notifications:', error);
    }
  }
}

export const creditNotificationService = CreditNotificationService.getInstance();

