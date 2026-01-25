/**
 * WebSocket service for real-time Family Sharing orb synchronization
 * Optimized for performance and fast connection
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { WS_URL } from '../../../config/api';
import logger from '../../../utils/logger';

// Build WebSocket URL for family orb sync
const getFamilyWSUrl = (): string => {
  // WS_URL already includes /ws/ at the end (e.g., ws://192.168.1.240:8000/ws/)
  // We need to replace it with our specific path
  const baseUrl = WS_URL || (__DEV__ ? 'ws://localhost:8000/ws/' : 'wss://api.richesreach.com/ws/');
  // Remove trailing /ws/ and add our specific path
  const cleanBase = baseUrl.replace(/\/ws\/?$/, ''); // Remove /ws or /ws/
  return `${cleanBase}/ws/family/orb-sync/`;
};

export interface OrbSyncMessage {
  type: 'sync_orb' | 'gesture' | 'ping';
  netWorth?: number;
  gesture?: string;
  viewMode?: string;
}

export interface OrbSyncEvent {
  type: 'orb_sync' | 'gesture' | 'initial_state';
  netWorth?: number;
  userId?: string;
  userName?: string;
  gesture?: string;
  viewMode?: string;
  lastSynced?: string;
  enabled?: boolean;
}

type EventCallback = (event: OrbSyncEvent) => void;

export class FamilyWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private eventCallbacks: Set<EventCallback> = new Set();
  private isConnecting = false;
  private isConnected = false;
  private token: string | null = null;

  /**
   * Connect to WebSocket with authentication
   */
  async connect(familyGroupId: string): Promise<void> {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    try {
      this.isConnecting = true;
      
      // Get auth token
      this.token = await AsyncStorage.getItem('token') || 
                   await AsyncStorage.getItem('authToken');
      
      if (!this.token) {
        logger.warn('[FamilyWS] No auth token found');
        return;
      }

      // Build WebSocket URL with token
      const wsUrl = getFamilyWSUrl();
      const url = `${wsUrl}?token=${encodeURIComponent(this.token)}&familyGroupId=${familyGroupId}`;
      
      this.ws = new WebSocket(url);
      
      this.setupEventHandlers();
      
    } catch (error) {
      logger.error('[FamilyWS] Connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect(familyGroupId);
    }
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      logger.log('[FamilyWS] Connected');
      this.isConnected = true;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      
      // Start ping interval (keep connection alive)
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      try {
        const data: OrbSyncEvent = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        logger.error('[FamilyWS] Failed to parse message:', error);
      }
    };

    this.ws.onerror = (error) => {
      // Only log errors in dev, and make them warnings (404s are expected if backend isn't deployed)
      if (__DEV__) {
        logger.warn('[FamilyWS] WebSocket error (expected if backend not deployed):', error);
      }
      this.isConnected = false;
    };

    this.ws.onclose = (event) => {
      // 1006 = abnormal closure (often 404 from server)
      // Only log in dev, and make it a warning
      if (__DEV__) {
        if (event.code === 1006) {
          logger.warn('[FamilyWS] Disconnected: Backend WebSocket endpoint not available (404). This is expected if the backend is not running.');
        } else {
          logger.log('[FamilyWS] Disconnected:', event.code, event.reason);
        }
      }
      this.isConnected = false;
      this.stopPingInterval();
      
      // Auto-reconnect if not intentional close and not 404
      if (event.code !== 1000 && event.code !== 1006) {
        // Will reconnect via scheduleReconnect if needed
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: OrbSyncEvent): void {
    // Notify all callbacks
    this.eventCallbacks.forEach(callback => {
      try {
        callback(event);
      } catch (error) {
        logger.error('[FamilyWS] Callback error:', error);
      }
    });
  }

  /**
   * Send message to WebSocket
   */
  send(message: OrbSyncMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      logger.warn('[FamilyWS] Cannot send, not connected');
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      logger.error('[FamilyWS] Send error:', error);
    }
  }

  /**
   * Sync orb state
   */
  syncOrbState(netWorth: number, viewMode?: string): void {
    this.send({
      type: 'sync_orb',
      netWorth,
      viewMode,
    });
  }

  /**
   * Send gesture event
   */
  sendGesture(gesture: string): void {
    this.send({
      type: 'gesture',
      gesture,
    });
  }

  /**
   * Subscribe to events
   */
  onEvent(callback: EventCallback): () => void {
    this.eventCallbacks.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.eventCallbacks.delete(callback);
    };
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    this.stopPingInterval();
    
    if (this.ws) {
      this.ws.close(1000, 'Intentional disconnect');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.eventCallbacks.clear();
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(familyGroupId: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      logger.warn('[FamilyWS] Max reconnection attempts reached');
      return;
    }

    if (this.reconnectTimer) {
      return; // Already scheduled
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect(familyGroupId);
    }, delay);
  }

  /**
   * Start ping interval to keep connection alive
   */
  private startPingInterval(): void {
    this.stopPingInterval();
    
    this.pingInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Get connection status
   */
  get isReady(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
let instance: FamilyWebSocketService | null = null;

export const getFamilyWebSocketService = (): FamilyWebSocketService => {
  if (!instance) {
    instance = new FamilyWebSocketService();
  }
  return instance;
};

