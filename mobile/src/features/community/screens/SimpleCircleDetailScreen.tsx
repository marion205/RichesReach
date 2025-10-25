import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  Alert,
  Image,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  Dimensions,
  ActivityIndicator,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Notifications from 'expo-notifications';
// import * as Haptics from 'expo-haptics'; // Commented out for now - install with: expo install expo-haptics
import { useAnimatedStyle, useSharedValue, withSpring, withTiming } from 'react-native-reanimated';
import * as ImagePicker from 'expo-image-picker';
import { Video } from 'expo-av';
import Animated from 'react-native-reanimated';
import RichesLiveStreaming from '../../../components/RichesLiveStreaming';
import AdvancedLiveStreaming from '../../../components/AdvancedLiveStreaming';
import VoiceAI from '../../../components/VoiceAI';
import VoiceAIIntegration from '../../../components/VoiceAIIntegration';

const { height: screenHeight } = Dimensions.get('window');

interface SimpleCircleDetailProps {
  route: {
    params: {
      circle: {
        id: string;
        name: string;
        description: string;
        memberCount: number;
        category: string;
      };
    };
  };
  navigation: any;
}

// Mock posts data (updated with videos)
const mockPosts = [
  {
    id: '1',
    user: { id: 'user1', name: 'Marcus Johnson', avatar: 'https://via.placeholder.com/40/007AFF/ffffff?text=MJ' },
    content: 'Just closed a deal on a multi-family property in Atlanta! Cash flow is looking strong. #RealEstate #WealthBuilding',
    timestamp: '2h ago',
    likes: 45,
    comments: 12,
    isLiked: false,
    media: { uri: 'https://via.placeholder.com/300x200/34C759/ffffff?text=Property+Deal', type: 'image' as const },
  },
  {
    id: '2',
    user: { id: 'user2', name: 'Aisha Williams', avatar: 'https://via.placeholder.com/40/FF9500/ffffff?text=AW' },
    content: 'Quick tip: Use tax-loss harvesting before year-end to offset gains. Saved me $8K last year! What\'s your go-to tax strategy? #TaxOptimization',
    timestamp: '5h ago',
    likes: 23,
    comments: 8,
    isLiked: true,
    media: null,
  },
  {
    id: '3',
    user: { id: 'user3', name: 'Dr. Maria Rodriguez', avatar: 'https://via.placeholder.com/40/5856D6/ffffff?text=MR' },
    content: 'Bitcoin just hit $75K! Time to rebalance crypto allocations? Sharing my DeFi strategy thread below. #Crypto #Investing',
    timestamp: '1d ago',
    likes: 67,
    comments: 21,
    isLiked: false,
    media: { uri: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBun.mp4', type: 'video' as const },
  },
];

interface Media {
  uri: string;
  type: 'image' | 'video';
}

interface Post {
  id: string;
  user: { id: string; name: string; avatar: string };
  content: string;
  timestamp: string;
  likes: number;
  comments: number;
  isLiked: boolean;
  media?: Media | null;
}

export default function SimpleCircleDetailScreen({ route, navigation }: SimpleCircleDetailProps) {
  const { circle } = route.params;
  const [isLive, setIsLive] = useState(false);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [newPostText, setNewPostText] = useState('');
  const [selectedMedia, setSelectedMedia] = useState<Media | null>(null);
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [liveStreamModalVisible, setLiveStreamModalVisible] = useState(false);
  const [isLiveHost, setIsLiveHost] = useState(false);
  const [useAdvancedStreaming, setUseAdvancedStreaming] = useState(true);
  const [voiceAIModalVisible, setVoiceAIModalVisible] = useState(false);
  const [voiceAISettings, setVoiceAISettings] = useState({
    enabled: true,
    voice: 'default',
    speed: 1.0,
    emotion: 'neutral',
    autoPlay: false,
  });
  const videoRef = useRef<Video>(null);

  // Reanimated values for responsive interactions
  const likeScale = useSharedValue(1);
  const commentOpacity = useSharedValue(1);
  const mediaScale = useSharedValue(1);

  // Notification setup
  useEffect(() => {
    const setupNotifications = async () => {
      const { status } = await Notifications.getPermissionsAsync();
      if (status !== 'granted') {
        const { status: newStatus } = await Notifications.requestPermissionsAsync();
        setNotificationsEnabled(newStatus === 'granted');
      } else {
        setNotificationsEnabled(true);
      }

      // Listen for notifications
      const subscription = Notifications.addNotificationReceivedListener((notification) => {
        if (notification.request.content.data.type === 'like' || notification.request.content.data.type === 'comment') {
          // Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          onRefresh();
        }
      });

      return () => subscription.remove();
    };

    setupNotifications();
  }, []);

  // Keyboard listener
  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => setKeyboardVisible(true));
    const keyboardDidHideListener = Keyboard.addListener('keyboardDidHide', () => setKeyboardVisible(false));

    return () => {
      keyboardDidShowListener.remove();
      keyboardDidHideListener.remove();
    };
  }, []);

  // Load Posts Function (Hybrid: Real API + Mock Fallback)
  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      console.log('🔄 Attempting to load real posts from API...');
      
      // Try to get real posts from your Django backend
      const response = await fetch(`http://localhost:8000/api/wealth-circles/${circle.id}/posts/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Note: Not including auth header since we're using bypass
        },
      });

      if (response.ok) {
        const apiPosts = await response.json();
        console.log('✅ Successfully loaded real posts:', apiPosts.length);
        
        // Transform API data to match our interface
        const transformed = apiPosts.map((post: any) => ({
          id: post.id?.toString() || Date.now().toString(),
          content: post.content || post.text || 'No content',
          media: post.media ? {
            uri: post.media.url || post.media,
            type: post.media.type || 'image'
          } : undefined,
          user: {
            id: post.user?.id?.toString() || post.author_id?.toString() || '1',
            name: post.user?.name || post.author_name || 'Anonymous User',
            avatar: post.user?.avatar || post.author_avatar || 'https://via.placeholder.com/40',
          },
          timestamp: post.created_at || post.timestamp || 'Just now',
          likes: post.likes_count || post.likes || 0,
          comments: post.comments_count || post.comments || 0,
          isLiked: post.is_liked || false,
        }));
        
        setPosts(transformed);
        console.log('🎉 Using real API data for posts');
      } else {
        console.log('⚠️ API returned error, falling back to mock data');
        setPosts(mockPosts);
      }
    } catch (err) {
      console.error('❌ Error loading posts from API:', err);
      console.log('🔄 Falling back to mock data...');
      setPosts(mockPosts);
    } finally {
      setLoading(false);
    }
  }, [circle.id]);

  // Load posts on component mount
  useEffect(() => {
    loadPosts();
  }, [loadPosts]);

  // Pick Media Function (Image or Video)
  const pickMedia = async (mediaType: 'image' | 'video') => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (permission.status !== 'granted') {
      Alert.alert('Permission Required', `Please grant access to your ${mediaType}s.`);
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: mediaType === 'image' ? ImagePicker.MediaTypeOptions.Images : ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
      videoMaxDuration: 60,
    });

    if (!result.canceled && result.assets?.[0]) {
      const asset = result.assets[0];
      if (asset.type === (mediaType === 'image' ? 'image' : 'video')) {
        setSelectedMedia({ uri: asset.uri, type: mediaType });
        mediaScale.value = withSpring(0.95, {}, () => {
          mediaScale.value = withTiming(1);
        });
        // Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
    }
  };

  const removeMedia = () => {
    setSelectedMedia(null);
        // Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const toggleLike = (postId: string) => {
    likeScale.value = withSpring(1.4, {}, () => {
      likeScale.value = withTiming(1);
    });
    // Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    setPosts(prev => prev.map(post =>
      post.id === postId
        ? { ...post, isLiked: !post.isLiked, likes: post.isLiked ? post.likes - 1 : post.likes + 1 }
        : post
    ));

    // Simulate notification for others
    if (!posts.find(p => p.id === postId)?.isLiked) {
      Notifications.scheduleNotificationAsync({
        content: {
          title: 'New Like!',
          body: `Someone liked your post in ${circle.name}`,
          data: { type: 'like' },
        },
        trigger: null,
      });
    }
  };

  const onPostPress = (postId: string) => {
    commentOpacity.value = withTiming(0.5, { duration: 150 }, () => {
      commentOpacity.value = withTiming(1, { duration: 150 });
    });
        // Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    Alert.alert('Comments', `Opening ${posts.find(p => p.id === postId)?.comments || 0} comments for post ${postId}`);
  };

  const onRefresh = () => {
    setRefreshing(true);
    // Haptics.notificationAsync(Haptics.NotificationFeedbackType.Light);
    loadPosts().finally(() => {
      setRefreshing(false);
    });
  };

  const submitPost = async () => {
    if (!newPostText.trim() && !selectedMedia) return;
    setSubmitting(true);
    // Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

    setTimeout(() => {
      const newPost: Post = {
        id: Date.now().toString(),
        user: { id: 'currentUser', name: 'You', avatar: 'https://via.placeholder.com/40/007AFF/ffffff?text=You' },
        content: newPostText,
        timestamp: 'Just now',
        likes: 0,
        comments: 0,
        isLiked: false,
        media: selectedMedia || undefined,
      };
      setPosts(prev => [newPost, ...prev]);
      setNewPostText('');
      setSelectedMedia(null);
      setSubmitting(false);
      Keyboard.dismiss();

      Notifications.scheduleNotificationAsync({
        content: {
          title: 'New Post!',
          body: `You posted in ${circle.name}`,
          data: { type: 'post' },
        },
        trigger: null,
      });
    }, 1000);
  };

  const animatedLikeStyle = useAnimatedStyle(() => ({
    transform: [{ scale: likeScale.value }],
  }));

  const animatedCommentStyle = useAnimatedStyle(() => ({
    opacity: commentOpacity.value,
  }));

  const animatedMediaStyle = useAnimatedStyle(() => ({
    transform: [{ scale: mediaScale.value }],
  }));

  const renderPost = ({ item }: { item: Post }) => (
    <TouchableOpacity style={styles.postContainer} onPress={() => onPostPress(item.id)} activeOpacity={0.7}>
      {/* User Header */}
      <View style={styles.postHeader}>
        <Image source={{ uri: item.user.avatar }} style={styles.userAvatar} />
        <View style={styles.userInfo}>
          <Text style={styles.userName}>{item.user.name}</Text>
          <Text style={styles.postTimestamp}>{item.timestamp}</Text>
        </View>
      </View>

      {/* Content */}
      <Text style={styles.postContent}>{item.content}</Text>

      {/* Media */}
      {item.media && (
        <Animated.View style={animatedMediaStyle}>
          {item.media.type === 'image' ? (
            <Image source={{ uri: item.media.uri }} style={styles.postMedia} />
          ) : (
            <Video
              ref={videoRef}
              source={{ uri: item.media.uri }}
              style={styles.postMedia}
              useNativeControls
              isMuted
              shouldPlay={false}
            />
          )}
        </Animated.View>
      )}

      {/* Interactions */}
      <View style={styles.interactions}>
        <Animated.View style={[styles.interactionButton, animatedLikeStyle]}>
          <TouchableOpacity onPress={() => toggleLike(item.id)}>
            <Text style={[styles.interactionText, item.isLiked && styles.likedText]}>Like {item.likes}</Text>
          </TouchableOpacity>
        </Animated.View>
        <Animated.View style={[styles.interactionButton, animatedCommentStyle]}>
          <TouchableOpacity>
            <Text style={styles.interactionText}>Comment {item.comments}</Text>
          </TouchableOpacity>
        </Animated.View>
        <TouchableOpacity style={styles.interactionButton}>
          <Text style={styles.interactionText}>Share</Text>
        </TouchableOpacity>
      </View>

      {/* Voice AI Response */}
      {voiceAISettings.enabled && (
        <View style={styles.voiceAIContainer}>
          <Text style={styles.voiceAILabel}>AI Financial Advisor</Text>
          <VoiceAI
            text={generateAIResponse(item.content)}
            voice={voiceAISettings.voice as any}
            speed={voiceAISettings.speed}
            emotion={voiceAISettings.emotion as any}
            autoPlay={voiceAISettings.autoPlay}
            style={styles.voiceAIComponent}
          />
        </View>
      )}

      <View style={styles.divider} />
    </TouchableOpacity>
  );

  const startLiveStream = () => {
    setIsLiveHost(true);
    setLiveStreamModalVisible(true);
    console.log('🎥 Starting RichesReach live stream for circle:', circle.name);
  };

  const joinLiveStream = () => {
    setIsLiveHost(false);
    setLiveStreamModalVisible(true);
    console.log('📺 Joining RichesReach live stream for circle:', circle.name);
  };

  const endLiveStream = () => {
    setLiveStreamModalVisible(false);
    setIsLiveHost(false);
    console.log('🔴 Live stream ended');
  };

  const closeLiveStreamModal = () => {
    setLiveStreamModalVisible(false);
    setIsLiveHost(false);
  };

  // Voice AI Functions
  const openVoiceAISettings = () => {
    setVoiceAIModalVisible(true);
  };

  const closeVoiceAIModal = () => {
    setVoiceAIModalVisible(false);
  };

  const handleVoiceSettingsChange = (settings: any) => {
    setVoiceAISettings(settings);
  };

  const generateAIResponse = async (postContent: string): Promise<string> => {
    // Simulate AI response generation
    const responses = [
      `Based on your post about "${postContent.slice(0, 30)}...", here's my analysis: The market trends suggest a positive outlook for this sector. Consider diversifying your portfolio to manage risk effectively.`,
      `Great insights in your post! From a financial perspective, this aligns with current market conditions. I recommend monitoring key indicators and adjusting your strategy accordingly.`,
      `Your post highlights important market dynamics. As your AI financial advisor, I suggest reviewing your asset allocation and considering long-term growth opportunities.`,
      `Excellent analysis! This perspective on the market is valuable. I'd recommend focusing on fundamental analysis and maintaining a balanced approach to investing.`,
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
      <View style={styles.innerContainer}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>{circle.name}</Text>
            <Text style={styles.memberCount}>{circle.memberCount} members • {circle.category}</Text>
          </View>
          <TouchableOpacity style={styles.headerAction}>
            <Text style={styles.headerActionText}>...</Text>
          </TouchableOpacity>
        </View>

        {/* Circle Description */}
        <ScrollView style={styles.descriptionScroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.circleDescription}>{circle.description}</Text>
        </ScrollView>

        {/* Quick Actions Bar */}
        <View style={styles.actionsBar}>
          {!isLive ? (
            <TouchableOpacity onPress={startLiveStream} style={styles.actionButton}>
              <LinearGradient colors={['#FF3B30', '#FF9500']} style={styles.actionGradient}>
                <Text style={styles.actionText}>Go Live</Text>
              </LinearGradient>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity onPress={endLiveStream} style={styles.actionButton}>
              <LinearGradient colors={['#FF3B30', '#FF6B6B']} style={styles.actionGradient}>
                <Text style={styles.actionText}>End Live</Text>
              </LinearGradient>
            </TouchableOpacity>
          )}
          <TouchableOpacity onPress={joinLiveStream} style={styles.actionButton}>
            <LinearGradient colors={['#34C759', '#30D158']} style={styles.actionGradient}>
              <Text style={styles.actionText}>Join Live</Text>
            </LinearGradient>
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={() => setUseAdvancedStreaming(!useAdvancedStreaming)}
          >
            <LinearGradient 
              colors={useAdvancedStreaming ? ['#FF9500', '#FFCC02'] : ['#007AFF', '#5856D6']} 
              style={styles.actionGradient}
            >
              <Text style={styles.actionText}>
                {useAdvancedStreaming ? 'Advanced' : 'Basic'}
              </Text>
            </LinearGradient>
          </TouchableOpacity>
          <TouchableOpacity onPress={openVoiceAISettings} style={styles.actionButton}>
            <LinearGradient colors={['#4ECDC4', '#44A08D']} style={styles.actionGradient}>
              <Text style={styles.actionText}>Voice AI</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {/* Posts Feed */}
        <FlatList
          data={posts}
          renderItem={renderPost}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#007AFF" />
          }
          contentContainerStyle={styles.postsList}
          ListHeaderComponent={
            <Text style={styles.feedHeader}>Latest Posts</Text>
          }
          ListEmptyComponent={
            loading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={styles.loadingText}>Loading posts...</Text>
              </View>
            ) : (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No posts yet</Text>
                <Text style={styles.emptySubtext}>Be the first to share something!</Text>
              </View>
            )
          }
          ListFooterComponent={<View style={styles.footerSpacer} />}
        />
      </View>

      {/* Post Creation Form */}
      {!keyboardVisible && (
        <View style={styles.composeContainer}>
          <TouchableOpacity style={styles.composeAvatar}>
            <Image source={{ uri: 'https://via.placeholder.com/40/007AFF/ffffff?text=You' }} style={styles.composeAvatarImage} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.composeInputContainer} onPress={() => setKeyboardVisible(true)}>
            <Text style={styles.composePlaceholder}>What's happening in {circle.name}?</Text>
          </TouchableOpacity>
          <View style={styles.composeMediaActions}>
            <TouchableOpacity style={styles.mediaAction} onPress={() => pickMedia('image')}>
              <Text style={styles.mediaActionText}>Photo</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.mediaAction} onPress={() => pickMedia('video')}>
              <Text style={styles.mediaActionText}>Video</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Keyboard-Aware Post Form */}
      {keyboardVisible && (
        <View style={styles.keyboardForm}>
          <TextInput
            style={styles.postInput}
            placeholder={`Share your thoughts in ${circle.name}...`}
            value={newPostText}
            onChangeText={setNewPostText}
            multiline
            maxLength={280}
            onSubmitEditing={submitPost}
            blurOnSubmit={false}
          />
          {selectedMedia && (
            <View style={styles.mediaPreviewContainer}>
              {selectedMedia.type === 'image' ? (
                <Animated.Image source={{ uri: selectedMedia.uri }} style={[styles.mediaPreview, animatedMediaStyle]} />
              ) : (
                <Animated.View style={[styles.mediaPreviewContainerVideo, animatedMediaStyle]}>
                  <Video
                    ref={videoRef}
                    source={{ uri: selectedMedia.uri }}
                    style={styles.mediaPreviewVideo}
                    useNativeControls
                    isMuted
                    shouldPlay
                  />
                </Animated.View>
              )}
              <TouchableOpacity style={styles.removeMediaBtn} onPress={removeMedia}>
                <Text style={styles.removeMediaText}>×</Text>
              </TouchableOpacity>
            </View>
          )}
          <TouchableOpacity 
            style={[styles.submitButton, (!newPostText.trim() && !selectedMedia || submitting) && styles.submitDisabled]} 
            onPress={submitPost}
            disabled={!newPostText.trim() && !selectedMedia || submitting}
          >
            {submitting ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <Text style={styles.submitText}>Post</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* RichesReach Live Streaming Modal */}
      {useAdvancedStreaming ? (
        <AdvancedLiveStreaming
          visible={liveStreamModalVisible}
          onClose={closeLiveStreamModal}
          circleId={circle.id}
          isHost={isLiveHost}
          circleName={circle.name}
        />
      ) : (
        <RichesLiveStreaming
          visible={liveStreamModalVisible}
          onClose={closeLiveStreamModal}
          circleId={circle.id}
          isHost={isLiveHost}
          circleName={circle.name}
        />
      )}

      {/* Voice AI Integration Modal */}
      <VoiceAIIntegration
        visible={voiceAIModalVisible}
        onClose={closeVoiceAIModal}
        text="Your portfolio is performing well today. Consider diversifying your investments for better risk management."
        onVoiceSettingsChange={handleVoiceSettingsChange}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  innerContainer: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e8ed',
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  backButtonText: {
    fontSize: 20,
    color: '#1d9bf0',
    fontWeight: 'bold',
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#14171a',
  },
  memberCount: {
    fontSize: 14,
    color: '#657786',
    marginTop: 2,
  },
  headerAction: {
    padding: 8,
  },
  headerActionText: {
    fontSize: 18,
    color: '#657786',
  },
  descriptionScroll: {
    padding: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e8ed',
  },
  circleDescription: {
    fontSize: 16,
    lineHeight: 22,
    color: '#14171a',
  },
  actionsBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e8ed',
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 4,
  },
  actionGradient: {
    paddingVertical: 12,
    borderRadius: 20,
    alignItems: 'center',
  },
  actionText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  feedHeader: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#14171a',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e8ed',
  },
  postsList: {
    flex: 1,
  },
  postContainer: {
    backgroundColor: '#ffffff',
    marginVertical: 4,
    marginHorizontal: 8,
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  userAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#14171a',
  },
  postTimestamp: {
    fontSize: 13,
    color: '#657786',
  },
  postContent: {
    fontSize: 16,
    lineHeight: 20,
    color: '#14171a',
    marginBottom: 8,
  },
  postMedia: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginBottom: 12,
  },
  interactions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  interactionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 4,
  },
  interactionText: {
    fontSize: 14,
    color: '#657786',
    marginLeft: 4,
  },
  likedText: {
    color: '#e0245e',
  },
  divider: {
    height: 1,
    backgroundColor: '#e1e8ed',
    marginTop: 12,
  },
  footerSpacer: {
    height: 100,
  },
  composeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e1e8ed',
  },
  composeAvatar: {
    marginRight: 12,
  },
  composeAvatarImage: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  composeInputContainer: {
    flex: 1,
    backgroundColor: '#f7f9fa',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    justifyContent: 'center',
  },
  composePlaceholder: {
    fontSize: 16,
    color: '#657786',
  },
  composeMediaActions: {
    flexDirection: 'row',
  },
  mediaAction: {
    marginLeft: 8,
    padding: 8,
  },
  mediaActionText: {
    fontSize: 20,
    color: '#1d9bf0',
  },
  keyboardForm: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e1e8ed',
  },
  postInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    borderRadius: 20,
    paddingHorizontal: 16,
    backgroundColor: '#f7f9fa',
    fontSize: 16,
    marginRight: 8,
  },
  submitButton: {
    backgroundColor: '#1d9bf0',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  submitDisabled: {
    backgroundColor: '#cbd5e1',
  },
  submitText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  mediaPreviewContainer: {
    position: 'absolute',
    bottom: 80,
    right: 16,
    width: 80,
    height: 80,
    borderRadius: 8,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  mediaPreview: {
    width: '100%',
    height: '100%',
  },
  mediaPreviewContainerVideo: {
    width: 80,
    height: 80,
  },
  mediaPreviewVideo: {
    width: '100%',
    height: '100%',
  },
  removeMediaBtn: {
    position: 'absolute',
    top: 2,
    right: 2,
    backgroundColor: 'rgba(0,0,0,0.6)',
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeMediaText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
  },
  // Voice AI Styles
  voiceAIContainer: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#F0FDFC',
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#4ECDC4',
  },
  voiceAILabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4ECDC4',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  voiceAIComponent: {
    marginVertical: 0,
    backgroundColor: 'transparent',
  },
});