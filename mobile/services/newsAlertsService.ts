import AsyncStorage from '@react-native-async-storage/async-storage';
import { NewsArticle } from './newsService';

export interface NewsAlert {
  id: string;
  title: string;
  message: string;
  type: 'breaking' | 'market' | 'personal' | 'general';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: string;
  isRead: boolean;
  articleId?: string;
  category?: string;
  keywords?: string[];
}

export interface AlertPreference {
  enabled: boolean;
  types: string[];
  priority: string[];
  quietHours: {
    enabled: boolean;
    start: string; // HH:mm format
    end: string; // HH:mm format
  };
  frequency: 'immediate' | 'hourly' | 'daily';
}

class NewsAlertsService {
  private alerts: NewsAlert[] = [];
  private preferences: AlertPreference = {
    enabled: true,
    types: ['breaking', 'market', 'personal'],
    priority: ['urgent', 'high', 'medium'],
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00',
    },
    frequency: 'immediate',
  };

  constructor() {
    this.loadAlerts();
    this.loadPreferences();
  }

  // Load alerts from storage
  private async loadAlerts() {
    try {
      const saved = await AsyncStorage.getItem('newsAlerts');
      if (saved) {
        this.alerts = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Error loading news alerts:', error);
    }
  }

  // Load preferences from storage
  private async loadPreferences() {
    try {
      const saved = await AsyncStorage.getItem('newsAlertPreferences');
      if (saved) {
        this.preferences = { ...this.preferences, ...JSON.parse(saved) };
      }
    } catch (error) {
      console.error('Error loading alert preferences:', error);
    }
  }

  // Save alerts to storage
  private async saveAlerts() {
    try {
      await AsyncStorage.setItem('newsAlerts', JSON.stringify(this.alerts));
    } catch (error) {
      console.error('Error saving news alerts:', error);
    }
  }

  // Save preferences to storage
  private async savePreferences() {
    try {
      await AsyncStorage.setItem('newsAlertPreferences', JSON.stringify(this.preferences));
    } catch (error) {
      console.error('Error saving alert preferences:', error);
    }
  }

  // Create a new alert
  async createAlert(alert: Omit<NewsAlert, 'id' | 'timestamp' | 'isRead'>): Promise<NewsAlert> {
    const newAlert: NewsAlert = {
      ...alert,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      isRead: false,
    };

    this.alerts.unshift(newAlert);
    await this.saveAlerts();

    // Check if we should show notification
    if (this.shouldShowNotification(newAlert)) {
      this.showNotification(newAlert);
    }

    return newAlert;
  }

  // Get all alerts
  async getAlerts(): Promise<NewsAlert[]> {
    return [...this.alerts];
  }

  // Get unread alerts
  async getUnreadAlerts(): Promise<NewsAlert[]> {
    return this.alerts.filter(alert => !alert.isRead);
  }

  // Mark alert as read
  async markAsRead(alertId: string): Promise<void> {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.isRead = true;
      await this.saveAlerts();
    }
  }

  // Mark all alerts as read
  async markAllAsRead(): Promise<void> {
    this.alerts.forEach(alert => alert.isRead = true);
    await this.saveAlerts();
  }

  // Delete alert
  async deleteAlert(alertId: string): Promise<void> {
    this.alerts = this.alerts.filter(a => a.id !== alertId);
    await this.saveAlerts();
  }

  // Clear all alerts
  async clearAllAlerts(): Promise<void> {
    this.alerts = [];
    await this.saveAlerts();
  }

  // Update preferences
  async updatePreferences(preferences: Partial<AlertPreference>): Promise<void> {
    this.preferences = { ...this.preferences, ...preferences };
    await this.savePreferences();
  }

  // Get preferences
  getPreferences(): AlertPreference {
    return { ...this.preferences };
  }

  // Check if we should show notification based on preferences
  private shouldShowNotification(alert: NewsAlert): boolean {
    if (!this.preferences.enabled) return false;
    
    // Check if alert type is enabled
    if (!this.preferences.types.includes(alert.type)) return false;
    
    // Check if alert priority is enabled
    if (!this.preferences.priority.includes(alert.priority)) return false;
    
    // Check quiet hours
    if (this.preferences.quietHours.enabled) {
      const now = new Date();
      const currentTime = now.getHours() * 60 + now.getMinutes();
      const startTime = this.parseTime(this.preferences.quietHours.start);
      const endTime = this.parseTime(this.preferences.quietHours.end);
      
      if (startTime <= endTime) {
        // Same day (e.g., 22:00 to 08:00)
        if (currentTime >= startTime || currentTime <= endTime) return false;
      } else {
        // Overnight (e.g., 22:00 to 08:00)
        if (currentTime >= startTime && currentTime <= endTime) return false;
      }
    }
    
    return true;
  }

  // Parse time string (HH:mm) to minutes
  private parseTime(timeString: string): number {
    const [hours, minutes] = timeString.split(':').map(Number);
    return hours * 60 + minutes;
  }

  // Show notification (in a real app, this would use push notifications)
  private showNotification(alert: NewsAlert) {
    // For demo purposes, we'll just log the notification
    // In production, this would use React Native Push Notification or similar
    console.log('🔔 NEWS ALERT:', alert.title);
    console.log('📝 Message:', alert.message);
    console.log('🚨 Priority:', alert.priority);
    console.log('📊 Type:', alert.type);
    
    // You could also trigger a local notification here
    // or send to a push notification service
  }

  // Create breaking news alert
  async createBreakingNewsAlert(article: NewsArticle): Promise<NewsAlert> {
    return this.createAlert({
      title: '🚨 Breaking News',
      message: article.title,
      type: 'breaking',
      priority: 'urgent',
      articleId: article.id,
      category: article.category,
    });
  }

  // Create market alert
  async createMarketAlert(message: string, priority: 'medium' | 'high' = 'medium'): Promise<NewsAlert> {
    return this.createAlert({
      title: '📈 Market Update',
      message,
      type: 'market',
      priority,
    });
  }

  // Create personal alert based on user preferences
  async createPersonalAlert(article: NewsArticle, matchedKeywords: string[]): Promise<NewsAlert> {
    return this.createAlert({
      title: '👤 Personal Interest',
      message: `News about: ${matchedKeywords.join(', ')}`,
      type: 'personal',
      priority: 'medium',
      articleId: article.id,
      category: article.category,
      keywords: matchedKeywords,
    });
  }

  // Check if article should trigger personal alert
  shouldTriggerPersonalAlert(article: NewsArticle, userKeywords: string[]): boolean {
    if (userKeywords.length === 0) return false;
    
    const articleText = `${article.title} ${article.description}`.toLowerCase();
    const matchedKeywords = userKeywords.filter(keyword => 
      articleText.includes(keyword.toLowerCase())
    );
    
    return matchedKeywords.length > 0;
  }

  // Get alert statistics
  getAlertStats() {
    const total = this.alerts.length;
    const unread = this.alerts.filter(a => !a.isRead).length;
    const byType = this.alerts.reduce((acc, alert) => {
      acc[alert.type] = (acc[alert.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const byPriority = this.alerts.reduce((acc, alert) => {
      acc[alert.priority] = (acc[alert.priority] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total,
      unread,
      byType,
      byPriority,
    };
  }
}

export default new NewsAlertsService();
