import io, { Socket } from 'socket.io-client';
import { GiftedChat, IMessage } from 'react-native-gifted-chat';

export interface ChatConfig {
  serverUrl: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export interface ChatMessage extends IMessage {
  id: string;
  roomId: string;
  userId: string;
  userName: string;
  content: string;
  type: 'text' | 'image' | 'video' | 'system';
  timestamp: Date;
}

export interface UserInfo {
  userId: string;
  userName: string;
  avatar?: string;
}

export class SocketChatService {
  private socket: Socket | null = null;
  private config: ChatConfig;
  private currentRoom: string | null = null;
  private currentUser: UserInfo | null = null;
  private isConnected: boolean = false;

  // Event callbacks
  private onConnected?: () => void;
  private onDisconnected?: () => void;
  private onNewMessage?: (message: ChatMessage) => void;
  private onMessageHistory?: (messages: ChatMessage[]) => void;
  private onUserJoined?: (user: UserInfo) => void;
  private onUserLeft?: (userId: string) => void;
  private onTypingStart?: (user: UserInfo) => void;
  private onTypingStop?: (userId: string) => void;
  private onError?: (error: string) => void;

  constructor(config: ChatConfig) {
    this.config = {
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      ...config
    };
  }

  // Initialize the service
  async initialize(): Promise<void> {
    try {
      this.socket = io(this.config.serverUrl, {
        transports: ['websocket'],
        timeout: 20000,
        reconnection: true,
        reconnectionAttempts: this.config.reconnectAttempts,
        reconnectionDelay: this.config.reconnectDelay,
      });

      this.setupSocketListeners();
      console.log('✅ Socket Chat Service initialized');
    } catch (error) {
      console.error('❌ Failed to initialize Socket Chat Service:', error);
      throw error;
    }
  }

  // Set event callbacks
  setCallbacks(callbacks: {
    onConnected?: () => void;
    onDisconnected?: () => void;
    onNewMessage?: (message: ChatMessage) => void;
    onMessageHistory?: (messages: ChatMessage[]) => void;
    onUserJoined?: (user: UserInfo) => void;
    onUserLeft?: (userId: string) => void;
    onTypingStart?: (user: UserInfo) => void;
    onTypingStop?: (userId: string) => void;
    onError?: (error: string) => void;
  }) {
    this.onConnected = callbacks.onConnected;
    this.onDisconnected = callbacks.onDisconnected;
    this.onNewMessage = callbacks.onNewMessage;
    this.onMessageHistory = callbacks.onMessageHistory;
    this.onUserJoined = callbacks.onUserJoined;
    this.onUserLeft = callbacks.onUserLeft;
    this.onTypingStart = callbacks.onTypingStart;
    this.onTypingStop = callbacks.onTypingStop;
    this.onError = callbacks.onError;
  }

  // Setup socket event listeners
  private setupSocketListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('🔌 Connected to chat server');
      this.isConnected = true;
      this.onConnected?.();
    });

    this.socket.on('disconnect', () => {
      console.log('🔌 Disconnected from chat server');
      this.isConnected = false;
      this.onDisconnected?.();
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ Connection error:', error);
      this.onError?.(error.message);
    });

    this.socket.on('new-message', (message: ChatMessage) => {
      console.log('💬 New message received:', message);
      this.onNewMessage?.(message);
    });

    this.socket.on('chat-history', (messages: ChatMessage[]) => {
      console.log('📜 Chat history loaded:', messages.length, 'messages');
      this.onMessageHistory?.(messages);
    });

    this.socket.on('user-joined', (user: UserInfo) => {
      console.log('👤 User joined chat:', user);
      this.onUserJoined?.(user);
    });

    this.socket.on('user-left', (userId: string) => {
      console.log('👋 User left chat:', userId);
      this.onUserLeft?.(userId);
    });

    this.socket.on('typing-start', (user: UserInfo) => {
      console.log('⌨️ User started typing:', user);
      this.onTypingStart?.(user);
    });

    this.socket.on('typing-stop', (userId: string) => {
      console.log('⌨️ User stopped typing:', userId);
      this.onTypingStop?.(userId);
    });

    this.socket.on('error', (error: { message: string }) => {
      console.error('❌ Socket error:', error.message);
      this.onError?.(error.message);
    });
  }

  // Join a chat room
  async joinRoom(roomId: string, user: UserInfo): Promise<void> {
    if (!this.socket) {
      throw new Error('Socket Chat Service not initialized');
    }

    this.currentRoom = roomId;
    this.currentUser = user;

    this.socket.emit('join-room', {
      roomId,
      userId: user.userId,
      userName: user.userName
    });

    console.log(`💬 Joined chat room: ${roomId}`);
  }

  // Send a text message
  sendMessage(content: string): void {
    if (!this.socket || !this.currentRoom || !this.currentUser) {
      throw new Error('Not connected to chat room');
    }

    const message: ChatMessage = {
      _id: Date.now().toString(),
      id: Date.now().toString(),
      roomId: this.currentRoom,
      userId: this.currentUser.userId,
      userName: this.currentUser.userName,
      content,
      type: 'text',
      timestamp: new Date(),
      text: content,
      user: {
        _id: this.currentUser.userId,
        name: this.currentUser.userName,
        avatar: this.currentUser.avatar
      },
      createdAt: new Date()
    };

    this.socket.emit('send-message', {
      roomId: this.currentRoom,
      userId: this.currentUser.userId,
      userName: this.currentUser.userName,
      content,
      type: 'text'
    });

    console.log('📤 Message sent:', content);
  }

  // Send a system message
  sendSystemMessage(content: string): void {
    if (!this.socket || !this.currentRoom) {
      throw new Error('Not connected to chat room');
    }

    this.socket.emit('send-message', {
      roomId: this.currentRoom,
      userId: 'system',
      userName: 'System',
      content,
      type: 'system'
    });

    console.log('📤 System message sent:', content);
  }

  // Start typing indicator
  startTyping(): void {
    if (!this.socket || !this.currentRoom || !this.currentUser) return;

    this.socket.emit('typing-start', {
      roomId: this.currentRoom,
      userId: this.currentUser.userId,
      userName: this.currentUser.userName
    });
  }

  // Stop typing indicator
  stopTyping(): void {
    if (!this.socket || !this.currentRoom || !this.currentUser) return;

    this.socket.emit('typing-stop', {
      roomId: this.currentRoom,
      userId: this.currentUser.userId
    });
  }

  // Convert server message to GiftedChat format
  static convertToGiftedChatMessage(serverMessage: ChatMessage): IMessage {
    return {
      _id: serverMessage.id,
      text: serverMessage.content,
      createdAt: serverMessage.timestamp,
      user: {
        _id: serverMessage.userId,
        name: serverMessage.userName,
        avatar: serverMessage.userName.charAt(0).toUpperCase()
      },
      system: serverMessage.type === 'system'
    };
  }

  // Convert GiftedChat message to server format
  static convertFromGiftedChatMessage(giftedMessage: IMessage, roomId: string, userId: string, userName: string): ChatMessage {
    return {
      _id: giftedMessage._id,
      id: giftedMessage._id,
      roomId,
      userId,
      userName,
      content: giftedMessage.text || '',
      type: 'text',
      timestamp: giftedMessage.createdAt || new Date(),
      text: giftedMessage.text || '',
      user: {
        _id: userId,
        name: userName
      },
      createdAt: giftedMessage.createdAt || new Date()
    };
  }

  // Leave chat room
  leaveRoom(): void {
    if (!this.socket || !this.currentRoom || !this.currentUser) return;

    this.socket.emit('leave-room', {
      roomId: this.currentRoom,
      userId: this.currentUser.userId
    });

    this.currentRoom = null;
    this.currentUser = null;

    console.log('👋 Left chat room');
  }

  // Check if connected
  isSocketConnected(): boolean {
    return this.isConnected && this.socket?.connected || false;
  }

  // Check if in room
  isInChatRoom(): boolean {
    return this.currentRoom !== null;
  }

  // Get current room
  getCurrentRoom(): string | null {
    return this.currentRoom;
  }

  // Get current user
  getCurrentUser(): UserInfo | null {
    return this.currentUser;
  }

  // Disconnect
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

    this.isConnected = false;
    this.currentRoom = null;
    this.currentUser = null;

    console.log('🔌 Socket Chat Service disconnected');
  }
}
