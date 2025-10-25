import WebRTCService from '../WebRTCService';
import { MediaStream, RTCPeerConnection, RTCSessionDescription } from 'react-native-webrtc';

// Mock react-native-webrtc
jest.mock('react-native-webrtc', () => ({
  MediaStream: {
    getUserMedia: jest.fn(),
  },
  RTCPeerConnection: jest.fn(),
  RTCSessionDescription: jest.fn(),
  RTCIceCandidate: jest.fn(),
}));

// Mock socket.io-client
jest.mock('socket.io-client', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    emit: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    disconnect: jest.fn(),
    connected: true,
  })),
}));

describe('WebRTCService', () => {
  let webRTCService: WebRTCService;
  let mockSocket: any;
  let mockPeerConnection: any;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock socket
    mockSocket = {
      emit: jest.fn(),
      on: jest.fn(),
      off: jest.fn(),
      disconnect: jest.fn(),
      connected: true,
    };
    
    // Mock peer connection
    mockPeerConnection = {
      createOffer: jest.fn(),
      createAnswer: jest.fn(),
      setLocalDescription: jest.fn(),
      setRemoteDescription: jest.fn(),
      addIceCandidate: jest.fn(),
      addTrack: jest.fn(),
      removeTrack: jest.fn(),
      close: jest.fn(),
      onicecandidate: null,
      ontrack: null,
      onconnectionstatechange: null,
      connectionState: 'new',
      iceConnectionState: 'new',
    };
    
    (RTCPeerConnection as jest.Mock).mockImplementation(() => mockPeerConnection);
    
    // Mock MediaStream
    (MediaStream.getUserMedia as jest.Mock).mockResolvedValue({
      getTracks: () => [
        { kind: 'video', enabled: true, stop: jest.fn() },
        { kind: 'audio', enabled: true, stop: jest.fn() },
      ],
    });
    
    webRTCService = new WebRTCService({
      serverUrl: 'http://localhost:3001',
      stunServers: ['stun:stun.l.google.com:19302'],
    });
  });

  describe('Initialization', () => {
    it('should initialize with correct configuration', () => {
      expect(webRTCService).toBeDefined();
      expect(RTCPeerConnection).toHaveBeenCalledWith({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });
    });

    it('should set up event handlers', () => {
      expect(mockPeerConnection.onicecandidate).toBeDefined();
      expect(mockPeerConnection.ontrack).toBeDefined();
      expect(mockPeerConnection.onconnectionstatechange).toBeDefined();
    });
  });

  describe('Stream Management', () => {
    it('should start stream successfully', async () => {
      const mockStream = {
        getTracks: () => [
          { kind: 'video', enabled: true, stop: jest.fn() },
          { kind: 'audio', enabled: true, stop: jest.fn() },
        ],
      };
      
      (MediaStream.getUserMedia as jest.Mock).mockResolvedValue(mockStream);
      
      await webRTCService.startStream();
      
      expect(MediaStream.getUserMedia).toHaveBeenCalledWith({
        video: true,
        audio: true,
      });
      expect(mockPeerConnection.addTrack).toHaveBeenCalledTimes(2);
    });

    it('should handle stream start errors', async () => {
      const error = new Error('Permission denied');
      (MediaStream.getUserMedia as jest.Mock).mockRejectedValue(error);
      
      await expect(webRTCService.startStream()).rejects.toThrow('Permission denied');
    });

    it('should stop stream successfully', async () => {
      const mockTracks = [
        { kind: 'video', enabled: true, stop: jest.fn() },
        { kind: 'audio', enabled: true, stop: jest.fn() },
      ];
      
      webRTCService['localStream'] = {
        getTracks: () => mockTracks,
      } as any;
      
      await webRTCService.stopStream();
      
      mockTracks.forEach(track => {
        expect(track.stop).toHaveBeenCalled();
      });
    });
  });

  describe('Room Management', () => {
    it('should join room successfully', async () => {
      const roomId = 'test-room';
      const userId = 'test-user';
      
      await webRTCService.joinRoom(roomId, userId);
      
      expect(mockSocket.emit).toHaveBeenCalledWith('join_room', {
        roomId,
        userId,
      });
    });

    it('should leave room successfully', async () => {
      const roomId = 'test-room';
      
      await webRTCService.leaveRoom(roomId);
      
      expect(mockSocket.emit).toHaveBeenCalledWith('leave_room', { roomId });
    });
  });

  describe('Call Management', () => {
    it('should start call successfully', async () => {
      const targetUserId = 'target-user';
      
      mockPeerConnection.createOffer.mockResolvedValue({
        type: 'offer',
        sdp: 'test-sdp',
      });
      
      await webRTCService.startCall(targetUserId);
      
      expect(mockPeerConnection.createOffer).toHaveBeenCalled();
      expect(mockPeerConnection.setLocalDescription).toHaveBeenCalled();
      expect(mockSocket.emit).toHaveBeenCalledWith('call_offer', {
        offer: { type: 'offer', sdp: 'test-sdp' },
        targetUserId,
      });
    });

    it('should answer call successfully', async () => {
      const offer = { type: 'offer', sdp: 'test-sdp' };
      const callerId = 'caller-user';
      
      mockPeerConnection.createAnswer.mockResolvedValue({
        type: 'answer',
        sdp: 'test-answer-sdp',
      });
      
      await webRTCService.answerCall(offer, callerId);
      
      expect(mockPeerConnection.setRemoteDescription).toHaveBeenCalledWith(offer);
      expect(mockPeerConnection.createAnswer).toHaveBeenCalled();
      expect(mockPeerConnection.setLocalDescription).toHaveBeenCalled();
      expect(mockSocket.emit).toHaveBeenCalledWith('call_answer', {
        answer: { type: 'answer', sdp: 'test-answer-sdp' },
        callerId,
      });
    });

    it('should end call successfully', async () => {
      await webRTCService.endCall();
      
      expect(mockPeerConnection.close).toHaveBeenCalled();
      expect(mockSocket.emit).toHaveBeenCalledWith('end_call');
    });
  });

  describe('ICE Candidate Handling', () => {
    it('should handle ICE candidate events', () => {
      const mockCandidate = {
        candidate: 'test-candidate',
        sdpMLineIndex: 0,
        sdpMid: '0',
      };
      
      // Trigger the ICE candidate event
      if (mockPeerConnection.onicecandidate) {
        mockPeerConnection.onicecandidate({ candidate: mockCandidate });
      }
      
      expect(mockSocket.emit).toHaveBeenCalledWith('ice_candidate', {
        candidate: mockCandidate,
      });
    });

    it('should handle ICE candidate with null candidate', () => {
      // Trigger the ICE candidate event with null candidate
      if (mockPeerConnection.onicecandidate) {
        mockPeerConnection.onicecandidate({ candidate: null });
      }
      
      // Should not emit when candidate is null
      expect(mockSocket.emit).not.toHaveBeenCalledWith('ice_candidate', expect.any(Object));
    });
  });

  describe('Remote Stream Handling', () => {
    it('should handle remote track events', () => {
      const mockStream = {
        getTracks: () => [
          { kind: 'video', enabled: true },
          { kind: 'audio', enabled: true },
        ],
      };
      
      const mockEvent = {
        streams: [mockStream],
      };
      
      // Trigger the track event
      if (mockPeerConnection.ontrack) {
        mockPeerConnection.ontrack(mockEvent);
      }
      
      // Should call the onRemoteStream callback if set
      expect(webRTCService['onRemoteStream']).toBeDefined();
    });
  });

  describe('Connection State Handling', () => {
    it('should handle connection state changes', () => {
      const mockCallbacks = {
        onConnectionStateChange: jest.fn(),
      };
      
      webRTCService.setCallbacks(mockCallbacks);
      
      // Simulate connection state change
      mockPeerConnection.connectionState = 'connected';
      if (mockPeerConnection.onconnectionstatechange) {
        mockPeerConnection.onconnectionstatechange();
      }
      
      expect(mockCallbacks.onConnectionStateChange).toHaveBeenCalledWith('connected');
    });
  });

  describe('Error Handling', () => {
    it('should handle peer connection errors', () => {
      const mockCallbacks = {
        onError: jest.fn(),
      };
      
      webRTCService.setCallbacks(mockCallbacks);
      
      const error = new Error('Connection failed');
      webRTCService['handleError'](error);
      
      expect(mockCallbacks.onError).toHaveBeenCalledWith(error);
    });

    it('should handle socket connection errors', () => {
      const mockCallbacks = {
        onError: jest.fn(),
      };
      
      webRTCService.setCallbacks(mockCallbacks);
      
      const error = new Error('Socket connection failed');
      webRTCService['handleSocketError'](error);
      
      expect(mockCallbacks.onError).toHaveBeenCalledWith(error);
    });
  });

  describe('Callback Management', () => {
    it('should set callbacks correctly', () => {
      const mockCallbacks = {
        onRemoteStream: jest.fn(),
        onConnectionStateChange: jest.fn(),
        onError: jest.fn(),
      };
      
      webRTCService.setCallbacks(mockCallbacks);
      
      expect(webRTCService['onRemoteStream']).toBe(mockCallbacks.onRemoteStream);
      expect(webRTCService['onConnectionStateChange']).toBe(mockCallbacks.onConnectionStateChange);
      expect(webRTCService['onError']).toBe(mockCallbacks.onError);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup resources on destroy', () => {
      webRTCService.destroy();
      
      expect(mockPeerConnection.close).toHaveBeenCalled();
      expect(mockSocket.disconnect).toHaveBeenCalled();
    });
  });

  describe('Media Control', () => {
    it('should mute audio track', () => {
      const mockAudioTrack = { enabled: true };
      webRTCService['localStream'] = {
        getAudioTracks: () => [mockAudioTrack],
      } as any;
      
      webRTCService.muteAudio();
      
      expect(mockAudioTrack.enabled).toBe(false);
    });

    it('should unmute audio track', () => {
      const mockAudioTrack = { enabled: false };
      webRTCService['localStream'] = {
        getAudioTracks: () => [mockAudioTrack],
      } as any;
      
      webRTCService.unmuteAudio();
      
      expect(mockAudioTrack.enabled).toBe(true);
    });

    it('should disable video track', () => {
      const mockVideoTrack = { enabled: true };
      webRTCService['localStream'] = {
        getVideoTracks: () => [mockVideoTrack],
      } as any;
      
      webRTCService.disableVideo();
      
      expect(mockVideoTrack.enabled).toBe(false);
    });

    it('should enable video track', () => {
      const mockVideoTrack = { enabled: false };
      webRTCService['localStream'] = {
        getVideoTracks: () => [mockVideoTrack],
      } as any;
      
      webRTCService.enableVideo();
      
      expect(mockVideoTrack.enabled).toBe(true);
    });
  });

  describe('Socket Event Handling', () => {
    it('should handle incoming call offers', () => {
      const mockCallbacks = {
        onIncomingCall: jest.fn(),
      };
      
      webRTCService.setCallbacks(mockCallbacks);
      
      const offer = { type: 'offer', sdp: 'test-sdp' };
      const callerId = 'caller-user';
      
      // Simulate incoming call offer
      webRTCService['handleIncomingCall'](offer, callerId);
      
      expect(mockCallbacks.onIncomingCall).toHaveBeenCalledWith(offer, callerId);
    });

    it('should handle call answers', async () => {
      const answer = { type: 'answer', sdp: 'test-answer-sdp' };
      
      await webRTCService['handleCallAnswer'](answer);
      
      expect(mockPeerConnection.setRemoteDescription).toHaveBeenCalledWith(answer);
    });

    it('should handle ICE candidates from remote', async () => {
      const candidate = {
        candidate: 'test-candidate',
        sdpMLineIndex: 0,
        sdpMid: '0',
      };
      
      await webRTCService['handleRemoteIceCandidate'](candidate);
      
      expect(mockPeerConnection.addIceCandidate).toHaveBeenCalledWith(candidate);
    });
  });
});
