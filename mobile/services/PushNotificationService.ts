import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
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
type: 'price_alert' | 'mention' | 'discussion_update' | 'follow' | 'general';
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
console.log('Must use physical device for Push Notifications');
return false;
}
// Check if running in Expo Go (which has limited notification support)
if (__DEV__ && !Constants.expoConfig?.extra?.eas) {
console.log('Running in Expo Go - notifications may not work properly');
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
console.log('Failed to get push token for push notification!');
return false;
}
// Get the push token
const token = await Notifications.getExpoPushTokenAsync({
projectId: Constants.expoConfig?.extra?.eas?.projectId,
});
this.expoPushToken = token.data;
console.log(' Push notification token:', this.expoPushToken);
// Save token to storage
await AsyncStorage.setItem('expoPushToken', this.expoPushToken);
// Configure notification channels for Android
if (Platform.OS === 'android') {
await this.setupAndroidChannels();
}
this.isInitialized = true;
return true;
} catch (error) {
console.error('Error initializing push notifications:', error);
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
console.error('Error setting up Android channels:', error);
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
console.log(' Local notification sent:', notification.title);
} catch (error) {
console.error('Error sending local notification:', error);
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
console.log(' Notification scheduled:', notificationId);
return notificationId;
} catch (error) {
console.error('Error scheduling notification:', error);
throw error;
}
}
/**
* Cancel a scheduled notification
*/
public async cancelNotification(notificationId: string): Promise<void> {
try {
await Notifications.cancelScheduledNotificationAsync(notificationId);
console.log(' Notification cancelled:', notificationId);
} catch (error) {
console.error('Error cancelling notification:', error);
}
}
/**
* Cancel all scheduled notifications
*/
public async cancelAllNotifications(): Promise<void> {
try {
await Notifications.cancelAllScheduledNotificationsAsync();
console.log(' All notifications cancelled');
} catch (error) {
console.error('Error cancelling all notifications:', error);
}
}
/**
* Get all scheduled notifications
*/
public async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
try {
return await Notifications.getAllScheduledNotificationsAsync();
} catch (error) {
console.error('Error getting scheduled notifications:', error);
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
console.log(' Notification received:', notification);
});
// Listener for user interactions with notifications
const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
console.log(' Notification response:', response);
const data = response.notification.request.content.data;
// Handle different notification types
if (data.type === 'price_alert') {
// Navigate to stock details
console.log('Navigate to stock:', data.symbol);
} else if (data.type === 'mention') {
// Navigate to discussion
console.log('Navigate to discussion:', data.discussionTitle);
} else if (data.type === 'follow') {
// Navigate to user profile
console.log('Navigate to user profile:', data.followerName);
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
Notifications.removeNotificationSubscription(notificationListener);
Notifications.removeNotificationSubscription(responseListener);
}
/**
* Check if notifications are enabled
*/
public async areNotificationsEnabled(): Promise<boolean> {
try {
const { status } = await Notifications.getPermissionsAsync();
return status === 'granted';
} catch (error) {
console.error('Error checking notification permissions:', error);
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
console.error('Error requesting notification permissions:', error);
return false;
}
}
}
// Export singleton instance
export const pushNotificationService = new PushNotificationService();
export default pushNotificationService;
