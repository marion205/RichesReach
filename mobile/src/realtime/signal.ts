import { io, Socket } from 'socket.io-client';
import { ENV } from '../config/env';
import { refreshJwt } from '../auth/token';
import logger from '../utils/logger';

export function connectSignal(getJwt: () => Promise<string> | string): Socket {
  const socket: Socket = io(ENV.SIGNAL_URL, {
    transports: ['websocket'],
    path: '/socket.io',
    autoConnect: false,
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 500,
    reconnectionDelayMax: 5000,
    timeout: 10000,
  });

  socket.on('connect_error', (err: unknown) => {
    const errorMessage = err instanceof Error ? err.message : String(err);
    logger.warn('[Signal] connect_error', errorMessage);
  });

  socket.on('connect_error', async (err: unknown) => {
    const errorMessage = err instanceof Error ? err.message : String(err);
    const msg = errorMessage;
    if (msg.includes('401')) {
      try {
        await refreshJwt();
        socket.disconnect();
        socket.connect();
      } catch (e) {
        const refreshError = e instanceof Error ? e.message : String(e);
        logger.warn('[Signal] refresh failed', refreshError);
      }
    }
  });

  (async () => {
    const token = await getJwt();
    // @ts-expect-error: socket.auth is a custom property for socket.io authentication
    socket.auth = { token };
    // @ts-expect-error: socket.io.opts.extraHeaders is a valid socket.io option but not in types
    socket.io.opts.extraHeaders = { Authorization: `Bearer ${token}` };
    socket.connect();
  })();

  return socket;
}


