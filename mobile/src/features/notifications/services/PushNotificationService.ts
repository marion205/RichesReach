import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';
// Configure notification behavior
Notifications.setNotificationHandler({
handleNotification: async () => ({
shouldShowAlert: true,
shouldPlaySound: true,
shouldSetBadge: true,
shouldShowBanner: true,
shouldShowList: true,
}),
});
export interface NotificationData {
type: 'price_alert' | 'mention' | 'discussion_update' | 'follow' | 'general' | 
      'transaction_confirmation' | 'governance_proposal' | 'payment_reminder' | 
      'referral_reward' | 'order_filled' | 'order_cancelled';
title: string;
body: string;
data?: any;
}
export interface PriceAlert {
symbol: string;
currentPrice: number;
targetPrice: number;
alertType: 'above' | 'below';
}
class PushNotificationService {
private expoPushToken: string | null = null;
private isInitialized = false;
/**
* Initialize push notifications
*/
public async initialize(): Promise<boolean> {
try {
if (this.isInitialized) {
return true;
}
// Check if device supports push notifications
if (!Device.isDevice) {
return false;
}
// Check if running in Expo Go (which has limited notification support)
if (__DEV__ && !Constants.expoConfig?.extra?.eas) {
// Return true but with limited functionality
this.isInitialized = true;
return true;
}
// Request permissions
const { status: existingStatus } = await Notifications.getPermissionsAsync();
let finalStatus = existingStatus;
if (existingStatus !== 'granted') {
const { status } = await Notifications.requestPermissionsAsync();
finalStatus = status;
}
if (finalStatus !== 'granted') {
return false;
}
// Get the push token
const token = await Notifications.getExpoPushTokenAsync({
projectId: Constants.expoConfig?.extra?.eas?.projectId,
});
this.expoPushToken = token.data;
// Save token to storage
await AsyncStorage.setItem('expoPushToken', this.expoPushToken);
// Configure notification channels for Android
if (Platform.OS === 'android') {
await this.setupAndroidChannels();
}
this.isInitialized = true;
return true;
} catch (error) {
logger.error('Error initializing push notifications:', error);
return false;
}
}
/**
* Setup Android notification channels
*/
private async setupAndroidChannels(): Promise<void> {
try {
await Notifications.setNotificationChannelAsync('price-alerts', {
name: 'Price Alerts',
description: 'Notifications for stock price alerts',
importance: Notifications.AndroidImportance.HIGH,
vibrationPattern: [0, 250, 250, 250],
lightColor: '#FF231F7C',
});
await Notifications.setNotificationChannelAsync('mentions', {
name: 'Mentions',
description: 'Notifications when someone mentions you',
importance: Notifications.AndroidImportance.HIGH,
vibrationPattern: [0, 250, 250, 250],
lightColor: '#FF231F7C',
});
await Notifications.setNotificationChannelAsync('discussions', {
name: 'Discussions',
description: 'Notifications for discussion updates',
importance: Notifications.AndroidImportance.DEFAULT,
});
await Notifications.setNotificationChannelAsync('transactions', {
name: 'Transactions',
description: 'Transaction confirmations and updates',
importance: Notifications.AndroidImportance.HIGH,
vibrationPattern: [0, 250, 250, 250],
lightColor: '#FF231F7C',
});
await Notifications.setNotificationChannelAsync('governance', {
name: 'Governance',
description: 'Governance proposals and voting updates',
importance: Notifications.AndroidImportance.HIGH,
vibrationPattern: [0, 250, 250, 250],
lightColor: '#FF231F7C',
});
await Notifications.setNotificationChannelAsync('payments', {
name: 'Payments',
description: 'Payment reminders and updates',
importance: Notifications.AndroidImportance.DEFAULT,
vibrationPattern: [0, 250, 250, 250],
lightColor: '#FF231F7C',
});
await Notifications.setNotificationChannelAsync('follows', {
name: 'Follows',
description: 'Notifications for new followers',
importance: Notifications.AndroidImportance.DEFAULT,
vibrationPattern: [0, 250, 250, 250],
lightColor: '#FF231F7C',
});
} catch (error) {
logger.error('Error setting up Android channels:', error);
}
}
/**
* Get the push token
*/
public getPushToken(): string | null {
return this.expoPushToken;
}
/**
* Send a local notification
*/
public async sendLocalNotification(notification: NotificationData): Promise<void> {
try {
const channelId = this.getChannelId(notification.type);
await Notifications.scheduleNotificationAsync({
content: {
title: notification.title,
body: notification.body,
data: notification.data || {},
sound: 'default',
},
trigger: null, // Show immediately
...(Platform.OS === 'android' && { channelId }),
});
} catch (error) {
logger.error('Error sending local notification:', error);
}
}
/**
* Send a price alert notification
*/
public async sendPriceAlert(alert: PriceAlert): Promise<void> {
const title = `Price Alert: ${alert.symbol}`;
const body = `${alert.symbol} is now $${alert.currentPrice.toFixed(2)} (${alert.alertType === 'above' ? 'above' : 'below'} $${alert.targetPrice.toFixed(2)})`;
await this.sendLocalNotification({
type: 'price_alert',
title,
body,
data: {
symbol: alert.symbol,
currentPrice: alert.currentPrice,
targetPrice: alert.targetPrice,
alertType: alert.alertType,
},
});
}
/**
* Send a mention notification
*/
public async sendMentionNotification(mentionerName: string, discussionTitle: string): Promise<void> {
const title = `You were mentioned by ${mentionerName}`;
const body = `In discussion: ${discussionTitle}`;
await this.sendLocalNotification({
type: 'mention',
title,
body,
data: {
mentionerName,
discussionTitle,
},
});
}
/**
* Send a discussion update notification
*/
public async sendDiscussionUpdateNotification(discussionTitle: string, updateType: string): Promise<void> {
const title = `Discussion Update: ${discussionTitle}`;
const body = `Someone ${updateType} the discussion`;
await this.sendLocalNotification({
type: 'discussion_update',
title,
body,
data: {
discussionTitle,
updateType,
},
});
}
/**
* Send a follow notification
*/
public async sendFollowNotification(followerName: string): Promise<void> {
const title = `New Follower`;
const body = `${followerName} started following you`;
await this.sendLocalNotification({
type: 'follow',
title,
body,
data: {
followerName,
},
});
}

/**
* Send a transaction confirmation notification
*/
public async sendTransactionConfirmation(
  transactionType: 'buy' | 'sell' | 'deposit' | 'withdrawal',
  symbol: string,
  amount: number,
  price?: number
): Promise<void> {
  const typeLabels = {
    buy: 'Purchase',
    sell: 'Sale',
    deposit: 'Deposit',
    withdrawal: 'Withdrawal',
  };
  const title = `${typeLabels[transactionType]} Confirmed`;
  const body = price 
    ? `${transactionType === 'buy' ? 'Bought' : 'Sold'} ${amount} ${symbol} at $${price.toFixed(2)}`
    : `${typeLabels[transactionType]} of $${amount.toFixed(2)} completed`;
  
  await this.sendLocalNotification({
    type: 'transaction_confirmation',
    title,
    body,
    data: {
      transactionType,
      symbol,
      amount,
      price,
    },
  });
}

/**
* Send a governance proposal notification
*/
public async sendGovernanceNotification(
  proposalTitle: string,
  proposalId: string,
  action: 'created' | 'voting_started' | 'voting_ended' | 'executed'
): Promise<void> {
  const actionLabels = {
    created: 'New Proposal',
    voting_started: 'Voting Started',
    voting_ended: 'Voting Ended',
    executed: 'Proposal Executed',
  };
  const title = actionLabels[action];
  const body = `${proposalTitle}${action === 'voting_started' ? ' - Cast your vote!' : ''}`;
  
  await this.sendLocalNotification({
    type: 'governance_proposal',
    title,
    body,
    data: {
      proposalId,
      proposalTitle,
      action,
    },
  });
}

/**
* Send a payment reminder notification
*/
public async sendPaymentReminder(
  billName: string,
  amount: number,
  dueDate: Date,
  daysUntilDue: number
): Promise<void> {
  const urgency = daysUntilDue <= 1 ? 'urgent' : daysUntilDue <= 3 ? 'soon' : 'upcoming';
  const title = urgency === 'urgent' ? '⚠️ Payment Due Today!' : 
                urgency === 'soon' ? 'Payment Due Soon' : 
                'Upcoming Payment';
  const body = `${billName}: $${amount.toFixed(2)} due ${daysUntilDue === 0 ? 'today' : `in ${daysUntilDue} day${daysUntilDue > 1 ? 's' : ''}`}`;
  
  await this.sendLocalNotification({
    type: 'payment_reminder',
    title,
    body,
    data: {
      billName,
      amount,
      dueDate: dueDate.toISOString(),
      daysUntilDue,
      urgency,
    },
  });
}

/**
* Schedule a payment reminder
*/
public async schedulePaymentReminder(
  billName: string,
  amount: number,
  dueDate: Date
): Promise<string> {
  const now = new Date();
  const daysUntilDue = Math.ceil((dueDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  
  // Schedule reminder 1 day before, 3 days before, and on due date
  const reminderDays = [Math.max(0, daysUntilDue - 3), Math.max(0, daysUntilDue - 1), Math.max(0, daysUntilDue)];
  const reminderTimes = reminderDays
    .filter(days => days >= 0)
    .map(days => {
      const reminderDate = new Date(dueDate);
      reminderDate.setDate(reminderDate.getDate() - days);
      return reminderDate;
    });

  const notificationIds: string[] = [];
  for (const reminderTime of reminderTimes) {
    if (reminderTime > now) {
      const notificationId = await this.scheduleNotification(
        {
          type: 'payment_reminder',
          title: daysUntilDue <= 1 ? '⚠️ Payment Due!' : 'Payment Reminder',
          body: `${billName}: $${amount.toFixed(2)} due ${daysUntilDue <= 1 ? 'today' : `in ${daysUntilDue} day${daysUntilDue > 1 ? 's' : ''}`}`,
          data: { billName, amount, dueDate: dueDate.toISOString(), daysUntilDue },
        },
        { type: 'date' as const, date: reminderTime } as any
      );
      notificationIds.push(notificationId);
    }
  }
  
  return notificationIds[0] || ''; // Return first notification ID
}

/**
* Send a referral reward notification
*/
public async sendReferralRewardNotification(
  rewardAmount: number,
  rewardType: 'token' | 'cash',
  referrerName?: string
): Promise<void> {
  const title = '🎉 Referral Reward!';
  const body = referrerName
    ? `You earned ${rewardAmount} ${rewardType === 'token' ? '$REACH tokens' : 'USD'} from ${referrerName}'s referral!`
    : `You earned ${rewardAmount} ${rewardType === 'token' ? '$REACH tokens' : 'USD'} from a referral!`;
  
  await this.sendLocalNotification({
    type: 'referral_reward',
    title,
    body,
    data: {
      rewardAmount,
      rewardType,
      referrerName,
    },
  });
}
/**
* Get channel ID for notification type
*/
private getChannelId(type: string): string {
switch (type) {
case 'price_alert':
return 'price-alerts';
case 'mention':
return 'mentions';
case 'discussion_update':
return 'discussions';
case 'follow':
return 'follows';
case 'transaction_confirmation':
case 'order_filled':
case 'order_cancelled':
return 'transactions';
case 'governance_proposal':
return 'governance';
case 'payment_reminder':
return 'payments';
case 'referral_reward':
return 'default';
default:
return 'default';
}
}
/**
* Schedule a notification for later
*/
public async scheduleNotification(
notification: NotificationData,
trigger: Notifications.NotificationTriggerInput
): Promise<string> {
try {
const channelId = this.getChannelId(notification.type);
const notificationId = await Notifications.scheduleNotificationAsync({
content: {
title: notification.title,
body: notification.body,
data: notification.data || {},
sound: 'default',
},
trigger,
...(Platform.OS === 'android' && { channelId }),
});
return notificationId;
} catch (error) {
logger.error('Error scheduling notification:', error);
throw error;
}
}
/**
* Cancel a scheduled notification
*/
public async cancelNotification(notificationId: string): Promise<void> {
try {
await Notifications.cancelScheduledNotificationAsync(notificationId);
} catch (error) {
logger.error('Error cancelling notification:', error);
}
}
/**
* Cancel all scheduled notifications
*/
public async cancelAllNotifications(): Promise<void> {
try {
await Notifications.cancelAllScheduledNotificationsAsync();
} catch (error) {
logger.error('Error cancelling all notifications:', error);
}
}
/**
* Get all scheduled notifications
*/
public async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
try {
return await Notifications.getAllScheduledNotificationsAsync();
} catch (error) {
logger.error('Error getting scheduled notifications:', error);
return [];
}
}
/**
* Set up notification listeners
*/
public setupNotificationListeners(): {
notificationListener: Notifications.Subscription;
responseListener: Notifications.Subscription;
} {
// Listener for notifications received while app is running
const notificationListener = Notifications.addNotificationReceivedListener(notification => {
});
  // Listener for user interactions with notifications
  const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
    const data = response.notification.request.content.data;
    // Handle different notification types
    if (data.type === 'price_alert') {
      // Navigate to stock details
    } else if (data.type === 'mention') {
      // Navigate to discussion
    } else if (data.type === 'follow') {
      // Navigate to user profile
    } else if (data.type === 'transaction_confirmation' || data.type === 'order_filled') {
      // Navigate to portfolio or order details
      const { DeviceEventEmitter } = require('react-native');
      DeviceEventEmitter.emit('navigateToPortfolio');
    } else if (data.type === 'governance_proposal') {
      // Navigate to governance screen
      const { DeviceEventEmitter } = require('react-native');
      DeviceEventEmitter.emit('navigateToGovernance', { proposalId: data.proposalId });
    } else if (data.type === 'payment_reminder') {
      // Navigate to banking or credit screen
      const { DeviceEventEmitter } = require('react-native');
      DeviceEventEmitter.emit('navigateToBanking');
    } else if (data.type === 'referral_reward') {
      // Navigate to referral screen
      const { DeviceEventEmitter } = require('react-native');
      DeviceEventEmitter.emit('navigateToReferrals');
    } else if (data.type === 'dawn_ritual') {
      // Trigger Dawn Ritual - emit event that PortfolioScreen can listen to
      const { DeviceEventEmitter } = require('react-native');
      DeviceEventEmitter.emit('openDawnRitual');
    } else if (data.type === 'autopilot_funds_moved') {
      // Open DeFi Auto-Pilot and optionally the repair proof (tap to see the proof)
      try {
        const { globalNavigate } = require('../../../navigation/NavigationService');
        globalNavigate('DeFiAutopilot', { repairId: data.repair_id || data.repairId });
      } catch (e) {
        logger.warn('Push deep link DeFiAutopilot failed', e);
      }
    }
  });
return {
notificationListener,
responseListener,
};
}
/**
* Remove notification listeners
*/
public removeNotificationListeners(
notificationListener: Notifications.Subscription,
responseListener: Notifications.Subscription
): void {
// Subscriptions have a .remove() method
notificationListener.remove();
responseListener.remove();
}
/**
* Check if notifications are enabled
*/
public async areNotificationsEnabled(): Promise<boolean> {
try {
const { status } = await Notifications.getPermissionsAsync();
return status === 'granted';
} catch (error) {
logger.error('Error checking notification permissions:', error);
return false;
}
}
/**
* Request notification permissions
*/
public async requestPermissions(): Promise<boolean> {
try {
const { status } = await Notifications.requestPermissionsAsync();
return status === 'granted';
} catch (error) {
logger.error('Error requesting notification permissions:', error);
return false;
}
}
}
// Export singleton instance
export const pushNotificationService = new PushNotificationService();
export default pushNotificationService;
