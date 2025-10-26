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
import { Video } from 'expo-av';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../../../theme/PersonalizedThemes';
import { WealthCircle } from '../../../components/WealthCircles2';
import io from 'socket.io-client';
import RtcEngine, { RtcLocalView, RtcRemoteView, ClientRole, RtcEngineEventHandler } from 'react-native-agora';
import {
  StreamChat,
  Chat,
  Channel,
  MessageList,
  MessageInput,
} from 'stream-chat-react-native';
import { StreamChat as StreamClient } from 'stream-chat';
import { getStreamConfig, getAgoraConfig } from '../../../config/streamConfig';

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

interface CircleDetailProps {
  route: {
    params: {
      circle: WealthCircle;
    };
  };
  navigation: any;
}

// Configuration
const streamConfig = getStreamConfig();
const agoraConfig = getAgoraConfig();
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function CircleDetailScreenEnhanced({ route, navigation }: CircleDetailProps) {
  const theme = useTheme();
  const { circle } = route.params;
  
  // State management
  const [posts, setPosts] = useState<CirclePost[]>([]);
  const [newPostText, setNewPostText] = useState('');
  const [selectedMedia, setSelectedMedia] = useState<{ uri: string; type: 'image' | 'video' } | null>(null);
  const [loading, setLoading] = useState(false);
  const [comments, setComments] = useState<{ [postId: string]: Comment[] }>({});
  const [compressing, setCompressing] = useState(false);
  
  // Live streaming states
  const [streamClient, setStreamClient] = useState<StreamClient | null>(null);
  const [activeStream, setActiveStream] = useState<{ host: string; channelId: string } | null>(null);
  const [isViewer, setIsViewer] = useState(false);
  const [liveModalVisible, setLiveModalVisible] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [viewerCount, setViewerCount] = useState(0);
  const [isHost, setIsHost] = useState(false);
  
  // Refs
  const socketRef = useRef<any>(null);
  const agoraEngine = useRef<any>(null);
  const videoRef = useRef<Video>(null);

  useEffect(() => {
    loadPosts();
    setupSocket();
    setupNotifications();
    initAgora();
    initStreamChat();
    navigation.setOptions({
      title: circle.name,
      headerStyle: { backgroundColor: theme.colors.primary },
      headerTintColor: theme.colors.text,
    });
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
      if (agoraEngine.current) {
        agoraEngine.current.destroy();
      }
    };
  }, [circle.id]);

  // Initialize Stream Chat
  const initStreamChat = useCallback(async () => {
    try {
      const userId = await AsyncStorage.getItem('userId') || 'demo-user';
      
      // Get Stream token from backend
      const tokenResponse = await fetch(`${API_BASE_URL}/api/stream/token?userId=${userId}`);
      if (!tokenResponse.ok) {
        throw new Error('Failed to get Stream token');
      }
      
      const { apiKey, token } = await tokenResponse.json();
      const client = StreamClient.getInstance(apiKey);
      
      await client.connectUser(
        { 
          id: userId, 
          name: 'User', 
          image: 'https://via.placeholder.com/40' 
        },
        token
      );
      setStreamClient(client);

      // Create/join channel for circle chat
      const channel = client.channel('messaging', circle.id, { 
        name: `${circle.name} Chat` 
      });
      await channel.watch();
      console.log('Stream Chat initialized for circle:', circle.id);
    } catch (err) {
      console.error('Stream Chat init error:', err);
    }
  }, [circle.id]);

  // Initialize Agora with event handlers
  const initAgora = useCallback(async () => {
    try {
      agoraEngine.current = await RtcEngine.create(agoraConfig.APP_ID);
      await agoraEngine.current.enableVideo();
      await agoraEngine.current.setChannelProfile('liveBroadcasting');

      // Event handlers for viewer count
      const eventHandler: RtcEngineEventHandler = {
        onUserJoined: (connection, remoteUid, elapsed) => {
          console.log('User joined:', remoteUid);
          setViewerCount(prev => prev + 1);
        },
        onUserOffline: (connection, remoteUid, reason) => {
          console.log('User left:', remoteUid);
          setViewerCount(prev => Math.max(0, prev - 1));
        },
        onJoinChannelSuccess: (channel, uid, elapsed) => {
          console.log('Joined channel:', channel);
        },
      };
      agoraEngine.current.addListener(eventHandler);
    } catch (err) {
      console.error('Agora init error:', err);
      Alert.alert('Error', 'Failed to initialize live streaming.');
    }
  }, []);

  // Load posts from backend
  const loadPosts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/wealth-circles/${circle.id}/posts/`);
      if (response.ok) {
        const data = await response.json();
        setPosts(data);
      }
    } catch (error) {
      console.error('Error loading posts:', error);
    } finally {
      setLoading(false);
    }
  }, [circle.id]);

  // Setup socket connection
  const setupSocket = useCallback(() => {
    socketRef.current = io(API_BASE_URL);
    
    socketRef.current.on('connect', () => {
      console.log('Connected to socket');
    });

    socketRef.current.on('new_post', (post: CirclePost) => {
      setPosts(prev => [post, ...prev]);
    });

    socketRef.current.on('new_comment', ({ postId, comment }: { postId: string; comment: Comment }) => {
      setComments(prev => ({
        ...prev,
        [postId]: [...(prev[postId] || []), comment]
      }));
    });

    socketRef.current.on('live_stream_started', ({ host, channelId }: { host: string; channelId: string }) => {
      setActiveStream({ host, channelId });
      Alert.alert('Live Now!', `${host} started a live stream in ${circle.name}. Join?`, [
        { text: 'Dismiss' },
        { text: 'Join', onPress: joinAsViewer },
      ]);
    });

    socketRef.current.on('live_stream_ended', () => {
      setActiveStream(null);
      setViewerCount(0);
    });

    socketRef.current.on('viewer_count_update', ({ count }: { count: number }) => {
      setViewerCount(count);
    });
  }, [circle.id, circle.name]);

  // Setup push notifications
  const setupNotifications = useCallback(async () => {
    if (!Device.isDevice) return;

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Failed to get push token for push notification!');
      return;
    }

    const token = (await Notifications.getExpoPushTokenAsync()).data;
    console.log('Push token:', token);

    // Register token with backend
    try {
      await fetch(`${API_BASE_URL}/api/register-push-token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: await AsyncStorage.getItem('userId') || 'demo-user',
          expoPushToken: token,
          circleId: circle.id
        })
      });
    } catch (error) {
      console.error('Error registering push token:', error);
    }
  }, [circle.id]);

  // Start live stream as host
  const startLiveStream = useCallback(async () => {
    if (!agoraEngine.current) return;
    setIsStreaming(true);
    setIsHost(true);
    setViewerCount(1); // Self as first viewer
    setLiveModalVisible(true);
    
    try {
      // Get Agora token from backend
      const tokenResponse = await fetch(`${API_BASE_URL}/api/agora/token?channel=${circle.id}&uid=0&role=publisher`);
      if (!tokenResponse.ok) {
        throw new Error('Failed to get Agora token');
      }
      
      const { appId, token, channel } = await tokenResponse.json();
      
      await agoraEngine.current.setClientRole(ClientRole.Broadcaster);
      await agoraEngine.current.joinChannel(token, channel, null, 0);
      const userId = await AsyncStorage.getItem('userId') || 'me';
      setActiveStream({ host: userId, channelId: circle.id });
      
      if (socketRef.current) {
        socketRef.current.emit('start_live_stream', { 
          circleId: circle.id, 
          host: userId 
        });
      }
    } catch (err) {
      console.error('Stream start error:', err);
      setIsStreaming(false);
      setIsHost(false);
    }
  }, [circle.id]);

  // Join as viewer
  const joinAsViewer = useCallback(async () => {
    if (!agoraEngine.current || !activeStream) return;
    setIsViewer(true);
    setIsHost(false);
    setLiveModalVisible(true);
    
    try {
      // Get Agora token from backend for viewer
      const tokenResponse = await fetch(`${API_BASE_URL}/api/agora/token?channel=${activeStream.channelId}&uid=0&role=subscriber`);
      if (!tokenResponse.ok) {
        throw new Error('Failed to get Agora token');
      }
      
      const { appId, token, channel } = await tokenResponse.json();
      
      await agoraEngine.current.setClientRole(ClientRole.Audience);
      await agoraEngine.current.joinChannel(token, channel, null, 0);
      
      if (socketRef.current) {
        socketRef.current.emit('join_live_stream', { 
          circleId: circle.id, 
          viewer: await AsyncStorage.getItem('userId') || 'viewer' 
        });
      }
    } catch (err) {
      console.error('Viewer join error:', err);
      setIsViewer(false);
    }
  }, [activeStream, circle.id]);

  // End live stream
  const endLiveStream = useCallback(async () => {
    if (!agoraEngine.current) return;
    await agoraEngine.current.leaveChannel();
    setIsStreaming(false);
    setIsViewer(false);
    setIsHost(false);
    setViewerCount(0);
    setLiveModalVisible(false);
    setActiveStream(null);
    
    if (socketRef.current) {
      socketRef.current.emit('end_live_stream', { circleId: circle.id });
    }
  }, [circle.id]);

  // Pick media (image or video)
  const pickMedia = useCallback(async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.All,
        allowsEditing: true,
        aspect: [16, 9],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        setSelectedMedia({
          uri: result.assets[0].uri,
          type: result.assets[0].type === 'video' ? 'video' : 'image'
        });
      }
    } catch (error) {
      console.error('Error picking media:', error);
    }
  }, []);

  // Compress video
  const compressVideo = useCallback(async (uri: string) => {
    try {
      setCompressing(true);
      // In a real implementation, you would use react-native-compressor
      // const compressedUri = await Video.compress(uri, { quality: 'medium' });
      // For now, return the original URI
      return uri;
    } catch (error) {
      console.error('Video compression error:', error);
      return uri;
    } finally {
      setCompressing(false);
    }
  }, []);

  // Upload media
  const uploadMedia = useCallback(async (media: { uri: string; type: 'image' | 'video' }) => {
    try {
      const formData = new FormData();
      formData.append('media', {
        uri: media.uri,
        type: media.type === 'video' ? 'video/mp4' : 'image/jpeg',
        name: `media.${media.type === 'video' ? 'mp4' : 'jpg'}`,
      } as any);

      const response = await fetch(`${API_BASE_URL}/api/upload-media/`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        const data = await response.json();
        return data.mediaUrl;
      }
      throw new Error('Upload failed');
    } catch (error) {
      console.error('Media upload error:', error);
      throw error;
    }
  }, []);

  // Submit post
  const submitPost = useCallback(async () => {
    if (!newPostText.trim() && !selectedMedia) return;

    try {
      setLoading(true);
      let mediaUrl = null;

      if (selectedMedia) {
        if (selectedMedia.type === 'video') {
          const compressedUri = await compressVideo(selectedMedia.uri);
          mediaUrl = await uploadMedia({ uri: compressedUri, type: 'video' });
        } else {
          mediaUrl = await uploadMedia(selectedMedia);
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/wealth-circles/${circle.id}/posts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      console.error('Error submitting post:', error);
      Alert.alert('Error', 'Failed to submit post');
    } finally {
      setLoading(false);
    }
  }, [newPostText, selectedMedia, circle.id, compressVideo, uploadMedia]);

  // Submit comment
  const submitComment = useCallback(async (postId: string, content: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/comments/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });

      if (response.ok) {
        const newComment = await response.json();
        setComments(prev => ({
          ...prev,
          [postId]: [...(prev[postId] || []), newComment]
        }));
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
    }
  }, []);

  // Render post item
  const renderPost = useCallback(({ item }: { item: CirclePost }) => (
    <View style={[styles.postCard, { backgroundColor: theme.colors.surface }]}>
      <View style={styles.postHeader}>
        <Image source={{ uri: item.user.avatar }} style={styles.avatar} />
        <View style={styles.postInfo}>
          <Text style={[styles.userName, { color: theme.colors.text }]}>{item.user.name}</Text>
          <Text style={[styles.timestamp, { color: theme.colors.textSecondary }]}>{item.timestamp}</Text>
        </View>
      </View>
      
      <Text style={[styles.postContent, { color: theme.colors.text }]}>{item.content}</Text>
      
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
              resizeMode="contain"
            />
          )}
        </View>
      )}
      
      <View style={styles.postActions}>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>❤️ {item.likes}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>💬 {item.comments.length}</Text>
        </TouchableOpacity>
      </View>
    </View>
  ), [theme.colors]);

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
            <RtcLocalView.Surface style={styles.localVideo} channelId={circle.id} />
          )}
          {isViewer && (
            <RtcRemoteView.Surface style={styles.remoteVideo} uid={0} channelId={circle.id} />
          )}
          {!isStreaming && !isViewer && (
            <Text style={styles.videoPlaceholder}>Waiting for host...</Text>
          )}
        </View>
        
        {/* Stream Chat Overlay */}
        {streamClient && (
          <View style={styles.chatOverlay}>
            <Channel channel={streamClient.channel('messaging', circle.id)}>
              <MessageList style={styles.messageList} />
              <MessageInput style={styles.messageInput} />
            </Channel>
          </View>
        )}
        
        {/* Viewer Count Display */}
        <View style={styles.viewerCountContainer}>
          <Text style={styles.viewerCountText}>{viewerCount} viewers</Text>
          <Text style={styles.viewerIcon}>👁️</Text>
        </View>
      </View>
    </Modal>
  );

  return (
    <KeyboardAvoidingView 
      style={[styles.container, { backgroundColor: theme.colors.background }]} 
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
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
              No posts yet. Be the first to share!
            </Text>
          </View>
        }
      />
      
      {/* Post Input */}
      <View style={[styles.inputContainer, { backgroundColor: theme.colors.surface }]}>
        <TextInput
          style={[styles.textInput, { color: theme.colors.text }]}
          placeholder="Share your thoughts..."
          placeholderTextColor={theme.colors.textSecondary}
          value={newPostText}
          onChangeText={setNewPostText}
          multiline
        />
        
        <View style={styles.inputActions}>
          <TouchableOpacity onPress={pickMedia} style={styles.mediaButton}>
            <Text style={styles.mediaButtonText}>📷</Text>
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
      
      {/* Join Live Button */}
      {activeStream && !liveModalVisible && (
        <TouchableOpacity onPress={joinAsViewer} style={styles.joinLiveButton}>
          <LinearGradient colors={['#34C759', '#30D158']} style={styles.joinLiveGradient}>
            <Text style={styles.joinLiveText}>Join Live 📺</Text>
          </LinearGradient>
        </TouchableOpacity>
      )}
      
      {renderLiveModal()}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  localVideo: {
    flex: 1,
  },
  remoteVideo: {
    flex: 1,
  },
  videoPlaceholder: {
    color: 'white',
    textAlign: 'center',
    marginTop: 100,
    fontSize: 18,
  },
  chatOverlay: {
    height: 200,
    backgroundColor: 'rgba(0,0,0,0.3)',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
  messageList: {
    flex: 1,
  },
  messageInput: {
    flex: 0,
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
});