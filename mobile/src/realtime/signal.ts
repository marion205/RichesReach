import { io, Socket } from 'socket.io-client';
import { ENV } from '../config/env';
import { refreshJwt } from '../auth/token';

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

  socket.on('connect_error', (err) => {
    console.warn('[Signal] connect_error', (err as any)?.message || err);
  });

  socket.on('connect_error', async (err: any) => {
    const msg = String(err?.message || '');
    if (msg.includes('401')) {
      try {
        await refreshJwt();
        socket.disconnect();
        socket.connect();
      } catch (e) {
        console.warn('[Signal] refresh failed', e);
      }
    }
  });

  (async () => {
    const token = await getJwt();
    // @ts-ignore
    socket.auth = { token };
    // @ts-ignore
    socket.io.opts.extraHeaders = { Authorization: `Bearer ${token}` };
    socket.connect();
  })();

  return socket;
}


