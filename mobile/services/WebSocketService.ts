import { Alert } from 'react-native';
// Use Expo Go compatible price alert service to avoid crashes
import expoGoCompatiblePriceAlertService from './ExpoGoCompatiblePriceAlertService';
// Import intelligent price alert service for "big day" detection
import intelligentPriceAlertService from './IntelligentPriceAlertService';
// Import real market data service
import MarketDataService, { StockQuote } from './MarketDataService';

export interface StockPrice {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: number;
}

export interface PriceAlert {
  symbol: string;
  price: number;
  alert_type: string;
  message: string;
  timestamp: number;
}

export interface DiscussionUpdate {
  id: string;
  title: string;
  content: string;
  user: {
    id: string;
    name: string;
    profilePic?: string;
  };
  stock?: {
    symbol: string;
    company_name: string;
  };
  discussion_type: string;
  visibility: string;
  score: number;
  comment_count: number;
  created_at: string;
}

export interface CommentUpdate {
  id: string;
  content: string;
  user: {
    id: string;
    name: string;
    profilePic?: string;
  };
  discussion_id: string;
  created_at: string;
}

export interface PortfolioUpdate {
  totalValue: number;
  totalCost: number;
  totalReturn: number;
  totalReturnPercent: number;
  holdings: Array<{
    symbol: string;
    companyName: string;
    shares: number;
    currentPrice: number;
    totalValue: number;
    costBasis: number;
    returnAmount: number;
    returnPercent: number;
    sector: string;
  }>;
  timestamp: number;
  marketStatus: 'open' | 'closed' | 'pre-market' | 'after-hours';
}

class WebSocketService {
  private stockPriceSocket: WebSocket | null = null;
  private discussionSocket: WebSocket | null = null;
  private portfolioSocket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private isConnected = false;
  private token: string | null = null;

  // Event callbacks
  private onStockPriceUpdate?: (price: StockPrice) => void;
  private onPriceAlert?: (alert: PriceAlert) => void;
  private onNewDiscussion?: (discussion: DiscussionUpdate) => void;
  private onNewComment?: (comment: CommentUpdate) => void;
  private onDiscussionUpdate?: (discussionId: string, updates: any) => void;
  private onPortfolioUpdate?: (portfolio: PortfolioUpdate) => void;
  private onConnectionStatusChange?: (connected: boolean) => void;

  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners() {
    // Handle app state changes
    // You can add app state listeners here if needed
  }

  public setToken(token: string) {
    this.token = token;
  }

  /**
   * Set up intelligent price alerts with user profile
   */
  public async setupIntelligentAlerts(userProfile?: {
    riskTolerance: 'conservative' | 'moderate' | 'aggressive';
    investmentHorizon: 'short' | 'medium' | 'long';
    portfolioSize: number;
    preferredSectors: string[];
    tradingFrequency: 'daily' | 'weekly' | 'monthly';
  }) {
    try {
      // Set default profile if none provided
      const profile = userProfile || {
        riskTolerance: 'moderate',
        investmentHorizon: 'medium',
        portfolioSize: 10000,
        preferredSectors: ['Technology', 'Healthcare', 'Finance'],
        tradingFrequency: 'weekly'
      };

      await intelligentPriceAlertService.setUserProfile(profile);
    } catch (error) {
      console.error('Error setting up intelligent alerts:', error);
    }
  }

  public setCallbacks(callbacks: {
    onStockPriceUpdate?: (price: StockPrice) => void;
    onPriceAlert?: (alert: PriceAlert) => void;
    onNewDiscussion?: (discussion: DiscussionUpdate) => void;
    onNewComment?: (comment: CommentUpdate) => void;
    onDiscussionUpdate?: (discussionId: string, updates: any) => void;
    onPortfolioUpdate?: (portfolio: PortfolioUpdate) => void;
    onConnectionStatusChange?: (connected: boolean) => void;
  }) {
    this.onStockPriceUpdate = callbacks.onStockPriceUpdate;
    this.onPriceAlert = callbacks.onPriceAlert;
    this.onNewDiscussion = callbacks.onNewDiscussion;
    this.onNewComment = callbacks.onNewComment;
    this.onDiscussionUpdate = callbacks.onDiscussionUpdate;
    this.onPortfolioUpdate = callbacks.onPortfolioUpdate;
    this.onConnectionStatusChange = callbacks.onConnectionStatusChange;
  }

  public connect() {
    if (this.isConnected) {
      return;
    }

    const baseUrl = 'ws://192.168.1.151:8001/ws';
    
    // Start real market data polling immediately
    this.startRealMarketDataPolling();
    
    // Connect to stock prices WebSocket
    this.connectStockPrices(baseUrl);
    
    // Connect to discussions WebSocket
    this.connectDiscussions(baseUrl);
    
    // Connect to portfolio WebSocket (disabled for now - using mock data)
    // this.connectPortfolio(baseUrl);
  }

  private connectStockPrices(baseUrl: string) {
    try {
      const url = `${baseUrl}/stock-prices/`;
      
      this.stockPriceSocket = new WebSocket(url);
      
      this.stockPriceSocket.onopen = () => {
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.isConnected = true;
        this.onConnectionStatusChange?.(true);
        
        // Send authentication token if available
        if (this.token) {
          this.stockPriceSocket?.send(JSON.stringify({
            type: 'authenticate',
            token: this.token
          }));
        }

        // Start real market data polling as fallback
        this.startRealMarketDataPolling();
      };

      this.stockPriceSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleStockPriceMessage(data);
        } catch (error) {
          console.error('Error parsing stock price message:', error);
        }
      };

      this.stockPriceSocket.onclose = (event) => {
        this.isConnected = false;
        this.onConnectionStatusChange?.(false);
        this.handleReconnect('stock-prices');
      };

      this.stockPriceSocket.onerror = (error) => {
        console.error('Stock prices WebSocket error:', error);
        // If WebSocket fails, fall back to real market data polling
        this.startRealMarketDataPolling();
      };

    } catch (error) {
      console.error('Error creating stock prices WebSocket:', error);
    }
  }

  private connectDiscussions(baseUrl: string) {
    try {
      const url = `${baseUrl}/discussions/`;
      
      this.discussionSocket = new WebSocket(url);
      
      this.discussionSocket.onopen = () => {
        
        // Send authentication token if available
        if (this.token) {
          this.discussionSocket?.send(JSON.stringify({
            type: 'authenticate',
            token: this.token
          }));
        }
      };

      this.discussionSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleDiscussionMessage(data);
        } catch (error) {
          console.error('Error parsing discussion message:', error);
        }
      };

      this.discussionSocket.onclose = (event) => {
        this.handleReconnect('discussions');
      };

      this.discussionSocket.onerror = (error) => {
        console.error('Discussions WebSocket error:', error);
      };

    } catch (error) {
      console.error('Error creating discussions WebSocket:', error);
    }
  }

  private connectPortfolio(baseUrl: string) {
    try {
      const url = `${baseUrl}/portfolio/`;
      
      this.portfolioSocket = new WebSocket(url);
      
      this.portfolioSocket.onopen = () => {
        
        // Send authentication token if available
        if (this.token) {
          this.portfolioSocket?.send(JSON.stringify({
            type: 'authenticate',
            token: this.token
          }));
        }
      };

      this.portfolioSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handlePortfolioMessage(data);
        } catch (error) {
          console.error('Error parsing portfolio WebSocket message:', error);
        }
      };

      this.portfolioSocket.onclose = () => {
        this.handleReconnect('portfolio');
      };

      this.portfolioSocket.onerror = (error) => {
        console.error('Portfolio WebSocket error:', error);
      };

    } catch (error) {
      console.error('Error creating portfolio WebSocket:', error);
    }
  }

  private handleStockPriceMessage(data: any) {
    switch (data.type) {
      case 'initial_prices':
        // Handle initial prices
        break;
        
      case 'stock_prices':
        // Handle stock prices
        break;
        
      case 'price_update':
        const priceUpdate = {
          symbol: data.symbol,
          price: data.price,
          change: data.change,
          change_percent: data.change_percent,
          volume: data.volume,
          timestamp: data.timestamp
        };
        
        this.onStockPriceUpdate?.(priceUpdate);
        
        // Check basic price alerts
        expoGoCompatiblePriceAlertService.checkAlerts([priceUpdate]);
        
        // Check for "big day" movements and trigger intelligent analysis
        this.checkForBigDayMovement(priceUpdate);
        break;
        
      case 'price_alert':
        this.onPriceAlert?.({
          symbol: data.symbol,
          price: data.price,
          alert_type: data.alert_type,
          message: data.message,
          timestamp: data.timestamp
        });
        
        // Show alert to user
        Alert.alert(
          'Price Alert',
          `${data.symbol}: ${data.message}`,
          [{ text: 'OK' }]
        );
        break;
        
      case 'pong':
        break;
        
      default:
        // Unknown message type
    }
  }

  private handleDiscussionMessage(data: any) {
    switch (data.type) {
      case 'new_discussion':
        this.onNewDiscussion?.(data.discussion);
        break;
        
      case 'new_comment':
        this.onNewComment?.(data.comment);
        break;
        
      case 'discussion_update':
        this.onDiscussionUpdate?.(data.discussion_id, data.updates);
        break;
        
      case 'pong':
        break;
        
      default:
        // Unknown message type
    }
  }

  private handlePortfolioMessage(data: any) {
    switch (data.type) {
      case 'portfolio_update':
        const portfolioUpdate: PortfolioUpdate = {
          totalValue: data.totalValue,
          totalCost: data.totalCost,
          totalReturn: data.totalReturn,
          totalReturnPercent: data.totalReturnPercent,
          holdings: data.holdings,
          timestamp: data.timestamp,
          marketStatus: data.marketStatus
        };
        
        this.onPortfolioUpdate?.(portfolioUpdate);
        break;
        
      case 'pong':
        break;
        
      default:
        // Unknown message type
    }
  }

  private handleReconnect(type: 'stock-prices' | 'discussions' | 'portfolio') {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.reconnectAttempts++;
    
    setTimeout(() => {
      if (type === 'stock-prices') {
        this.connectStockPrices('ws://localhost:8001/ws');
      } else if (type === 'discussions') {
        this.connectDiscussions('ws://localhost:8001/ws');
      } else if (type === 'portfolio') {
        this.connectPortfolio('ws://localhost:8001/ws');
      }
    }, this.reconnectDelay);
    
    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  public subscribeToStocks(symbols: string[]) {
    if (this.stockPriceSocket?.readyState === WebSocket.OPEN) {
      this.stockPriceSocket.send(JSON.stringify({
        type: 'subscribe_stocks',
        symbols: symbols
      }));
    }
  }

  public subscribeToPortfolio() {
    if (this.portfolioSocket?.readyState === WebSocket.OPEN) {
      this.portfolioSocket.send(JSON.stringify({
        type: 'subscribe_portfolio'
      }));
    }
  }

  public getWatchlistPrices() {
    if (this.stockPriceSocket?.readyState === WebSocket.OPEN) {
      this.stockPriceSocket.send(JSON.stringify({
        type: 'get_watchlist_prices'
      }));
    }
  }

  public ping() {
    if (this.stockPriceSocket?.readyState === WebSocket.OPEN) {
      this.stockPriceSocket.send(JSON.stringify({
        type: 'ping'
      }));
    }
    
    if (this.discussionSocket?.readyState === WebSocket.OPEN) {
      this.discussionSocket.send(JSON.stringify({
        type: 'ping'
      }));
    }
  }

  public disconnect() {
    // Stop real market data polling
    if (this.marketDataInterval) {
      clearInterval(this.marketDataInterval);
      this.marketDataInterval = undefined;
    }
    
    if (this.stockPriceSocket) {
      this.stockPriceSocket.close();
      this.stockPriceSocket = null;
    }
    
    if (this.discussionSocket) {
      this.discussionSocket.close();
      this.discussionSocket = null;
    }
    
    if (this.portfolioSocket) {
      this.portfolioSocket.close();
      this.portfolioSocket = null;
    }
    
    this.isConnected = false;
    this.onConnectionStatusChange?.(false);
  }

  public getConnectionStatus(): boolean {
    return this.isConnected;
  }

  /**
   * Check for significant price movements that might indicate a "big day"
   * and trigger intelligent analysis
   */
  private async checkForBigDayMovement(priceUpdate: StockPrice) {
    try {
      // Define thresholds for "big day" detection
      const BIG_DAY_THRESHOLDS = {
        priceChangePercent: 3.0, // 3% price change
        volumeSpike: 2.0, // 2x normal volume
        highVolume: 1000000, // 1M+ volume
      };

      const isSignificantPriceMove = Math.abs(priceUpdate.change_percent) >= BIG_DAY_THRESHOLDS.priceChangePercent;
      const isHighVolume = priceUpdate.volume >= BIG_DAY_THRESHOLDS.highVolume;
      
      // Check if this is a "big day" movement
      if (isSignificantPriceMove || isHighVolume) {

        // Generate mock historical data for analysis (in real app, fetch from API)
        const historicalData = this.generateMockHistoricalData(priceUpdate);
        
        // Generate mock market conditions
        const marketConditions = {
          marketTrend: this.determineMarketTrend(priceUpdate.change_percent),
          volatility: (isSignificantPriceMove ? 'high' : 'medium') as 'high' | 'medium' | 'low',
          volume: (isHighVolume ? 'high' : 'normal') as 'high' | 'low' | 'normal',
          sectorPerformance: priceUpdate.change_percent * 0.8, // Mock sector performance
        };

        // Trigger intelligent analysis
        const alerts = await intelligentPriceAlertService.analyzeStock(
          priceUpdate.symbol,
          priceUpdate,
          historicalData,
          marketConditions
        );

        // Process any generated alerts
        if (alerts.length > 0) {
          for (const alert of alerts) {
            // Show intelligent alert to user
            this.showIntelligentAlert(alert);
          }
        }
      }
    } catch (error) {
      console.error('Error in big day movement analysis:', error);
    }
  }

  /**
   * Generate mock historical data for technical analysis
   * In a real app, this would fetch from your API
   */
  // Real market data polling
  private marketDataInterval?: NodeJS.Timeout;
  private watchedSymbols: string[] = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'];

  private startRealMarketDataPolling() {
    // Clear any existing interval
    if (this.marketDataInterval) {
      clearInterval(this.marketDataInterval);
    }

    // Poll for real market data every 30 seconds during market hours
    this.marketDataInterval = setInterval(async () => {
      try {
        await this.fetchAndUpdateRealMarketData();
      } catch (error) {
        console.error('Error fetching real market data:', error);
      }
    }, 30000); // 30 seconds

    // Initial fetch
    this.fetchAndUpdateRealMarketData();
  }

  private async fetchAndUpdateRealMarketData() {
    try {
      const quotes = await MarketDataService.getMultipleQuotes(this.watchedSymbols);
      
      quotes.forEach(quote => {
        const stockPrice: StockPrice = {
          symbol: quote.symbol,
          price: quote.price,
          change: quote.change,
          change_percent: quote.changePercent,
          volume: quote.volume,
          timestamp: Date.now()
        };

        // Send real market data to listeners
        this.onStockPriceUpdate?.(stockPrice);
        
        // Check price alerts with real data
        expoGoCompatiblePriceAlertService.checkAlerts([stockPrice]);
        
        // Check for "big day" movements
        this.checkForBigDayMovement(stockPrice);
      });
    } catch (error) {
      console.error('Failed to fetch real market data:', error);
      // Fall back to mock data if real data fails
      this.generateMockStockPrices();
    }
  }

  private generateMockStockPrices() {
    this.watchedSymbols.forEach(symbol => {
      const mockPrice: StockPrice = {
        symbol,
        price: 100 + Math.random() * 200,
        change: (Math.random() - 0.5) * 10,
        change_percent: (Math.random() - 0.5) * 5,
        volume: Math.floor(Math.random() * 1000000),
        timestamp: Date.now()
      };

      this.onStockPriceUpdate?.(mockPrice);
      expoGoCompatiblePriceAlertService.checkAlerts([mockPrice]);
    });
  }

  private generateMockHistoricalData(currentPrice: StockPrice): StockPrice[] {
    const historicalData: StockPrice[] = [];
    const basePrice = currentPrice.price;
    const baseVolume = currentPrice.volume || 1000000;
    
    // Generate 50 days of mock data
    for (let i = 50; i >= 0; i--) {
      const daysAgo = i;
      const priceVariation = (Math.random() - 0.5) * 0.1; // ±5% variation
      const volumeVariation = (Math.random() - 0.5) * 0.5; // ±25% volume variation
      
      historicalData.push({
        symbol: currentPrice.symbol,
        price: basePrice * (1 + priceVariation),
        change: 0,
        change_percent: 0,
        volume: Math.max(100000, baseVolume * (1 + volumeVariation)),
        timestamp: currentPrice.timestamp - (daysAgo * 24 * 60 * 60 * 1000)
      });
    }
    
    return historicalData;
  }

  /**
   * Determine market trend based on price movement
   */
  private determineMarketTrend(changePercent: number): 'bullish' | 'bearish' | 'sideways' {
    if (changePercent > 2) return 'bullish';
    if (changePercent < -2) return 'bearish';
    return 'sideways';
  }

  /**
   * Show intelligent alert to user
   */
  private showIntelligentAlert(alert: any) {
    const alertTypeEmoji = {
      'buy_opportunity': '🟢',
      'sell_signal': '🔴',
      'technical_breakout': '🚀',
      'price_target': '🎯'
    };

    const emoji = alertTypeEmoji[alert.alertType as keyof typeof alertTypeEmoji] || '📊';
    const title = `${emoji} ${alert.symbol} ${alert.alertType.replace('_', ' ').toUpperCase()}`;
    
    let message = `Confidence: ${Math.round(alert.confidence)}%\n\n`;
    message += `Reason: ${alert.reason}\n\n`;
    message += `Technical Score: ${Math.round(alert.technicalScore)}/100\n`;
    message += `Market Score: ${Math.round(alert.marketScore)}/100\n`;
    message += `User Match: ${Math.round(alert.userScore)}/100`;
    
    if (alert.targetPrice) {
      message += `\n\nTarget Price: $${alert.targetPrice.toFixed(2)}`;
    }
    if (alert.stopLoss) {
      message += `\nStop Loss: $${alert.stopLoss.toFixed(2)}`;
    }

    // Show alert to user
    Alert.alert(
      title,
      message,
      [
        { text: 'Dismiss', style: 'cancel' },
        { text: 'View Details', onPress: () => {} }
      ]
    );

    // Also trigger the price alert callback
    this.onPriceAlert?.({
      symbol: alert.symbol,
      price: 0, // Current price not available in alert
      alert_type: 'intelligent_' + alert.alertType,
      message: `${alert.alertType.replace('_', ' ')} - ${alert.reason}`,
      timestamp: Date.now()
    });
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;
