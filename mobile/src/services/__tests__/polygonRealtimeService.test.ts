/**
 * Tests for Polygon Realtime Service
 */
import { initPolygonStream, closePolygonStream, usePolygonUpdates } from '../polygonRealtimeService';
import { GET_TRADING_QUOTE } from '../../graphql/tradingQueries';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: any) => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onclose: ((event: any) => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen({} as any);
      }
    }, 10);
  }

  send(data: string) {
    // Handle auth
    const message = JSON.parse(data);
    if (message.action === 'auth') {
      setTimeout(() => {
        if (this.onmessage) {
          this.onmessage({
            data: JSON.stringify({ ev: 'status', status: 'auth_success' }),
          } as any);
        }
      }, 10);
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({} as any);
    }
  }
}

// Mock Apollo Client
const mockApolloClient = {
  writeQuery: jest.fn(),
  readQuery: jest.fn(),
};

// Mock environment variable
const originalEnv = process.env.EXPO_PUBLIC_POLYGON_API_KEY;
beforeAll(() => {
  process.env.EXPO_PUBLIC_POLYGON_API_KEY = 'test_key';
  (global as any).WebSocket = MockWebSocket;
});

afterAll(() => {
  process.env.EXPO_PUBLIC_POLYGON_API_KEY = originalEnv;
  delete (global as any).WebSocket;
});

// Mock console
const consoleLog = jest.spyOn(console, 'log').mockImplementation();
const consoleWarn = jest.spyOn(console, 'warn').mockImplementation();
const consoleError = jest.spyOn(console, 'error').mockImplementation();

describe('polygonRealtimeService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    closePolygonStream();
  });

  describe('initPolygonStream', () => {
    it('should initialize WebSocket connection', (done) => {
      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        expect(consoleLog).toHaveBeenCalledWith(
          expect.stringContaining('Polygon WebSocket connected')
        );
        done();
      }, 50);
    });

    it('should authenticate with API key', (done) => {
      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        expect(consoleLog).toHaveBeenCalledWith(
          expect.stringContaining('authenticated successfully')
        );
        done();
      }, 100);
    });

    it('should subscribe to symbols after authentication', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      let sentMessages: string[] = [];

      const originalSend = ws.send.bind(ws);
      ws.send = (data: string) => {
        sentMessages.push(data);
        originalSend(data);
      };

      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL', 'MSFT']);

      setTimeout(() => {
        // Should have auth message and subscribe message
        expect(sentMessages.length).toBeGreaterThan(0);
        done();
      }, 150);
    });

    it('should not initialize if API key is missing', () => {
      const originalKey = process.env.EXPO_PUBLIC_POLYGON_API_KEY;
      delete process.env.EXPO_PUBLIC_POLYGON_API_KEY;

      initPolygonStream(mockApolloClient, ['AAPL']);

      expect(consoleWarn).toHaveBeenCalledWith(
        expect.stringContaining('Polygon API key not found')
      );

      process.env.EXPO_PUBLIC_POLYGON_API_KEY = originalKey;
    });

    it('should update subscriptions if already connected', (done) => {
      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        // Second call should update subscriptions, not create new connection
        initPolygonStream(mockApolloClient, ['AAPL', 'MSFT']);

        setTimeout(() => {
          // Should not create multiple connections
          expect(consoleLog).toHaveBeenCalled();
          done();
        }, 50);
      }, 100);
    });
  });

  describe('message handling', () => {
    it('should handle trade events and update Apollo cache', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        // Simulate trade event
        const tradeEvent = {
          ev: 'T',
          sym: 'T.AAPL',
          p: 180.50,
          t: Date.now(),
        };

        if (ws.onmessage) {
          ws.onmessage({
            data: JSON.stringify(tradeEvent),
          } as any);
        }

        setTimeout(() => {
          expect(mockApolloClient.writeQuery).toHaveBeenCalledWith({
            query: GET_TRADING_QUOTE,
            variables: { symbol: 'AAPL' },
            data: expect.objectContaining({
              tradingQuote: expect.objectContaining({
                symbol: 'AAPL',
                bid: expect.any(Number),
                ask: expect.any(Number),
              }),
            }),
          });
          done();
        }, 50);
      }, 100);
    });

    it('should handle quote events and update Apollo cache', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        // Simulate quote event
        const quoteEvent = {
          ev: 'Q',
          sym: 'Q.AAPL',
          bp: 180.45,
          ap: 180.55,
          t: Date.now(),
        };

        if (ws.onmessage) {
          ws.onmessage({
            data: JSON.stringify(quoteEvent),
          } as any);
        }

        setTimeout(() => {
          expect(mockApolloClient.writeQuery).toHaveBeenCalledWith({
            query: GET_TRADING_QUOTE,
            variables: { symbol: 'AAPL' },
            data: expect.objectContaining({
              tradingQuote: expect.objectContaining({
                symbol: 'AAPL',
                bid: 180.45,
                ask: 180.55,
              }),
            }),
          });
          done();
        }, 50);
      }, 100);
    });

    it('should handle status messages', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        if (ws.onmessage) {
          ws.onmessage({
            data: JSON.stringify({ ev: 'status', status: 'connected' }),
          } as any);
        }

        setTimeout(() => {
          expect(consoleLog).toHaveBeenCalled();
          done();
        }, 50);
      }, 100);
    });

    it('should handle auth failure', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        if (ws.onmessage) {
          ws.onmessage({
            data: JSON.stringify({ ev: 'status', status: 'auth_failed' }),
          } as any);
        }

        setTimeout(() => {
          expect(consoleError).toHaveBeenCalledWith(
            expect.stringContaining('auth failed')
          );
          done();
        }, 50);
      }, 100);
    });
  });

  describe('closePolygonStream', () => {
    it('should close WebSocket connection', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      const closeSpy = jest.spyOn(ws, 'close');
      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        closePolygonStream();
        expect(closeSpy).toHaveBeenCalled();
        done();
      }, 100);
    });
  });

  describe('reconnection logic', () => {
    it('should attempt reconnection on close', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL']);

      setTimeout(() => {
        ws.close();

        setTimeout(() => {
          expect(consoleLog).toHaveBeenCalledWith(
            expect.stringContaining('reconnecting')
          );
          done();
        }, 50);
      }, 100);
    });
  });

  describe('subscription management', () => {
    it('should unsubscribe from removed symbols', (done) => {
      const ws = new MockWebSocket('wss://socket.polygon.io/stocks');
      let sentMessages: string[] = [];

      const originalSend = ws.send.bind(ws);
      ws.send = (data: string) => {
        sentMessages.push(data);
        originalSend(data);
      };

      (global as any).WebSocket = jest.fn(() => ws);

      initPolygonStream(mockApolloClient, ['AAPL', 'MSFT']);

      setTimeout(() => {
        // Update to only AAPL
        initPolygonStream(mockApolloClient, ['AAPL']);

        setTimeout(() => {
          const unsubscribeMessages = sentMessages.filter(msg => {
            const parsed = JSON.parse(msg);
            return parsed.action === 'unsubscribe';
          });
          expect(unsubscribeMessages.length).toBeGreaterThan(0);
          done();
        }, 100);
      }, 150);
    });
  });
});

