import AsyncStorage from '@react-native-async-storage/async-storage';
// Use Expo Go compatible notification service to avoid crashes
import expoGoCompatibleNotificationService from './ExpoGoCompatibleNotificationService';
export interface StockPrice {
symbol: string;
price: number;
change: number;
change_percent: number;
volume: number;
timestamp: number;
}
export interface TechnicalIndicators {
rsi: number; // Relative Strength Index (0-100)
macd: number; // MACD line
macdSignal: number; // MACD signal line
sma20: number; // 20-day Simple Moving Average
sma50: number; // 50-day Simple Moving Average
bollingerUpper: number; // Bollinger Bands upper
bollingerLower: number; // Bollinger Bands lower
volume: number;
volumeSMA: number; // Volume moving average
}
export interface MarketConditions {
marketTrend: 'bullish' | 'bearish' | 'sideways';
volatility: 'low' | 'medium' | 'high';
volume: 'low' | 'normal' | 'high';
sectorPerformance: number; // Sector performance percentage
}
export interface UserProfile {
riskTolerance: 'conservative' | 'moderate' | 'aggressive';
investmentHorizon: 'short' | 'medium' | 'long';
portfolioSize: number;
preferredSectors: string[];
tradingFrequency: 'daily' | 'weekly' | 'monthly';
}
export interface IntelligentAlert {
id: string;
symbol: string;
alertType: 'buy_opportunity' | 'sell_signal' | 'price_target' | 'technical_breakout';
confidence: number; // 0-100 confidence score
reason: string;
technicalScore: number; // 0-100 technical analysis score
marketScore: number; // 0-100 market condition score
userScore: number; // 0-100 user profile match score
targetPrice?: number;
stopLoss?: number;
isActive: boolean;
createdAt: number;
triggeredAt?: number;
expiresAt: number;
}
class IntelligentPriceAlertService {
private readonly STORAGE_KEY = 'intelligent_alerts';
private readonly USER_PROFILE_KEY = 'user_trading_profile';
private alerts: IntelligentAlert[] = [];
private userProfile: UserProfile | null = null;
private isInitialized = false;
/**
* Initialize the service
*/
public async initialize(): Promise<void> {
if (this.isInitialized) {
return;
}
await this.loadAlerts();
await this.loadUserProfile();
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
console.error('Error loading intelligent alerts:', error);
this.alerts = [];
}
}
/**
* Load user profile from storage
*/
private async loadUserProfile(): Promise<void> {
try {
const profileString = await AsyncStorage.getItem(this.USER_PROFILE_KEY);
if (profileString) {
this.userProfile = JSON.parse(profileString);
}
} catch (error) {
console.error('Error loading user profile:', error);
this.userProfile = null;
}
}
/**
* Save alerts to storage
*/
private async saveAlerts(): Promise<void> {
try {
await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.alerts));
} catch (error) {
console.error('Error saving intelligent alerts:', error);
}
}
/**
* Set user trading profile
*/
public async setUserProfile(profile: UserProfile): Promise<void> {
this.userProfile = profile;
await AsyncStorage.setItem(this.USER_PROFILE_KEY, JSON.stringify(profile));
}
/**
* Get user trading profile
*/
public getUserProfile(): UserProfile | null {
return this.userProfile;
}
/**
* Analyze stock and generate intelligent alerts
*/
public async analyzeStock(
symbol: string,
currentPrice: StockPrice,
historicalData: StockPrice[],
marketConditions: MarketConditions
): Promise<IntelligentAlert[]> {
await this.initialize();
const alerts: IntelligentAlert[] = [];
// Calculate technical indicators
const indicators = this.calculateTechnicalIndicators(historicalData);
// Generate different types of alerts
const buyOpportunity = this.analyzeBuyOpportunity(symbol, currentPrice, indicators, marketConditions);
if (buyOpportunity) {
alerts.push(buyOpportunity);
}
const sellSignal = this.analyzeSellSignal(symbol, currentPrice, indicators, marketConditions);
if (sellSignal) {
alerts.push(sellSignal);
}
const technicalBreakout = this.analyzeTechnicalBreakout(symbol, currentPrice, indicators, marketConditions);
if (technicalBreakout) {
alerts.push(technicalBreakout);
}
// Save new alerts
this.alerts.push(...alerts);
await this.saveAlerts();
return alerts;
}
/**
* Calculate technical indicators
*/
private calculateTechnicalIndicators(data: StockPrice[]): TechnicalIndicators {
if (data.length < 50) {
// Not enough data for reliable indicators
return {
rsi: 50,
macd: 0,
macdSignal: 0,
sma20: data[data.length - 1]?.price || 0,
sma50: data[data.length - 1]?.price || 0,
bollingerUpper: data[data.length - 1]?.price || 0,
bollingerLower: data[data.length - 1]?.price || 0,
volume: data[data.length - 1]?.volume || 0,
volumeSMA: data[data.length - 1]?.volume || 0,
};
}
const prices = data.map(d => d.price);
const volumes = data.map(d => d.volume);
return {
rsi: this.calculateRSI(prices, 14),
macd: this.calculateMACD(prices)[0],
macdSignal: this.calculateMACD(prices)[1],
sma20: this.calculateSMA(prices, 20),
sma50: this.calculateSMA(prices, 50),
bollingerUpper: this.calculateBollingerBands(prices, 20)[0],
bollingerLower: this.calculateBollingerBands(prices, 20)[1],
volume: volumes[volumes.length - 1],
volumeSMA: this.calculateSMA(volumes, 20),
};
}
/**
* Analyze buy opportunity
*/
private analyzeBuyOpportunity(
symbol: string,
currentPrice: StockPrice,
indicators: TechnicalIndicators,
marketConditions: MarketConditions
): IntelligentAlert | null {
let technicalScore = 0;
let marketScore = 0;
let userScore = 0;
const reasons: string[] = [];
// RSI Analysis (Oversold conditions)
if (indicators.rsi < 30) {
technicalScore += 25;
reasons.push('RSI indicates oversold conditions');
} else if (indicators.rsi < 40) {
technicalScore += 15;
reasons.push('RSI shows potential oversold');
}
// Moving Average Analysis
if (currentPrice.price < indicators.sma20 && indicators.sma20 > indicators.sma50) {
technicalScore += 20;
reasons.push('Price below 20-day SMA with bullish trend');
}
// Bollinger Bands Analysis
if (currentPrice.price <= indicators.bollingerLower) {
technicalScore += 20;
reasons.push('Price at lower Bollinger Band');
}
// MACD Analysis
if (indicators.macd > indicators.macdSignal && indicators.macd < 0) {
technicalScore += 15;
reasons.push('MACD showing potential bullish crossover');
}
// Volume Analysis
if (currentPrice.volume > indicators.volumeSMA * 1.5) {
technicalScore += 10;
reasons.push('High volume indicates strong interest');
}
// Market Conditions Analysis
if (marketConditions.marketTrend === 'bullish') {
marketScore += 30;
reasons.push('Bullish market conditions');
} else if (marketConditions.marketTrend === 'sideways') {
marketScore += 15;
reasons.push('Sideways market - good for value buying');
}
if (marketConditions.volatility === 'high') {
marketScore += 10;
reasons.push('High volatility creates opportunities');
}
// User Profile Analysis
if (this.userProfile) {
if (this.userProfile.riskTolerance === 'aggressive' && marketConditions.volatility === 'high') {
userScore += 25;
reasons.push('High volatility matches aggressive risk tolerance');
} else if (this.userProfile.riskTolerance === 'conservative' && marketConditions.volatility === 'low') {
userScore += 25;
reasons.push('Low volatility matches conservative risk tolerance');
}
if (this.userProfile.investmentHorizon === 'long' && marketConditions.marketTrend === 'bullish') {
userScore += 20;
reasons.push('Long-term horizon with bullish market');
}
}
const totalScore = (technicalScore + marketScore + userScore) / 3;
const confidence = Math.min(100, totalScore);
// Only create alert if confidence is above threshold
if (confidence >= 60) {
return {
id: this.generateId(),
symbol,
alertType: 'buy_opportunity',
confidence,
reason: reasons.join('; '),
technicalScore,
marketScore,
userScore,
targetPrice: this.calculateTargetPrice(currentPrice.price, indicators),
stopLoss: this.calculateStopLoss(currentPrice.price, indicators),
isActive: true,
createdAt: Date.now(),
expiresAt: Date.now() + (24 * 60 * 60 * 1000), // 24 hours
};
}
return null;
}
/**
* Analyze sell signal
*/
private analyzeSellSignal(
symbol: string,
currentPrice: StockPrice,
indicators: TechnicalIndicators,
marketConditions: MarketConditions
): IntelligentAlert | null {
let technicalScore = 0;
const reasons: string[] = [];
// RSI Analysis (Overbought conditions)
if (indicators.rsi > 70) {
technicalScore += 30;
reasons.push('RSI indicates overbought conditions');
} else if (indicators.rsi > 60) {
technicalScore += 15;
reasons.push('RSI shows potential overbought');
}
// Moving Average Analysis
if (currentPrice.price > indicators.sma20 && indicators.sma20 < indicators.sma50) {
technicalScore += 20;
reasons.push('Price above 20-day SMA with bearish trend');
}
// Bollinger Bands Analysis
if (currentPrice.price >= indicators.bollingerUpper) {
technicalScore += 20;
reasons.push('Price at upper Bollinger Band');
}
// MACD Analysis
if (indicators.macd < indicators.macdSignal && indicators.macd > 0) {
technicalScore += 15;
reasons.push('MACD showing potential bearish crossover');
}
const confidence = Math.min(100, technicalScore);
if (confidence >= 70) {
return {
id: this.generateId(),
symbol,
alertType: 'sell_signal',
confidence,
reason: reasons.join('; '),
technicalScore,
marketScore: 0,
userScore: 0,
isActive: true,
createdAt: Date.now(),
expiresAt: Date.now() + (12 * 60 * 60 * 1000), // 12 hours
};
}
return null;
}
/**
* Analyze technical breakout
*/
private analyzeTechnicalBreakout(
symbol: string,
currentPrice: StockPrice,
indicators: TechnicalIndicators,
marketConditions: MarketConditions
): IntelligentAlert | null {
let technicalScore = 0;
const reasons: string[] = [];
// Volume breakout
if (currentPrice.volume > indicators.volumeSMA * 2) {
technicalScore += 30;
reasons.push('Volume breakout detected');
}
// Price breakout above resistance (SMA)
if (currentPrice.price > indicators.sma20 && currentPrice.price > indicators.sma50) {
technicalScore += 25;
reasons.push('Price breakout above moving averages');
}
// Bollinger Band breakout
if (currentPrice.price > indicators.bollingerUpper) {
technicalScore += 20;
reasons.push('Bollinger Band breakout');
}
// MACD bullish crossover
if (indicators.macd > indicators.macdSignal && indicators.macd > 0) {
technicalScore += 15;
reasons.push('MACD bullish crossover');
}
const confidence = Math.min(100, technicalScore);
if (confidence >= 65) {
return {
id: this.generateId(),
symbol,
alertType: 'technical_breakout',
confidence,
reason: reasons.join('; '),
technicalScore,
marketScore: 0,
userScore: 0,
targetPrice: this.calculateTargetPrice(currentPrice.price, indicators),
isActive: true,
createdAt: Date.now(),
expiresAt: Date.now() + (6 * 60 * 60 * 1000), // 6 hours
};
}
return null;
}
/**
* Calculate target price based on technical analysis
*/
private calculateTargetPrice(currentPrice: number, indicators: TechnicalIndicators): number {
// Use Bollinger Bands for target price
const range = indicators.bollingerUpper - indicators.bollingerLower;
return currentPrice + (range * 0.5); // Target 50% of the range
}
/**
* Calculate stop loss based on technical analysis
*/
private calculateStopLoss(currentPrice: number, indicators: TechnicalIndicators): number {
// Use Bollinger Bands for stop loss
const range = indicators.bollingerUpper - indicators.bollingerLower;
return currentPrice - (range * 0.3); // Stop loss at 30% of the range
}
/**
* Calculate RSI (Relative Strength Index)
*/
private calculateRSI(prices: number[], period: number = 14): number {
if (prices.length < period + 1) return 50;
let gains = 0;
let losses = 0;
for (let i = 1; i <= period; i++) {
const change = prices[i] - prices[i - 1];
if (change > 0) {
gains += change;
} else {
losses += Math.abs(change);
}
}
const avgGain = gains / period;
const avgLoss = losses / period;
if (avgLoss === 0) return 100;
const rs = avgGain / avgLoss;
return 100 - (100 / (1 + rs));
}
/**
* Calculate MACD
*/
private calculateMACD(prices: number[]): [number, number] {
if (prices.length < 26) return [0, 0];
const ema12 = this.calculateEMA(prices, 12);
const ema26 = this.calculateEMA(prices, 26);
const macd = ema12 - ema26;
// Simplified signal line (9-period EMA of MACD)
const signal = macd * 0.9; // Simplified calculation
return [macd, signal];
}
/**
* Calculate EMA (Exponential Moving Average)
*/
private calculateEMA(prices: number[], period: number): number {
if (prices.length < period) return prices[prices.length - 1];
const multiplier = 2 / (period + 1);
let ema = prices[0];
for (let i = 1; i < prices.length; i++) {
ema = (prices[i] * multiplier) + (ema * (1 - multiplier));
}
return ema;
}
/**
* Calculate SMA (Simple Moving Average)
*/
private calculateSMA(prices: number[], period: number): number {
if (prices.length < period) {
return prices.reduce((sum, price) => sum + price, 0) / prices.length;
}
const recentPrices = prices.slice(-period);
return recentPrices.reduce((sum, price) => sum + price, 0) / period;
}
/**
* Calculate Bollinger Bands
*/
private calculateBollingerBands(prices: number[], period: number = 20): [number, number] {
const sma = this.calculateSMA(prices, period);
if (prices.length < period) {
return [sma, sma];
}
const recentPrices = prices.slice(-period);
const variance = recentPrices.reduce((sum, price) => sum + Math.pow(price - sma, 2), 0) / period;
const stdDev = Math.sqrt(variance);
return [sma + (2 * stdDev), sma - (2 * stdDev)];
}
/**
* Get all active alerts
*/
public async getActiveAlerts(): Promise<IntelligentAlert[]> {
await this.initialize();
const now = Date.now();
return this.alerts.filter(alert => 
alert.isActive && 
alert.expiresAt > now
);
}
/**
* Get alerts for a specific symbol
*/
public async getAlertsForSymbol(symbol: string): Promise<IntelligentAlert[]> {
await this.initialize();
return this.alerts.filter(alert => alert.symbol === symbol.toUpperCase());
}
/**
* Remove an alert
*/
public async removeAlert(alertId: string): Promise<void> {
await this.initialize();
this.alerts = this.alerts.filter(alert => alert.id !== alertId);
await this.saveAlerts();
}
/**
* Generate unique ID
*/
private generateId(): string {
return Date.now().toString(36) + Math.random().toString(36).substr(2);
}
}
// Export singleton instance
export const intelligentPriceAlertService = new IntelligentPriceAlertService();
export default intelligentPriceAlertService;
