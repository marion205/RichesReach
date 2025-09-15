import AsyncStorage from '@react-native-async-storage/async-storage';
// Use Expo Go compatible notification service to avoid crashes
import expoGoCompatibleNotificationService from './ExpoGoCompatibleNotificationService';
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
class PriceAlertService {
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
}
/**
* Load alerts from storage
*/
private async loadAlerts(): Promise<void> {
try {
const alertsString = await AsyncStorage.getItem(this.STORAGE_KEY);
if (alertsString) {
this.alerts = JSON.parse(alertsString);
}
} catch (error) {
console.error('Error loading price alerts:', error);
this.alerts = [];
}
}
/**
* Save alerts to storage
*/
private async saveAlerts(): Promise<void> {
try {
await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.alerts));
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
return alert;
}
/**
* Remove a price alert
*/
public async removeAlert(alertId: string): Promise<void> {
await this.initialize();
this.alerts = this.alerts.filter(alert => alert.id !== alertId);
await this.saveAlerts();
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
// Send push notification
await expoGoCompatibleNotificationService.sendPriceAlert({
symbol: alert.symbol,
currentPrice: currentPrice.price,
targetPrice: alert.targetPrice,
alertType: alert.alertType,
});
// Mark alert as triggered
await this.updateAlert(alert.id, {
triggeredAt: Date.now(),
isActive: false,
});
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
}
/**
* Clear triggered alerts
*/
public async clearTriggeredAlerts(): Promise<void> {
this.alerts = this.alerts.filter(alert => !alert.triggeredAt);
await this.saveAlerts();
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
} catch (error) {
console.error('Error importing price alerts:', error);
throw error;
}
}
}
// Export singleton instance
export const priceAlertService = new PriceAlertService();
export default priceAlertService;
