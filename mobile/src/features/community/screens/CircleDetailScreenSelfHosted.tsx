import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Image,
  Alert,
  ScrollView,
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import { Video, Audio } from 'expo-av';
import * as Notifications from 'expo-notifications';
import { isExpoGo } from '../../../utils/expoGoCheck';
import * as Device from 'expo-device';

// Conditionally import WebRTC (not available in Expo Go)
// Using unknown for conditional imports that may not be available
let RTCIceCandidate: unknown = null;
let RTCPeerConnection: unknown = null;
let RTCSessionDescription: unknown = null;
let RTCView: React.ComponentType<unknown> | null = null;
let MediaStreamClass: unknown = null;
let MediaStreamTrack: unknown = null;

try {
  if (!isExpoGo()) {
    const webrtc = require('react-native-webrtc');
    RTCIceCandidate = webrtc.RTCIceCandidate;
    RTCPeerConnection = webrtc.RTCPeerConnection;
    RTCSessionDescription = webrtc.RTCSessionDescription;
    RTCView = webrtc.RTCView;
    MediaStreamClass = webrtc.MediaStream;
    MediaStreamTrack = webrtc.MediaStreamTrack;
  }
} catch (e) {
  // WebRTC not available in Expo Go - this is expected
}
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../../../theme/PersonalizedThemes';
// WealthCircle is not exported - using local interface instead
import { WebRTCService } from '../../../services/WebRTCService';
import { SocketChatService } from '../../../services/SocketChatService';
import { API_BASE } from '../../../config/api';
// import { GiftedChat, IMessage } from 'react-native-gifted-chat'; // Package not installed
type IMessage = any; // Placeholder type
import MediasoupLiveStreaming from '../../../components/MediasoupLiveStreaming';
import LiveStreamCamera from '../../../components/LiveStreamCamera';
import loggerModule from '../../../utils/logger';
// Ensure logger is always available with safe wrapper functions
const loggerBase = loggerModule || {
  log: (...args: any[]) => console.log(...args),
  warn: (...args: any[]) => console.warn(...args),
  error: (...args: any[]) => console.error(...args),
  info: (...args: any[]) => console.info(...args),
  debug: (...args: any[]) => console.debug(...args),
};

// Safe logger wrapper that never throws
const logger = {
  log: (...args: any[]) => {
    try {
      if (loggerBase && loggerBase.log) {
        loggerBase.log(...args);
      } else {
        console.log(...args);
      }
    } catch (e) {
      console.log(...args);
    }
  },
  warn: (...args: any[]) => {
    try {
      if (loggerBase && loggerBase.warn) {
        loggerBase.warn(...args);
      } else {
        console.warn(...args);
      }
    } catch (e) {
      console.warn(...args);
    }
  },
  error: (...args: any[]) => {
    try {
      if (loggerBase && loggerBase.error) {
        loggerBase.error(...args);
      } else {
        console.error(...args);
      }
    } catch (e) {
      console.error(...args);
    }
  },
  info: (...args: any[]) => {
    try {
      if (loggerBase && loggerBase.info) {
        loggerBase.info(...args);
      } else {
        console.info(...args);
      }
    } catch (e) {
      console.info(...args);
    }
  },
  debug: (...args: any[]) => {
    try {
      if (loggerBase && loggerBase.debug) {
        loggerBase.debug(...args);
      } else {
        console.debug(...args);
      }
    } catch (e) {
      console.debug(...args);
    }
  },
};

// Configuration
// API_BASE already imported above (line 52)

const STREAMING_SERVER_URL = process.env.EXPO_PUBLIC_SFU_SERVER_URL || API_BASE;
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || API_BASE;
const WHISPER_API_URL = process.env.EXPO_PUBLIC_WHISPER_API_URL || API_BASE.replace(':8000', ':3001');

// Interfaces
interface CirclePost {
  id: string;
  content: string;
  media?: {
    url: string;
    type: 'image' | 'video';
  };
  user: {
    id: string;
    name: string;
    avatar: string;
  };
  timestamp: string;
  likes: number;
  comments: Comment[];
}

interface Comment {
  id: string;
  content: string;
  user: {
    id: string;
    name: string;
    avatar: string;
  };
  timestamp: string;
  likes: number;
}

interface NavigationProp {
  navigate: (screen: string, params?: Record<string, unknown>) => void;
  goBack: () => void;
  setOptions?: (options: any) => void;
  [key: string]: unknown;
}

interface CircleDetailProps {
  route: {
    params: {
      circle: any; // WealthCircle type - using any for now
    };
  };
  navigation: NavigationProp;
}

export default function CircleDetailScreenSelfHosted({ route, navigation }: CircleDetailProps) {
  const theme = useTheme();
  const { circle } = route.params;
  
  // State management
  const [posts, setPosts] = useState<CirclePost[]>([]);
  const [newPostText, setNewPostText] = useState('');
  const [selectedMedia, setSelectedMedia] = useState<{ uri: string; type: 'image' | 'video' } | null>(null);
  const [loading, setLoading] = useState(false);
  const [compressing, setCompressing] = useState(false);
  const [expandedPostId, setExpandedPostId] = useState<string | null>(null);
  
  // Voice recording states
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  // Video chat states
  const [callModalVisible, setCallModalVisible] = useState(false);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);
  const [isCalling, setIsCalling] = useState(false);
  const [callPartner, setCallPartner] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [newComment, setNewComment] = useState<{ [postId: string]: string }>({});
  
  // Live streaming states
  const [liveModalVisible, setLiveModalVisible] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isViewer, setIsViewer] = useState(false);
  const [viewerCount, setViewerCount] = useState(0);
  const [isHost, setIsHost] = useState(false);
  const [activeStream, setActiveStream] = useState<{ host: string; channelId: string } | null>(null);
  
  // Mediasoup live streaming states
  interface StreamInfo {
    id?: string;
    active?: boolean;
    host?: string;
    circleId?: any;
    isHost?: boolean;
    [key: string]: unknown;
  }
  const [liveStreamModalVisible, setLiveStreamModalVisible] = useState(false);
  const [currentStream, setCurrentStream] = useState<StreamInfo | null>(null);
  const [liveStreamCameraVisible, setLiveStreamCameraVisible] = useState(false);
  
  // Chat states
  const [chatMessages, setChatMessages] = useState<IMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [newChatMessage, setNewChatMessage] = useState('');
  
  // Services
  const webRTCService = useRef<WebRTCService | null>(null);
  const chatService = useRef<SocketChatService | null>(null);
  const videoRef = useRef<Video>(null);
  
  // WebRTC refs
  const pc = useRef<RTCPeerConnection | null>(null);
  const videoSocket = useRef<any | null>(null);
  
  // WebRTC configuration
  const rtcConfiguration = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
      // Add TURN server for production: { urls: 'turn:your-turn-server.com', username: '...', credential: '...' }
    ],
  };

  useEffect(() => {
    loadPosts();
    initializeServices();
    setupNotifications();
    navigation.setOptions({
      title: circle.name,
      headerStyle: { backgroundColor: theme.currentTheme.colors.primary },
      headerTintColor: theme.currentTheme.colors.text,
    });
    
    return () => {
      cleanup();
    };
  }, [circle.id]);

  // Initialize WebRTC and Chat services
  const initializeServices = useCallback(async () => {
    try {
      // Initialize WebRTC service
      webRTCService.current = new WebRTCService({
        serverUrl: STREAMING_SERVER_URL,
        stunServers: [
          'stun:stun.l.google.com:19302',
          'stun:stun1.l.google.com:19302'
        ]
      });

      webRTCService.current.setCallbacks({
        onRoomJoined: (roomInfo) => {
          logger.log('📺 Joined room:', roomInfo);
          setViewerCount(roomInfo.viewerCount);
          setIsHost(roomInfo.isHost);
        },
        onUserJoined: (userInfo, viewerCount) => {
          logger.log('👤 User joined:', userInfo);
          setViewerCount(viewerCount);
        },
        onUserLeft: (userId, viewerCount) => {
          logger.log('👋 User left:', userId);
          setViewerCount(viewerCount);
        },
        onRemoteStream: (userId, stream) => {
          logger.log('📺 Remote stream received from:', userId);
        },
        onError: (error) => {
          logger.error('❌ WebRTC error:', error);
          Alert.alert('Streaming Error', error);
        }
      });

      await webRTCService.current.initialize();

      // Initialize Chat service
      chatService.current = new SocketChatService({
        serverUrl: STREAMING_SERVER_URL
      });

      chatService.current.setCallbacks({
        onConnected: () => {
          logger.log('💬 Chat connected');
        },
        onNewMessage: (message) => {
          const giftedMessage = SocketChatService.convertToGiftedChatMessage(message);
          setChatMessages(prev => [...prev, giftedMessage]);
        },
        onMessageHistory: (messages) => {
          const giftedMessages = messages.map(SocketChatService.convertToGiftedChatMessage);
          setChatMessages(giftedMessages);
        },
        onUserJoined: (user) => {
          logger.log('👤 User joined chat:', user);
        },
        onUserLeft: (userId) => {
          logger.log('👋 User left chat:', userId);
        },
        onTypingStart: (user) => {
          setIsTyping(true);
        },
        onTypingStop: (userId) => {
          setIsTyping(false);
        },
        onError: (error) => {
          logger.error('❌ Chat error:', error);
        }
      });

      await chatService.current.initialize();

      // Initialize WebRTC video chat
      initializeVideoChat();

      logger.log('✅ Services initialized successfully');
    } catch (error) {
      logger.error('❌ Failed to initialize services:', error);
      Alert.alert('Initialization Error', 'Failed to initialize streaming and chat services');
    }
  }, []);

  // Initialize WebRTC video chat
  const initializeVideoChat = useCallback(() => {
    try {
      // Create peer connection
      pc.current = new (RTCPeerConnection as any)(rtcConfiguration);
      
      // Create video socket connection - use chatService socket if available
      videoSocket.current = chatService.current ? (chatService.current as any).socket : null;
      
      // Set up peer connection event handlers
      pc.current.onicecandidate = (event) => {
        if (event.candidate && videoSocket.current && callPartner) {
          videoSocket.current.emit('ice-candidate', { 
            candidate: event.candidate, 
            to: callPartner 
          });
        }
      };

      pc.current.ontrack = (event) => {
        logger.log('📺 Remote stream received');
        setRemoteStream(event.streams[0]);
      };

      pc.current.onconnectionstatechange = () => {
        logger.log('🔗 Connection state:', pc.current?.connectionState);
        if (pc.current?.connectionState === 'disconnected' || 
            pc.current?.connectionState === 'failed') {
          endVideoCall();
        }
      };

      // Set up socket event handlers
      setupVideoSocketHandlers();
      
    } catch (error) {
      logger.error('Error initializing video chat:', error);
    }
  }, [callPartner]);

  // Load posts from backend
  const loadPosts = useCallback(async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/wealth-circles/${circle.id}/posts/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPosts(data);
      } else {
        // Use mock data for development
        setPosts(MOCK_POSTS);
      }
    } catch (error) {
      logger.error('Error loading posts:', error);
      setPosts(MOCK_POSTS);
    } finally {
      setLoading(false);
    }
  }, [circle.id]);

  // Setup push notifications
  const setupNotifications = useCallback(async () => {
    if (!Device.isDevice) return;

    try {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        logger.log('Failed to get push token for push notification!');
        return;
      }

      const token = (await Notifications.getExpoPushTokenAsync()).data;
      logger.log('Push token:', token);

      // Register token with backend
      const userId = await AsyncStorage.getItem('userId') || 'demo-user';
      await fetch(`${API_BASE_URL}/api/register-push-token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          expoPushToken: token,
          circleId: circle.id
        })
      });
    } catch (error) {
      logger.error('Error registering push token:', error);
    }
  }, [circle.id]);

  // Start live stream as host
  const startLiveStream = useCallback(async () => {
    logger.log('🎥 [DEBUG] ========== startLiveStream() called ==========');
    logger.log('🎥 [DEBUG] webRTCService.current available:', !!webRTCService.current);
    logger.log('🎥 [DEBUG] Circle ID:', circle.id);
    
    if (!webRTCService.current) {
      logger.error('❌ [DEBUG] webRTCService.current is null/undefined');
      Alert.alert('Error', 'Streaming service not initialized');
      return;
    }

    try {
      logger.log('🎥 [DEBUG] Requesting camera permissions...');
      // Request camera and microphone permissions
      const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();
      logger.log('🎥 [DEBUG] Camera permission status:', cameraStatus);
      
      logger.log('🎥 [DEBUG] Requesting audio permissions...');
      const { status: audioStatus } = await Audio.requestPermissionsAsync();
      logger.log('🎥 [DEBUG] Audio permission status:', audioStatus);
      
      if (cameraStatus !== 'granted') {
        logger.warn('⚠️ [DEBUG] Camera permission denied:', cameraStatus);
        Alert.alert(
          'Camera Permission Required',
          'Please grant camera permission to start live streaming.',
          [{ text: 'OK' }]
        );
        return;
      }
      
      if (audioStatus !== 'granted') {
        logger.warn('⚠️ [DEBUG] Audio permission denied:', audioStatus);
        Alert.alert(
          'Microphone Permission Required',
          'Please grant microphone permission to start live streaming.',
          [{ text: 'OK' }]
        );
        return;
      }

      logger.log('✅ [DEBUG] All permissions granted');
      logger.log('🎥 [DEBUG] Getting user info from AsyncStorage...');
      
      const userId = await AsyncStorage.getItem('userId') || 'demo-user';
      const userName = await AsyncStorage.getItem('userName') || 'User';
      logger.log('🎥 [DEBUG] User ID:', userId);
      logger.log('🎥 [DEBUG] User Name:', userName);
      
      logger.log('🎥 [DEBUG] Calling webRTCService.joinRoom()...');
      logger.log('🎥 [DEBUG] Room ID:', circle.id);
      logger.log('🎥 [DEBUG] Is Host: true');
      
      await webRTCService.current.joinRoom(circle.id, userId, userName, true);
      
      logger.log('✅ [DEBUG] joinRoom() completed successfully');
      logger.log('🎥 [DEBUG] Setting UI state...');
      
      setIsStreaming(true);
      setIsHost(true);
      setViewerCount(1);
      setLiveModalVisible(true);
      setActiveStream({ host: userId, channelId: circle.id });

      logger.log('✅ [DEBUG] UI state updated');
      logger.log('🎥 [DEBUG] Joining chat room...');

      // Join chat room
      if (chatService.current) {
        await chatService.current.joinRoom(circle.id, {
          userId,
          userName,
          avatar: 'https://via.placeholder.com/40'
        });
        logger.log('✅ [DEBUG] Chat room joined');
      } else {
        logger.warn('⚠️ [DEBUG] chatService.current is null, skipping chat join');
      }

      logger.log('✅ [DEBUG] Live stream started successfully!');
      logger.log('🎥 Live stream started');
    } catch (error: any) {
      logger.error('❌ [DEBUG] Stream start error occurred');
      logger.error('❌ [DEBUG] Error name:', error?.name);
      logger.error('❌ [DEBUG] Error message:', error?.message);
      logger.error('❌ [DEBUG] Error stack:', error?.stack?.substring(0, 500));
      logger.error('❌ [DEBUG] Full error:', JSON.stringify(error, Object.getOwnPropertyNames(error)).substring(0, 1000));
      logger.error('Stream start error:', error);
      Alert.alert('Streaming Error', 'Failed to start live stream');
    }
  }, [circle.id]);

  // Join as viewer
  const joinAsViewer = useCallback(async () => {
    if (!webRTCService.current || !activeStream) {
      Alert.alert('Error', 'Streaming service not initialized or no active stream');
      return;
    }

    try {
      const userId = await AsyncStorage.getItem('userId') || 'demo-user';
      const userName = await AsyncStorage.getItem('userName') || 'User';
      
      await webRTCService.current.joinRoom(activeStream.channelId, userId, userName, false);
      
      setIsViewer(true);
      setIsHost(false);
      setLiveModalVisible(true);

      // Join chat room
      if (chatService.current) {
        await chatService.current.joinRoom(activeStream.channelId, {
          userId,
          userName,
          avatar: 'https://via.placeholder.com/40'
        });
      }

      logger.log('👁️ Joined as viewer');
    } catch (error) {
      logger.error('Viewer join error:', error);
      Alert.alert('Streaming Error', 'Failed to join live stream');
    }
  }, [activeStream]);

  // End live stream
  const endLiveStream = useCallback(async () => {
    try {
      if (webRTCService.current) {
        await webRTCService.current.leaveRoom();
      }
      
      if (chatService.current) {
        chatService.current.leaveRoom();
      }

      setIsStreaming(false);
      setIsViewer(false);
      setIsHost(false);
      setViewerCount(0);
      setLiveModalVisible(false);
      setActiveStream(null);

      logger.log('🔚 Live stream ended');
    } catch (error) {
      logger.error('End stream error:', error);
    }
  }, []);

  // Pick media (image or video)
  const pickMedia = useCallback(async (mediaType: 'image' | 'video') => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (permission.status !== 'granted') {
        Alert.alert('Permission needed', `Please grant access to your ${mediaType}s.`);
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: mediaType === 'image' ? 'images' : 'videos',
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        videoMaxDuration: 60,
      });

      if (!result.canceled && result.assets[0]) {
        setSelectedMedia({
          uri: result.assets[0].uri,
          type: result.assets[0].type === 'video' ? 'video' : 'image'
        });
      }
    } catch (error) {
      logger.error('Error picking media:', error);
    }
  }, []);

  // Compress video (simplified for demo)
  const compressVideo = useCallback(async (uri: string) => {
    setCompressing(true);
    try {
      // In a real implementation, you would use react-native-compressor
      // For now, return the original URI
      return uri;
    } catch (error) {
      logger.error('Video compression error:', error);
      return uri;
    } finally {
      setCompressing(false);
    }
  }, []);

  // Mediasoup live streaming functions
  const startLiveStreaming = useCallback(async () => {
    try {
      const userId = await AsyncStorage.getItem('userId') || 'demo-user';
      const userName = await AsyncStorage.getItem('userName') || 'User';
      
      setCurrentStream({
        host: userName,
        circleId: circle.id,
        isHost: true
      });
      
      // Open LiveStreamCamera modal (expo-camera with front camera)
      setLiveStreamCameraVisible(true);
      
      logger.log('🎥 Starting live stream in circle:', circle.name);
    } catch (error) {
      logger.error('Error starting live stream:', error);
      Alert.alert('Error', 'Failed to start live stream');
    }
  }, [circle.id, circle.name]);

  const closeLiveStreamModal = useCallback(() => {
    setLiveStreamModalVisible(false);
    setLiveStreamCameraVisible(false);
    setCurrentStream(null);
  }, []);

  // Handler for LiveStreamCamera start
  const handleLiveStreamCameraStart = useCallback(async ({ circleId, camera }: { circleId: string; camera: any }) => {
    logger.log('🎥 [DEBUG] LiveStreamCamera start requested for circle:', circleId);
    // Call the existing startLiveStream function which handles WebRTC
    // The expo-camera is just for preview, WebRTC handles the actual streaming
    await startLiveStream();
  }, [startLiveStream]);

  // Handler for LiveStreamCamera stop
  const handleLiveStreamCameraStop = useCallback(async ({ circleId, camera }: { circleId: string; camera: any }) => {
    logger.log('🛑 [DEBUG] LiveStreamCamera stop requested for circle:', circleId);
    // Call the existing endLiveStream function
    await endLiveStream();
    setLiveStreamCameraVisible(false);
  }, [endLiveStream]);

  // Upload media
  const uploadMedia = useCallback(async (media: { uri: string; type: 'image' | 'video' }) => {
    try {
      let finalUri = media.uri;
      if (media.type === 'video') {
        finalUri = await compressVideo(media.uri);
      }

      interface FormDataMedia {
        uri: string;
        type: string;
        name: string;
      }
      const formData = new FormData();
      const mediaData: FormDataMedia = {
        uri: finalUri,
        type: media.type === 'video' ? 'video/mp4' : 'image/jpeg',
        name: `media.${media.type === 'video' ? 'mp4' : 'jpg'}`,
      };
      formData.append('media', mediaData as unknown as Blob);

      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/upload-media/`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        return data.mediaUrl;
      }
      throw new Error('Upload failed');
    } catch (error) {
      logger.error('Media upload error:', error);
      throw error;
    }
  }, [compressVideo]);

  // Submit post
  const submitPost = useCallback(async () => {
    if (!newPostText.trim() && !selectedMedia) return;

    try {
      setLoading(true);
      let mediaUrl = null;

      if (selectedMedia) {
        mediaUrl = await uploadMedia(selectedMedia);
      }

      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/wealth-circles/${circle.id}/posts/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: newPostText,
          media: mediaUrl ? { url: mediaUrl, type: selectedMedia?.type } : null
        })
      });

      if (response.ok) {
        const newPost = await response.json();
        setPosts(prev => [newPost, ...prev]);
        setNewPostText('');
        setSelectedMedia(null);
      }
    } catch (error) {
      logger.error('Error submitting post:', error);
      Alert.alert('Error', 'Failed to submit post');
    } finally {
      setLoading(false);
    }
  }, [newPostText, selectedMedia, circle.id, uploadMedia]);

  // Submit comment
  const submitComment = useCallback(async (postId: string) => {
    const content = newComment[postId]?.trim();
    if (!content) return;

    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/comments/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content })
      });

      if (response.ok) {
        const newComment = await response.json();
        setPosts(prev => prev.map(post => 
          post.id === postId 
            ? { ...post, comments: [...(post.comments || []), newComment] }
            : post
        ));
        setNewComment(prev => ({ ...prev, [postId]: '' }));
      }
    } catch (error) {
      logger.error('Error submitting comment:', error);
    }
  }, [newComment]);

  // Toggle comments
  const toggleComments = (postId: string) => {
    setExpandedPostId(prev => prev === postId ? null : postId);
  };

  // Setup video socket handlers
  const setupVideoSocketHandlers = useCallback(() => {
    if (!videoSocket.current) return;

    videoSocket.current.on('call-offer', ({ offer, from }) => {
      Alert.alert('Incoming Call', `${from} is calling. Answer?`, [
        { text: 'Decline', onPress: () => videoSocket.current?.emit('call-decline', { to: from }) },
        { text: 'Answer', onPress: () => answerVideoCall(offer, from) },
      ]);
    });

    videoSocket.current.on('call-answer', ({ answer }) => {
      pc.current?.setRemoteDescription(new (RTCSessionDescription as any)(answer));
    });

    videoSocket.current.on('ice-candidate', ({ candidate }) => {
      pc.current?.addIceCandidate(new (RTCIceCandidate as any)(candidate));
    });

    videoSocket.current.on('call-decline', ({ from }) => {
      Alert.alert('Call Declined', `${from} declined the call.`);
      endVideoCall();
    });

    videoSocket.current.on('end-call', () => endVideoCall());
  }, []);

  // Start video call
  const startVideoCall = useCallback(async (partnerId: string) => {
    setCallPartner(partnerId);
    setIsCalling(true);
    setCallModalVisible(true);

    try {
      const stream = await (MediaStreamClass as any).getUserMedia({ video: true, audio: true });
      stream.getTracks().forEach(track => pc.current?.addTrack(track, stream));
      setLocalStream(stream);

      const offer = await pc.current?.createOffer();
      await pc.current?.setLocalDescription(offer);
      
      const userId = await AsyncStorage.getItem('userId');
      videoSocket.current?.emit('call-offer', { 
        offer, 
        to: partnerId, 
        from: userId 
      });
    } catch (err) {
      logger.error('Call start error:', err);
      Alert.alert('Error', 'Failed to start call. Check camera and microphone permissions.');
    }
  }, []);

  // Answer video call
  const answerVideoCall = useCallback(async (offer: RTCSessionDescriptionInit, from: string) => {
    setCallPartner(from);
    setCallModalVisible(true);

    try {
      const stream = await (MediaStreamClass as any).getUserMedia({ video: true, audio: true });
      stream.getTracks().forEach(track => pc.current?.addTrack(track, stream));
      setLocalStream(stream);

      await pc.current?.setRemoteDescription(new (RTCSessionDescription as any)(offer));
      const answer = await pc.current?.createAnswer();
      await pc.current?.setLocalDescription(answer!);
      
      videoSocket.current?.emit('call-answer', { answer, to: from });
    } catch (err) {
      logger.error('Answer error:', err);
      Alert.alert('Error', 'Failed to answer call.');
    }
  }, []);

  // End video call
  const endVideoCall = useCallback(() => {
    localStream?.getTracks().forEach(track => track.stop());
    remoteStream?.getTracks().forEach(track => track.stop());
    setLocalStream(null);
    setRemoteStream(null);
    setCallModalVisible(false);
    setIsCalling(false);
    setCallPartner(null);
    setIsMuted(false);
    setIsVideoEnabled(true);
    
    if (pc.current) {
      pc.current.close();
      pc.current = new (RTCPeerConnection as any)(rtcConfiguration);
    }
    
    videoSocket.current?.emit('end-call', { to: callPartner });
  }, [localStream, remoteStream, callPartner]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  }, [localStream]);

  // Toggle video
  const toggleVideo = useCallback(() => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsVideoEnabled(videoTrack.enabled);
      }
    }
  }, [localStream]);

  // Voice recording functions
  const startRecording = useCallback(async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Grant microphone access for voice posts.');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      const newRecording = new Audio.Recording();
      await newRecording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: (Audio as any).RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_MPEG_4 || 2,
          audioEncoder: (Audio as any).RECORDING_OPTION_ANDROID_AUDIO_ENCODER_AAC || 3,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: (Audio as any).RECORDING_OPTION_IOS_OUTPUT_FORMAT_MPEG4AAC || 'mpeg4aac',
          audioQuality: (Audio as any).RECORDING_OPTION_IOS_AUDIO_QUALITY_HIGH || 'high',
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      });
      
      await newRecording.startAsync();
      setRecording(newRecording);
      setIsRecording(true);
      
      logger.log('🎤 Recording started');
    } catch (err) {
      logger.error('Recording start error:', err);
      Alert.alert('Recording Error', 'Failed to start recording. Please try again.');
    }
  }, []);

  const stopRecordingAndTranscribe = useCallback(async () => {
    if (!recording) return;
    
    try {
      setIsTranscribing(true);
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      setIsRecording(false);

      if (!uri) {
        throw new Error('No recording URI available');
      }

      logger.log('🎤 Recording stopped, starting transcription...');

      // Upload to backend for transcription
      interface FormDataAudio {
        uri: string;
        type: string;
        name: string;
      }
      const formData = new FormData();
      const audioData: FormDataAudio = {
        uri,
        type: 'audio/m4a',
        name: 'voice.m4a',
      };
      formData.append('audio', audioData as unknown as Blob);

      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${WHISPER_API_URL}/api/transcribe-audio/`, {
        method: 'POST',
        body: formData,
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        const { transcription, audioUrl } = await response.json();
        logger.log('✅ Transcription completed:', transcription);
        
        // Set as post text + audio media
        setNewPostText(transcription);
        if (audioUrl) {
          setSelectedMedia({ uri: audioUrl, type: 'video' }); // Treat audio as 'video' for playback
        }
        
        Alert.alert('Transcription Complete', `"${transcription}"`);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Transcription failed');
      }
    } catch (err) {
      // Only show alert if it's not a network error (Whisper API may not be running)
      if (!(err instanceof TypeError && err.message === 'Network request failed')) {
        logger.error('Transcription error:', err);
        Alert.alert('Transcription Error', 'Failed to process voice. Please try again.');
      }
    } finally {
      setIsTranscribing(false);
    }
  }, [recording]);

  // Send chat message
  const onSendChatMessage = useCallback((messages: IMessage[] = []) => {
    if (chatService.current && messages.length > 0) {
      chatService.current.sendMessage(messages[0].text || '');
    }
  }, []);

  // Render post item
  const renderPost = useCallback(({ item }: { item: CirclePost }) => (
    <View style={[styles.postCard, { backgroundColor: theme.currentTheme.colors.surface }]}>
      <View style={styles.postHeader}>
        <Image source={{ uri: item.user.avatar }} style={styles.avatar} />
        <View style={styles.postInfo}>
          <Text style={[styles.userName, { color: theme.currentTheme.colors.text }]}>{item.user.name}</Text>
          <Text style={[styles.timestamp, { color: theme.currentTheme.colors.textSecondary }]}>{item.timestamp}</Text>
        </View>
      </View>
      
      <Text style={[styles.postContent, { color: theme.currentTheme.colors.text }]}>{item.content}</Text>
      
      {item.media && (
        <View style={styles.mediaContainer}>
          {item.media.type === 'image' ? (
            <Image source={{ uri: item.media.url }} style={styles.media} />
          ) : (
            <Video
              ref={videoRef}
              source={{ uri: item.media.url }}
              style={styles.media}
              useNativeControls
              {...({ resizeMode: "contain" } as any)}
            />
          )}
        </View>
      )}
      
      <View style={styles.postActions}>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>❤️ {item.likes}</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.actionButton}
          onPress={() => toggleComments(item.id)}
        >
          <Text style={styles.actionText}>💬 {item.comments.length}</Text>
        </TouchableOpacity>
      </View>

      {/* Comments Section */}
      {expandedPostId === item.id && (
        <View style={styles.commentsSection}>
          <FlatList
            data={item.comments || []}
            renderItem={({ item: comment }) => (
              <View style={styles.commentItem}>
                <Image source={{ uri: comment.user.avatar }} style={styles.commentAvatar} />
                <View style={styles.commentContent}>
                  <Text style={[styles.commentUser, { color: theme.currentTheme.colors.text }]}>{comment.user.name}</Text>
                  <Text style={[styles.commentText, { color: theme.currentTheme.colors.text }]}>{comment.content}</Text>
                  <Text style={[styles.commentTime, { color: theme.currentTheme.colors.textSecondary }]}>{comment.timestamp}</Text>
                </View>
              </View>
            )}
            keyExtractor={(comment) => comment.id}
            scrollEnabled={false}
          />
          
          <View style={styles.commentInputContainer}>
            <TextInput
              style={[styles.commentInput, { color: theme.currentTheme.colors.text }]}
              placeholder="Add a comment..."
              placeholderTextColor={theme.currentTheme.colors.textSecondary}
              value={newComment[item.id] || ''}
              onChangeText={(text) => setNewComment(prev => ({ ...prev, [item.id]: text }))}
              multiline
            />
            <TouchableOpacity 
              onPress={() => submitComment(item.id)} 
              style={styles.commentSubmit}
              disabled={!newComment[item.id]?.trim()}
            >
              <Text style={styles.commentSubmitText}>Send</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  ), [theme.currentTheme.colors, expandedPostId, newComment, submitComment]);

  // Render live modal
  const renderLiveModal = () => (
    <Modal visible={liveModalVisible} animationType="slide">
      <View style={styles.liveModal}>
        <View style={styles.liveHeader}>
          <Text style={styles.liveTitle}>Live in {circle.name}</Text>
          <TouchableOpacity onPress={endLiveStream}>
            <Text style={styles.endLiveText}>End</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.videoContainer}>
          {isStreaming && (
            <View style={styles.localVideoContainer}>
              <Text style={styles.videoPlaceholder}>Local Video Stream</Text>
            </View>
          )}
          {isViewer && (
            <View style={styles.remoteVideoContainer}>
              <Text style={styles.videoPlaceholder}>Remote Video Stream</Text>
            </View>
          )}
          {!isStreaming && !isViewer && (
            <Text style={styles.videoPlaceholder}>Waiting for host...</Text>
          )}
        </View>
        
        {/* Chat Overlay */}
        <View style={styles.chatOverlay}>
          {/* GiftedChat not available - using simple chat UI */}
          <ScrollView style={styles.chatMessages}>
            {chatMessages.map((msg: any, idx: number) => (
              <View key={idx} style={[styles.chatBubble, msg.user?._id === 'current-user' ? styles.chatBubbleRight : styles.chatBubbleLeft]}>
                <Text style={styles.chatBubbleText}>{msg.text}</Text>
              </View>
            ))}
          </ScrollView>
          <View style={styles.chatInputToolbar}>
            <TextInput
              style={styles.chatInput}
              placeholder="Type a message..."
              value={newChatMessage}
              onChangeText={setNewChatMessage}
              multiline
            />
            <TouchableOpacity onPress={() => {
              if (newChatMessage.trim()) {
                onSendChatMessage([{ _id: Date.now().toString(), text: newChatMessage, user: { _id: 'current-user', name: 'User' }, createdAt: new Date() } as IMessage]);
                setNewChatMessage('');
              }
            }}>
              <Text style={styles.chatSendButton}>Send</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Viewer Count Display */}
        <View style={styles.viewerCountContainer}>
          <Text style={styles.viewerCountText}>{viewerCount} viewers</Text>
          <Text style={styles.viewerIcon}>👁️</Text>
        </View>
      </View>
    </Modal>
  );

  // Cleanup
  const cleanup = useCallback(() => {
    if (webRTCService.current) {
      webRTCService.current.disconnect();
    }
    if (chatService.current) {
      chatService.current.disconnect();
    }
  }, []);

  if (loading && posts.length === 0) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.currentTheme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.currentTheme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.currentTheme.colors.textSecondary }]}>
          Loading posts...
        </Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView 
      style={[styles.container, { backgroundColor: theme.currentTheme.colors.background }]} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <FlatList
        data={posts}
        renderItem={renderPost}
        keyExtractor={(item) => item.id}
        refreshing={loading}
        onRefresh={loadPosts}
        contentContainerStyle={styles.postsList}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={[styles.emptyText, { color: theme.currentTheme.colors.textSecondary }]}>
              No posts yet. Be the first to share!
            </Text>
          </View>
        }
      />
      
      {/* Post Input */}
      <View style={[styles.inputContainer, { backgroundColor: theme.currentTheme.colors.surface }]}>
        <TextInput
          style={[styles.textInput, { color: theme.currentTheme.colors.text }]}
          placeholder="Share your thoughts..."
          placeholderTextColor={theme.currentTheme.colors.textSecondary}
          value={newPostText}
          onChangeText={setNewPostText}
          multiline
        />
        
        <View style={styles.inputActions}>
          <TouchableOpacity 
            onPress={isRecording ? stopRecordingAndTranscribe : startRecording} 
            style={styles.micButton} 
            disabled={isTranscribing}
          >
            <LinearGradient 
              colors={isRecording ? ['#FF3B30', '#FF9500'] : ['#34C759', '#30D158']} 
              style={[styles.micGradient, isRecording && styles.micActive]}
            >
              {isTranscribing ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.micText}>{isRecording ? '⏹️' : '🎤'}</Text>
              )}
            </LinearGradient>
          </TouchableOpacity>
          
          <TouchableOpacity onPress={() => pickMedia('image')} style={styles.mediaButton}>
            <Text style={styles.mediaButtonText}>📷</Text>
          </TouchableOpacity>
          
          <TouchableOpacity onPress={() => pickMedia('video')} style={styles.mediaButton}>
            <Text style={styles.mediaButtonText}>🎥</Text>
          </TouchableOpacity>
          
          {selectedMedia && (
            <View style={styles.selectedMedia}>
              <Text style={styles.selectedMediaText}>
                {selectedMedia.type === 'video' ? '🎥' : '📷'} Selected
              </Text>
              <TouchableOpacity onPress={() => setSelectedMedia(null)}>
                <Text style={styles.removeMediaText}>✕</Text>
              </TouchableOpacity>
            </View>
          )}
          
          <TouchableOpacity 
            onPress={submitPost} 
            style={styles.submitButton}
            disabled={loading || compressing}
          >
            {loading || compressing ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <Text style={styles.submitButtonText}>Post</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
      
      {/* Go Live Button */}
      {!activeStream && (
        <TouchableOpacity onPress={startLiveStream} style={styles.goLiveButton}>
          <LinearGradient colors={['#FF3B30', '#FF9500']} style={styles.goLiveGradient}>
            <Text style={styles.goLiveText}>Go Live 🎥</Text>
          </LinearGradient>
        </TouchableOpacity>
      )}
      
      {/* Video Call Button */}
      <TouchableOpacity 
        onPress={() => startVideoCall('partner-user-id')} 
        style={styles.videoCallButton}
      >
        <LinearGradient colors={['#007AFF', '#5856D6']} style={styles.videoCallGradient}>
          <Text style={styles.videoCallText}>📹 Call</Text>
        </LinearGradient>
      </TouchableOpacity>

      {/* Mediasoup Live Streaming Button */}
      <TouchableOpacity 
        onPress={startLiveStreaming} 
        style={styles.liveStreamButton}
      >
        <LinearGradient colors={['#FF3B30', '#FF9500']} style={styles.liveStreamGradient}>
          <Text style={styles.liveStreamText}>🎥 Go Live</Text>
        </LinearGradient>
      </TouchableOpacity>
      
      {/* Join Live Button */}
      {activeStream && !liveModalVisible && (
        <TouchableOpacity onPress={joinAsViewer} style={styles.joinLiveButton}>
          <LinearGradient colors={['#34C759', '#30D158']} style={styles.joinLiveGradient}>
            <Text style={styles.joinLiveText}>Join Live 📺</Text>
          </LinearGradient>
        </TouchableOpacity>
      )}
      
      {renderLiveModal()}
      
      {/* Video Call Modal */}
      <Modal visible={callModalVisible} animationType="slide">
        <View style={styles.videoCallModal}>
          <View style={styles.videoCallHeader}>
            <Text style={styles.videoCallTitle}>
              Video Call with {callPartner}
            </Text>
            <TouchableOpacity onPress={endVideoCall}>
              <Text style={styles.endCallText}>End</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.videoCallContainer}>
            {remoteStream && (
              <RTCView 
                {...({ streamURL: (remoteStream as any).toURL?.() || '', style: styles.remoteVideo, objectFit: "cover" } as any)}
              />
            )}
            {localStream && (
              <RTCView 
                {...({ streamURL: (localStream as any)?.toURL?.() || '', style: styles.localVideo, objectFit: "cover" } as any)}
              />
            )}
            {!remoteStream && (
              <View style={styles.callingContainer}>
                <Text style={styles.callingText}>
                  {isCalling ? 'Calling...' : 'Waiting for connection...'}
                </Text>
                <ActivityIndicator size="large" color="#007AFF" style={styles.callingSpinner} />
              </View>
            )}
          </View>
          
          {/* Call Controls */}
          <View style={styles.callControls}>
            <TouchableOpacity onPress={toggleMute} style={styles.controlButton}>
              <Text style={styles.controlButtonText}>
                {isMuted ? '🔇' : '🎤'}
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity onPress={endVideoCall} style={styles.endCallButton}>
              <Text style={styles.endCallButtonText}>📞</Text>
            </TouchableOpacity>
            
            <TouchableOpacity onPress={toggleVideo} style={styles.controlButton}>
              <Text style={styles.controlButtonText}>
                {isVideoEnabled ? '📹' : '📷'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Mediasoup Live Streaming Modal */}
      <MediasoupLiveStreaming
        visible={liveStreamModalVisible}
        onClose={closeLiveStreamModal}
        circleId={circle.id}
        isHost={(currentStream?.isHost as boolean) || false}
      />

      {/* LiveStreamCamera Modal - Expo Camera with Front Camera */}
      {liveStreamCameraVisible && (
        <Modal
          visible={liveStreamCameraVisible}
          animationType="slide"
          presentationStyle="fullScreen"
          onRequestClose={closeLiveStreamModal}
        >
          <LiveStreamCamera
            circleId={circle.id}
            circleName={circle.name}
            visible={liveStreamCameraVisible}
            onStartLiveStream={handleLiveStreamCameraStart}
            onStopLiveStream={handleLiveStreamCameraStop}
            onClose={closeLiveStreamModal}
          />
        </Modal>
      )}
    </KeyboardAvoidingView>
  );
}

// Mock posts for development
const MOCK_POSTS: CirclePost[] = [
  {
    id: '1',
    content: 'Check out this quick video on portfolio diversification! 📹',
    media: { url: 'https://via.placeholder.com/300x200/FF3B30/ffffff?text=Video+Thumbnail', type: 'video' },
    user: { id: 'user1', name: 'Alex Rivera', avatar: 'https://via.placeholder.com/40' },
    timestamp: '2 hours ago',
    likes: 12,
    comments: [
      { id: 'c1', content: 'Great tips!', user: { id: 'user2', name: 'Jordan Lee', avatar: 'https://via.placeholder.com/40' }, timestamp: '1 hour ago', likes: 2 },
    ],
  },
  {
    id: '2',
    content: 'Just hit a new milestone in my investment journey! 🚀',
    user: { id: 'user2', name: 'Jordan Lee', avatar: 'https://via.placeholder.com/40' },
    timestamp: '4 hours ago',
    likes: 8,
    comments: [],
  },
];

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    marginTop: 16,
  },
  postsList: {
    padding: 16,
    paddingBottom: 100,
  },
  postCard: {
    marginBottom: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  postInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  timestamp: {
    fontSize: 12,
    marginTop: 2,
  },
  postContent: {
    fontSize: 16,
    lineHeight: 22,
    marginBottom: 12,
  },
  mediaContainer: {
    marginBottom: 12,
  },
  media: {
    width: '100%',
    height: 200,
    borderRadius: 8,
  },
  postActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  actionButton: {
    padding: 8,
  },
  actionText: {
    fontSize: 14,
    color: '#666',
  },
  commentsSection: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    marginTop: 12,
    borderRadius: 8,
  },
  commentItem: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  commentAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    marginRight: 8,
  },
  commentContent: {
    flex: 1,
  },
  commentUser: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  commentText: {
    fontSize: 14,
    marginTop: 2,
  },
  commentTime: {
    fontSize: 10,
    marginTop: 2,
  },
  commentInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  commentInput: {
    flex: 1,
    minHeight: 36,
    maxHeight: 80,
    borderRadius: 18,
    paddingHorizontal: 12,
    backgroundColor: 'white',
    marginRight: 8,
  },
  commentSubmit: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: '#667eea',
  },
  commentSubmitText: {
    color: 'white',
    fontWeight: '600',
  },
  inputContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 100,
    marginBottom: 12,
  },
  inputActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  mediaButton: {
    padding: 8,
  },
  mediaButtonText: {
    fontSize: 24,
  },
  micButton: {
    marginRight: 8,
  },
  micGradient: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  micActive: {
    shadowColor: '#FF3B30',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 8,
    elevation: 8,
  },
  micText: {
    fontSize: 20,
    color: 'white',
  },
  audioContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 12,
    marginVertical: 8,
  },
  audioLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  audioPlayer: {
    height: 40,
    width: '100%',
  },
  selectedMedia: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  selectedMediaText: {
    fontSize: 14,
    marginRight: 8,
  },
  removeMediaText: {
    fontSize: 16,
    color: '#ff4444',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  submitButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  goLiveButton: {
    position: 'absolute',
    bottom: 100,
    right: 16,
    zIndex: 1,
  },
  goLiveGradient: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
  },
  goLiveText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  joinLiveButton: {
    position: 'absolute',
    bottom: 100,
    right: 16,
    zIndex: 1,
    marginTop: 8,
  },
  joinLiveGradient: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
  },
  joinLiveText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  liveModal: {
    flex: 1,
    backgroundColor: 'black',
  },
  liveHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  liveTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  endLiveText: {
    color: '#ff4444',
    fontSize: 16,
    fontWeight: 'bold',
  },
  videoContainer: {
    flex: 1,
    backgroundColor: 'black',
  },
  localVideoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#333',
  },
  remoteVideoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#555',
  },
  videoPlaceholder: {
    color: 'white',
    fontSize: 18,
    textAlign: 'center',
  },
  chatOverlay: {
    flex: 1,
  },
  chatMessages: {
    flex: 1,
    padding: 8,
  },
  chatOverlayDuplicate: {
    height: 200,
    backgroundColor: 'rgba(0,0,0,0.3)',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
  chatBubble: {
    padding: 8,
    borderRadius: 12,
    marginVertical: 2,
    maxWidth: '80%',
  },
  chatBubbleLeft: {
    backgroundColor: 'rgba(255,255,255,0.9)',
    alignSelf: 'flex-start',
  },
  chatBubbleRight: {
    backgroundColor: '#007AFF',
    alignSelf: 'flex-end',
  },
  chatBubbleText: {
    fontSize: 14,
    color: 'white',
  },
  chatInputToolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    backgroundColor: 'rgba(255,255,255,0.9)',
  },
  chatInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8,
  },
  chatSendButton: {
    color: '#007AFF',
    fontWeight: 'bold',
  },
  viewerCountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 10,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  viewerCountText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginRight: 8,
  },
  viewerIcon: {
    fontSize: 16,
    color: 'white',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 50,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
  },
  // Video call styles
  videoCallButton: {
    position: 'absolute',
    bottom: 200,
    right: 16,
    zIndex: 1,
  },
  videoCallGradient: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 25,
  },
  videoCallText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  videoCallModal: {
    flex: 1,
    backgroundColor: 'black',
  },
  videoCallHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  videoCallTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  videoCallContainer: {
    flex: 1,
    position: 'relative',
  },
  remoteVideo: {
    flex: 1,
    backgroundColor: '#333',
  },
  localVideo: {
    position: 'absolute',
    top: 20,
    right: 20,
    width: 120,
    height: 160,
    borderRadius: 8,
    backgroundColor: '#555',
  },
  callingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  callingText: {
    color: 'white',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 20,
  },
  callingSpinner: {
    marginTop: 20,
  },
  callControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlButtonText: {
    fontSize: 24,
  },
  endCallButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#FF3B30',
    justifyContent: 'center',
    alignItems: 'center',
  },
  endCallText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  endCallButtonText: {
    fontSize: 28,
  },
  
  // Live streaming button styles
  liveStreamButton: {
    position: 'absolute',
    bottom: 200,
    right: 16,
    zIndex: 1,
  },
  liveStreamGradient: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 25,
  },
  liveStreamText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
});
