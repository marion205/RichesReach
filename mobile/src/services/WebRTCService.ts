// Minimal interface for future WebRTC integration (signaling to be added server-side)
export interface RTCConfig {
  iceServers: { urls: string }[];
}

export interface SignalingClient {
  send(event: string, payload: any): void;
  on(event: string, handler: (payload: any) => void): void;
}

export class WebRTCServiceStub {
  constructor(private signaling?: SignalingClient, private config?: RTCConfig) {}
  async joinRoom(_roomId: string) {
    // no-op stub for now
  }
  async leaveRoom() {}
}

import io, { Socket } from 'socket.io-client';
import { isExpoGo } from '../utils/expoGoCheck';
import logger from '../utils/logger';

// Conditionally import WebRTC (not available in Expo Go)
let RTCPeerConnection: any = null;
let RTCView: any = null;
let MediaStream: any = null;
let mediaDevices: any = null;

try {
  if (!isExpoGo()) {
    const webrtc = require('react-native-webrtc');
    RTCPeerConnection = webrtc.RTCPeerConnection;
    RTCView = webrtc.RTCView;
    MediaStream = webrtc.MediaStream;
    mediaDevices = webrtc.mediaDevices;
  }
} catch (e) {
  logger.warn('react-native-webrtc not available (Expo Go mode)');
}

export interface WebRTCConfig {
  serverUrl: string;
  stunServers: string[];
  turnServers?: RTCIceServer[];
}

export interface RoomInfo {
  roomId: string;
  viewerCount: number;
  isHost: boolean;
}

export interface UserInfo {
  userId: string;
  userName: string;
}

export interface Message {
  id: string;
  roomId: string;
  userId: string;
  userName: string;
  content: string;
  type: string;
  timestamp: Date;
}

export class WebRTCService {
  private socket: Socket | null = null;
  private peerConnection: any = null; // RTCPeerConnection | null
  private localStream: any = null; // MediaStream | null
  private remoteStreams: Map<string, any> = new Map(); // Map<string, MediaStream>
  private config: WebRTCConfig;
  private currentRoom: string | null = null;
  private userId: string | null = null;
  private isHost: boolean = false;
  private isAvailable: boolean;

  constructor(config: WebRTCConfig) {
    this.config = config;
    this.isAvailable = RTCPeerConnection !== null && !isExpoGo();
  }

  // Check if WebRTC is available
  static isAvailable(): boolean {
    return RTCPeerConnection !== null && !isExpoGo();
  }

  // Event callbacks
  private onRoomJoined?: (roomInfo: RoomInfo) => void;
  private onUserJoined?: (userInfo: UserInfo, viewerCount: number) => void;
  private onUserLeft?: (userId: string, viewerCount: number) => void;
  private onNewMessage?: (message: Message) => void;
  private onChatHistory?: (messages: Message[]) => void;
  private onRemoteStream?: (userId: string, stream: MediaStream) => void;
  private onError?: (error: string) => void;

  // Initialize the service
  async initialize(): Promise<void> {
    if (!this.isAvailable) {
      logger.warn('⚠️ WebRTC not available in Expo Go. Service will use fallback mode.');
      return;
    }

    try {
      // Initialize socket connection
      this.socket = io(this.config.serverUrl, {
        transports: ['websocket'],
        timeout: 20000,
      });

      this.setupSocketListeners();
      logger.log('✅ WebRTC Service initialized');
    } catch (error) {
      logger.error('❌ Failed to initialize WebRTC Service:', error);
      throw error;
    }
  }

  // Set event callbacks
  setCallbacks(callbacks: {
    onRoomJoined?: (roomInfo: RoomInfo) => void;
    onUserJoined?: (userInfo: UserInfo, viewerCount: number) => void;
    onUserLeft?: (userId: string, viewerCount: number) => void;
    onNewMessage?: (message: Message) => void;
    onChatHistory?: (messages: Message[]) => void;
    onRemoteStream?: (userId: string, stream: MediaStream) => void;
    onError?: (error: string) => void;
  }) {
    this.onRoomJoined = callbacks.onRoomJoined;
    this.onUserJoined = callbacks.onUserJoined;
    this.onUserLeft = callbacks.onUserLeft;
    this.onNewMessage = callbacks.onNewMessage;
    this.onChatHistory = callbacks.onChatHistory;
    this.onRemoteStream = callbacks.onRemoteStream;
    this.onError = callbacks.onError;
  }

  // Setup socket event listeners
  private setupSocketListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      logger.log('🔌 Connected to streaming server');
    });

    this.socket.on('disconnect', () => {
      logger.log('🔌 Disconnected from streaming server');
    });

    this.socket.on('room-joined', (data: RoomInfo) => {
      logger.log('📺 Joined room:', data);
      this.onRoomJoined?.(data);
    });

    this.socket.on('user-joined', (data: { userId: string; userName: string; viewerCount: number }) => {
      logger.log('👤 User joined:', data);
      this.onUserJoined?.({ userId: data.userId, userName: data.userName }, data.viewerCount);
    });

    this.socket.on('user-left', (data: { userId: string; viewerCount: number }) => {
      logger.log('👋 User left:', data);
      this.onUserLeft?.(data.userId, data.viewerCount);
    });

    this.socket.on('new-message', (message: Message) => {
      logger.log('💬 New message:', message);
      this.onNewMessage?.(message);
    });

    this.socket.on('chat-history', (messages: Message[]) => {
      logger.log('📜 Chat history loaded:', messages.length, 'messages');
      this.onChatHistory?.(messages);
    });

    this.socket.on('transport-created', async (data: any) => {
      logger.log('🚚 Transport created:', data);
      await this.handleTransportCreated(data);
    });

    this.socket.on('new-producer', async (data: { producerId: string; userId: string }) => {
      logger.log('📹 New producer:', data);
      await this.handleNewProducer(data);
    });

    this.socket.on('error', (error: { message: string }) => {
      logger.error('❌ Socket error:', error.message);
      this.onError?.(error.message);
    });
  }

  // Join a room
  async joinRoom(roomId: string, userId: string, userName: string, isHost: boolean = false): Promise<void> {
    if (!this.socket) {
      throw new Error('WebRTC Service not initialized');
    }

    this.currentRoom = roomId;
    this.userId = userId;
    this.isHost = isHost;

    // Join room via socket
    this.socket.emit('join-room', {
      roomId,
      userId,
      userName,
      isHost
    });

    // Initialize peer connection
    await this.initializePeerConnection();

    // Get user media if host
    if (isHost) {
      await this.startLocalStream();
    }
  }

  // Initialize peer connection
  private async initializePeerConnection(): Promise<void> {
    if (!RTCPeerConnection) {
      logger.warn('⚠️ RTCPeerConnection not available (Expo Go)');
      return;
    }

    const iceServers: RTCIceServer[] = this.config.stunServers.map(stun => ({ urls: stun }));
    if (this.config.turnServers) {
      iceServers.push(...this.config.turnServers);
    }

    this.peerConnection = new RTCPeerConnection({
      iceServers,
      iceCandidatePoolSize: 10,
    });

    // Handle remote streams
    this.peerConnection.ontrack = (event) => {
      logger.log('📺 Remote stream received');
      const [remoteStream] = event.streams;
      if (remoteStream && this.userId) {
        this.remoteStreams.set(this.userId, remoteStream);
        this.onRemoteStream?.(this.userId, remoteStream);
      }
    };

    // Handle ICE candidates
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate && this.socket) {
        this.socket.emit('ice-candidate', {
          roomId: this.currentRoom,
          candidate: event.candidate
        });
      }
    };
  }

  // Start local media stream
  private async startLocalStream(): Promise<void> {
    if (!mediaDevices) {
      logger.warn('⚠️ mediaDevices not available (Expo Go)');
      return;
    }

    try {
      const stream = await mediaDevices.getUserMedia({
        video: {
          width: { min: 640, ideal: 1280, max: 1920 },
          height: { min: 480, ideal: 720, max: 1080 },
          frameRate: { min: 15, ideal: 30, max: 30 },
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.localStream = stream;

      // Add tracks to peer connection
      stream.getTracks().forEach(track => {
        this.peerConnection?.addTrack(track, stream);
      });

      logger.log('📹 Local stream started');
    } catch (error) {
      logger.error('❌ Failed to start local stream:', error);
      throw error;
    }
  }

  // Handle transport creation
  private async handleTransportCreated(data: any): Promise<void> {
    if (!this.socket || !this.currentRoom || !this.userId) return;

    // Connect transport
    this.socket.emit('connect-transport', {
      roomId: this.currentRoom,
      userId: this.userId,
      transportId: data.id,
      dtlsParameters: data.dtlsParameters
    });

    // If host, produce media
    if (this.isHost && this.localStream) {
      const videoTrack = this.localStream.getVideoTracks()[0];
      const audioTrack = this.localStream.getAudioTracks()[0];

      if (videoTrack) {
        this.socket.emit('produce', {
          roomId: this.currentRoom,
          userId: this.userId,
          kind: 'video',
          rtpParameters: videoTrack.getSettings()
        });
      }

      if (audioTrack) {
        this.socket.emit('produce', {
          roomId: this.currentRoom,
          userId: this.userId,
          kind: 'audio',
          rtpParameters: audioTrack.getSettings()
        });
      }
    }
  }

  // Handle new producer
  private async handleNewProducer(data: { producerId: string; userId: string }): Promise<void> {
    if (!this.socket || !this.currentRoom || !this.userId || this.isHost) return;

    // Request to consume the producer
    this.socket.emit('consume', {
      roomId: this.currentRoom,
      userId: this.userId,
      producerId: data.producerId,
      rtpCapabilities: this.peerConnection?.getCapabilities()
    });
  }

  // Send chat message
  sendMessage(content: string, type: string = 'text'): void {
    if (!this.socket || !this.currentRoom || !this.userId) return;

    this.socket.emit('send-message', {
      roomId: this.currentRoom,
      userId: this.userId,
      userName: 'User', // Future enhancement: Get from user context/auth service
      content,
      type
    });
  }

  // Leave room
  async leaveRoom(): Promise<void> {
    if (!this.socket || !this.currentRoom || !this.userId) return;

    // Stop local stream
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }

    // Close peer connection
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    // Leave room via socket
    this.socket.emit('leave-room', {
      roomId: this.currentRoom,
      userId: this.userId
    });

    // Clear state
    this.currentRoom = null;
    this.userId = null;
    this.isHost = false;
    this.remoteStreams.clear();

    logger.log('👋 Left room');
  }

  // Get local stream
  getLocalStream(): MediaStream | null {
    return this.localStream;
  }

  // Get remote streams
  getRemoteStreams(): Map<string, MediaStream> {
    return this.remoteStreams;
  }

  // Check if connected
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Check if in room
  isInRoom(): boolean {
    return this.currentRoom !== null;
  }

  // Check if host
  isHostUser(): boolean {
    return this.isHost;
  }

  // Disconnect
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }

    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    this.remoteStreams.clear();
    this.currentRoom = null;
    this.userId = null;
    this.isHost = false;

    logger.log('🔌 WebRTC Service disconnected');
  }
}
