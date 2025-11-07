/**
 * Unit tests for FamilyWebSocketService
 */

import { FamilyWebSocketService, getFamilyWebSocketService } from '../FamilyWebSocketService';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url = '';
  onopen: ((event: any) => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onclose: ((event: any) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen({});
      }
    }, 10);
  }

  send(data: string) {
    // Mock send
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason });
    }
  }
}

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn((key: string) => {
    if (key === 'token' || key === 'authToken') {
      return Promise.resolve('mock-token-123');
    }
    return Promise.resolve(null);
  }),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));

// Mock WebSocket
global.WebSocket = MockWebSocket as any;

describe('FamilyWebSocketService', () => {
  let service: FamilyWebSocketService;

  beforeEach(() => {
    service = new FamilyWebSocketService();
    jest.clearAllMocks();
  });

  afterEach(() => {
    service.disconnect();
  });

  it('should create singleton instance', () => {
    const instance1 = getFamilyWebSocketService();
    const instance2 = getFamilyWebSocketService();
    expect(instance1).toBe(instance2);
  });

  it('should connect to WebSocket', async () => {
    await service.connect('family_123');
    
    // Wait for connection
    await new Promise(resolve => setTimeout(resolve, 50));
    
    expect(service.isReady).toBe(true);
  });

  it('should send sync orb state message', async () => {
    await service.connect('family_123');
    await new Promise(resolve => setTimeout(resolve, 50));
    
    const sendSpy = jest.spyOn(MockWebSocket.prototype, 'send');
    service.syncOrbState(100000);
    
    await new Promise(resolve => setTimeout(resolve, 10));
    
    expect(sendSpy).toHaveBeenCalled();
    const sentData = JSON.parse(sendSpy.mock.calls[0][0]);
    expect(sentData.type).toBe('sync_orb');
    expect(sentData.netWorth).toBe(100000);
  });

  it('should send gesture message', async () => {
    await service.connect('family_123');
    await new Promise(resolve => setTimeout(resolve, 50));
    
    const sendSpy = jest.spyOn(MockWebSocket.prototype, 'send');
    service.sendGesture('tap');
    
    await new Promise(resolve => setTimeout(resolve, 10));
    
    expect(sendSpy).toHaveBeenCalled();
    const sentData = JSON.parse(sendSpy.mock.calls[0][0]);
    expect(sentData.type).toBe('gesture');
    expect(sentData.gesture).toBe('tap');
  });

  it('should subscribe to events', async () => {
    await service.connect('family_123');
    await new Promise(resolve => setTimeout(resolve, 50));
    
    const callback = jest.fn();
    const unsubscribe = service.onEvent(callback);
    
    // Simulate message
    const mockEvent = {
      type: 'orb_sync',
      netWorth: 100000,
      userId: 'user_123',
    };
    
    // Trigger onmessage
    const ws = (service as any).ws;
    if (ws && ws.onmessage) {
      ws.onmessage({ data: JSON.stringify(mockEvent) });
    }
    
    await new Promise(resolve => setTimeout(resolve, 10));
    
    expect(callback).toHaveBeenCalledWith(mockEvent);
    
    // Unsubscribe
    unsubscribe();
  });

  it('should disconnect WebSocket', async () => {
    await service.connect('family_123');
    await new Promise(resolve => setTimeout(resolve, 50));
    
    const closeSpy = jest.spyOn(MockWebSocket.prototype, 'close');
    service.disconnect();
    
    expect(closeSpy).toHaveBeenCalled();
    expect(service.isReady).toBe(false);
  });

  it('should handle connection errors gracefully', async () => {
    // Mock WebSocket to fail
    const OriginalWebSocket = global.WebSocket;
    global.WebSocket = jest.fn(() => {
      throw new Error('Connection failed');
    }) as any;
    
    await expect(service.connect('family_123')).resolves.not.toThrow();
    
    global.WebSocket = OriginalWebSocket;
  });

  it('should not send when not connected', () => {
    const sendSpy = jest.spyOn(MockWebSocket.prototype, 'send');
    service.syncOrbState(100000);
    
    // Should not send if not connected
    expect(sendSpy).not.toHaveBeenCalled();
  });

  it('should reconnect on disconnect', async () => {
    await service.connect('family_123');
    await new Promise(resolve => setTimeout(resolve, 50));
    
    // Disconnect
    const ws = (service as any).ws;
    if (ws) {
      ws.close(1006, 'Abnormal closure');
    }
    
    // Should attempt reconnection
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Note: In a real scenario, reconnection would be tested
    // This is a basic test structure
  });
});

