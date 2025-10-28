import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  StyleSheet,
  Dimensions,
  Alert,
  ActivityIndicator,
  FlatList,
  Platform,
} from 'react-native';
import { Video, ResizeMode, AVPlaybackStatus } from 'expo-av';
import * as Haptics from 'expo-haptics';
import { NewsItem } from '../types/news';
import NewsService from '../services/NewsService';

const { width, height } = Dimensions.get('window');

const NewsFeed: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [videoDurations, setVideoDurations] = useState<{[key: string]: number}>({});
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const videoRefs = useRef<{[key: string]: any}>({});

  const newsService = useMemo(() => new NewsService(), []);

  useEffect(() => {
    loadNewsByCategory('all');
  }, []);

  useEffect(() => {
    if (selectedCategory) loadNewsByCategory(selectedCategory);
  }, [selectedCategory]);

  const loadNewsByCategory = async (category: string) => {
    try {
      loading ? setLoading(true) : setRefreshing(true);
      let news: NewsItem[] = [];
      switch (category) {
        case 'crypto':
          news = await newsService.getCryptoNews();
          break;
        case 'earnings':
          news = await newsService.getEarningsNews();
          break;
        case 'market':
          news = await newsService.getMarketNews();
          break;
        case 'tech':
        case 'politics':
        case 'all':
        default:
          news = await newsService.getFinancialNews();
          break;
      }
      setNewsItems(news);
    } catch (e) {
      console.error('Error loading news by category:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const categories = [
    { key: 'all', label: 'All', icon: '📰' },
    { key: 'market', label: 'Market', icon: '📈' },
    { key: 'earnings', label: 'Earnings', icon: '💰' },
    { key: 'tech', label: 'Tech', icon: '💻' },
    { key: 'crypto', label: 'Crypto', icon: '₿' },
    { key: 'politics', label: 'Politics', icon: '🏛️' },
  ];

  const filteredNews =
    selectedCategory === 'all'
      ? newsItems
      : newsItems.filter((n) => n.category === selectedCategory);

  const handleNewsPress = (newsItem: NewsItem) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (!newsItem.hasVideo) {
      // Open news article in a proper modal with better formatting
      Alert.alert(
        newsItem.title,
        `${newsItem.content}\n\nSource: ${newsItem.source}\nTime: ${newsItem.timestamp}\nRead Time: ${newsItem.readTime}`,
        [
          { text: 'Close', style: 'default' },
          { text: 'Read More', style: 'default', onPress: () => {
            // In a real app, this would open the full article URL
            console.log(`Opening full article: ${newsItem.title}`);
            // You could use Linking.openURL(newsItem.url) if you had real URLs
          }}
        ]
      );
    }
  };

  const handleVideoPress = async (newsItem: NewsItem) => {
    console.log(`🎬 Video press for ${newsItem.id}:`, {
      currentSelected: selectedNews?.id,
      currentPlaying: isPlaying,
      newItem: newsItem.id
    });
    
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    if (selectedNews?.id === newsItem.id) {
      // Same video - toggle play/pause or restart if finished
      if (isPlaying) {
        setIsPlaying(false);
        console.log(`⏸️ Pausing video`);
      } else {
        // Check if video finished - if so, restart from beginning
        const videoRef = videoRefs.current[newsItem.id];
        if (videoRef) {
          try {
            const status = await videoRef.getStatusAsync();
            if (status.isLoaded && status.didJustFinish) {
              await videoRef.replayAsync();
              console.log(`🔄 Restarting finished video from beginning`);
            } else {
              setIsPlaying(true);
              console.log(`▶️ Resuming video`);
            }
          } catch (error) {
            console.error('Error checking video status:', error);
            setIsPlaying(true);
          }
        } else {
          setIsPlaying(true);
        }
      }
    } else {
      // Different video - start new one
      setSelectedNews(newsItem);
      setIsPlaying(true);
      console.log(`▶️ Starting new video: ${newsItem.id}`);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      market: '#4ECDC4',
      earnings: '#FF6B6B',
      tech: '#FFEAA7',
      crypto: '#FFD700',
      politics: '#A8E6CF',
    } as const;
    return (colors as any)[category] || '#666';
  };

  const renderNewsItem = useCallback(
    ({ item }: { item: NewsItem }) => {
      const isSelected = selectedNews?.id === item.id;

      return (
        <TouchableOpacity style={styles.newsItem} onPress={() => handleNewsPress(item)}>
          <View style={styles.newsHeader}>
            <View style={styles.sourceContainer}>
              <Text style={styles.source}>{item.source}</Text>
              <Text style={styles.timestamp}>{item.timestamp}</Text>
            </View>
            {item.isBreaking && (
              <View style={styles.breakingBadge}>
                <Text style={styles.breakingText}>BREAKING</Text>
              </View>
            )}
          </View>

          <Text style={styles.newsTitle}>{item.title}</Text>

          {item.stockSymbol && (
            <View style={styles.stockInfo}>
              <Text style={styles.stockSymbol}>{item.stockSymbol}</Text>
                <Text
                  style={[
                    styles.stockChange,
                    { color: item.stockChange! >= 0 ? '#4ECDC4' : '#FF6B6B' },
                  ]}
                >
                  {item.stockChange! >= 0 ? '+' : ''}
                  {item.stockChange!.toFixed(2)}%
                </Text>
            </View>
          )}

          {item.hasVideo ? (
            <TouchableOpacity
              style={styles.videoContainer}
              onPress={() => handleVideoPress(item)}
              activeOpacity={0.9}
            >
              {/* Thumbnail (only visible when not playing) */}
              {!(isSelected && isPlaying) && (
                <Image 
                  source={{ uri: item.thumbnailUrl }} 
                  style={{
                    position: 'absolute',
                    top: 0, left: 0, right: 0, bottom: 0,
                    width: '100%',
                    height: '100%',
                  }}
                  resizeMode="cover"
                />
              )}

              {/* Only render video when it should be playing */}
              {(isSelected && isPlaying) && (
                <Video
                  ref={(ref) => {
                    if (ref) {
                      videoRefs.current[item.id] = ref;
                    }
                  }}
                  source={{ uri: item.videoUrl }}
                  style={[styles.absFill, { zIndex: 2 }]}
                  resizeMode={ResizeMode.COVER}
                  shouldPlay={true}
                  isLooping={false}
                  useNativeControls={false}
                  isMuted={false}
                  onPlaybackStatusUpdate={(status) => {
                    console.log(`Video ${item.id} status:`, status);
                    if (status.isLoaded) {
                      // Store duration when video loads
                      if (status.durationMillis && !videoDurations[item.id]) {
                        console.log(`📏 Storing duration for ${item.id}: ${status.durationMillis}ms`);
                        setVideoDurations(prev => ({
                          ...prev,
                          [item.id]: status.durationMillis || 0
                        }));
                      }
                      // Auto-pause when video finishes
                      if (status.didJustFinish) {
                        setIsPlaying(false);
                        console.log(`Video ${item.id} finished, pausing`);
                      }
                    }
                  }}
                  onError={(err) => console.error(`Video ${item.id} error:`, err)}
                  onLoadStart={() => console.log(`Video ${item.id} load start`)}
                  onLoad={(status) => {
                    console.log(`Video ${item.id} loaded:`, status);
                    if (status.isLoaded && status.durationMillis) {
                      console.log(`📏 onLoad storing duration for ${item.id}: ${status.durationMillis}ms`);
                      setVideoDurations(prev => ({
                        ...prev,
                        [item.id]: status.durationMillis || 0
                      }));
                    }
                  }}
                />
              )}

              {/* Overlays */}
              {!(isSelected && isPlaying) && (
                <View style={[styles.playButton, { zIndex: 3 }]} pointerEvents="none">
                  <Text style={styles.playIcon}>▶️</Text>
                </View>
              )}
              <View style={[styles.durationBadge, { zIndex: 3 }]} pointerEvents="none">
                <Text style={styles.videoDuration}>
                  {videoDurations[item.id] 
                    ? `${Math.floor(videoDurations[item.id] / 60000)}:${Math.floor((videoDurations[item.id] % 60000) / 1000).toString().padStart(2, '0')}`
                    : '2:45'
                  }
                </Text>
                {/* Debug duration */}
                <Text style={[styles.videoDuration, { fontSize: 10, color: '#ff0000' }]}>
                  {videoDurations[item.id] ? `${videoDurations[item.id]}ms` : 'no duration'}
                </Text>
              </View>
              
              {/* Debug overlay */}
              {(isSelected && isPlaying) && (
                <View style={[styles.debugOverlay, { zIndex: 10 }]} pointerEvents="none">
                  <Text style={styles.debugText}>VIDEO PLAYING</Text>
                </View>
              )}
            </TouchableOpacity>
          ) : (
            <Text style={styles.newsContent} numberOfLines={3}>
              {item.content}
            </Text>
          )}

          <View style={styles.newsFooter}>
            <Text style={styles.readTime}>{item.readTime}</Text>
            <View
              style={[styles.categoryBadge, { backgroundColor: getCategoryColor(item.category) }]}
            >
              <Text style={styles.categoryText}>{item.category.toUpperCase()}</Text>
            </View>
          </View>
        </TouchableOpacity>
      );
    },
    [selectedNews, isPlaying]
  );

  const renderCategoryTabs = () => (
    <View style={styles.tabsWrapper}>
      <FlatList
        data={categories}
        horizontal
        keyExtractor={(c) => c.key}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.categoryContainer}
        renderItem={({ item: cat }) => (
          <TouchableOpacity
            style={[
              styles.categoryButton,
              selectedCategory === cat.key && styles.activeCategoryButton,
            ]}
            onPress={() => {
              setSelectedCategory(cat.key);
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            }}
          >
            <Text style={styles.categoryIcon}>{cat.icon}</Text>
            <Text
              style={[
                styles.categoryLabel,
                selectedCategory === cat.key && styles.activeCategoryLabel,
              ]}
            >
              {cat.label}
            </Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Market News</Text>
        <TouchableOpacity style={styles.searchButton}>
          <Text style={styles.searchIcon}>🔍</Text>
        </TouchableOpacity>
      </View>

      {/* List with sticky category tabs */}
      <FlatList
        data={filteredNews}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderNewsItem}
        contentContainerStyle={styles.newsContainer}
        ListHeaderComponent={renderCategoryTabs}
        stickyHeaderIndices={[0]}
        refreshing={refreshing}
        onRefresh={() => loadNewsByCategory(selectedCategory)}
        removeClippedSubviews
        {...(Platform.OS === 'ios' ? { contentInsetAdjustmentBehavior: 'never' } : {})}
        ListEmptyComponent={
          !loading ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>No news yet.</Text>
            </View>
          ) : null
        }
      />

      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#4ECDC4" />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#212529' },
  searchButton: { padding: 8 },
  searchIcon: { fontSize: 20, color: '#6c757d' },

  // Tabs
  tabsWrapper: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  categoryContainer: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  categoryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    borderRadius: 12,
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  activeCategoryButton: { backgroundColor: '#007AFF', borderColor: '#007AFF' },
  categoryIcon: { fontSize: 12, marginRight: 4 },
  categoryLabel: { fontSize: 12, fontWeight: '500', color: '#6c757d' },
  activeCategoryLabel: { color: '#fff' },

  // List container
  newsContainer: {
    paddingTop: 8,
    paddingHorizontal: 8,
    paddingBottom: 8,
  },

  // Card
  newsItem: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e9ecef',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  newsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  sourceContainer: { flexDirection: 'row', alignItems: 'center' },
  source: { fontSize: 12, fontWeight: '600', color: '#007AFF', marginRight: 8 },
  timestamp: { fontSize: 11, color: '#6c757d' },
  breakingBadge: { backgroundColor: '#dc3545', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  breakingText: { fontSize: 9, fontWeight: 'bold', color: '#fff' },
  newsTitle: { fontSize: 14, fontWeight: 'bold', color: '#212529', lineHeight: 18, marginBottom: 4 },

  stockInfo: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  stockSymbol: { fontSize: 14, fontWeight: 'bold', color: '#212529', marginRight: 8 },
  stockChange: { fontSize: 14, fontWeight: '600' },

  // Video
  videoContainer: {
    position: 'relative',
    height: 200,              // <<< key: gives the container size
    marginBottom: 12,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  absFill: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: 0,
    width: '100%',
    height: '100%',
  },
  playButton: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -25 }, { translateY: -25 }],
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playIcon: { fontSize: 20, color: '#fff' },
  durationBadge: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  videoDuration: { fontSize: 12, color: '#fff', fontWeight: '600' },
  debugOverlay: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: 'rgba(255,0,0,0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  debugText: { fontSize: 12, color: '#fff', fontWeight: 'bold' },

  newsContent: { fontSize: 12, color: '#6c757d', lineHeight: 16, marginBottom: 6 },
  newsFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  readTime: { fontSize: 12, color: '#6c757d' },
  categoryBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
  categoryText: { fontSize: 10, fontWeight: 'bold', color: '#000' },

  // Loading overlay
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'transparent',
  },

  // Empty state
  emptyState: { paddingVertical: 40, alignItems: 'center' },
  emptyText: { color: '#6c757d' },
});

export default NewsFeed;