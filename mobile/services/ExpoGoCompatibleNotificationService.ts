/**
 * Expo Go Compatible Notification Service
 * This service provides basic functionality without native modules
 * that cause "Exception in HostFunction" errors in Expo Go
 */

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

class ExpoGoCompatibleNotificationService {
  private isInitialized = false;

  /**
   * Initialize the service (Expo Go compatible)
   */
  public async initialize(): Promise<boolean> {
    try {
      if (this.isInitialized) {
        return true;
      }

      console.log('📱 Expo Go Compatible Notification Service initialized');
      this.isInitialized = true;
      return true;
    } catch (error) {
      console.error('Error initializing Expo Go compatible notification service:', error);
      return false;
    }
  }

  /**
   * Send a local notification (console log for Expo Go)
   */
  public async sendLocalNotification(notification: NotificationData): Promise<void> {
    try {
      console.log('📱 NOTIFICATION:', notification.title);
      console.log('📱 MESSAGE:', notification.body);
      console.log('📱 TYPE:', notification.type);
      if (notification.data) {
        console.log('📱 DATA:', notification.data);
      }
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
   * Setup notification listeners (Expo Go compatible)
   */
  public setupNotificationListeners(): {
    notificationListener: any;
    responseListener: any;
  } {
    console.log('📱 Setting up Expo Go compatible notification listeners');
    
    return {
      notificationListener: { remove: () => {} },
      responseListener: { remove: () => {} }
    };
  }

  /**
   * Remove notification listeners
   */
  public removeNotificationListeners(
    notificationListener: any,
    responseListener: any
  ): void {
    console.log('📱 Removing Expo Go compatible notification listeners');
  }

  /**
   * Check if notifications are enabled
   */
  public async areNotificationsEnabled(): Promise<boolean> {
    return true; // Always enabled in Expo Go compatible mode
  }

  /**
   * Request notification permissions
   */
  public async requestPermissions(): Promise<boolean> {
    return true; // Always granted in Expo Go compatible mode
  }
}

// Export singleton instance
export const expoGoCompatibleNotificationService = new ExpoGoCompatibleNotificationService();
export default expoGoCompatibleNotificationService;
