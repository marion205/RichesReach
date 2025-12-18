import { io, Socket } from 'socket.io-client';
import { ENV } from '../config/env';
import { refreshJwt } from '../auth/token';
import logger from '../utils/logger';

export function connectSignal(getJwt: () => Promise<string> | string): Socket {
  // Parse the SIGNAL_URL - it might be ws://host:port/path, but socket.io needs http://host:port
  let signalUrl = ENV.SIGNAL_URL;
  
  // If URL contains a path (like /fireside), extract just the base URL
  try {
    const url = new URL(signalUrl);
    // Convert ws:// to http:// (socket.io-client handles WebSocket upgrade internally)
    const protocol = url.protocol === 'ws:' ? 'http:' : url.protocol === 'wss:' ? 'https:' : url.protocol;
    // Remove path and keep just protocol + host + port
    signalUrl = `${protocol}//${url.host}`;
    logger.log(`[Signal] Parsed WebSocket URL: ${signalUrl} (original: ${ENV.SIGNAL_URL})`);
  } catch (e) {
    // If URL parsing fails, try to clean it up manually
    signalUrl = signalUrl.replace(/\/fireside.*$/, '').replace(/\/$/, '');
    // Convert ws:// to http://
    signalUrl = signalUrl.replace(/^ws:\/\//, 'http://').replace(/^wss:\/\//, 'https://');
    logger.warn(`[Signal] Failed to parse URL, using cleaned version: ${signalUrl}`);
  }
  
  logger.log(`[Signal] Connecting socket.io to ${signalUrl}`);
  logger.log(`[Signal] Original SIGNAL_URL: ${ENV.SIGNAL_URL}`);
  logger.log(`[Signal] Using path: /socket.io`);
  logger.log(`[Signal] Forcing websocket transport for Expo compatibility`);

  const socket: Socket = io(signalUrl, {
    path: '/socket.io',         // must match socketio_path on server
    transports: ['websocket'],  // Force websocket only (avoids polling issues in Expo)
    forceNew: true,             // Helps with reconnects
    timeout: 10000,
    autoConnect: false,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
  });

  // Connection event handlers with detailed logging
  socket.on('connect', () => {
    logger.log(`✅ [Fireside] Socket connected! ID: ${socket.id}`);
    console.log(`✅ [Fireside] Socket connected! ID: ${socket.id}`);
  });

  socket.on('connect_error', (err: any) => {
    const errorDetails = {
      message: err?.message,
      description: err?.description,
      data: err?.data,
      type: err?.type,
      code: err?.code,
    };
    logger.warn('❌ [Fireside] connect_error', errorDetails);
    console.error('❌ [Fireside] Connection error:', err?.message || String(err));
    
    // Handle 401 auth errors
    const errorMessage = err?.message || String(err);
    if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
      (async () => {
        try {
          await refreshJwt();
          const token = await getJwt();
          // @ts-expect-error: socket.auth is a custom property for socket.io authentication
          socket.auth = { token };
          // @ts-expect-error: socket.io.opts.extraHeaders is a valid socket.io option but not in types
          socket.io.opts.extraHeaders = { Authorization: `Bearer ${token}` };
          socket.disconnect();
          socket.connect();
        } catch (e) {
          const refreshError = e instanceof Error ? e.message : String(e);
          logger.warn('[Signal] refresh failed', refreshError);
        }
      })();
    }
  });

  socket.on('error', (err: any) => {
    logger.warn('❌ [Fireside] error', err);
  });

  socket.on('disconnect', (reason: string) => {
    logger.log(`👋 [Fireside] Socket disconnected: ${reason}`);
    console.log(`👋 [Fireside] Disconnected: ${reason}`);
  });

  // Additional debugging events
  socket.on('reconnect', (attemptNumber: number) => {
    logger.log(`🔄 [Fireside] Reconnected after ${attemptNumber} attempts`);
    console.log(`🔄 [Fireside] Reconnected after ${attemptNumber} attempts`);
  });

  socket.on('reconnect_attempt', (attemptNumber: number) => {
    logger.log(`🔄 [Fireside] Reconnection attempt ${attemptNumber}`);
  });

  socket.on('reconnect_error', (error: any) => {
    logger.warn(`❌ [Fireside] Reconnection error:`, error);
    console.error(`❌ [Fireside] Reconnection error:`, error?.message || String(error));
  });

  socket.on('reconnect_failed', () => {
    logger.error(`❌ [Fireside] Reconnection failed after all attempts`);
    console.error(`❌ [Fireside] Reconnection failed after all attempts`);
  });

  // Connect with auth token
  (async () => {
    try {
      const token = await getJwt();
      // @ts-expect-error: socket.auth is a custom property for socket.io authentication
      socket.auth = { token };
      // @ts-expect-error: socket.io.opts.extraHeaders is a valid socket.io option but not in types
      socket.io.opts.extraHeaders = { Authorization: `Bearer ${token}` };
      socket.connect();
    } catch (e) {
      const error = e instanceof Error ? e.message : String(e);
      logger.warn('[Signal] Failed to get token, connecting without auth', error);
      socket.connect();
    }
  })();

  return socket;
}


