import React, { useState, useEffect, useRef } from 'react';
import {
View,
Text,
StyleSheet,
ScrollView,
TouchableOpacity,
RefreshControl,
Alert,
Modal,
TextInput,
KeyboardAvoidingView,
Platform,
Image,
FlatList,
Share,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useApolloClient } from '@apollo/client';
import { gql, useQuery, useMutation } from '@apollo/client';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import * as Clipboard from 'expo-clipboard';
import SocialNav from '../components/SocialNav';
import PostRow from '../components/PostRow';
import PredictionModal from '../../../components/forms/PredictionModal';
import PollModal from '../../../components/forms/PollModal';
import TickerChips from '../../../components/TickerChips';
import FollowingRibbon from '../components/FollowingRibbon';
import useTickerFollows from '../../../shared/hooks/useTickerFollows';
import { GET_FOLLOWING_FEED } from '../../../feed';
import { MINI_QUOTES } from '../../../tickerFollows';
import LoadingErrorState from '../../../components/common/LoadingErrorState';
import SocialFeed from '../components/SocialFeed';
import DiscoverUsers from '../components/DiscoverUsers';
import FinancialNews from '../../stocks/components/FinancialNews';
import webSocketService from '../../../services/WebSocketService';
import errorService, { ErrorType, ErrorSeverity } from '../../../services/ErrorService';
// GraphQL Queries
const GET_TRENDING_DISCUSSIONS = gql`
query GetTrendingDiscussions {
stockDiscussions {
id
title
content
createdAt
score
commentCount
user {
id
name
email
}
stock {
symbol
companyName
}
comments {
id
content
createdAt
user {
name
}
}
}
}
`;
const GET_SOCIAL_FEED = gql`
query GetSocialFeed {
socialFeed {
id
title
content
createdAt
score
commentCount
user {
id
name
email
}
stock {
symbol
companyName
}
comments {
id
content
createdAt
user {
name
}
}
}
}
`;
const COMMENT_ON_DISCUSSION = gql`
mutation CreateDiscussionComment($discussionId: ID!, $content: String!) {
createDiscussionComment(discussionId: $discussionId, content: $content) {
success
message
comment {
id
content
user {
name
}
}
}
}
`;
const CREATE_DISCUSSION = gql`
mutation CreateStockDiscussion($title: String!, $content: String!, $stockSymbol: String, $discussionType: String, $visibility: String) {
createStockDiscussion(title: $title, content: $content, stockSymbol: $stockSymbol, discussionType: $discussionType, visibility: $visibility) {
success
message
discussion {
id
title
content
discussionType
visibility
createdAt
user {
name
profilePic
}
stock {
symbol
companyName
}
}
}
}
`;
const UPVOTE_DISCUSSION = gql`
mutation UpvoteDiscussion($discussionId: ID!) {
voteDiscussion(discussionId: $discussionId, voteType: "upvote") {
success
message
discussion {
id
score
}
}
}
`;
const DOWNVOTE_DISCUSSION = gql`
mutation DownvoteDiscussion($discussionId: ID!) {
voteDiscussion(discussionId: $discussionId, voteType: "downvote") {
success
message
discussion {
id
score
}
}
}
`;
const TOGGLE_FOLLOW = gql`
mutation ToggleFollow($userId: ID!) {
toggleFollow(userId: $userId) {
success
following
user {
id
name
followersCount
followingCount
isFollowingUser
}
}
}
`;
// Real data will be fetched from GraphQL queries
// Real data will be fetched from GraphQL queries
// Real data will be fetched from GraphQL queries
// Discussion Categories
const DISCUSSION_CATEGORIES = {
GENERAL: { id: 'general', name: 'General', icon: 'message-circle', color: '#8E8E93' },
BEGINNER: { id: 'beginner', name: 'Beginner Questions', icon: 'help-circle', color: '#AF52DE' },
PORTFOLIO: { id: 'portfolio', name: 'Portfolio Review', icon: 'pie-chart', color: '#34C759' },
NEWS: { id: 'news', name: 'Market News', icon: 'newspaper', color: '#FF9500' },
STRATEGY: { id: 'strategy', name: 'Investment Strategy', icon: 'target', color: '#007AFF' },
CRYPTO: { id: 'crypto', name: 'Crypto Discussion', icon: 'bitcoin', color: '#FF3B30' },
EARNINGS: { id: 'earnings', name: 'Earnings Reports', icon: 'trending-up', color: '#32D74B' },
DIVIDENDS: { id: 'dividends', name: 'Dividends', icon: 'dollar-sign', color: '#FFD60A' },
};
interface SocialScreenProps {
onNavigate?: (screen: string, params?: any) => void;
}
const SocialScreen: React.FC<SocialScreenProps> = ({ onNavigate }) => {
const [refreshing, setRefreshing] = useState(false);
const [showCreateModal, setShowCreateModal] = useState(false);
const [showPrediction, setShowPrediction] = useState(false);
const [showPoll, setShowPoll] = useState(false);

// Ticker follows hook
const { symbols: followedSymbols, set: followedTickerSet } = useTickerFollows();
const [createTitle, setCreateTitle] = useState('');
const [createContent, setCreateContent] = useState('');
const [createStock, setCreateStock] = useState('');
const [createVisibility, setCreateVisibility] = useState<'public' | 'followers'>('followers');
const [createCategory, setCreateCategory] = useState<string>('general');
// Media state
const [selectedImage, setSelectedImage] = useState<string | null>(null);
const [selectedVideo, setSelectedVideo] = useState<string | null>(null);
const [mediaType, setMediaType] = useState<'image' | 'video' | null>(null);
// TextInput refs
const contentInputRef = useRef<TextInput>(null);
// Comment modal state
const [showCommentModal, setShowCommentModal] = useState(false);
const [commentContent, setCommentContent] = useState('');
const [selectedDiscussionId, setSelectedDiscussionId] = useState('');
const [isCommenting, setIsCommenting] = useState(false);
// Discussion detail modal state
const [showDiscussionDetail, setShowDiscussionDetail] = useState(false);
const [discussionDetail, setDiscussionDetail] = useState<any>(null);
const [modalUserVote, setModalUserVote] = useState<'upvote' | 'downvote' | null>(null);
const [modalLocalScore, setModalLocalScore] = useState(0);
// Feed type state
const [feedType, setFeedType] = useState<'trending' | 'following' | 'discover' | 'news'>('trending');
const handleFeedTypeChange = (newFeedType: 'trending' | 'following' | 'discover' | 'news') => {
setFeedType(newFeedType);
};
// WebSocket connection state
const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
// User following state
const [showUserModal, setShowUserModal] = useState(false);
const [userModalType, setUserModalType] = useState<'suggested' | 'following'>('suggested');
const client = useApolloClient();

// GraphQL queries and mutations
const { 
data: discussionsData, 
loading: discussionsLoading, 
error: discussionsError,
refetch: refetchDiscussions,
networkStatus
} = useQuery(
feedType === 'trending' ? GET_TRENDING_DISCUSSIONS : GET_SOCIAL_FEED,
{
errorPolicy: 'all',
notifyOnNetworkStatusChange: true,          // lets the RefreshControl show while reloading
fetchPolicy: 'cache-and-network',           // fast UI from cache, then refresh
nextFetchPolicy: 'cache-first',
onError: (error) => {
errorService.handleGraphQLError(error, 'SocialScreen', 'fetch_discussions');
}
}
);

// Following feed query
const { data: followingData, loading: followingLoading, error: followingError, refetch: refetchFollowing } = useQuery(
  GET_FOLLOWING_FEED,
  {
    skip: feedType !== 'following' || !followedSymbols || !followedSymbols.length,
    variables: { symbols: followedSymbols || [], limit: 50 },
    fetchPolicy: 'cache-and-network',
  }
);

// Debounced refetch to avoid thundering herds
const refetchDebounced = React.useRef<NodeJS.Timeout | null>(null);
const safeRefetch = React.useCallback(() => {
  if (refetchDebounced.current) clearTimeout(refetchDebounced.current);
  refetchDebounced.current = setTimeout(() => { refetchDiscussions(); }, 350);
}, [refetchDiscussions]);

const [commentOnDiscussion] = useMutation(COMMENT_ON_DISCUSSION, {
onError: (error) => {
errorService.handleGraphQLError(error, 'SocialScreen', 'comment_discussion');
}
});
const [createStockDiscussion] = useMutation(CREATE_DISCUSSION, {
onError: (error) => {
errorService.handleGraphQLError(error, 'SocialScreen', 'create_discussion');
}
});
const [upvoteDiscussion] = useMutation(UPVOTE_DISCUSSION, {
onError: (error) => {
errorService.handleGraphQLError(error, 'SocialScreen', 'upvote_discussion');
}
});
const [downvoteDiscussion] = useMutation(DOWNVOTE_DISCUSSION, {
onError: (error) => {
errorService.handleGraphQLError(error, 'SocialScreen', 'downvote_discussion');
}
});
const [toggleFollow] = useMutation(TOGGLE_FOLLOW, {
onError: (error) => {
errorService.handleGraphQLError(error, 'SocialScreen', 'toggle_follow');
}
});
// WebSocket setup
useEffect(() => {
const setupWebSocket = async () => {
try {
// Get auth token
const token = await AsyncStorage.getItem('authToken');
if (token) {
webSocketService.setToken(token);
}
// Set up WebSocket callbacks
webSocketService.setCallbacks({
      onConnectionStatusChange: (connected) => {
        setIsWebSocketConnected(connected);
        // Don't show error for WebSocket disconnection - it's optional
        if (__DEV__) {
          console.log('WebSocket connection status:', connected);
        }
      },
      onNewDiscussion: () => safeRefetch(),
      onNewComment: () => safeRefetch(),
      onDiscussionUpdate: () => safeRefetch()
});
// Connect to WebSocket (disabled for now - no server running)
// webSocketService.connect();
// Set up ping interval to keep connection alive (disabled for now)
// const pingInterval = setInterval(() => {
//   webSocketService.ping();
// }, 30000); // Ping every 30 seconds
return () => {
  // clearInterval(pingInterval);
  // webSocketService.disconnect();
};
} catch (error) {
// Error setting up WebSocket
}
};
const cleanup = setupWebSocket();
return () => {
cleanup.then(cleanupFn => cleanupFn?.());
};
}, []);
const onRefresh = async () => {
setRefreshing(true);
try {
await client.refetchQueries({
include: ['GetTrendingDiscussions'],
});
} catch (error) {
errorService.handleError(error, {
type: ErrorType.API,
severity: ErrorSeverity.MEDIUM,
customMessage: 'Failed to refresh data. Please try again.',
screen: 'SocialScreen',
action: 'refresh_data',
showAlert: false,
showToast: true,
});
} finally {
setRefreshing(false);
}
};
const handleCreatePress = () => {
setShowCreateModal(true);
};
const handleUpvote = React.useCallback(async (discussionId: string) => {
  try {
    await upvoteDiscussion({ 
      variables: { discussionId },
      update: (cache, { data }) => {
        if (data?.voteDiscussion?.success) {
          // Update the cache with the new score
          cache.modify({
            id: cache.identify({ __typename: 'StockDiscussion', id: discussionId }),
            fields: {
              score() { return data.voteDiscussion.discussion.score; }
            }
          });
        }
      }
    });
  } catch (error) {
    console.error('Upvote failed:', error);
  }
}, [upvoteDiscussion]);

const handleDownvote = React.useCallback(async (discussionId: string) => {
  try {
    await downvoteDiscussion({ 
      variables: { discussionId },
      update: (cache, { data }) => {
        if (data?.voteDiscussion?.success) {
          // Update the cache with the new score
          cache.modify({
            id: cache.identify({ __typename: 'StockDiscussion', id: discussionId }),
            fields: {
              score() { return data.voteDiscussion.discussion.score; }
            }
          });
        }
      }
    });
  } catch (error) {
    console.error('Downvote failed:', error);
  }
}, [downvoteDiscussion]);
const handleToggleFollow = async (userId: string) => {
try {
const result = await toggleFollow({
variables: { userId }
});
if (result.data?.toggleFollow?.success) {
// Refetch all relevant data
await Promise.all([
refetchDiscussions()
]);
} else {
}
} catch (error) {
// Follow toggle error
}
};

const handleShareDiscussion = React.useCallback(async (discussion: any) => {
  try {
    const shareContent = {
      message: `${discussion.title}\n\n${discussion.content}`,
      url: `richesreach://discussion/${discussion.id}`,
    };
    await Share.share(shareContent);
  } catch (error) {
    console.error('Error sharing discussion:', error);
  }
}, []);

const handleCopyToClipboard = React.useCallback(async (text: string) => {
  try {
    await Clipboard.setStringAsync(text);
    Alert.alert('Copied!', 'Text copied to clipboard');
  } catch (error) {
    console.error('Error copying to clipboard:', error);
    Alert.alert('Error', 'Failed to copy to clipboard');
  }
}, []);

const handleSaveDiscussion = React.useCallback(async (discussion: any) => {
  try {
    // For now, copy the discussion content to clipboard as a save action
    const saveText = `${discussion.title}\n\n${discussion.content}`;
    await handleCopyToClipboard(saveText);
    console.log('Discussion saved to clipboard:', discussion.id);
  } catch (error) {
    console.error('Error saving discussion:', error);
  }
}, [handleCopyToClipboard]);
// Helper function to determine if submit button should be disabled
const isSubmitDisabled = () => {
const hasMedia = selectedImage || selectedVideo;
const hasContent = createContent.trim().length > 0;
const hasValidTitle = createTitle.trim().length >= 5;
// Must have a valid title
if (!hasValidTitle) return true;
// Must have either content (with min length) or media
if (!hasMedia && !hasContent) return true;
if (hasContent && createContent.trim().length < 10) return true;
return false;
};
// Get discussions data based on feed type
const discussions = React.useMemo(() => {
  if (feedType === 'following') {
    return followingData?.feedByTickers || [];
  } else if (feedType === 'trending') {
    return discussionsData?.stockDiscussions || [];
  } else if (feedType === 'social') {
    // Handle socialFeed data structure - now returns proper structure
    const socialData = discussionsData?.socialFeed;
    if (Array.isArray(socialData)) {
      return socialData;
    }
    return [];
  }
  return [];
}, [feedType, discussionsData, followingData]);

// Get all unique ticker symbols from discussions for live quotes
const allTickerSymbols = React.useMemo(() => {
  const symbols = new Set<string>();
  if (discussions && Array.isArray(discussions)) {
    discussions.forEach((discussion: any) => {
      // Handle different data structures
      if (discussion?.stock?.symbol) {
        symbols.add(discussion.stock.symbol);
      }
      if (discussion?.tickers && Array.isArray(discussion.tickers)) {
        discussion.tickers.forEach((ticker: string) => symbols.add(ticker));
      }
      // Handle socialFeed structure - now has proper stock data
      if (discussion?.stock?.symbol) {
        symbols.add(discussion.stock.symbol);
      }
    });
  }
  return Array.from(symbols);
}, [discussions]);

// Live quotes query
const { data: quotesData } = useQuery(MINI_QUOTES, {
  variables: { symbols: allTickerSymbols },
  skip: allTickerSymbols.length === 0,
  pollInterval: 30000, // Update every 30 seconds
});

// Convert quotes data to the format expected by PostRow
const liveQuotes = React.useMemo(() => {
  if (!quotesData?.quotes) return {};
  const quotes: Record<string, { price: number; chg: number }> = {};
  quotesData.quotes.forEach((quote: any) => {
    quotes[quote.symbol] = {
      price: quote.last,
      chg: quote.changePct
    };
  });
  return quotes;
}, [quotesData]);

const handleDiscussionComment = React.useCallback((discussionId: string) => {
  const d = discussions.find((x: any) => x.id === discussionId);
  if (!d) return;
  setDiscussionDetail(d);
  setSelectedDiscussionId(discussionId);
  setCommentContent('');
  setShowCommentModal(false);
  setShowDiscussionDetail(true);
}, [discussions]);
const handleCommentSubmit = async () => {
if (!commentContent.trim()) {
Alert.alert('Error', 'Please enter a comment');
return;
}
// Starting comment submission
setIsCommenting(true);
try {
const result = await commentOnDiscussion({ 
variables: { 
discussionId: selectedDiscussionId, 
content: commentContent.trim() 
} 
});
if (result.data?.createDiscussionComment?.success) {
} else {
}
// Refetch discussions to update comment count
// Add a small delay to ensure backend has processed the comment
await new Promise(resolve => setTimeout(resolve, 500));
const refetchResult = await refetchDiscussions();
// Close modal and reset
setShowCommentModal(false);
setCommentContent('');
setSelectedDiscussionId('');
Alert.alert('Success', 'Comment added successfully!');
} catch (error) {
// Comment submission failed
Alert.alert('Error', 'Failed to add comment. Please try again.');
} finally {
setIsCommenting(false);
}
};
// Media picker functions
const pickImage = async () => {
try {
const result = await ImagePicker.launchImageLibraryAsync({
mediaTypes: 'images',
allowsEditing: true,
aspect: [16, 9],
quality: 0.8,
});
if (!result.canceled && result.assets[0]) {
setSelectedImage(result.assets[0].uri);
setSelectedVideo(null);
setMediaType('image');
} else {
}
} catch (error) {
// Error picking image
Alert.alert('Error', 'Failed to pick image');
}
};
const pickVideo = async () => {
try {
const result = await ImagePicker.launchImageLibraryAsync({
mediaTypes: 'videos',
allowsEditing: true,
quality: 0.8,
});
if (!result.canceled && result.assets[0]) {
setSelectedVideo(result.assets[0].uri);
setSelectedImage(null);
setMediaType('video');
} else {
}
} catch (error) {
// Error picking video
Alert.alert('Error', 'Failed to pick video');
}
};
const showMediaOptions = () => {
Alert.alert(
'Add Media',
'Choose the type of media you want to add',
[
{
text: 'Photo',
onPress: pickImage,
},
{
text: 'Video',
onPress: pickVideo,
},
{
text: 'Cancel',
style: 'cancel',
},
],
{ cancelable: true }
);
};
const removeMedia = () => {
setSelectedImage(null);
setSelectedVideo(null);
setMediaType(null);
};
const handleModalVote = (voteType: 'upvote' | 'downvote') => {
if (modalUserVote === voteType) {
// Remove vote if clicking same button
setModalUserVote(null);
// Revert the score change
if (voteType === 'upvote') {
setModalLocalScore(prev => prev - 1);
} else {
setModalLocalScore(prev => prev + 1);
}
} else {
// Handle vote change
if (modalUserVote === null) {
// First vote
setModalUserVote(voteType);
if (voteType === 'upvote') {
setModalLocalScore(prev => prev + 1);
} else {
setModalLocalScore(prev => prev - 1);
}
} else {
// Switching from one vote to another
if (modalUserVote === 'upvote' && voteType === 'downvote') {
// Switching from upvote to downvote: -1 (remove upvote) -1 (add downvote) = -2
setModalLocalScore(prev => prev - 2);
} else if (modalUserVote === 'downvote' && voteType === 'upvote') {
// Switching from downvote to upvote: +1 (remove downvote) +1 (add upvote) = +2
setModalLocalScore(prev => prev + 2);
}
setModalUserVote(voteType);
}
}
};
const handleInlineCommentSubmit = async () => {
if (!commentContent.trim()) {
Alert.alert('Error', 'Please enter a comment');
return;
}
setIsCommenting(true);
try {
await commentOnDiscussion({ 
variables: { 
discussionId: selectedDiscussionId, 
content: commentContent.trim() 
} 
});
// Refetch discussions to update comment count and comments
await client.refetchQueries({ include: ['GetTrendingDiscussions'] });
// Clear comment input but keep modal open
setCommentContent('');
// Update local discussion detail with new comment immediately
if (discussionDetail) {
const newComment = {
id: Date.now().toString(), // Temporary ID
content: commentContent.trim(),
createdAt: new Date().toISOString(),
user: { name: 'Test User' } // Use current user name
};
setDiscussionDetail({
...discussionDetail,
comments: [...(discussionDetail.comments || []), newComment],
commentCount: (discussionDetail.commentCount || 0) + 1
});
}
// Refetch data in background to get real comment data
setTimeout(async () => {
try {
await client.refetchQueries({ include: ['GetTrendingDiscussions'] });
// Update discussion detail with fresh data from server
const freshDiscussion = discussionsData?.stockDiscussions?.find((d: any) => d.id === selectedDiscussionId);
if (freshDiscussion) {
setDiscussionDetail(freshDiscussion);
}
} catch (error) {
// Failed to refresh discussion
}
}, 1000);
} catch (error) {
// Failed to add comment
Alert.alert('Error', 'Failed to add comment. Please try again.');
} finally {
setIsCommenting(false);
}
};
const handleDiscussionPress = React.useCallback((discussionId: string) => {
  const d = discussions.find((x: any) => x.id === discussionId);
  if (!d) return;
  setDiscussionDetail(d);
  setSelectedDiscussionId(discussionId);
  setCommentContent('');
  setShowCommentModal(false);
  setShowDiscussionDetail(true);
  setModalUserVote(null);
  setModalLocalScore(d.score || 0);
}, [discussions]);
const handleCreateSubmit = async () => {
// Use the helper function for validation
if (isSubmitDisabled()) {
Alert.alert('Error', 'Please check your input and try again');
return;
}
// Validate minimum length requirements
if (createTitle.trim().length < 5) {
Alert.alert('Error', 'Title must be at least 5 characters long');
return;
}
try {
// Prepare content with media information
let finalContent = createContent.trim();
// Add media information to content if media is selected
if (selectedImage) {
finalContent += `\n\n[IMAGE: ${selectedImage}]`;
}
if (selectedVideo) {
finalContent += `\n\n[VIDEO: ${selectedVideo}]`;
}
// Creating discussion
const variables = {
title: createTitle.trim(),
content: finalContent,
stockSymbol: createStock.trim() || null, // Optional - like Reddit posts
discussionType: 'general', // Default to general discussion
visibility: createVisibility // Public or followers only
};
const result = await createStockDiscussion({
variables: variables
});
// Discussion created successfully
if (result.data?.createStockDiscussion?.success) {
Alert.alert('Success', 'Discussion created successfully!');
// Refetch discussions to show the new item
await refetchDiscussions();
setShowCreateModal(false);
setCreateTitle('');
setCreateContent('');
setCreateStock('');
setCreateVisibility('followers'); // Reset to default
// Clear media
setSelectedImage(null);
setSelectedVideo(null);
setMediaType(null);
} else {
Alert.alert('Error', result.data?.createStockDiscussion?.message || 'Failed to create discussion');
}
} catch (error) {
// Failed to create discussion
Alert.alert('Error', `Failed to create discussion: ${(error as any)?.message || 'Unknown error'}`);
}
};
// FlatList implementation for Reddit-style feed
const keyExtractor = React.useCallback((item: any) => item?.id || `item-${Math.random()}`, []);


// Reddit-like list container - now using full-bleed design

const listEmpty = React.useMemo(() => (
  <View style={styles.emptyState}>
    <Text style={styles.emptyStateText}>No discussions yet</Text>
    <Text style={styles.emptyStateSubtext}>Be the first to start a discussion!</Text>
  </View>
), []);

// Render item function using PostRow
const renderItem = React.useCallback(({ item }: { item: any }) => {
  // Add safety checks for item structure
  if (!item || !item.id) {
    return null;
  }
  
  return (
    <PostRow
      discussion={item}
      onPress={() => handleDiscussionPress(item.id)}
      onUpvote={() => handleUpvote(item.id)}
      onDownvote={() => handleDownvote(item.id)}
      onComment={() => handleDiscussionComment(item.id)}
      onFollow={() => handleToggleFollow(item.user?.id || '')}
      onShare={() => handleShareDiscussion(item)}
      onSave={() => handleSaveDiscussion(item)}
      onPressTicker={(symbol) => onNavigate?.('Stock', { symbol })}
      liveQuotes={liveQuotes}
      followedTickerSet={followedTickerSet}
    />
  );
}, [handleDiscussionPress, handleUpvote, handleDownvote, handleDiscussionComment, handleToggleFollow, onNavigate]);

const RedditList = (
  <FlatList
    data={discussions}
    keyExtractor={keyExtractor}
    renderItem={renderItem}
    ItemSeparatorComponent={() => <View style={{ height: 8, backgroundColor: '#F9FAFB' }} />}
    ListEmptyComponent={listEmpty}
    ListHeaderComponent={
      <View style={{ borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#E5E7EB' }}>
        {/* Header content will be added by the parent component */}
      </View>
    }
    ListFooterComponent={<View style={{ height: 24 }} />}
    contentContainerStyle={{ paddingBottom: 24 }}
    refreshControl={
      <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
    }
    removeClippedSubviews
    initialNumToRender={8}
    maxToRenderPerBatch={8}
    windowSize={7}
    updateCellsBatchingPeriod={50}
    showsVerticalScrollIndicator={false}
  />
);

const renderContent = () => {
  if (feedType === 'following') {
    return <SocialFeed onNavigate={onNavigate || (() => {})} />;
  }
  if (feedType === 'discover') {
    return <DiscoverUsers onNavigate={onNavigate || (() => {})} />;
  }
  if (feedType === 'news') {
    return <FinancialNews limit={15} />;
  }
  return RedditList;
};
return (
<View style={styles.container}>
{/* Header */}
<View style={styles.header}>
<Text style={styles.headerTitle}>Discussion Hub</Text>
<View style={styles.headerButtons}>
  <TouchableOpacity style={[styles.createButton, { backgroundColor: '#FF6B35' }]} onPress={() => setShowPrediction(true)}>
    <Icon name="target" size={20} color="#FFFFFF" />
  </TouchableOpacity>
  <TouchableOpacity style={[styles.createButton, { backgroundColor: '#6366F1' }]} onPress={() => setShowPoll(true)}>
    <Icon name="bar-chart-2" size={20} color="#FFFFFF" />
  </TouchableOpacity>
  <TouchableOpacity style={[styles.createButton, { backgroundColor: '#34C759' }]} onPress={handleCreatePress}>
    <Icon name="plus" size={24} color="#FFFFFF" />
  </TouchableOpacity>
</View>
</View>
{/* Followed Tickers Display */}
{feedType === 'following' && followedSymbols && followedSymbols.length > 0 && (
  <FollowingRibbon
    symbols={followedSymbols}
    liveQuotes={liveQuotes} // optional; falls back gracefully if missing
    onPressSymbol={(symbol) => onNavigate?.('Stock', { symbol })}
    onManagePress={() => {
      Alert.alert(
        'Manage Followed Tickers',
        `You're following ${followedSymbols.length} ticker${followedSymbols.length !== 1 ? 's' : ''}: ${followedSymbols.join(', ')}`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'View Profile', 
            onPress: () => onNavigate?.('profile'),
            style: 'default'
          }
        ]
      );
    }}
  />
)}

      {/* Navigation */}
      <SocialNav 
        feedType={feedType}
        onFeedTypeChange={handleFeedTypeChange}
      />
      
      {/* Leaderboard Quick Access */}
      <TouchableOpacity 
        style={styles.leaderboardButton}
        onPress={() => onNavigate?.('portfolio-leaderboard')}
      >
        <Icon name="award" size={20} color="#FFD700" />
        <Text style={styles.leaderboardButtonText}>View Leaderboard</Text>
        <Icon name="chevron-right" size={18} color="#8E8E93" />
      </TouchableOpacity>
      {/* Content */}
      <View style={styles.content}>
        {feedType === 'trending' ? (
          <>
            <LoadingErrorState
              loading={discussionsLoading}
              error={discussionsError?.message}
              onRetry={onRefresh}
              showEmpty={!discussionsLoading && (!discussionsData?.stockDiscussions || discussionsData.stockDiscussions.length === 0)}
              emptyMessage="No discussions yet. Be the first to start a conversation!"
            />
            {!discussionsLoading && !discussionsError && discussionsData?.stockDiscussions && discussionsData.stockDiscussions.length > 0 && renderContent()}
          </>
        ) : (
          renderContent()
        )}
      </View>
{/* Create Modal */}
<Modal
visible={showCreateModal}
animationType="slide"
transparent={true}
onShow={() => {
}}
>
<KeyboardAvoidingView
behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
style={styles.modalContainer}
>
<View style={styles.modalContent}>
<View style={styles.modalHeader}>
<Text style={styles.modalTitle}>Create New Discussion</Text>
<TouchableOpacity
onPress={() => setShowCreateModal(false)}
style={styles.closeButton}
>
<Icon name="x" size={24} color="#8E8E93" />
</TouchableOpacity>
</View>
<ScrollView style={styles.modalBody} keyboardShouldPersistTaps="handled">
{(
<>
<Text style={styles.modalLabel}>Title</Text>
<TextInput
style={styles.textInput}
value={createTitle}
onChangeText={(text) => {
setCreateTitle(text);
}}
placeholder="Enter discussion title"
/>
<Text style={styles.modalLabel}>Stock Symbol (Optional)</Text>
<TextInput
style={styles.textInput}
value={createStock}
onChangeText={(text) => {
setCreateStock(text);
}}
placeholder="e.g., AAPL (leave blank for general discussion)"
autoCapitalize="characters"
/>
<Text style={styles.modalLabel}>Category</Text>
<ScrollView 
horizontal 
showsHorizontalScrollIndicator={false}
style={styles.categoryScrollView}
contentContainerStyle={styles.categoryContainer}
>
{Object.values(DISCUSSION_CATEGORIES).map((category) => (
<TouchableOpacity
key={category.id}
style={[
styles.categoryButton,
createCategory === category.id && styles.categoryButtonSelected,
{ borderColor: category.color }
]}
onPress={() => setCreateCategory(category.id)}
>
<Icon 
name={category.icon} 
size={16} 
color={createCategory === category.id ? '#FFFFFF' : category.color} 
/>
<Text style={[
styles.categoryButtonText,
createCategory === category.id && styles.categoryButtonTextSelected,
{ color: createCategory === category.id ? '#FFFFFF' : category.color }
]}>
{category.name}
</Text>
</TouchableOpacity>
))}
</ScrollView>
<Text style={styles.modalLabel}>Post Visibility</Text>
<View style={styles.visibilityContainer}>
<TouchableOpacity
style={[
styles.visibilityOption,
createVisibility === 'public' && styles.visibilityOptionSelected
]}
onPress={() => {
setCreateVisibility('public');
}}
>
<Icon 
name="globe" 
size={16} 
color={createVisibility === 'public' ? '#FFFFFF' : '#007AFF'} 
/>
<Text style={[
styles.visibilityOptionText,
createVisibility === 'public' && styles.visibilityOptionTextSelected
]}>
Public
</Text>
<Text style={[
styles.visibilityOptionSubtext,
createVisibility === 'public' && styles.visibilityOptionSubtextSelected
]}>
Everyone can see
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[
styles.visibilityOption,
createVisibility === 'followers' && styles.visibilityOptionSelected
]}
onPress={() => {
setCreateVisibility('followers');
}}
>
<Icon 
name="users" 
size={16} 
color={createVisibility === 'followers' ? '#FFFFFF' : '#007AFF'} 
/>
<Text style={[
styles.visibilityOptionText,
createVisibility === 'followers' && styles.visibilityOptionTextSelected
]}>
Followers Only
</Text>
<Text style={[
styles.visibilityOptionSubtext,
createVisibility === 'followers' && styles.visibilityOptionSubtextSelected
]}>
Only followers can see
</Text>
</TouchableOpacity>
</View>
<Text style={styles.modalLabel}>Description</Text>
<TextInput
ref={contentInputRef}
style={[styles.textInput, styles.textArea]}
value={createContent}
onChangeText={(text) => {
setCreateContent(text);
}}
placeholder="Share your thoughts, analysis, or questions (optional if you upload media). You can include links to images, videos, or articles!"
multiline
numberOfLines={4}
autoCapitalize="sentences"
autoCorrect={true}
spellCheck={true}
keyboardType="default"
returnKeyType="default"
blurOnSubmit={false}
textContentType="none"
autoComplete="off"
dataDetectorTypes="all"
selectTextOnFocus={false}
clearButtonMode="never"
onContentSizeChange={(event) => {
// Allow dynamic height for multiline
}}
onSelectionChange={(event) => {
}}
onFocus={() => {
}}
onBlur={() => {
}}
contextMenuHidden={false}
allowFontScaling={true}
maxLength={2000}
editable={true}
caretHidden={false}
importantForAutofill="no"
/>
{/* Media Upload Section */}
<Text style={styles.modalLabel}>Add Media (Optional)</Text>
<View style={styles.mediaUploadContainer}>
<TouchableOpacity 
style={[
styles.mediaButton,
(selectedImage || selectedVideo) && styles.mediaButtonSelected
]} 
onPress={showMediaOptions}
>
<Icon 
name={selectedImage ? "image" : selectedVideo ? "video" : "plus"} 
size={20} 
color={(selectedImage || selectedVideo) ? "#FFFFFF" : "#007AFF"} 
/>
<Text style={[
styles.mediaButtonText,
(selectedImage || selectedVideo) && styles.mediaButtonTextSelected
]}>
{selectedImage ? "Photo Added" : selectedVideo ? "Video Added" : "Add Media"}
</Text>
</TouchableOpacity>
</View>
{/* Media Attachment Indicator */}
{(selectedImage || selectedVideo) && (
<View style={styles.mediaAttachmentIndicator}>
<View style={styles.mediaAttachmentContent}>
<Icon 
name={selectedImage ? "image" : "video"} 
size={16} 
color="#007AFF" 
/>
<Text style={styles.mediaAttachmentText}>
{selectedImage ? "Image attached" : "Video attached"}
</Text>
<TouchableOpacity 
onPress={removeMedia} 
style={styles.removeAttachmentButton}
>
<Icon name="x" size={14} color="#8E8E93" />
</TouchableOpacity>
</View>
</View>
)}
</>
)}
</ScrollView>
<View style={styles.modalFooter}>
<TouchableOpacity
style={styles.closeButtonFooter}
onPress={() => setShowCreateModal(false)}
>
<Text style={styles.closeButtonText}>Cancel</Text>
</TouchableOpacity>
<TouchableOpacity
style={[
styles.commentSubmitButton,
isSubmitDisabled() && styles.commentSubmitButtonDisabled
]}
onPress={() => {
handleCreateSubmit();
}}
disabled={isSubmitDisabled()}
>
<Text style={styles.commentSubmitText}>Create</Text>
</TouchableOpacity>
</View>
</View>
</KeyboardAvoidingView>
</Modal>
{/* Comment Modal */}
<Modal
visible={showCommentModal}
animationType="slide"
transparent={true}
>
<KeyboardAvoidingView
behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
style={styles.modalContainer}
>
<View style={styles.modalContent}>
<View style={styles.modalHeader}>
<Text style={styles.modalTitle}>Add Comment</Text>
<TouchableOpacity
onPress={() => setShowCommentModal(false)}
style={styles.closeButton}
>
<Icon name="x" size={24} color="#8E8E93" />
</TouchableOpacity>
</View>
<View style={styles.modalBody}>
<Text style={styles.modalLabel}>Comment</Text>
<TextInput
style={[styles.textInput, styles.textArea]}
value={commentContent}
onChangeText={setCommentContent}
placeholder="Enter your comment..."
multiline
numberOfLines={4}
/>
</View>
<View style={styles.modalFooter}>
<TouchableOpacity
style={styles.closeButtonFooter}
onPress={() => setShowCommentModal(false)}
>
<Text style={styles.closeButtonText}>Cancel</Text>
</TouchableOpacity>
<TouchableOpacity
style={[
styles.commentSubmitButton,
!commentContent.trim() && styles.commentSubmitButtonDisabled
]}
onPress={handleCommentSubmit}
disabled={!commentContent.trim() || isCommenting}
>
<Text style={styles.commentSubmitText}>
{isCommenting ? 'Adding...' : 'Add Comment'}
</Text>
</TouchableOpacity>
</View>
</View>
</KeyboardAvoidingView>
</Modal>
{/* Discussion Detail Modal */}
<Modal
visible={showDiscussionDetail}
animationType="slide"
transparent={true}
onShow={() => {
}}
>
<KeyboardAvoidingView
behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
style={styles.modalContainer}
>
<View style={styles.modalContent}>
<View style={styles.modalHeader}>
<Text style={styles.modalTitle}>{discussionDetail?.title}</Text>
<TouchableOpacity
onPress={() => setShowDiscussionDetail(false)}
style={styles.closeButton}
>
<Icon name="x" size={24} color="#8E8E93" />
</TouchableOpacity>
</View>
<ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
{/* Discussion Content Card */}
<View style={styles.contentCard}>
<View style={styles.contentHeader}>
<View style={styles.userInfo}>
<View style={styles.userAvatar}>
<Text style={styles.userAvatarText}>
{discussionDetail?.user?.name?.charAt(0) || 'U'}
</Text>
</View>
<View style={styles.userDetails}>
<Text style={styles.userName}>{discussionDetail?.user?.name}</Text>
<Text style={styles.postTime}>
{discussionDetail?.createdAt ? new Date(discussionDetail.createdAt).toLocaleDateString() : ''}
</Text>
</View>
</View>
<View style={styles.headerActions}>
{discussionDetail?.stock && (
<View style={styles.stockBadge}>
<Text style={styles.stockSymbol}>{discussionDetail.stock.symbol}</Text>
</View>
)}
<View style={styles.actionButtons}>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => handleShareDiscussion(discussionDetail)}
>
<Icon name="share-2" size={18} color="#007AFF" />
<Text style={styles.actionButtonText}>Share</Text>
</TouchableOpacity>
<TouchableOpacity 
style={[styles.actionButton, styles.saveButton]}
onPress={() => handleSaveDiscussion(discussionDetail)}
>
<Icon name="bookmark" size={18} color="#FF9500" />
<Text style={[styles.actionButtonText, styles.saveButtonText]}>Save</Text>
</TouchableOpacity>
</View>
</View>
</View>
<Text style={styles.discussionContent}>
{discussionDetail?.content?.replace(/\[(IMAGE|VIDEO):\s*[^\]]+\]/g, '').trim()}
</Text>
{/* Display media if present */}
{(() => {
if (!discussionDetail?.content) return null;
const mediaRegex = /\[(IMAGE|VIDEO):\s*([^\]]+)\]/g;
const mediaItems = [];
let match;
while ((match = mediaRegex.exec(discussionDetail.content)) !== null) {
mediaItems.push({
type: match[1].toLowerCase(),
uri: match[2].trim()
});
}
if (mediaItems.length === 0) return null;
return (
<View style={styles.mediaContainer}>
{mediaItems.map((media, index) => {
if (media.type === 'image') {
return (
<TouchableOpacity 
key={`media-${index}`} 
style={styles.mediaItem}
onPress={() => {
// For now, just show an alert with the image path
// In a real app, you'd want to open a full-screen image viewer
}}
>
<Image source={{ uri: media.uri }} style={styles.mediaImage} />
<View style={styles.mediaOverlay}>
<Icon name="image" size={20} color="white" />
</View>
</TouchableOpacity>
);
} else if (media.type === 'video') {
return (
<TouchableOpacity 
key={`media-${index}`} 
style={styles.mediaItem}
onPress={() => {
}}
>
<View style={styles.videoPlaceholder}>
<Icon name="play-circle" size={40} color="#FF4500" />
<Text style={styles.videoText}>Video</Text>
</View>
</TouchableOpacity>
);
}
return null;
})}
</View>
);
})()}
{discussionDetail?.stock && (
<View style={styles.stockInfo}>
<Icon name="trending-up" size={16} color="#34C759" />
<Text style={styles.stockName}>{discussionDetail.stock.companyName}</Text>
</View>
)}
</View>
{/* Voting Section */}
<View style={styles.votingCard}>
<Text style={styles.votingTitle}>Vote on this discussion</Text>
<View style={styles.votingButtons}>
<TouchableOpacity 
style={[styles.downvoteButton, modalUserVote === 'downvote' && styles.downvoteButtonActive]}
onPress={() => handleModalVote('downvote')}
>
<Icon name="chevron-down" size={20} color={modalUserVote === 'downvote' ? "#FFFFFF" : "#FF3B30"} />
<Text style={[styles.downvoteText, modalUserVote === 'downvote' && styles.downvoteTextActive]}>Downvote</Text>
</TouchableOpacity>
<View style={styles.scoreDisplay}>
<Text style={styles.scoreNumber}>{modalLocalScore}</Text>
<Text style={styles.scoreLabel}>Score</Text>
</View>
<TouchableOpacity 
style={[styles.upvoteButton, modalUserVote === 'upvote' && styles.upvoteButtonActive]}
onPress={() => handleModalVote('upvote')}
>
<Icon name="chevron-up" size={20} color={modalUserVote === 'upvote' ? "#FFFFFF" : "#34C759"} />
<Text style={[styles.upvoteText, modalUserVote === 'upvote' && styles.upvoteTextActive]}>Upvote</Text>
</TouchableOpacity>
</View>
</View>
{/* Comments Section */}
<View style={styles.commentsCard}>
<View style={styles.commentsHeader}>
<Icon name="message-circle" size={20} color="#007AFF" />
<Text style={styles.commentsTitle}>Comments ({discussionDetail?.commentCount || 0})</Text>
</View>
<View style={styles.commentsList}>
{discussionDetail?.comments?.length > 0 ? (
discussionDetail.comments.map((comment: any, index: number) => (
<View key={index} style={styles.commentCard}>
<View style={styles.commentHeader}>
<View style={styles.commentUserAvatar}>
<Text style={styles.commentUserAvatarText}>
{comment.user?.name?.charAt(0) || 'U'}
</Text>
</View>
<View style={styles.commentUserInfo}>
<Text style={styles.commentUserName}>{comment.user?.name}</Text>
<Text style={styles.commentTime}>
{comment.createdAt ? new Date(comment.createdAt).toLocaleDateString() : ''}
</Text>
</View>
</View>
<Text style={styles.commentContent}>{comment.content}</Text>
</View>
))
) : (
<View style={styles.noCommentsCard}>
<Icon name="message-circle" size={32} color="#C7C7CC" />
<Text style={styles.noCommentsText}>No comments yet</Text>
<Text style={styles.noCommentsSubtext}>Be the first to share your thoughts!</Text>
</View>
)}
</View>
</View>
{/* Add Comment Section */}
<View style={styles.addCommentCard}>
<Text style={styles.addCommentTitle}>Add a comment</Text>
<View style={styles.commentInputContainer}>
<TextInput
style={styles.commentInput}
value={commentContent}
onChangeText={setCommentContent}
placeholder="Share your thoughts..."
placeholderTextColor="#8E8E93"
multiline
numberOfLines={3}
/>
<TouchableOpacity
style={[
styles.commentSubmitButton,
!commentContent.trim() && styles.commentSubmitButtonDisabled
]}
onPress={handleInlineCommentSubmit}
disabled={!commentContent.trim() || isCommenting}
>
<Icon name="send" size={16} color="#FFFFFF" />
<Text style={styles.commentSubmitText}>
{isCommenting ? 'Posting...' : 'Post'}
</Text>
</TouchableOpacity>
</View>
</View>
{/* Add bottom padding for better scrolling */}
<View style={styles.bottomPadding} />
</ScrollView>
<View style={styles.modalFooter}>
<TouchableOpacity
style={styles.closeButtonFooter}
onPress={() => setShowDiscussionDetail(false)}
>
<Text style={styles.closeButtonText}>Close</Text>
</TouchableOpacity>
</View>
</View>
</KeyboardAvoidingView>
</Modal>

{/* Prediction Modal */}
<PredictionModal
  visible={showPrediction}
  onClose={() => setShowPrediction(false)}
  onCreated={() => {
    refetchDiscussions?.();
    setShowPrediction(false);
  }}
/>

{/* Poll Modal */}
<PollModal
  visible={showPoll}
  onClose={() => setShowPoll(false)}
  onCreated={() => {
    refetchDiscussions?.();
    setShowPoll(false);
  }}
/>
</View>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#FFFFFF',
paddingTop: 0,
},
header: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingHorizontal: 12,
paddingVertical: 10,
paddingTop: 18,
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  leaderboardButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  leaderboardButtonText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
headerTitle: {
fontSize: 24,
fontWeight: '700',
color: '#1C1C1E',
},
createButton: {
width: 40,
height: 40,
borderRadius: 20,
backgroundColor: '#34C759',
justifyContent: 'center',
alignItems: 'center',
},
content: {
flex: 1,
backgroundColor: '#FFFFFF',
},
modalContainer: {
flex: 1,
justifyContent: 'flex-end',
backgroundColor: 'rgba(0, 0, 0, 0.5)',
},
modalContent: {
backgroundColor: '#FFFFFF',
borderTopLeftRadius: 20,
borderTopRightRadius: 20,
paddingBottom: 34,
maxHeight: '90%',
flex: 1,
},
modalHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingHorizontal: 20,
paddingVertical: 16,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
modalTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
},
closeButton: {
padding: 4,
},
modalBody: {
paddingHorizontal: 20,
paddingVertical: 16,
flex: 1,
},
modalLabel: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 8,
marginTop: 16,
},
descriptionHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
marginTop: 16,
},
textInput: {
borderWidth: 1,
borderColor: '#E5E5EA',
borderRadius: 12,
paddingHorizontal: 16,
paddingVertical: 12,
fontSize: 16,
backgroundColor: '#FFFFFF',
},
textArea: {
height: 100,
textAlignVertical: 'top',
},
modalFooter: {
paddingHorizontal: 20,
paddingVertical: 16,
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
},
closeButtonFooter: {
paddingVertical: 16,
borderRadius: 12,
backgroundColor: '#F2F2F7',
alignItems: 'center',
},
closeButtonText: {
fontSize: 16,
fontWeight: '600',
color: '#8E8E93',
},
// New Card Styles
contentCard: {
backgroundColor: '#FFFFFF',
borderRadius: 16,
padding: 20,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 3,
},
contentHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'flex-start',
marginBottom: 16,
},
headerActions: {
alignItems: 'flex-end',
gap: 8,
},
actionButtons: {
flexDirection: 'row',
gap: 8,
},
actionButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#FFFFFF',
paddingHorizontal: 16,
paddingVertical: 10,
borderRadius: 25,
borderWidth: 2,
borderColor: '#007AFF',
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
minWidth: 80,
justifyContent: 'center',
},
actionButtonText: {
fontSize: 14,
fontWeight: '700',
marginLeft: 6,
color: '#007AFF',
},
saveButton: {
borderColor: '#FF9500',
},
saveButtonText: {
color: '#FF9500',
},
userInfo: {
flexDirection: 'row',
alignItems: 'center',
flex: 1,
},
userAvatar: {
width: 40,
height: 40,
borderRadius: 20,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
marginRight: 12,
},
userAvatarText: {
color: '#FFFFFF',
fontSize: 16,
fontWeight: '600',
},
userDetails: {
flex: 1,
},
userName: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 2,
},
postTime: {
fontSize: 14,
color: '#8E8E93',
},
stockBadge: {
backgroundColor: '#F0F8FF',
paddingHorizontal: 12,
paddingVertical: 6,
borderRadius: 12,
borderWidth: 1,
borderColor: '#007AFF',
},
stockSymbol: {
fontSize: 14,
fontWeight: '600',
color: '#007AFF',
},
discussionContent: {
fontSize: 16,
lineHeight: 24,
color: '#1C1C1E',
marginBottom: 16,
},
stockInfo: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F8F9FA',
paddingHorizontal: 12,
paddingVertical: 8,
borderRadius: 8,
},
stockName: {
fontSize: 14,
color: '#1C1C1E',
marginLeft: 6,
fontWeight: '500',
},
// Voting Section
votingCard: {
backgroundColor: '#FFFFFF',
borderRadius: 16,
padding: 20,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 3,
},
votingTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 16,
textAlign: 'center',
},
votingButtons: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
},
upvoteButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F0FDF4',
paddingHorizontal: 16,
paddingVertical: 12,
borderRadius: 12,
borderWidth: 1,
borderColor: '#34C759',
flex: 1,
marginRight: 8,
justifyContent: 'center',
},
upvoteText: {
fontSize: 14,
fontWeight: '600',
color: '#34C759',
marginLeft: 6,
},
upvoteButtonActive: {
backgroundColor: '#34C759',
borderColor: '#34C759',
},
upvoteTextActive: {
color: '#FFFFFF',
},
downvoteButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#FEF2F2',
paddingHorizontal: 16,
paddingVertical: 12,
borderRadius: 12,
borderWidth: 1,
borderColor: '#FF3B30',
flex: 1,
marginLeft: 8,
justifyContent: 'center',
},
downvoteText: {
fontSize: 14,
fontWeight: '600',
color: '#FF3B30',
marginLeft: 6,
},
downvoteButtonActive: {
backgroundColor: '#FF3B30',
borderColor: '#FF3B30',
},
downvoteTextActive: {
color: '#FFFFFF',
},
scoreDisplay: {
alignItems: 'center',
paddingHorizontal: 20,
},
scoreNumber: {
fontSize: 24,
fontWeight: '700',
color: '#1C1C1E',
},
scoreLabel: {
fontSize: 12,
color: '#8E8E93',
marginTop: 2,
},
// Comments Section
commentsCard: {
backgroundColor: '#FFFFFF',
borderRadius: 16,
padding: 20,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 3,
},
commentsHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 16,
},
commentsTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginLeft: 8,
},
commentsList: {
gap: 12,
},
commentCard: {
backgroundColor: '#F8F9FA',
borderRadius: 12,
padding: 16,
},
commentHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 8,
},
commentUserAvatar: {
width: 32,
height: 32,
borderRadius: 16,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
marginRight: 10,
},
commentUserAvatarText: {
color: '#FFFFFF',
fontSize: 14,
fontWeight: '600',
},
commentUserInfo: {
flex: 1,
},
commentUserName: {
fontSize: 14,
fontWeight: '600',
color: '#1C1C1E',
},
commentTime: {
fontSize: 12,
color: '#8E8E93',
marginTop: 1,
},
commentContent: {
fontSize: 14,
lineHeight: 20,
color: '#1C1C1E',
},
noCommentsCard: {
alignItems: 'center',
paddingVertical: 32,
},
noCommentsText: {
fontSize: 16,
fontWeight: '600',
color: '#8E8E93',
marginTop: 12,
},
noCommentsSubtext: {
fontSize: 14,
color: '#C7C7CC',
marginTop: 4,
},
// Add Comment Section
addCommentCard: {
backgroundColor: '#FFFFFF',
borderRadius: 16,
padding: 20,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 3,
},
addCommentTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 16,
},
// Media Styles
mediaContainer: {
marginTop: 16,
gap: 12,
},
mediaItem: {
position: 'relative',
borderRadius: 12,
overflow: 'hidden',
},
mediaImage: {
width: '100%',
height: 200,
resizeMode: 'cover',
},
mediaOverlay: {
position: 'absolute',
top: 8,
right: 8,
backgroundColor: 'rgba(0, 0, 0, 0.6)',
borderRadius: 20,
padding: 8,
},
videoPlaceholder: {
width: '100%',
height: 200,
backgroundColor: '#F2F2F7',
justifyContent: 'center',
alignItems: 'center',
borderRadius: 12,
},
videoText: {
fontSize: 14,
color: '#8E8E93',
marginTop: 8,
},
emptyState: {
alignItems: 'center',
padding: 40,
},
emptyStateIcon: {
marginBottom: 16,
},
emptyStateText: {
fontSize: 18,
fontWeight: 'bold',
color: '#666',
marginBottom: 8,
textAlign: 'center',
},
emptyStateSubtext: {
fontSize: 14,
color: '#999',
textAlign: 'center',
marginBottom: 20,
lineHeight: 20,
},
emptyStateButton: {
backgroundColor: '#007AFF',
paddingHorizontal: 24,
paddingVertical: 12,
borderRadius: 8,
},
emptyStateButtonText: {
color: '#FFFFFF',
fontSize: 16,
fontWeight: '600',
},
discussionStock: {
fontSize: 14,
color: '#007AFF',
marginBottom: 12,
},
discussionUser: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 8,
},
discussionDate: {
fontSize: 12,
color: '#999',
marginBottom: 16,
},
commentsSection: {
marginBottom: 16,
},
commentItem: {
backgroundColor: '#F2F2F7',
padding: 12,
borderRadius: 8,
marginBottom: 8,
},
commentUser: {
fontSize: 14,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 4,
},
noComments: {
fontSize: 14,
color: '#8E8E93',
fontStyle: 'italic',
textAlign: 'center',
padding: 20,
},
addCommentButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#F2F2F7',
padding: 12,
borderRadius: 8,
gap: 8,
},
addCommentText: {
fontSize: 14,
color: '#007AFF',
fontWeight: '600',
},
bottomPadding: {
height: 100,
},
inlineCommentSection: {
marginTop: 20,
paddingTop: 20,
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
},
commentInputContainer: {
gap: 12,
},
commentInput: {
borderWidth: 1,
borderColor: '#E5E5EA',
borderRadius: 12,
paddingHorizontal: 16,
paddingVertical: 12,
fontSize: 16,
backgroundColor: '#FFFFFF',
minHeight: 80,
textAlignVertical: 'top',
marginBottom: 12,
},
commentSubmitButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#007AFF',
paddingHorizontal: 20,
paddingVertical: 12,
borderRadius: 12,
},
commentSubmitButtonDisabled: {
backgroundColor: '#C7C7CC',
},
commentSubmitText: {
fontSize: 16,
fontWeight: '600',
color: '#FFFFFF',
marginLeft: 6,
},
// Media upload styles
mediaUploadContainer: {
alignItems: 'center',
marginBottom: 16,
},
mediaButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#F2F2F7',
padding: 12,
borderRadius: 8,
borderWidth: 1,
borderColor: '#E5E5EA',
gap: 8,
minWidth: 120,
},
mediaButtonText: {
fontSize: 14,
color: '#007AFF',
fontWeight: '500',
},
mediaButtonSelected: {
backgroundColor: '#007AFF',
borderColor: '#007AFF',
},
mediaButtonTextSelected: {
color: '#FFFFFF',
},
mediaPreview: {
marginBottom: 16,
},
mediaPreviewLabel: {
fontSize: 14,
color: '#1C1C1E',
marginBottom: 8,
fontWeight: '500',
},
mediaPreviewItem: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F2F2F7',
padding: 12,
borderRadius: 8,
borderWidth: 1,
borderColor: '#E5E5EA',
},
mediaPreviewText: {
flex: 1,
fontSize: 14,
color: '#1C1C1E',
},
removeMediaButton: {
padding: 4,
marginLeft: 8,
},
mediaAttachmentIndicator: {
marginBottom: 16,
backgroundColor: '#F0F8FF',
borderRadius: 8,
borderWidth: 1,
borderColor: '#007AFF',
},
mediaAttachmentContent: {
flexDirection: 'row',
alignItems: 'center',
padding: 12,
},
mediaAttachmentText: {
flex: 1,
fontSize: 14,
color: '#007AFF',
fontWeight: '500',
marginLeft: 8,
},
removeAttachmentButton: {
padding: 4,
marginLeft: 8,
},
categoryScrollView: {
marginBottom: 16,
},
categoryContainer: {
paddingHorizontal: 4,
gap: 8,
},
categoryButton: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 12,
paddingVertical: 8,
borderRadius: 20,
borderWidth: 1,
backgroundColor: '#FFFFFF',
gap: 6,
},
categoryButtonSelected: {
backgroundColor: '#007AFF',
},
categoryButtonText: {
fontSize: 12,
fontWeight: '500',
},
categoryButtonTextSelected: {
color: '#FFFFFF',
},
visibilityContainer: {
flexDirection: 'row',
marginBottom: 16,
gap: 12,
},
visibilityOption: {
flex: 1,
padding: 16,
borderRadius: 12,
borderWidth: 2,
borderColor: '#E5E5EA',
backgroundColor: '#FFFFFF',
alignItems: 'center',
},
visibilityOptionSelected: {
borderColor: '#007AFF',
backgroundColor: '#007AFF',
},
visibilityOptionText: {
fontSize: 16,
fontWeight: '600',
color: '#007AFF',
marginTop: 8,
marginBottom: 4,
},
visibilityOptionTextSelected: {
color: '#FFFFFF',
},
visibilityOptionSubtext: {
fontSize: 12,
color: '#8E8E93',
textAlign: 'center',
},
visibilityOptionSubtextSelected: {
color: '#FFFFFF',
},
});
export default SocialScreen;
