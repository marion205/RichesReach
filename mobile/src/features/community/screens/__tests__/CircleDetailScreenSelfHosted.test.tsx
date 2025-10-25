import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import CircleDetailScreenSelfHosted from '../CircleDetailScreenSelfHosted';
import { WealthCircle } from '../../../../components/WealthCircles2';

// Mock dependencies
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

jest.mock('react-native-webrtc', () => ({
  RTCIceCandidate: jest.fn(),
  RTCPeerConnection: jest.fn(),
  RTCSessionDescription: jest.fn(),
  RTCView: 'RTCView',
  MediaStream: {
    getUserMedia: jest.fn(),
  },
}));

jest.mock('expo-av', () => ({
  Audio: {
    requestPermissionsAsync: jest.fn(),
    setAudioModeAsync: jest.fn(),
    Recording: jest.fn(),
  },
  Video: 'Video',
}));

jest.mock('expo-image-picker', () => ({
  requestMediaLibraryPermissionsAsync: jest.fn(),
  launchImageLibraryAsync: jest.fn(),
  MediaTypeOptions: {
    Images: 'Images',
    Videos: 'Videos',
  },
}));

jest.mock('expo-notifications', () => ({
  setNotificationHandler: jest.fn(),
  requestPermissionsAsync: jest.fn(),
  getExpoPushTokenAsync: jest.fn(),
  addNotificationReceivedListener: jest.fn(),
  addNotificationResponseReceivedListener: jest.fn(),
}));

jest.mock('expo-device', () => ({
  isDevice: true,
}));

jest.mock('expo-constants', () => ({
  expoConfig: {
    extra: {
      eas: {
        projectId: 'test-project-id',
      },
    },
  },
}));

jest.mock('socket.io-client', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    emit: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    disconnect: jest.fn(),
  })),
}));

jest.mock('../../../services/WebRTCService', () => ({
  WebRTCService: jest.fn().mockImplementation(() => ({
    initialize: jest.fn(),
    setCallbacks: jest.fn(),
    startStream: jest.fn(),
    stopStream: jest.fn(),
    joinRoom: jest.fn(),
    leaveRoom: jest.fn(),
  })),
}));

jest.mock('../../../services/SocketChatService', () => ({
  SocketChatService: jest.fn().mockImplementation(() => ({
    initialize: jest.fn(),
    setCallbacks: jest.fn(),
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
    onMessage: jest.fn(),
  })),
}));

jest.mock('react-native-gifted-chat', () => ({
  GiftedChat: 'GiftedChat',
  IMessage: {},
}));

// Mock theme
const mockTheme = {
  colors: {
    background: '#ffffff',
    surface: '#f5f5f5',
    text: '#000000',
    textSecondary: '#666666',
    primary: '#007AFF',
  },
};

jest.mock('../../../../theme/PersonalizedThemes', () => ({
  useTheme: () => mockTheme,
}));

// Mock navigation
const mockNavigation = {
  navigate: jest.fn(),
  setOptions: jest.fn(),
  goBack: jest.fn(),
};

// Mock route
const mockRoute = {
  params: {
    circle: {
      id: 'test-circle-1',
      name: 'Test Wealth Circle',
      description: 'A test circle for unit testing',
      memberCount: 5,
      totalValue: 1000000,
      performance: 12.5,
      category: 'investment',
      isPrivate: false,
      isJoined: true,
      members: [],
      recentActivity: [],
      rules: [],
      tags: ['testing', 'investment'],
      createdBy: 'test-user',
      createdAt: '2024-01-01T00:00:00Z',
    } as WealthCircle,
  },
};

describe('CircleDetailScreenSelfHosted', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock AsyncStorage
    (AsyncStorage.getItem as jest.Mock).mockResolvedValue('test-token');
    
    // Mock fetch
    global.fetch = jest.fn();
    
    // Mock Alert
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders without crashing', () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      expect(getByText('Test Wealth Circle')).toBeTruthy();
    });

    it('renders the video call button', () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      expect(getByText('📹 Call')).toBeTruthy();
    });

    it('renders the microphone button', () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      expect(getByText('🎤')).toBeTruthy();
    });

    it('renders media picker buttons', () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      expect(getByText('📷')).toBeTruthy();
      expect(getByText('🎥')).toBeTruthy();
    });
  });

  describe('Video Chat Functionality', () => {
    it('initializes WebRTC peer connection on mount', async () => {
      const { RTCPeerConnection } = require('react-native-webrtc');
      
      render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      await waitFor(() => {
        expect(RTCPeerConnection).toHaveBeenCalled();
      });
    });

    it('shows video call modal when call button is pressed', async () => {
      const { getByText, queryByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const callButton = getByText('📹 Call');
      
      await act(async () => {
        fireEvent.press(callButton);
      });
      
      // Modal should be visible
      expect(queryByText('Video Call with partner-user-id')).toBeTruthy();
    });

    it('handles incoming call offer', async () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      // Simulate incoming call
      await act(async () => {
        // Trigger the socket event handler
        const mockSocket = require('socket.io-client').default();
        const callOfferHandler = mockSocket.on.mock.calls.find(
          call => call[0] === 'call-offer'
        )?.[1];
        
        if (callOfferHandler) {
          callOfferHandler({
            offer: { type: 'offer', sdp: 'test-sdp' },
            from: 'test-user'
          });
        }
      });
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Incoming Call',
        'test-user is calling. Answer?',
        expect.any(Array)
      );
    });

    it('handles call decline', async () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      await act(async () => {
        const mockSocket = require('socket.io-client').default();
        const callDeclineHandler = mockSocket.on.mock.calls.find(
          call => call[0] === 'call-decline'
        )?.[1];
        
        if (callDeclineHandler) {
          callDeclineHandler({ from: 'test-user' });
        }
      });
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Call Declined',
        'test-user declined the call.'
      );
    });

    it('toggles mute functionality', async () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const callButton = getByText('📹 Call');
      
      await act(async () => {
        fireEvent.press(callButton);
      });
      
      // Find mute button in modal
      const muteButton = getByText('🎤');
      
      await act(async () => {
        fireEvent.press(muteButton);
      });
      
      // Should toggle to muted state
      expect(getByText('🔇')).toBeTruthy();
    });

    it('toggles video functionality', async () => {
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const callButton = getByText('📹 Call');
      
      await act(async () => {
        fireEvent.press(callButton);
      });
      
      // Find video toggle button in modal
      const videoButton = getByText('📹');
      
      await act(async () => {
        fireEvent.press(videoButton);
      });
      
      // Should toggle to camera off state
      expect(getByText('📷')).toBeTruthy();
    });
  });

  describe('Voice Recording Functionality', () => {
    it('requests microphone permissions before recording', async () => {
      const { Audio } = require('expo-av');
      Audio.requestPermissionsAsync.mockResolvedValue({ status: 'granted' });
      
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const micButton = getByText('🎤');
      
      await act(async () => {
        fireEvent.press(micButton);
      });
      
      expect(Audio.requestPermissionsAsync).toHaveBeenCalled();
    });

    it('shows recording state when microphone is pressed', async () => {
      const { Audio } = require('expo-av');
      Audio.requestPermissionsAsync.mockResolvedValue({ status: 'granted' });
      
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const micButton = getByText('🎤');
      
      await act(async () => {
        fireEvent.press(micButton);
      });
      
      // Should show stop recording button
      expect(getByText('⏹️')).toBeTruthy();
    });

    it('handles transcription API call', async () => {
      const { Audio } = require('expo-av');
      Audio.requestPermissionsAsync.mockResolvedValue({ status: 'granted' });
      
      // Mock successful transcription response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          transcription: 'This is a test transcription',
          audioUrl: '/uploads/test-audio.m4a',
          processingTime: 1500,
          model: 'ggml-tiny.en-q5_0.bin'
        }),
      });
      
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const micButton = getByText('🎤');
      
      // Start recording
      await act(async () => {
        fireEvent.press(micButton);
      });
      
      // Stop recording and transcribe
      const stopButton = getByText('⏹️');
      await act(async () => {
        fireEvent.press(stopButton);
      });
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/transcribe-audio/'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });

    it('handles transcription errors gracefully', async () => {
      const { Audio } = require('expo-av');
      Audio.requestPermissionsAsync.mockResolvedValue({ status: 'granted' });
      
      // Mock failed transcription response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Transcription failed' }),
      });
      
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const micButton = getByText('🎤');
      
      // Start recording
      await act(async () => {
        fireEvent.press(micButton);
      });
      
      // Stop recording and transcribe
      const stopButton = getByText('⏹️');
      await act(async () => {
        fireEvent.press(stopButton);
      });
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Transcription Error',
        'Failed to process voice. Please try again.'
      );
    });
  });

  describe('Media Upload Functionality', () => {
    it('handles image picker permissions', async () => {
      const { ImagePicker } = require('expo-image-picker');
      ImagePicker.requestMediaLibraryPermissionsAsync.mockResolvedValue({
        status: 'granted'
      });
      ImagePicker.launchImageLibraryAsync.mockResolvedValue({
        canceled: false,
        assets: [{ uri: 'test-image.jpg', type: 'image' }]
      });
      
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const imageButton = getByText('📷');
      
      await act(async () => {
        fireEvent.press(imageButton);
      });
      
      expect(ImagePicker.requestMediaLibraryPermissionsAsync).toHaveBeenCalled();
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    });

    it('handles video picker permissions', async () => {
      const { ImagePicker } = require('expo-image-picker');
      ImagePicker.requestMediaLibraryPermissionsAsync.mockResolvedValue({
        status: 'granted'
      });
      ImagePicker.launchImageLibraryAsync.mockResolvedValue({
        canceled: false,
        assets: [{ uri: 'test-video.mp4', type: 'video' }]
      });
      
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const videoButton = getByText('🎥');
      
      await act(async () => {
        fireEvent.press(videoButton);
      });
      
      expect(ImagePicker.requestMediaLibraryPermissionsAsync).toHaveBeenCalled();
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    });
  });

  describe('Post Submission', () => {
    it('submits post with text content', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'new-post-1',
          content: 'Test post content',
          user: { id: 'test-user', name: 'Test User' },
          timestamp: '2024-01-01T00:00:00Z',
          likes: 0,
          comments: 0,
        }),
      });
      
      const { getByPlaceholderText, getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const textInput = getByPlaceholderText('Share your thoughts...');
      const postButton = getByText('Post');
      
      await act(async () => {
        fireEvent.changeText(textInput, 'Test post content');
        fireEvent.press(postButton);
      });
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/wealth-circles/test-circle-1/posts/'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token',
          }),
          body: JSON.stringify({
            content: 'Test post content',
            media: null
          }),
        })
      );
    });

    it('submits post with media content', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ mediaUrl: '/uploads/test-image.jpg' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            id: 'new-post-1',
            content: 'Test post with image',
            media: { url: '/uploads/test-image.jpg', type: 'image' },
            user: { id: 'test-user', name: 'Test User' },
            timestamp: '2024-01-01T00:00:00Z',
            likes: 0,
            comments: 0,
          }),
        });
      
      const { getByPlaceholderText, getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const textInput = getByPlaceholderText('Share your thoughts...');
      const postButton = getByText('Post');
      
      // Mock media selection
      const { ImagePicker } = require('expo-image-picker');
      ImagePicker.launchImageLibraryAsync.mockResolvedValue({
        canceled: false,
        assets: [{ uri: 'test-image.jpg', type: 'image' }]
      });
      
      await act(async () => {
        fireEvent.changeText(textInput, 'Test post with image');
        fireEvent.press(postButton);
      });
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/upload-media/'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('handles network errors gracefully', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      const { getByPlaceholderText, getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const textInput = getByPlaceholderText('Share your thoughts...');
      const postButton = getByText('Post');
      
      await act(async () => {
        fireEvent.changeText(textInput, 'Test post');
        fireEvent.press(postButton);
      });
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'Failed to submit post'
      );
    });

    it('handles permission denied for microphone', async () => {
      const { Audio } = require('expo-av');
      Audio.requestPermissionsAsync.mockResolvedValue({ status: 'denied' });
      
      const { getByText } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      const micButton = getByText('🎤');
      
      await act(async () => {
        fireEvent.press(micButton);
      });
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Permission needed',
        'Grant microphone access for voice posts.'
      );
    });
  });

  describe('Component Lifecycle', () => {
    it('cleans up resources on unmount', () => {
      const { unmount } = render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      unmount();
      
      // Verify cleanup functions are called
      const mockSocket = require('socket.io-client').default();
      expect(mockSocket.disconnect).toHaveBeenCalled();
    });

    it('initializes services on mount', async () => {
      render(
        <CircleDetailScreenSelfHosted
          route={mockRoute}
          navigation={mockNavigation}
        />
      );
      
      await waitFor(() => {
        expect(mockNavigation.setOptions).toHaveBeenCalledWith({
          title: 'Test Wealth Circle',
          headerStyle: { backgroundColor: mockTheme.colors.primary },
          headerTintColor: mockTheme.colors.text,
        });
      });
    });
  });
});
