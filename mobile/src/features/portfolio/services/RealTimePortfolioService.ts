import { SecureMarketDataService } from '../../stocks/services/SecureMarketDataService';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';
export interface PortfolioHolding {
symbol: string;
companyName: string;
shares: number;
costBasis: number; // Total cost paid for shares
currentPrice: number; // Real-time price
totalValue: number; // shares * currentPrice
returnAmount: number; // totalValue - costBasis
returnPercent: number; // (returnAmount / costBasis) * 100
sector?: string;
lastUpdated: string;
}
export interface PortfolioMetrics {
totalValue: number;
totalCost: number;
totalReturn: number;
totalReturnPercent: number;
dayChange: number;
dayChangePercent: number;
holdings: PortfolioHolding[];
lastUpdated: string;
}
export interface StockQuote {
  symbol: string;
  price: number;
  change?: number;
  changePercent?: number;
}

export interface PortfolioUpdate {
type: 'price_update' | 'portfolio_refresh' | 'error';
data: PortfolioMetrics | StockQuote | string;
timestamp: number;
}
class RealTimePortfolioService {
private updateInterval?: ReturnType<typeof setInterval>;
private isTracking: boolean = false;
private updateCallbacks: ((update: PortfolioUpdate) => void)[] = [];
private lastPortfolioData: PortfolioMetrics | null = null;
private updateFrequency: number = 30000; // 30 seconds
// Get portfolio data (simplified - no real-time tracking)
public async getPortfolioData(): Promise<PortfolioMetrics | null> {
try {
// Get current portfolio data
const portfolioData = await this.getCurrentPortfolio();
if (!portfolioData) {
return null;
}
// Get real-time quotes for all holdings
const symbols = portfolioData.holdings.map(holding => holding.symbol);
const service = SecureMarketDataService.getInstance();
const quotes = await service.fetchQuotes(symbols);
// Update holdings with real-time prices
const updatedHoldings: PortfolioHolding[] = portfolioData.holdings.map(holding => {
const quote = quotes.find(q => q.symbol === holding.symbol);
if (quote) {
const currentPrice = quote.price;
const totalValue = holding.shares * currentPrice;
const returnAmount = totalValue - holding.costBasis;
const returnPercent = holding.costBasis ? (returnAmount / holding.costBasis) * 100 : 0;
return {
...holding,
currentPrice,
totalValue,
returnAmount,
returnPercent,
lastUpdated: new Date().toISOString()
};
}
return holding;
});
// Calculate portfolio metrics
const totalValue = updatedHoldings.reduce((sum, holding) => sum + holding.totalValue, 0);
const totalCost = updatedHoldings.reduce((sum, holding) => sum + holding.costBasis, 0);
const totalReturn = totalValue - totalCost;
const totalReturnPercent = totalCost ? (totalReturn / totalCost) * 100 : 0;
// Calculate day change
const dayChange = this.calculateDayChange(updatedHoldings, quotes);
const base = this.lastPortfolioData?.totalValue ?? 0;
const dayChangePercent = base ? ((totalValue - base) / base) * 100 : 0;
const updatedPortfolio: PortfolioMetrics = {
totalValue,
totalCost,
totalReturn,
totalReturnPercent,
dayChange,
dayChangePercent,
holdings: updatedHoldings,
lastUpdated: new Date().toISOString()
};
// Store updated portfolio
await this.savePortfolio(updatedPortfolio);
this.lastPortfolioData = updatedPortfolio;
return updatedPortfolio;
} catch (error) {
logger.error('Error loading portfolio data:', error);
return null;
}
}
// Subscribe to portfolio updates
public onPortfolioUpdate(callback: (update: PortfolioUpdate) => void) {
this.updateCallbacks.push(callback);
}
// Unsubscribe from portfolio updates
public offPortfolioUpdate(callback: (update: PortfolioUpdate) => void) {
const index = this.updateCallbacks.indexOf(callback);
if (index > -1) {
this.updateCallbacks.splice(index, 1);
}
}
// Notify all subscribers of portfolio updates
private notifySubscribers(update: PortfolioUpdate) {
this.updateCallbacks.forEach(callback => {
try {
callback(update);
} catch (error) {
logger.error('Error in portfolio update callback:', error);
}
});
}
// Update portfolio with real-time data
private async updatePortfolio() {
try {
// Get current portfolio data
const portfolioData = await this.getCurrentPortfolio();
if (!portfolioData) {
return;
}
// Get real-time quotes for all holdings
const symbols = portfolioData.holdings.map(holding => holding.symbol);
const service = SecureMarketDataService.getInstance();
const quotes = await service.fetchQuotes(symbols);
// Update holdings with real-time prices
const updatedHoldings: PortfolioHolding[] = portfolioData.holdings.map(holding => {
const quote = quotes.find(q => q.symbol === holding.symbol);
if (quote) {
const currentPrice = quote.price;
const totalValue = holding.shares * currentPrice;
const returnAmount = totalValue - holding.costBasis;
const returnPercent = holding.costBasis ? (returnAmount / holding.costBasis) * 100 : 0;
return {
...holding,
currentPrice,
totalValue,
returnAmount,
returnPercent,
lastUpdated: new Date().toISOString()
};
}
return holding;
});
// Calculate portfolio metrics
const totalValue = updatedHoldings.reduce((sum, holding) => sum + holding.totalValue, 0);
const totalCost = updatedHoldings.reduce((sum, holding) => sum + holding.costBasis, 0);
const totalReturn = totalValue - totalCost;
const totalReturnPercent = totalCost ? (totalReturn / totalCost) * 100 : 0;
// Calculate day change
const dayChange = this.calculateDayChange(updatedHoldings, quotes);
const base = this.lastPortfolioData?.totalValue ?? 0;
const dayChangePercent = base ? ((totalValue - base) / base) * 100 : 0;
const updatedPortfolio: PortfolioMetrics = {
totalValue,
totalCost,
totalReturn,
totalReturnPercent,
dayChange,
dayChangePercent,
holdings: updatedHoldings,
lastUpdated: new Date().toISOString()
};
// Store updated portfolio
await this.savePortfolio(updatedPortfolio);
this.lastPortfolioData = updatedPortfolio;
// Notify subscribers
this.notifySubscribers({
type: 'portfolio_refresh',
data: updatedPortfolio,
timestamp: Date.now()
});
} catch (error) {
logger.error('Error updating portfolio:', error);
this.notifySubscribers({
type: 'error',
data: (error as Error).message || 'Failed to update portfolio',
timestamp: Date.now()
});
}
}
// Calculate day change for portfolio
private calculateDayChange(holdings: PortfolioHolding[], quotes: StockQuote[]): number {
return holdings.reduce((totalChange, holding) => {
const quote = quotes.find(q => q.symbol === holding.symbol);
if (quote) {
const dayChange = quote.change * holding.shares;
return totalChange + dayChange;
}
return totalChange;
}, 0);
}
// Get current portfolio data
private async getCurrentPortfolio(): Promise<PortfolioMetrics | null> {
try {
const stored = await AsyncStorage.getItem('real_time_portfolio');
if (stored) {
return JSON.parse(stored);
}
// If no stored portfolio, create a sample portfolio for demonstration
return this.createSamplePortfolio();
} catch (error) {
logger.error('Error loading portfolio:', error);
return null;
}
}
// Save portfolio data
private async savePortfolio(portfolio: PortfolioMetrics) {
try {
await AsyncStorage.setItem('real_time_portfolio', JSON.stringify(portfolio));
} catch (error) {
logger.error('Error saving portfolio:', error);
}
}
// Create sample portfolio for demonstration
private createSamplePortfolio(): PortfolioMetrics {
const sampleHoldings: PortfolioHolding[] = [
{
symbol: 'AAPL',
companyName: 'Apple Inc.',
shares: 10,
costBasis: 2000, // $200 per share average
currentPrice: 0, // Will be updated with real data
totalValue: 0,
returnAmount: 0,
returnPercent: 0,
sector: 'Technology',
lastUpdated: new Date().toISOString()
},
{
symbol: 'MSFT',
companyName: 'Microsoft Corporation',
shares: 5,
costBasis: 1500, // $300 per share average
currentPrice: 0,
totalValue: 0,
returnAmount: 0,
returnPercent: 0,
sector: 'Technology',
lastUpdated: new Date().toISOString()
},
{
symbol: 'TSLA',
companyName: 'Tesla, Inc.',
shares: 3,
costBasis: 900, // $300 per share average
currentPrice: 0,
totalValue: 0,
returnAmount: 0,
returnPercent: 0,
sector: 'Automotive',
lastUpdated: new Date().toISOString()
}
];
return {
totalValue: 0,
totalCost: 4400,
totalReturn: 0,
totalReturnPercent: 0,
dayChange: 0,
dayChangePercent: 0,
holdings: sampleHoldings,
lastUpdated: new Date().toISOString()
};
}
// Add new holding to portfolio
public async addHolding(holding: Omit<PortfolioHolding, 'currentPrice' | 'totalValue' | 'returnAmount' | 'returnPercent' | 'lastUpdated'>) {
try {
const portfolio = await this.getCurrentPortfolio();
if (!portfolio) return;
// Get current price for the new holding
const service = SecureMarketDataService.getInstance();
const quotes = await service.fetchQuotes([holding.symbol]);
const quote = quotes[0];
const currentPrice = quote.price;
const totalValue = holding.shares * currentPrice;
const returnAmount = totalValue - holding.costBasis;
const returnPercent = holding.costBasis ? (returnAmount / holding.costBasis) * 100 : 0;
const newHolding: PortfolioHolding = {
...holding,
currentPrice,
totalValue,
returnAmount,
returnPercent,
lastUpdated: new Date().toISOString()
};
portfolio.holdings.push(newHolding);
await this.savePortfolio(portfolio);
// Trigger immediate update
this.updatePortfolio();
} catch (error) {
logger.error('Error adding holding:', error);
}
}
// Remove holding from portfolio
public async removeHolding(symbol: string) {
try {
const portfolio = await this.getCurrentPortfolio();
if (!portfolio) return;
portfolio.holdings = portfolio.holdings.filter(h => h.symbol !== symbol);
await this.savePortfolio(portfolio);
// Trigger immediate update
this.updatePortfolio();
} catch (error) {
logger.error('Error removing holding:', error);
}
}
// Update holding quantity
public async updateHoldingQuantity(symbol: string, newShares: number, additionalCost?: number) {
try {
const portfolio = await this.getCurrentPortfolio();
if (!portfolio) return;
const holding = portfolio.holdings.find(h => h.symbol === symbol);
if (!holding) return;
// Update cost basis if additional shares were purchased
if (additionalCost) {
holding.costBasis += additionalCost;
}
holding.shares = newShares;
await this.savePortfolio(portfolio);
// Trigger immediate update
this.updatePortfolio();
} catch (error) {
logger.error('Error updating holding quantity:', error);
}
}
// Get current portfolio metrics
public async getCurrentMetrics(): Promise<PortfolioMetrics | null> {
return this.getCurrentPortfolio();
}
// Set update frequency
public setUpdateFrequency(seconds: number) {
this.updateFrequency = seconds * 1000;
// Restart tracking with new frequency
if (this.isTracking) {
this.stopTracking();
this.startTracking();
}
}
// Check if tracking is active
public isActive(): boolean {
return this.isTracking;
}

// Start real-time tracking
public startTracking() {
if (this.isTracking) return;
this.isTracking = true;
this.updateInterval = setInterval(() => this.updatePortfolio(), this.updateFrequency);
}

// Stop real-time tracking
public stopTracking() {
if (this.updateInterval) {
clearInterval(this.updateInterval as unknown as number);
this.updateInterval = undefined;
}
this.isTracking = false;
}
}
export default new RealTimePortfolioService();
