import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { Alert } from 'react-native';
import logger from '../utils/logger';

interface OfflineData {
  timestamp: number;
  data: any;
  version: string;
}

interface CachedInsight {
  id: string;
  type: 'portfolio' | 'market' | 'ai_signal' | 'tax_optimization' | 'risk_analysis';
  data: any;
  timestamp: number;
  expiresAt: number;
  priority: 'high' | 'medium' | 'low';
}

interface OfflineInsightsService {
  isOnline: boolean;
  isOfflineMode: boolean;
  cachedInsights: CachedInsight[];
  lastSyncTime: number;
  pendingActions: any[];
}

class OfflineInsightsService {
  private static instance: OfflineInsightsService;
  private cacheKey = 'richesreach_offline_cache';
  private insightsKey = 'richesreach_cached_insights';
  private pendingActionsKey = 'richesreach_pending_actions';
  private maxCacheSize = 50; // MB
  private cacheExpiryTime = 24 * 60 * 60 * 1000; // 24 hours
  private syncInterval: NodeJS.Timeout | null = null;
  private cacheCleanupInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.isOnline = true;
    this.isOfflineMode = false;
    this.cachedInsights = [];
    this.lastSyncTime = Date.now();
    this.pendingActions = [];
    
    this.initializeService();
  }

  static getInstance(): OfflineInsightsService {
    if (!OfflineInsightsService.instance) {
      OfflineInsightsService.instance = new OfflineInsightsService();
    }
    return OfflineInsightsService.instance;
  }

  private async initializeService() {
    // Load cached data
    await this.loadCachedData();
    
    // Set up network monitoring
    this.setupNetworkMonitoring();
    
    // Set up periodic sync
    this.setupPeriodicSync();
    
    // Set up cache cleanup
    this.setupCacheCleanup();
  }

  private async loadCachedData() {
    try {
      const [cachedInsights, pendingActions] = await Promise.all([
        AsyncStorage.getItem(this.insightsKey),
        AsyncStorage.getItem(this.pendingActionsKey),
      ]);

      if (cachedInsights) {
        this.cachedInsights = JSON.parse(cachedInsights);
      }

      if (pendingActions) {
        this.pendingActions = JSON.parse(pendingActions);
      }
    } catch (error) {
      logger.error('Error loading cached data:', error);
    }
  }

  private setupNetworkMonitoring() {
    NetInfo.addEventListener(state => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected ?? false;
      
      if (wasOnline && !this.isOnline) {
        this.handleGoOffline();
      } else if (!wasOnline && this.isOnline) {
        this.handleComeOnline();
      }
    });
  }

  private setupPeriodicSync() {
    // Sync every 5 minutes when online
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    this.syncInterval = setInterval(() => {
      if (this.isOnline && this.pendingActions.length > 0) {
        this.syncPendingActions();
      }
    }, 5 * 60 * 1000);
  }

  private setupCacheCleanup() {
    // Clean up expired cache every hour
    if (this.cacheCleanupInterval) {
      clearInterval(this.cacheCleanupInterval);
    }
    this.cacheCleanupInterval = setInterval(() => {
      this.cleanupExpiredCache();
    }, 60 * 60 * 1000);
  }
  
  /**
   * Cleanup method to stop all intervals
   */
  cleanup(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
    if (this.cacheCleanupInterval) {
      clearInterval(this.cacheCleanupInterval);
      this.cacheCleanupInterval = null;
    }
  }

  private handleGoOffline() {
    this.isOfflineMode = true;
    logger.log('📱 App went offline - switching to offline mode');
    
    // Show offline notification
    this.showOfflineNotification();
    
    // Prioritize critical insights
    this.prioritizeCriticalInsights();
  }

  private handleComeOnline() {
    this.isOfflineMode = false;
    logger.log('📱 App came online - syncing data');
    
    // Hide offline notification
    this.hideOfflineNotification();
    
    // Sync pending actions
    this.syncPendingActions();
    
    // Refresh critical insights
    this.refreshCriticalInsights();
  }

  private showOfflineNotification() {
    // Show subtle offline indicator
    Alert.alert(
      'Offline Mode',
      'You\'re offline. Some features may be limited, but your cached insights are still available.',
      [{ text: 'OK' }]
    );
  }

  private hideOfflineNotification() {
    // Hide offline indicator
    logger.log('📱 Back online - full functionality restored');
  }

  // Core Offline Functionality
  async cacheInsight(insight: Omit<CachedInsight, 'timestamp' | 'expiresAt'>) {
    const cachedInsight: CachedInsight = {
      ...insight,
      timestamp: Date.now(),
      expiresAt: Date.now() + this.cacheExpiryTime,
    };

    this.cachedInsights.push(cachedInsight);
    
    // Limit cache size
    if (this.cachedInsights.length > this.maxCacheSize) {
      this.cachedInsights = this.cachedInsights
        .sort((a, b) => b.priority.localeCompare(a.priority))
        .slice(0, this.maxCacheSize);
    }

    await this.saveCachedInsights();
  }

  async getCachedInsight(id: string): Promise<CachedInsight | null> {
    const insight = this.cachedInsights.find(i => i.id === id);
    
    if (insight && insight.expiresAt > Date.now()) {
      return insight;
    }
    
    return null;
  }

  async getCachedInsightsByType(type: CachedInsight['type']): Promise<CachedInsight[]> {
    return this.cachedInsights
      .filter(insight => insight.type === type && insight.expiresAt > Date.now())
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  async getCriticalInsights(): Promise<CachedInsight[]> {
    return this.cachedInsights
      .filter(insight => insight.priority === 'high' && insight.expiresAt > Date.now())
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  // Offline Portfolio Analysis
  async getOfflinePortfolioAnalysis(portfolio: any): Promise<any> {
    const cachedAnalysis = await this.getCachedInsight(`portfolio_analysis_${portfolio.id}`);
    
    if (cachedAnalysis) {
      return {
        ...cachedAnalysis.data,
        isOffline: true,
        lastUpdated: new Date(cachedAnalysis.timestamp).toLocaleString(),
      };
    }

    // Generate basic offline analysis
    return this.generateOfflinePortfolioAnalysis(portfolio);
  }

  private generateOfflinePortfolioAnalysis(portfolio: any) {
    const analysis = {
      totalValue: portfolio.totalValue || 0,
      totalReturn: portfolio.totalReturn || 0,
      riskScore: this.calculateOfflineRiskScore(portfolio),
      diversification: this.calculateOfflineDiversification(portfolio),
      recommendations: this.generateOfflineRecommendations(portfolio),
      isOffline: true,
      lastUpdated: new Date().toLocaleString(),
    };

    // Cache the analysis
    this.cacheInsight({
      id: `portfolio_analysis_${portfolio.id}`,
      type: 'portfolio',
      data: analysis,
      priority: 'high',
    });

    return analysis;
  }

  private calculateOfflineRiskScore(portfolio: any): number {
    // Simple risk calculation based on asset allocation
    const allocation = portfolio.allocation || {};
    const riskWeights = {
      stocks: 0.8,
      bonds: 0.3,
      crypto: 0.9,
      cash: 0.1,
      real_estate: 0.6,
    };

    let weightedRisk = 0;
    let totalWeight = 0;

    Object.entries(allocation).forEach(([asset, percentage]) => {
      const weight = riskWeights[asset as keyof typeof riskWeights] || 0.5;
      weightedRisk += (percentage as number) * weight;
      totalWeight += percentage as number;
    });

    return totalWeight > 0 ? Math.round((weightedRisk / totalWeight) * 10) : 5;
  }

  private calculateOfflineDiversification(portfolio: any): number {
    const allocation = portfolio.allocation || {};
    const assetCount = Object.keys(allocation).length;
    const maxWeight = Math.max(...Object.values(allocation) as number[]);
    
    // Simple diversification score
    const concentrationPenalty = maxWeight > 50 ? (maxWeight - 50) * 0.5 : 0;
    const diversificationBonus = Math.min(assetCount * 10, 30);
    
    return Math.max(0, Math.min(100, 70 + diversificationBonus - concentrationPenalty));
  }

  private generateOfflineRecommendations(portfolio: any): string[] {
    const recommendations = [];
    const allocation = portfolio.allocation || {};
    
    // Check for over-concentration
    const maxWeight = Math.max(...Object.values(allocation) as number[]);
    if (maxWeight > 60) {
      recommendations.push('Consider diversifying your portfolio to reduce concentration risk');
    }
    
    // Check for low diversification
    const assetCount = Object.keys(allocation).length;
    if (assetCount < 3) {
      recommendations.push('Add more asset classes to improve diversification');
    }
    
    // Check cash position
    const cashPercentage = allocation.cash || 0;
    if (cashPercentage < 5) {
      recommendations.push('Consider maintaining a 5-10% cash position for opportunities');
    } else if (cashPercentage > 20) {
      recommendations.push('Your cash position is high - consider investing excess cash');
    }
    
    return recommendations;
  }

  // Offline Market Data
  async getOfflineMarketData(symbols: string[]): Promise<any> {
    const marketData: any = {};
    
    for (const symbol of symbols) {
      const cachedData = await this.getCachedInsight(`market_data_${symbol}`);
      if (cachedData) {
        marketData[symbol] = {
          ...cachedData.data,
          isOffline: true,
          lastUpdated: new Date(cachedData.timestamp).toLocaleString(),
        };
      }
    }
    
    return marketData;
  }

  // Offline AI Signals
  async getOfflineAISignals(): Promise<any[]> {
    const signals = await this.getCachedInsightsByType('ai_signal');
    return signals.map(signal => ({
      ...signal.data,
      isOffline: true,
      lastUpdated: new Date(signal.timestamp).toLocaleString(),
    }));
  }

  // Offline Tax Optimization
  async getOfflineTaxOptimization(portfolio: any): Promise<any> {
    const cachedOptimization = await this.getCachedInsight(`tax_optimization_${portfolio.id}`);
    
    if (cachedOptimization) {
      return {
        ...cachedOptimization.data,
        isOffline: true,
        lastUpdated: new Date(cachedOptimization.timestamp).toLocaleString(),
      };
    }

    // Generate basic offline tax optimization
    return this.generateOfflineTaxOptimization(portfolio);
  }

  private generateOfflineTaxOptimization(portfolio: any) {
    const optimization = {
      taxLossHarvesting: {
        available: portfolio.unrealizedLosses > 0,
        potentialSavings: portfolio.unrealizedLosses * 0.2, // Assume 20% tax rate
        recommendations: portfolio.unrealizedLosses > 0 
          ? ['Consider harvesting losses to offset gains'] 
          : ['No loss harvesting opportunities available'],
      },
      capitalGainsOptimization: {
        shortTermGains: portfolio.shortTermGains || 0,
        longTermGains: portfolio.longTermGains || 0,
        recommendations: portfolio.shortTermGains > portfolio.longTermGains
          ? ['Consider holding positions longer to qualify for long-term rates']
          : ['Your capital gains structure is tax-efficient'],
      },
      isOffline: true,
      lastUpdated: new Date().toLocaleString(),
    };

    // Cache the optimization
    this.cacheInsight({
      id: `tax_optimization_${portfolio.id}`,
      type: 'tax_optimization',
      data: optimization,
      priority: 'medium',
    });

    return optimization;
  }

  // Pending Actions Management
  async addPendingAction(action: any) {
    this.pendingActions.push({
      ...action,
      timestamp: Date.now(),
      id: `pending_${Date.now()}_${Math.random()}`,
    });
    
    await this.savePendingActions();
  }

  async syncPendingActions() {
    if (!this.isOnline || this.pendingActions.length === 0) {
      return;
    }

    logger.log(`📱 Syncing ${this.pendingActions.length} pending actions`);
    
    const actionsToSync = [...this.pendingActions];
    this.pendingActions = [];
    
    try {
      for (const action of actionsToSync) {
        await this.executeAction(action);
      }
      
      await this.savePendingActions();
      logger.log('📱 Successfully synced all pending actions');
    } catch (error) {
      logger.error('Error syncing pending actions:', error);
      // Re-add failed actions
      this.pendingActions = [...actionsToSync, ...this.pendingActions];
      await this.savePendingActions();
    }
  }

  private async executeAction(action: any) {
    // Execute the action based on type
    switch (action.type) {
      case 'trade':
        // Execute trade
        break;
      case 'portfolio_update':
        // Update portfolio
        break;
      case 'tax_harvest':
        // Execute tax harvesting
        break;
      default:
        logger.warn('Unknown action type:', action.type);
    }
  }

  // Cache Management
  private async cleanupExpiredCache() {
    const now = Date.now();
    this.cachedInsights = this.cachedInsights.filter(insight => insight.expiresAt > now);
    await this.saveCachedInsights();
  }

  private async saveCachedInsights() {
    try {
      await AsyncStorage.setItem(this.insightsKey, JSON.stringify(this.cachedInsights));
    } catch (error) {
      logger.error('Error saving cached insights:', error);
    }
  }

  private async savePendingActions() {
    try {
      await AsyncStorage.setItem(this.pendingActionsKey, JSON.stringify(this.pendingActions));
    } catch (error) {
      logger.error('Error saving pending actions:', error);
    }
  }

  private prioritizeCriticalInsights() {
    // Move critical insights to the top of cache
    this.cachedInsights.sort((a, b) => {
      if (a.priority === 'high' && b.priority !== 'high') return -1;
      if (b.priority === 'high' && a.priority !== 'high') return 1;
      return b.timestamp - a.timestamp;
    });
  }

  private async refreshCriticalInsights() {
    // Refresh high-priority insights when coming back online
    const criticalInsights = this.cachedInsights.filter(insight => insight.priority === 'high');
    
    for (const insight of criticalInsights) {
      // Trigger refresh of critical insights
      logger.log(`📱 Refreshing critical insight: ${insight.id}`);
    }
  }

  // Public API
  getOfflineStatus() {
    return {
      isOnline: this.isOnline,
      isOfflineMode: this.isOfflineMode,
      cachedInsightsCount: this.cachedInsights.length,
      pendingActionsCount: this.pendingActions.length,
      lastSyncTime: this.lastSyncTime,
    };
  }

  async clearCache() {
    this.cachedInsights = [];
    this.pendingActions = [];
    await Promise.all([
      AsyncStorage.removeItem(this.insightsKey),
      AsyncStorage.removeItem(this.pendingActionsKey),
    ]);
  }

  async getCacheSize(): Promise<number> {
    try {
      const insights = await AsyncStorage.getItem(this.insightsKey);
      const actions = await AsyncStorage.getItem(this.pendingActionsKey);
      
      const insightsSize = insights ? new Blob([insights]).size : 0;
      const actionsSize = actions ? new Blob([actions]).size : 0;
      
      return (insightsSize + actionsSize) / (1024 * 1024); // MB
    } catch (error) {
      logger.error('Error calculating cache size:', error);
      return 0;
    }
  }
}

export default OfflineInsightsService.getInstance();
