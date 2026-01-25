import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
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
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Notifications from 'expo-notifications';
// import * as Haptics from 'expo-haptics'; // Commented out for now - install with: expo install expo-haptics
import { useAnimatedStyle, useSharedValue, withSpring, withTiming } from 'react-native-reanimated';
import * as ImagePicker from 'expo-image-picker';
import { Video } from 'expo-av';
import Animated from 'react-native-reanimated';
import LiveStreamCamera from '../../../components/LiveStreamCamera';
import VoiceAI from '../../../components/VoiceAI';
import VoiceAIIntegration from '../../../components/VoiceAIIntegration';
import { API_BASE_URL } from '../../../config/api';
import { debounce } from '../../../utils/debounce';
import { imageCache } from '../../../utils/imageCache';

// Create a safe logger that always works, even if the import fails
const createSafeLogger = () => {
  let loggerBase: any = null;
  
  try {
    const loggerModule = require('../../../utils/logger');
    loggerBase = loggerModule?.default || loggerModule?.logger || loggerModule;
  } catch (e) {
    // Import failed, use console fallback
  }
  
  const safeConsole = typeof console !== 'undefined' ? console : {
    log: () => {},
    warn: () => {},
    error: () => {},
    info: () => {},
    debug: () => {},
  };
  
  return {
    log: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.log === 'function') {
          loggerBase.log(...args);
        } else {
          safeConsole.log(...args);
        }
      } catch (e) {
        safeConsole.log(...args);
      }
    },
    warn: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.warn === 'function') {
          loggerBase.warn(...args);
        } else {
          safeConsole.warn(...args);
        }
      } catch (e) {
        safeConsole.warn(...args);
      }
    },
    error: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.error === 'function') {
          loggerBase.error(...args);
        } else {
          safeConsole.error(...args);
        }
      } catch (e) {
        safeConsole.error(...args);
      }
    },
    info: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.info === 'function') {
          loggerBase.info(...args);
        } else {
          safeConsole.info(...args);
        }
      } catch (e) {
        safeConsole.info(...args);
      }
    },
    debug: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.debug === 'function') {
          loggerBase.debug(...args);
        } else {
          safeConsole.debug(...args);
        }
      } catch (e) {
        safeConsole.debug(...args);
      }
    },
  };
};

// Initialize logger immediately - this ensures it's always defined
let logger = createSafeLogger();

// Final safety check - ensure logger is always a valid object
if (!logger || typeof logger !== 'object') {
  logger = {
    log: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.log) {
          console.log(...args);
        }
      } catch (e) {}
    },
    warn: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.warn) {
          console.warn(...args);
        }
      } catch (e) {}
    },
    error: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.error) {
          console.error(...args);
        }
      } catch (e) {}
    },
    info: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.info) {
          console.info(...args);
        }
      } catch (e) {}
    },
    debug: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.debug) {
          console.debug(...args);
        }
      } catch (e) {}
    },
  };
}

// Ensure all methods exist
if (!logger.log) logger.log = () => {};
if (!logger.warn) logger.warn = () => {};
if (!logger.error) logger.error = () => {};
if (!logger.info) logger.info = () => {};
if (!logger.debug) logger.debug = () => {};

// Cached Image Component for optimized rendering
const CachedImage = React.memo<{ uri: string; style: any }>(({ uri, style }) => {
  const [imageUri, setImageUri] = useState<string | null>(null);

  useEffect(() => {
    const loadImage = async () => {
      if (!uri) return;
      
      // Check cache first
      const cached = await imageCache.getCachedData<string>(`image_${uri}`);
      if (cached) {
        setImageUri(cached);
        return;
      }

      // Preload and cache
      try {
        await imageCache.preloadImage(uri);
        setImageUri(uri);
        await imageCache.cacheData(`image_${uri}`, uri);
      } catch (error) {
        logger.warn('Failed to load image:', uri);
        setImageUri(uri); // Fallback to direct URI
      }
    };

    loadImage();
  }, [uri]);

  if (!imageUri) {
    return <View style={style} />;
  }

  return <Image source={{ uri: imageUri }} style={style} />;
});

CachedImage.displayName = 'CachedImage';

const { height: screenHeight } = Dimensions.get('window');

interface Circle {
  id: string;
  name: string;
  description: string;
  memberCount?: number;
  member_count?: number;
  category?: string;
  cultural_focus?: string;
  [key: string]: unknown;
}

interface NavigationProp {
  navigate: (screen: string, params?: Record<string, unknown>) => void;
  goBack: () => void;
  [key: string]: unknown;
}

interface SimpleCircleDetailProps {
  route: {
    params: {
      circle: Circle;
    };
  };
  navigation: NavigationProp;
}

// Mock posts data for demo - BIPOC Investment Strategies focused
const mockPosts = [
  {
    id: '1',
    user: { id: 'user1', name: 'Marcus Johnson', avatar: 'https://via.placeholder.com/40/007AFF/ffffff?text=MJ' },
    content: 'Just closed a deal on a multi-family property in Atlanta! Cash flow is looking strong. Building generational wealth one property at a time. #RealEstate #WealthBuilding #BIPOCInvesting',
    timestamp: '2h ago',
    likes: 45,
    comments: 12,
    isLiked: false,
    media: { uri: 'https://via.placeholder.com/300x200/34C759/ffffff?text=Property+Deal', type: 'image' as const },
  },
  {
    id: '2',
    user: { id: 'user2', name: 'Aisha Williams', avatar: 'https://via.placeholder.com/40/FF9500/ffffff?text=AW' },
    content: 'Quick tip: Use tax-loss harvesting before year-end to offset gains. Saved me $8K last year! What\'s your go-to tax strategy? #TaxOptimization #FinancialLiteracy',
    timestamp: '5h ago',
    likes: 23,
    comments: 8,
    isLiked: true,
    media: null,
  },
  {
    id: '3',
    user: { id: 'user3', name: 'Dr. Maria Rodriguez', avatar: 'https://via.placeholder.com/40/5856D6/ffffff?text=MR' },
    content: 'Diversifying into emerging markets has been game-changing for my portfolio. Sharing my strategy for investing in African and Latin American markets. #GlobalInvesting #Diversification',
    timestamp: '1d ago',
    likes: 67,
    comments: 21,
    isLiked: false,
    media: null,
  },
  {
    id: '4',
    user: { id: 'user4', name: 'James Chen', avatar: 'https://via.placeholder.com/40/34C759/ffffff?text=JC' },
    content: 'Building a community investment fund with 20 other BIPOC investors. We\'re pooling resources to access deals that were previously out of reach. Power in numbers! 💪 #CommunityWealth #CooperativeInvesting',
    timestamp: '3d ago',
    likes: 89,
    comments: 34,
    isLiked: false,
    media: null,
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
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [newPostText, setNewPostText] = useState('');
  const [selectedMedia, setSelectedMedia] = useState<Media | null>(null);
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [liveStreamModalVisible, setLiveStreamModalVisible] = useState(false);
  const [isLiveHost, setIsLiveHost] = useState(false);
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

  // Load Posts Function (Hybrid: Real API + Mock Fallback with Timeout) - with pagination
  const loadPosts = useCallback(async (pageNum: number = 1, append: boolean = false) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    try {
      logger.log('🔄 Attempting to load real posts from API...');
      
      // Add timeout to prevent infinite loading
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 5000)
      );
      
      // Try to get real posts from your Django backend with pagination
      const postsUrl = `${API_BASE_URL}/api/wealth-circles/${circle.id}/posts/?page=${pageNum}&limit=10`;
      logger.log('📝 [DEBUG] Fetching posts from:', postsUrl);
      logger.log('📝 [DEBUG] API_BASE_URL:', API_BASE_URL);
      logger.log('📝 [DEBUG] Circle ID:', circle.id);
      logger.log('📝 [DEBUG] Page:', pageNum);
      
      const fetchPromise = fetch(postsUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Note: Not including auth header since we're using bypass
        },
      });

      const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

      logger.log('📝 [DEBUG] Posts response status:', response.status, response.statusText);
      logger.log('📝 [DEBUG] Posts response ok:', response.ok);

      if (response.ok) {
        const apiPosts = await response.json();
        logger.log('✅ Successfully loaded real posts:', apiPosts.length);
        
        // Only use real data if we have posts
        if (apiPosts && apiPosts.length > 0) {
          // Transform API data to match our interface
          interface ApiPost {
            id?: string | number;
            content?: string;
            text?: string;
            media?: { url?: string; type?: string } | string | null;
            user?: { id?: string | number; name?: string; avatar?: string } | null;
            author_id?: string | number;
            author_name?: string;
            author_avatar?: string;
            created_at?: string;
            timestamp?: string;
            likes_count?: number;
            likes?: number;
            comments_count?: number;
            comments?: number;
            is_liked?: boolean;
            [key: string]: unknown;
          }
          const transformed = (apiPosts as ApiPost[]).map((post) => ({
            id: post.id?.toString() || Date.now().toString(),
            content: post.content || post.text || 'No content',
            media: post.media ? {
              uri: typeof post.media === 'object' ? (post.media.url || '') : String(post.media),
              type: typeof post.media === 'object' ? (post.media.type || 'image') : 'image'
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
          
          if (append) {
            setPosts(prev => [...prev, ...transformed] as Post[]);
          } else {
            setPosts(transformed as Post[]);
          }
          setHasMore(transformed.length === 10); // If we got 10 posts, there might be more
          logger.log('🎉 Using real API data for posts');
        } else {
          // No posts from API, use mock data for demo
          if (!append) {
            logger.log('📝 No posts from API, using mock data for demo');
            setPosts(mockPosts);
          }
          setHasMore(false);
        }
      } else {
        const errorText = await response.text().catch(() => '');
        logger.warn('⚠️ [DEBUG] Posts API returned error');
        logger.warn('⚠️ [DEBUG] Status:', response.status, response.statusText);
        logger.warn('⚠️ [DEBUG] Response body:', errorText.substring(0, 300));
        logger.log('⚠️ API returned error, falling back to mock data');
        setPosts(mockPosts);
      }
    } catch (err: any) {
      logger.error('❌ [DEBUG] Error loading posts from API');
      logger.error('❌ [DEBUG] Error name:', err?.name);
      logger.error('❌ [DEBUG] Error message:', err?.message);
      logger.error('❌ [DEBUG] Error stack:', err?.stack?.substring(0, 300));
      logger.error('❌ Error loading posts from API:', err);
      logger.log('🔄 Falling back to mock data for demo...');
      // Always set mock posts for demo if API fails
      setPosts(mockPosts);
    } finally {
      // Always set loading to false, even if there was an error
      setLoading(false);
      setLoadingMore(false);
    }
  }, [circle.id]);

  // Debounced version of loadPosts to prevent excessive API calls
  const debouncedLoadPosts = useMemo(
    () => debounce((pageNum: number, append: boolean) => {
      loadPosts(pageNum, append);
    }, 300),
    [loadPosts]
  );

  // Load more posts (lazy loading)
  const loadMorePosts = useCallback(() => {
    if (!loadingMore && hasMore && !loading) {
      const nextPage = page + 1;
      setPage(nextPage);
      loadPosts(nextPage, true);
    }
  }, [page, loadingMore, hasMore, loading, loadPosts]);

  // Load posts on component mount
  useEffect(() => {
    setPage(1);
    setHasMore(true);
    loadPosts(1, false);
  }, [circle.id]); // Only reload when circle.id changes

  // Debug: log post shape to catch invalid children
  useEffect(() => {
    try {
      if (posts && posts.length) {
        logger.log('🔍 Posts Data Dump:', JSON.stringify(posts.slice(0, 2), null, 2));
        logger.log('🚨 First Post Keys:', Object.keys(posts[0] || {}));
        logger.log('🚨 User Shape:', posts[0]?.user);
      }
    } catch {}
  }, [posts]);

  // Pick Media Function (Image or Video)
  const pickMedia = async (mediaType: 'image' | 'video') => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (permission.status !== 'granted') {
      Alert.alert('Permission Required', `Please grant access to your ${mediaType}s.`);
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: mediaType === 'image' ? 'images' : 'videos',
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

  const renderPost = ({ item }: { item: Post }) => {
    interface PostWithFlexibleFields {
      id?: string | number;
      user?: { name?: string } | string;
      content?: string | object;
      timestamp?: string | Date;
      likes?: number | { count?: number };
      comments?: number | { count?: number };
      media?: any;
      [key: string]: unknown;
    }
    const flexibleItem = item as unknown as PostWithFlexibleFields;
    const safeUser = typeof flexibleItem.user === 'object'
      ? flexibleItem.user?.name || 'Anonymous'
      : String(flexibleItem.user ?? 'Unknown');
    const safeContent = typeof flexibleItem.content === 'object'
      ? JSON.stringify(flexibleItem.content).slice(0, 200)
      : String(flexibleItem.content ?? '');
    const safeTimestamp = flexibleItem.timestamp instanceof Date
      ? flexibleItem.timestamp.toLocaleString()
      : new Date(String(flexibleItem.timestamp || Date.now())).toLocaleString();
    const safeLikes = typeof flexibleItem.likes === 'number'
      ? String(flexibleItem.likes)
      : String((flexibleItem.likes && typeof flexibleItem.likes === 'object' ? flexibleItem.likes.count : undefined) ?? 0);
    const safeComments = typeof flexibleItem.comments === 'number'
      ? String(flexibleItem.comments)
      : String((flexibleItem.comments && typeof flexibleItem.comments === 'object' ? flexibleItem.comments.count : undefined) ?? 0);

    return (
    <TouchableOpacity style={styles.postContainer} onPress={() => onPostPress(item.id)} activeOpacity={0.7}>
      {/* User Header */}
      <View style={styles.postHeader}>
        <CachedImage uri={item.user.avatar} style={styles.userAvatar} />
        <View style={styles.userInfo}>
          <Text style={styles.userName}>{safeUser}</Text>
          <Text style={styles.postTimestamp}>{safeTimestamp}</Text>
        </View>
      </View>

      {/* Content */}
      <Text style={styles.postContent}>{safeContent}</Text>

      {/* Media */}
      {item.media && (
        <Animated.View style={animatedMediaStyle}>
          {item.media.type === 'image' ? (
            <CachedImage uri={item.media.uri} style={styles.postMedia} />
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
            <Text style={[styles.interactionText, item.isLiked && styles.likedText]}>Like {safeLikes}</Text>
          </TouchableOpacity>
        </Animated.View>
        <Animated.View style={[styles.interactionButton, animatedCommentStyle]}>
          <TouchableOpacity>
            <Text style={styles.interactionText}>Comment {safeComments}</Text>
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
            text={generateAIResponse(safeContent)}
            voice={String(voiceAISettings.voice) as 'default' | 'finance_expert' | 'friendly_advisor' | 'confident_analyst'}
            speed={voiceAISettings.speed}
            emotion={String(voiceAISettings.emotion) as 'neutral' | 'confident' | 'friendly' | 'analytical' | 'encouraging'}
            autoPlay={voiceAISettings.autoPlay}
            style={styles.voiceAIComponent}
          />
        </View>
      )}

      <View style={styles.divider} />
    </TouchableOpacity>
  );
  };

  const startLiveStream = () => {
    setIsLiveHost(true);
    setLiveStreamModalVisible(true);
    logger.log('🎥 Starting RichesReach live stream for circle:', circle.name);
  };

  const joinLiveStream = () => {
    setIsLiveHost(false);
    setLiveStreamModalVisible(true);
    logger.log('📺 Joining RichesReach live stream for circle:', circle.name);
  };

  const endLiveStream = () => {
    setLiveStreamModalVisible(false);
    setIsLiveHost(false);
    logger.log('🔴 Live stream ended');
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

  interface VoiceSettings {
    enabled?: boolean;
    voice?: string;
    speed?: number;
    emotion?: string;
    autoPlay?: boolean;
    [key: string]: unknown;
  }
  const handleVoiceSettingsChange = (settings: VoiceSettings): void => {
    setVoiceAISettings({
      enabled: settings.enabled ?? voiceAISettings.enabled,
      voice: settings.voice ?? voiceAISettings.voice,
      speed: settings.speed ?? voiceAISettings.speed,
      emotion: settings.emotion ?? voiceAISettings.emotion,
      autoPlay: settings.autoPlay ?? voiceAISettings.autoPlay,
    });
  };

  const generateAIResponse = (postContent: string): string => {
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
    <KeyboardAvoidingView testID="simple-circle-detail-screen" style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
      <View style={styles.innerContainer}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity testID="back-button" onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>{String(circle.name)}</Text>
            <Text style={styles.memberCount}>{String(circle.memberCount || circle.member_count || 0)} members • {String(circle.category || circle.cultural_focus || '')}</Text>
          </View>
          <TouchableOpacity style={styles.headerAction}>
            <Text style={styles.headerActionText}>...</Text>
          </TouchableOpacity>
        </View>

        {/* Circle Description */}
        <ScrollView style={styles.descriptionScroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.circleDescription}>{String(circle.description)}</Text>
        </ScrollView>

        {/* Quick Actions Bar */}
        <View style={styles.actionsBar}>
          {!isLive ? (
            <TouchableOpacity testID="go-live-button" onPress={startLiveStream} style={styles.actionButton}>
              <LinearGradient colors={['#FF3B30', '#FF9500']} style={styles.actionGradient}>
                <Text style={styles.actionText}>Go Live</Text>
              </LinearGradient>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity testID="end-live-button" onPress={endLiveStream} style={styles.actionButton}>
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
          <TouchableOpacity onPress={openVoiceAISettings} style={styles.actionButton}>
            <LinearGradient colors={['#4ECDC4', '#44A08D']} style={styles.actionGradient}>
              <Text style={styles.actionText}>Voice AI</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {/* Posts Feed */}
        <FlatList
          testID="posts-list"
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
            ) : posts.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No posts yet</Text>
                <Text style={styles.emptySubtext}>Be the first to share something!</Text>
              </View>
            ) : null
          }
          ListFooterComponent={
            loadingMore ? (
              <View style={{ padding: 20, alignItems: 'center' }}>
                <ActivityIndicator size="small" color="#007AFF" />
              </View>
            ) : (
              <View style={styles.footerSpacer} />
            )
          }
          onEndReached={loadMorePosts}
          onEndReachedThreshold={0.5}
          removeClippedSubviews={true}
          maxToRenderPerBatch={10}
          windowSize={10}
          initialNumToRender={5}
          updateCellsBatchingPeriod={50}
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
            testID="message-input"
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
            testID="send-message-button"
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

      {/* RichesReach Live Streaming Modal - Using LiveStreamCamera for front camera preview */}
      <Modal
        visible={liveStreamModalVisible}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={closeLiveStreamModal}
      >
        <LiveStreamCamera
          circleId={circle.id}
          circleName={circle.name}
          visible={liveStreamModalVisible}
          onStartLiveStream={async ({ circleId, camera }) => {
            logger.log('🎥 [SimpleCircleDetailScreen] Starting live stream for circle:', circleId);
            setIsLive(true);
            // Add your actual streaming logic here
            // For now, just mark as live
          }}
          onStopLiveStream={async ({ circleId, camera }) => {
            logger.log('🛑 [SimpleCircleDetailScreen] Stopping live stream for circle:', circleId);
            setIsLive(false);
            setLiveStreamModalVisible(false);
            // Add your actual streaming stop logic here
          }}
          onClose={closeLiveStreamModal}
        />
      </Modal>

      {/* Voice AI Integration Modal */}
      <VoiceAIIntegration
        visible={voiceAIModalVisible}
        onClose={closeVoiceAIModal}
        text="Your portfolio is performing well today. Consider diversifying your investments for better risk management."
        onVoiceSettingsChange={handleVoiceSettingsChange as any}
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