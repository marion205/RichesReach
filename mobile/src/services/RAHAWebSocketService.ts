/**
 * RAHA WebSocket Service
 * Manages WebSocket connection for real-time RAHA signals and price updates
 */
import { io, Socket } from "socket.io-client";
import logger from "../utils/logger";
import { API_BASE } from "../config/api";

export interface RAHASignal {
  id: string;
  symbol: string;
  signalType?: string;
  signal_type?: string; // Backward compatibility
  price: number | string;
  stopLoss?: number | string;
  stop_loss?: number | string; // Backward compatibility
  takeProfit?: number | string;
  take_profit?: number | string; // Backward compatibility
  confidenceScore?: number;
  confidence_score?: number; // Backward compatibility
  timeframe: string;
  strategyName?: string;
  strategy_name?: string; // Backward compatibility
}

export interface PriceUpdate {
  symbol: string;
  price: {
    price: number;
    change: number;
    changePercent: number;
    volume?: number;
  };
}

export interface BacktestComplete {
  backtest_id: string;
  backtest: {
    id: string;
    symbol: string;
    status: string;
    metrics?: any;
  };
}

type SignalCallback = (signal: RAHASignal) => void;
type PriceUpdateCallback = (update: PriceUpdate) => void;
type BacktestCallback = (backtest: BacktestComplete) => void;

class RAHAWebSocketService {
  private socket: Socket | null = null;
  private isConnected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;

  private signalCallbacks: Set<SignalCallback> = new Set();
  private priceUpdateCallbacks: Set<PriceUpdateCallback> = new Set();
  private backtestCallbacks: Set<BacktestCallback> = new Set();

  private apiBaseUrl: string;

  constructor() {
    // Use API_BASE from config (handles device detection automatically)
    // This ensures we use the same URL as other services (LAN IP for physical devices, localhost for simulator)
    this.apiBaseUrl = API_BASE;
    // Remove trailing slash
    this.apiBaseUrl = this.apiBaseUrl.replace(/\/$/, "");
    logger.log(`🔌 [RAHA WebSocket] Using API base: ${this.apiBaseUrl}`);
  }

  /**
   * Connect to WebSocket server
   */
  connect(token?: string): void {
    // Demo mode: skip WebSocket connection entirely
    if (process.env.EXPO_PUBLIC_DEMO_MODE === 'true') {
      logger.log("🎭 [RAHA WebSocket] Demo mode — skipping connection");
      return;
    }

    if (this.socket?.connected) {
      logger.log("🔌 WebSocket already connected");
      return;
    }

    try {
      const url = `${this.apiBaseUrl}/socket.io/`;
      logger.log(`🔌 [RAHA WebSocket] Connecting to: ${url}`);

      this.socket = io(url, {
        transports: ["websocket", "polling"],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        reconnectionDelayMax: 5000,
        timeout: 20000,
        auth: token ? { token } : undefined,
      });

      this.setupEventHandlers();

    } catch (error) {
      logger.error("❌ WebSocket connection error:", error);
      this.isConnected = false;
    }
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.socket) {return;}

    this.socket.on("connect", () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      logger.log("✅ [RAHA WebSocket] Connected successfully");
    });

    this.socket.on("disconnect", (reason) => {
      this.isConnected = false;
      logger.log(`👋 [RAHA WebSocket] Disconnected: ${reason}`);
    });

    this.socket.on("connect_error", (error) => {
      this.reconnectAttempts++;
      logger.error(`❌ [RAHA WebSocket] Connection error: ${error.message}`);
      logger.error(
        `❌ [RAHA WebSocket] Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
      );
      logger.error(`❌ [RAHA WebSocket] URL: ${this.apiBaseUrl}/socket.io/`);

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        logger.error("❌ [RAHA WebSocket] Max reconnection attempts reached");
        logger.error(
          `❌ [RAHA WebSocket] Check if server is running at ${this.apiBaseUrl}`
        );
        logger.error(
          `❌ [RAHA WebSocket] Verify Socket.io is enabled on the backend`
        );
      }
    });

    this.socket.on("connected", (data) => {
      logger.log("📡 WebSocket handshake complete:", data);
    });

    // RAHA Signal event
    this.socket.on("raha_signal", (data: { signal: RAHASignal }) => {
      logger.log("📊 Received RAHA signal:", data.signal);
      this.signalCallbacks.forEach((callback) => {
        try {
          callback(data.signal);
        } catch (error) {
          logger.error("❌ Error in signal callback:", error);
        }
      });
    });

    // Price update event
    this.socket.on(
      "price_update",
      (data: { symbol: string; price: PriceUpdate["price"] }) => {
        logger.log(`💰 Price update for ${data.symbol}:`, data.price);
        const update: PriceUpdate = {
          symbol: data.symbol,
          price: data.price,
        };
        this.priceUpdateCallbacks.forEach((callback) => {
          try {
            callback(update);
          } catch (error) {
            logger.error("❌ Error in price update callback:", error);
          }
        });
      },
    );

      // Backtest complete event
      this.socket.on("backtest_complete", (data: BacktestComplete) => {
        logger.log("✅ Backtest complete:", data);
        this.backtestCallbacks.forEach((callback) => {
          try {
            callback(data);
          } catch (error) {
            logger.error("❌ Error in backtest callback:", error);
          }
        });
      });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      logger.log("👋 WebSocket disconnected");
    }
  }

  /**
   * Subscribe to price updates for a symbol
   */
  subscribeToSymbol(symbol: string): void {
    if (!this.socket?.connected) {
      logger.warn("⚠️  WebSocket not connected - cannot subscribe to symbol");
      return;
    }

    this.socket.emit("subscribe_symbol", { symbol: symbol.toUpperCase() });
    logger.log(`📊 Subscribed to ${symbol}`);
  }

  /**
   * Unsubscribe from price updates for a symbol
   */
  unsubscribeFromSymbol(symbol: string): void {
    if (!this.socket?.connected) {
      return;
    }

    this.socket.emit("unsubscribe_symbol", { symbol: symbol.toUpperCase() });
    logger.log(`📊 Unsubscribed from ${symbol}`);
  }

  /**
   * Register callback for RAHA signals
   */
  onSignal(callback: SignalCallback): () => void {
    this.signalCallbacks.add(callback);
    return () => {
      this.signalCallbacks.delete(callback);
    };
  }

  /**
   * Register callback for price updates
   */
  onPriceUpdate(callback: PriceUpdateCallback): () => void {
    this.priceUpdateCallbacks.add(callback);
    return () => {
      this.priceUpdateCallbacks.delete(callback);
    };
  }

  /**
   * Register callback for backtest completion
   */
  onBacktestComplete(callback: BacktestCallback): () => void {
    this.backtestCallbacks.add(callback);
    return () => {
      this.backtestCallbacks.delete(callback);
    };
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): boolean {
    return this.isConnected && this.socket?.connected === true;
  }
}

// Export singleton instance
const rahaWebSocketService = new RAHAWebSocketService();
export default rahaWebSocketService;
