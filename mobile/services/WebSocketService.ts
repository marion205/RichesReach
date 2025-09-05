import { Alert } from 'react-native';
import priceAlertService from './PriceAlertService';

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

class WebSocketService {
  private stockPriceSocket: WebSocket | null = null;
  private discussionSocket: WebSocket | null = null;
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

  public setCallbacks(callbacks: {
    onStockPriceUpdate?: (price: StockPrice) => void;
    onPriceAlert?: (alert: PriceAlert) => void;
    onNewDiscussion?: (discussion: DiscussionUpdate) => void;
    onNewComment?: (comment: CommentUpdate) => void;
    onDiscussionUpdate?: (discussionId: string, updates: any) => void;
    onConnectionStatusChange?: (connected: boolean) => void;
  }) {
    this.onStockPriceUpdate = callbacks.onStockPriceUpdate;
    this.onPriceAlert = callbacks.onPriceAlert;
    this.onNewDiscussion = callbacks.onNewDiscussion;
    this.onNewComment = callbacks.onNewComment;
    this.onDiscussionUpdate = callbacks.onDiscussionUpdate;
    this.onConnectionStatusChange = callbacks.onConnectionStatusChange;
  }

  public connect() {
    if (this.isConnected) {
      console.log('WebSocket already connected');
      return;
    }

    const baseUrl = 'ws://192.168.1.151:8000/ws';
    
    // Connect to stock prices WebSocket
    this.connectStockPrices(baseUrl);
    
    // Connect to discussions WebSocket
    this.connectDiscussions(baseUrl);
  }

  private connectStockPrices(baseUrl: string) {
    try {
      const url = `${baseUrl}/stock-prices/`;
      console.log('🔌 Connecting to stock prices WebSocket:', url);
      
      this.stockPriceSocket = new WebSocket(url);
      
      this.stockPriceSocket.onopen = () => {
        console.log('✅ Stock prices WebSocket connected');
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
        console.log('❌ Stock prices WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.onConnectionStatusChange?.(false);
        this.handleReconnect('stock-prices');
      };

      this.stockPriceSocket.onerror = (error) => {
        console.error('❌ Stock prices WebSocket error:', error);
      };

    } catch (error) {
      console.error('Error creating stock prices WebSocket:', error);
    }
  }

  private connectDiscussions(baseUrl: string) {
    try {
      const url = `${baseUrl}/discussions/`;
      console.log('🔌 Connecting to discussions WebSocket:', url);
      
      this.discussionSocket = new WebSocket(url);
      
      this.discussionSocket.onopen = () => {
        console.log('✅ Discussions WebSocket connected');
        
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
        console.log('❌ Discussions WebSocket disconnected:', event.code, event.reason);
        this.handleReconnect('discussions');
      };

      this.discussionSocket.onerror = (error) => {
        console.error('❌ Discussions WebSocket error:', error);
      };

    } catch (error) {
      console.error('Error creating discussions WebSocket:', error);
    }
  }

  private handleStockPriceMessage(data: any) {
    console.log('📊 Stock price message received:', data.type);
    
    switch (data.type) {
      case 'initial_prices':
        console.log('📈 Initial prices received:', data.prices);
        // Handle initial prices
        break;
        
      case 'stock_prices':
        console.log('📈 Stock prices received:', data.prices);
        // Handle stock prices
        break;
        
      case 'price_update':
        console.log('📈 Price update received:', data.symbol, data.price);
        const priceUpdate = {
          symbol: data.symbol,
          price: data.price,
          change: data.change,
          change_percent: data.change_percent,
          volume: data.volume,
          timestamp: data.timestamp
        };
        
        this.onStockPriceUpdate?.(priceUpdate);
        
        // Check price alerts
        priceAlertService.checkAlerts([priceUpdate]);
        break;
        
      case 'price_alert':
        console.log('🚨 Price alert received:', data.symbol, data.message);
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
        console.log('🏓 Pong received');
        break;
        
      default:
        console.log('Unknown stock price message type:', data.type);
    }
  }

  private handleDiscussionMessage(data: any) {
    console.log('💬 Discussion message received:', data.type);
    
    switch (data.type) {
      case 'new_discussion':
        console.log('💬 New discussion received:', data.discussion.title);
        this.onNewDiscussion?.(data.discussion);
        break;
        
      case 'new_comment':
        console.log('💬 New comment received:', data.comment.content);
        this.onNewComment?.(data.comment);
        break;
        
      case 'discussion_update':
        console.log('💬 Discussion update received:', data.discussion_id);
        this.onDiscussionUpdate?.(data.discussion_id, data.updates);
        break;
        
      case 'pong':
        console.log('🏓 Pong received');
        break;
        
      default:
        console.log('Unknown discussion message type:', data.type);
    }
  }

  private handleReconnect(type: 'stock-prices' | 'discussions') {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log(`❌ Max reconnection attempts reached for ${type}`);
      return;
    }

    this.reconnectAttempts++;
    console.log(`🔄 Attempting to reconnect ${type} (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (type === 'stock-prices') {
        this.connectStockPrices('ws://192.168.1.151:8000/ws');
      } else {
        this.connectDiscussions('ws://192.168.1.151:8000/ws');
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
      console.log('📊 Subscribed to stocks:', symbols);
    }
  }

  public getWatchlistPrices() {
    if (this.stockPriceSocket?.readyState === WebSocket.OPEN) {
      this.stockPriceSocket.send(JSON.stringify({
        type: 'get_watchlist_prices'
      }));
      console.log('📊 Requested watchlist prices');
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
    console.log('🔌 Disconnecting WebSockets');
    
    if (this.stockPriceSocket) {
      this.stockPriceSocket.close();
      this.stockPriceSocket = null;
    }
    
    if (this.discussionSocket) {
      this.discussionSocket.close();
      this.discussionSocket = null;
    }
    
    this.isConnected = false;
    this.onConnectionStatusChange?.(false);
  }

  public getConnectionStatus(): boolean {
    return this.isConnected;
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;
