/**
 * Expo Go Compatible Price Alert Service
 * This service provides basic price alert functionality without native modules
 * that cause "Exception in HostFunction" errors in Expo Go
 */

export interface PriceAlert {
  id: string;
  symbol: string;
  targetPrice: number;
  alertType: 'above' | 'below';
  isActive: boolean;
  createdAt: number;
  triggeredAt?: number;
}

export interface StockPrice {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
}

class ExpoGoCompatiblePriceAlertService {
  private readonly STORAGE_KEY = 'price_alerts';
  private alerts: PriceAlert[] = [];
  private isInitialized = false;

  /**
   * Initialize the service
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    await this.loadAlerts();
    this.isInitialized = true;
    console.log('📊 Expo Go Compatible Price Alert Service initialized');
  }

  /**
   * Load alerts from storage (simplified for Expo Go)
   */
  private async loadAlerts(): Promise<void> {
    try {
      // In Expo Go, we'll use a simple in-memory storage
      // In production, this would use AsyncStorage
      this.alerts = [];
      console.log('📊 Price alerts loaded (Expo Go compatible mode)');
    } catch (error) {
      console.error('Error loading price alerts:', error);
      this.alerts = [];
    }
  }

  /**
   * Save alerts to storage (simplified for Expo Go)
   */
  private async saveAlerts(): Promise<void> {
    try {
      // In Expo Go, we'll just log the alerts
      console.log('📊 Price alerts saved (Expo Go compatible mode):', this.alerts.length);
    } catch (error) {
      console.error('Error saving price alerts:', error);
    }
  }

  /**
   * Add a new price alert
   */
  public async addAlert(symbol: string, targetPrice: number, alertType: 'above' | 'below'): Promise<PriceAlert> {
    await this.initialize();

    // Check if alert already exists for this symbol and target price
    const existingAlert = this.alerts.find(
      alert => alert.symbol === symbol && 
               alert.targetPrice === targetPrice && 
               alert.alertType === alertType &&
               alert.isActive
    );

    if (existingAlert) {
      throw new Error('Alert already exists for this price');
    }

    const alert: PriceAlert = {
      id: this.generateId(),
      symbol: symbol.toUpperCase(),
      targetPrice,
      alertType,
      isActive: true,
      createdAt: Date.now(),
    };

    this.alerts.push(alert);
    await this.saveAlerts();

    console.log('📊 Price alert added (Expo Go compatible):', alert);
    return alert;
  }

  /**
   * Remove a price alert
   */
  public async removeAlert(alertId: string): Promise<void> {
    await this.initialize();

    this.alerts = this.alerts.filter(alert => alert.id !== alertId);
    await this.saveAlerts();

    console.log('📊 Price alert removed (Expo Go compatible):', alertId);
  }

  /**
   * Update a price alert
   */
  public async updateAlert(alertId: string, updates: Partial<PriceAlert>): Promise<void> {
    await this.initialize();

    const alertIndex = this.alerts.findIndex(alert => alert.id === alertId);
    if (alertIndex !== -1) {
      this.alerts[alertIndex] = { ...this.alerts[alertIndex], ...updates };
      await this.saveAlerts();
      console.log('📊 Price alert updated (Expo Go compatible):', alertId);
    }
  }

  /**
   * Get all alerts
   */
  public async getAllAlerts(): Promise<PriceAlert[]> {
    await this.initialize();
    return [...this.alerts];
  }

  /**
   * Get active alerts
   */
  public async getActiveAlerts(): Promise<PriceAlert[]> {
    await this.initialize();
    return this.alerts.filter(alert => alert.isActive);
  }

  /**
   * Get alerts for a specific symbol
   */
  public async getAlertsForSymbol(symbol: string): Promise<PriceAlert[]> {
    await this.initialize();
    return this.alerts.filter(alert => alert.symbol === symbol.toUpperCase());
  }

  /**
   * Check price alerts against current prices
   */
  public async checkAlerts(prices: StockPrice[]): Promise<void> {
    await this.initialize();

    const activeAlerts = this.alerts.filter(alert => alert.isActive);
    
    for (const alert of activeAlerts) {
      const currentPrice = prices.find(price => price.symbol === alert.symbol);
      
      if (!currentPrice) {
        continue;
      }

      const shouldTrigger = this.shouldTriggerAlert(alert, currentPrice.price);
      
      if (shouldTrigger) {
        await this.triggerAlert(alert, currentPrice);
      }
    }
  }

  /**
   * Check if an alert should trigger
   */
  private shouldTriggerAlert(alert: PriceAlert, currentPrice: number): boolean {
    if (alert.alertType === 'above') {
      return currentPrice >= alert.targetPrice;
    } else {
      return currentPrice <= alert.targetPrice;
    }
  }

  /**
   * Trigger a price alert
   */
  private async triggerAlert(alert: PriceAlert, currentPrice: StockPrice): Promise<void> {
    try {
      // In Expo Go compatible mode, just log the alert
      console.log('🚨 PRICE ALERT TRIGGERED (Expo Go compatible):');
      console.log(`   Symbol: ${alert.symbol}`);
      console.log(`   Current Price: $${currentPrice.price.toFixed(2)}`);
      console.log(`   Target Price: $${alert.targetPrice.toFixed(2)}`);
      console.log(`   Alert Type: ${alert.alertType}`);

      // Mark alert as triggered
      await this.updateAlert(alert.id, {
        triggeredAt: Date.now(),
        isActive: false,
      });

      console.log('🚨 Price alert triggered (Expo Go compatible):', alert.symbol, currentPrice.price);
    } catch (error) {
      console.error('Error triggering price alert:', error);
    }
  }

  /**
   * Clear all alerts
   */
  public async clearAllAlerts(): Promise<void> {
    this.alerts = [];
    await this.saveAlerts();
    console.log('📊 All price alerts cleared (Expo Go compatible)');
  }

  /**
   * Clear triggered alerts
   */
  public async clearTriggeredAlerts(): Promise<void> {
    this.alerts = this.alerts.filter(alert => !alert.triggeredAt);
    await this.saveAlerts();
    console.log('📊 Triggered price alerts cleared (Expo Go compatible)');
  }

  /**
   * Get alert statistics
   */
  public async getAlertStats(): Promise<{
    total: number;
    active: number;
    triggered: number;
    bySymbol: { [symbol: string]: number };
  }> {
    await this.initialize();

    const active = this.alerts.filter(alert => alert.isActive).length;
    const triggered = this.alerts.filter(alert => alert.triggeredAt).length;
    
    const bySymbol: { [symbol: string]: number } = {};
    this.alerts.forEach(alert => {
      bySymbol[alert.symbol] = (bySymbol[alert.symbol] || 0) + 1;
    });

    return {
      total: this.alerts.length,
      active,
      triggered,
      bySymbol,
    };
  }

  /**
   * Generate a unique ID
   */
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * Export alerts to JSON
   */
  public async exportAlerts(): Promise<string> {
    await this.initialize();
    return JSON.stringify(this.alerts, null, 2);
  }

  /**
   * Import alerts from JSON
   */
  public async importAlerts(alertsJson: string): Promise<void> {
    try {
      const importedAlerts: PriceAlert[] = JSON.parse(alertsJson);
      
      // Validate imported alerts
      for (const alert of importedAlerts) {
        if (!alert.id || !alert.symbol || !alert.targetPrice || !alert.alertType) {
          throw new Error('Invalid alert format');
        }
      }

      this.alerts = importedAlerts;
      await this.saveAlerts();
      
      console.log('📊 Price alerts imported successfully (Expo Go compatible)');
    } catch (error) {
      console.error('Error importing price alerts:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const expoGoCompatiblePriceAlertService = new ExpoGoCompatiblePriceAlertService();
export default expoGoCompatiblePriceAlertService;
