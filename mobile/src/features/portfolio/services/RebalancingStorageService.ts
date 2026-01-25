import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';
export interface RebalancingResult {
id: string;
timestamp: string;
success: boolean;
message: string;
changesMade: string[];
stockTrades: StockTrade[];
newPortfolioValue: number;
rebalanceCost: number;
estimatedImprovement: string;
riskTolerance: string;
maxRebalancePercentage: number;
}
export interface StockTrade {
action: string;
symbol: string;
companyName: string;
shares: number;
price: number;
totalValue: number;
reason?: string;
}
class RebalancingStorageService {
private static instance: RebalancingStorageService;
private readonly STORAGE_KEY = 'rebalancing_results';
private readonly MAX_RESULTS = 10; // Keep only last 10 rebalancing results
public static getInstance(): RebalancingStorageService {
if (!RebalancingStorageService.instance) {
RebalancingStorageService.instance = new RebalancingStorageService();
}
return RebalancingStorageService.instance;
}
/**
* Save a rebalancing result to persistent storage
*/
async saveRebalancingResult(result: Omit<RebalancingResult, 'id' | 'timestamp'>): Promise<void> {
try {
const rebalancingResult: RebalancingResult = {
...result,
id: `rebalance_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
timestamp: new Date().toISOString(),
};
// Get existing results
const existingResults = await this.getRebalancingResults();
// Add new result to the beginning
const updatedResults = [rebalancingResult, ...existingResults].slice(0, this.MAX_RESULTS);
// Save to AsyncStorage
await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedResults));
} catch (error) {
logger.error('Error saving rebalancing result:', error);
throw error;
}
}
/**
* Get all saved rebalancing results
*/
async getRebalancingResults(): Promise<RebalancingResult[]> {
try {
const resultsJson = await AsyncStorage.getItem(this.STORAGE_KEY);
if (!resultsJson) {
return [];
}
const results = JSON.parse(resultsJson);
return Array.isArray(results) ? results : [];
} catch (error) {
logger.error('Error getting rebalancing results:', error);
return [];
}
}
/**
* Get the most recent rebalancing result
*/
async getLatestRebalancingResult(): Promise<RebalancingResult | null> {
try {
const results = await this.getRebalancingResults();
return results.length > 0 ? results[0] : null;
} catch (error) {
logger.error('Error getting latest rebalancing result:', error);
return null;
}
}
/**
* Clear all rebalancing results
*/
async clearAllResults(): Promise<void> {
try {
await AsyncStorage.removeItem(this.STORAGE_KEY);
} catch (error) {
logger.error('Error clearing rebalancing results:', error);
throw error;
}
}
/**
* Clear old results (keep only the most recent ones)
*/
async clearOldResults(keepCount: number = 5): Promise<void> {
try {
const results = await this.getRebalancingResults();
const recentResults = results.slice(0, keepCount);
await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(recentResults));
} catch (error) {
logger.error('Error clearing old rebalancing results:', error);
throw error;
}
}
/**
* Export rebalancing results as a formatted string
*/
async exportResults(): Promise<string> {
try {
const results = await this.getRebalancingResults();
if (results.length === 0) {
return 'No rebalancing results found.';
}
let exportText = 'REBALANCING RESULTS EXPORT\n';
exportText += '='.repeat(50) + '\n\n';
results.forEach((result, index) => {
exportText += `REBALANCING #${index + 1}\n`;
exportText += `Date: ${new Date(result.timestamp).toLocaleString()}\n`;
exportText += `Status: ${result.success ? 'SUCCESS' : 'FAILED'}\n`;
exportText += `Message: ${result.message}\n`;
exportText += `Risk Tolerance: ${result.riskTolerance}\n`;
exportText += `Max Rebalance: ${result.maxRebalancePercentage}%\n`;
exportText += `New Portfolio Value: $${result.newPortfolioValue.toFixed(2)}\n`;
exportText += `Rebalance Cost: $${result.rebalanceCost.toFixed(2)}\n`;
if (result.estimatedImprovement) {
exportText += `Estimated Improvement: ${result.estimatedImprovement}\n`;
}
if (result.changesMade.length > 0) {
exportText += `\nSector Changes:\n`;
result.changesMade.forEach(change => {
exportText += `• ${change}\n`;
});
}
if (result.stockTrades.length > 0) {
exportText += `\nStock Trades:\n`;
result.stockTrades.forEach(trade => {
exportText += `• ${trade.action} ${trade.shares} shares of ${trade.symbol} (${trade.companyName})\n`;
exportText += ` Price: $${trade.price.toFixed(2)} | Total: $${trade.totalValue.toFixed(2)}\n`;
if (trade.reason) {
exportText += ` Reason: ${trade.reason}\n`;
}
});
}
exportText += '\n' + '-'.repeat(40) + '\n\n';
});
return exportText;
} catch (error) {
logger.error('Error exporting rebalancing results:', error);
return 'Error exporting results.';
}
}
/**
* Get rebalancing statistics
*/
async getRebalancingStats(): Promise<{
totalRebalancings: number;
successfulRebalancings: number;
totalCost: number;
averageCost: number;
lastRebalancingDate: string | null;
}> {
try {
const results = await this.getRebalancingResults();
const successful = results.filter(r => r.success);
const totalCost = results.reduce((sum, r) => sum + r.rebalanceCost, 0);
return {
totalRebalancings: results.length,
successfulRebalancings: successful.length,
totalCost,
averageCost: results.length > 0 ? totalCost / results.length : 0,
lastRebalancingDate: results.length > 0 ? results[0].timestamp : null,
};
} catch (error) {
logger.error('Error getting rebalancing stats:', error);
return {
totalRebalancings: 0,
successfulRebalancings: 0,
totalCost: 0,
averageCost: 0,
lastRebalancingDate: null,
};
}
}
}
export default RebalancingStorageService;
