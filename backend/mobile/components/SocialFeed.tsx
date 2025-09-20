import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
TouchableOpacity,
ScrollView,
Image,
RefreshControl,
Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { gql, useQuery, useMutation } from '@apollo/client';
import MockUserService from '../services/MockUserService';
// GraphQL Queries
const GET_SOCIAL_FEED = gql`
query GetSocialFeed($limit: Int, $offset: Int) {
socialFeed(limit: $limit, offset: $offset) {
id
type
createdAt
user {
id
name
profilePic
experienceLevel
}
content
portfolio {
id
name
totalValue
totalReturnPercent
}
stock {
symbol
companyName
currentPrice
changePercent
}
likesCount
commentsCount
isLiked
comments {
id
content
createdAt
user {
id
name
profilePic
}
}
}
}
`;
const LIKE_POST = gql`
mutation LikePost($postId: ID!) {
likePost(postId: $postId) {
success
message
}
}
`;
const UNLIKE_POST = gql`
mutation UnlikePost($postId: ID!) {
unlikePost(postId: $postId) {
success
message
}
}
`;
const ADD_COMMENT = gql`
mutation AddComment($postId: ID!, $content: String!) {
addComment(postId: $postId, content: $content) {
success
message
comment {
id
content
createdAt
user {
id
name
profilePic
}
}
}
}
`;
interface SocialFeedProps {
onNavigate: (screen: string, params?: any) => void;
userId?: string; // If provided, shows feed for specific user
}
interface SocialPost {
id: string;
type: 'portfolio_update' | 'stock_purchase' | 'stock_sale' | 'achievement' | 'learning_complete' | 'market_comment';
createdAt: string;
user: {
id: string;
name: string;
profilePic?: string;
experienceLevel: string;
};
content: string;
portfolio?: {
id: string;
name: string;
totalValue: number;
totalReturnPercent: number;
};
stock?: {
symbol: string;
companyName: string;
currentPrice: number;
changePercent: number;
};
likesCount: number;
commentsCount: number;
isLiked: boolean;
comments: Array<{
id: string;
content: string;
createdAt: string;
user: {
id: string;
name: string;
profilePic?: string;
};
}>;
}
const SocialFeed: React.FC<SocialFeedProps> = ({ onNavigate, userId }) => {
const [refreshing, setRefreshing] = useState(false);
const [showComments, setShowComments] = useState<{ [key: string]: boolean }>({});
const [posts, setPosts] = useState<any[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const mockUserService = MockUserService.getInstance();
// Load posts from mock service
const loadPosts = () => {
setLoading(true);
setError(null);
try {
const mockPosts = mockUserService.getSocialFeedPosts();
setPosts(mockPosts);
} catch (err) {
setError('Failed to load posts');
console.error('Error loading posts:', err);
} finally {
setLoading(false);
}
};
const handleRefresh = async () => {
setRefreshing(true);
try {
loadPosts();
} catch (error) {
console.error('Error refreshing feed:', error);
} finally {
setRefreshing(false);
}
};
// Load posts when component mounts
useEffect(() => {
loadPosts();
}, []);
const handleLikeToggle = async (postId: string, isLiked: boolean) => {
try {
// For now, just update the local state since we're using mock data
setPosts(prevPosts => 
prevPosts.map(post => 
post.id === postId 
? { 
...post, 
isLiked: !isLiked, 
likesCount: isLiked ? post.likesCount - 1 : post.likesCount + 1 
}
: post
)
);
} catch (error) {
console.error('Error toggling like:', error);
Alert.alert('Error', 'Failed to update like status. Please try again.');
}
};
const handleAddComment = async (postId: string, content: string) => {
try {
// For now, just update the local state since we're using mock data
setPosts(prevPosts => 
prevPosts.map(post => 
post.id === postId 
? { 
...post, 
commentsCount: post.commentsCount + 1,
comments: [
...post.comments,
{
id: `comment-${Date.now()}`,
content,
createdAt: new Date().toISOString(),
user: { name: 'You', profilePic: null }
}
]
}
: post
)
);
} catch (error) {
console.error('Error adding comment:', error);
Alert.alert('Error', 'Failed to add comment. Please try again.');
}
};
const toggleComments = (postId: string) => {
setShowComments(prev => ({
...prev,
[postId]: !prev[postId],
}));
};
const getPostIcon = (type: string) => {
switch (type) {
case 'portfolio_update': return 'pie-chart';
case 'stock_purchase': return 'trending-up';
case 'stock_sale': return 'trending-down';
case 'achievement': return 'award';
case 'learning_complete': return 'book-open';
case 'market_comment': return 'message-circle';
default: return 'activity';
}
};
const getPostColor = (type: string) => {
switch (type) {
case 'portfolio_update': return '#007AFF';
case 'stock_purchase': return '#34C759';
case 'stock_sale': return '#FF3B30';
case 'achievement': return '#FFD700';
case 'learning_complete': return '#AF52DE';
case 'market_comment': return '#FF9500';
default: return '#8E8E93';
}
};
const formatTimeAgo = (dateString: string) => {
const date = new Date(dateString);
const now = new Date();
const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
if (diffInSeconds < 60) return 'Just now';
if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
return date.toLocaleDateString();
};
const renderPost = (post: SocialPost) => (
<View key={post.id} style={styles.postCard}>
{/* Post Header */}
<View style={styles.postHeader}>
<TouchableOpacity
style={styles.userInfo}
onPress={() => onNavigate('user-profile', { userId: post.user.id })}
>
{post.user.profilePic ? (
<Image source={{ uri: post.user.profilePic }} style={styles.userAvatar} />
) : (
<View style={styles.userAvatarPlaceholder}>
<Text style={styles.userAvatarText}>{post.user.name.charAt(0).toUpperCase()}</Text>
</View>
)}
<View style={styles.userDetails}>
<Text style={styles.userName}>{post.user.name}</Text>
<Text style={styles.userLevel}>
{post.user.experienceLevel.charAt(0).toUpperCase()}{post.user.experienceLevel.slice(1)} Investor
</Text>
</View>
</TouchableOpacity>
<View style={styles.postMeta}>
<Icon name={getPostIcon(post.type)} size={16} color={getPostColor(post.type)} />
<Text style={styles.postTime}>{formatTimeAgo(post.createdAt)}</Text>
</View>
</View>
{/* Post Content */}
<View style={styles.postContent}>
<Text style={styles.postText}>{post.content}</Text>
{/* Portfolio Info */}
{post.portfolio && (
<TouchableOpacity
style={styles.portfolioInfo}
onPress={() => onNavigate('portfolio-detail', { portfolioId: post.portfolio?.id })}
>
<View style={styles.portfolioHeader}>
<Text style={styles.portfolioName}>{post.portfolio.name}</Text>
<View style={[
styles.returnBadge,
{ backgroundColor: post.portfolio.totalReturnPercent >= 0 ? '#E8F5E8' : '#FFE8E8' }
]}>
<Text style={[
styles.returnText,
{ color: post.portfolio.totalReturnPercent >= 0 ? '#34C759' : '#FF3B30' }
]}>
{post.portfolio.totalReturnPercent >= 0 ? '+' : ''}{post.portfolio.totalReturnPercent.toFixed(2)}%
</Text>
</View>
</View>
<Text style={styles.portfolioValue}>
${post.portfolio.totalValue.toLocaleString()}
</Text>
</TouchableOpacity>
)}
{/* Stock Info */}
{post.stock && (
<TouchableOpacity
style={styles.stockInfo}
onPress={() => onNavigate('stock-detail', { symbol: post.stock?.symbol })}
>
<View style={styles.stockHeader}>
<Text style={styles.stockSymbol}>{post.stock.symbol}</Text>
<Text style={styles.stockName}>{post.stock.companyName}</Text>
</View>
<View style={styles.stockPrice}>
<Text style={styles.stockPriceValue}>${post.stock.currentPrice.toFixed(2)}</Text>
<Text style={[
styles.stockChange,
{ color: post.stock.changePercent >= 0 ? '#34C759' : '#FF3B30' }
]}>
{post.stock.changePercent >= 0 ? '+' : ''}{post.stock.changePercent.toFixed(2)}%
</Text>
</View>
</TouchableOpacity>
)}
</View>
{/* Post Actions */}
<View style={styles.postActions}>
<TouchableOpacity
style={styles.actionButton}
onPress={() => handleLikeToggle(post.id, post.isLiked)}
>
<Icon
name={post.isLiked ? 'heart' : 'heart'}
size={18}
color={post.isLiked ? '#FF3B30' : '#8E8E93'}
/>
<Text style={[styles.actionText, post.isLiked && styles.actionTextActive]}>
{post.likesCount}
</Text>
</TouchableOpacity>
<TouchableOpacity
style={styles.actionButton}
onPress={() => toggleComments(post.id)}
>
<Icon name="message-circle" size={18} color="#8E8E93" />
<Text style={styles.actionText}>{post.commentsCount}</Text>
</TouchableOpacity>
<TouchableOpacity
style={styles.actionButton}
onPress={() => onNavigate('share-post', { postId: post.id })}
>
<Icon name="share" size={18} color="#8E8E93" />
<Text style={styles.actionText}>Share</Text>
</TouchableOpacity>
</View>
{/* Comments Section */}
{showComments[post.id] && (
<View style={styles.commentsSection}>
{post.comments.map((comment) => (
<View key={comment.id} style={styles.comment}>
<View style={styles.commentHeader}>
{comment.user.profilePic ? (
<Image source={{ uri: comment.user.profilePic }} style={styles.commentAvatar} />
) : (
<View style={styles.commentAvatarPlaceholder}>
<Text style={styles.commentAvatarText}>{comment.user.name.charAt(0).toUpperCase()}</Text>
</View>
)}
<View style={styles.commentDetails}>
<Text style={styles.commentUserName}>{comment.user.name}</Text>
<Text style={styles.commentTime}>{formatTimeAgo(comment.createdAt)}</Text>
</View>
</View>
<Text style={styles.commentText}>{comment.content}</Text>
</View>
))}
<TouchableOpacity
style={styles.addCommentButton}
onPress={() => onNavigate('add-comment', { postId: post.id })}
>
<Icon name="plus" size={16} color="#007AFF" />
<Text style={styles.addCommentText}>Add a comment</Text>
</TouchableOpacity>
</View>
)}
</View>
);
if (loading) {
return (
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading social feed...</Text>
</View>
);
}
if (error) {
return (
<View style={styles.errorContainer}>
<Icon name="alert-circle" size={24} color="#FF3B30" />
<Text style={styles.errorText}>Unable to load social feed</Text>
<TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
<Text style={styles.retryButtonText}>Retry</Text>
</TouchableOpacity>
</View>
);
}
return (
<ScrollView
style={styles.container}
refreshControl={
<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
}
showsVerticalScrollIndicator={false}
>
{posts.length === 0 ? (
<View style={styles.emptyContainer}>
<Icon name="users" size={48} color="#8E8E93" />
<Text style={styles.emptyTitle}>No Activity Yet</Text>
<Text style={styles.emptyText}>
Follow other investors to see their portfolio updates and market insights
</Text>
<TouchableOpacity
style={styles.exploreButton}
onPress={() => onNavigate('discover-users')}
>
<Text style={styles.exploreButtonText}>Discover Investors</Text>
</TouchableOpacity>
</View>
) : (
posts.map(renderPost)
)}
</ScrollView>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 20,
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
},
errorContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 20,
},
errorText: {
fontSize: 16,
color: '#FF3B30',
marginTop: 8,
marginBottom: 16,
},
retryButton: {
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 20,
},
retryButtonText: {
fontSize: 16,
color: '#FFFFFF',
fontWeight: '600',
},
emptyContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
emptyTitle: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
emptyText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 22,
marginBottom: 24,
},
exploreButton: {
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 20,
},
exploreButtonText: {
fontSize: 16,
color: '#FFFFFF',
fontWeight: '600',
},
// Post Card
postCard: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginVertical: 8,
borderRadius: 16,
padding: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
// Post Header
postHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 12,
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
marginRight: 12,
},
userAvatarPlaceholder: {
width: 40,
height: 40,
borderRadius: 20,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
marginRight: 12,
},
userAvatarText: {
fontSize: 16,
fontWeight: 'bold',
color: '#FFFFFF',
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
userLevel: {
fontSize: 12,
color: '#8E8E93',
},
postMeta: {
flexDirection: 'row',
alignItems: 'center',
},
postTime: {
fontSize: 12,
color: '#8E8E93',
marginLeft: 6,
},
// Post Content
postContent: {
marginBottom: 16,
},
postText: {
fontSize: 16,
color: '#1C1C1E',
lineHeight: 22,
marginBottom: 12,
},
// Portfolio Info
portfolioInfo: {
backgroundColor: '#F2F2F7',
borderRadius: 12,
padding: 12,
marginBottom: 8,
},
portfolioHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
},
portfolioName: {
fontSize: 14,
fontWeight: '600',
color: '#1C1C1E',
},
returnBadge: {
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 12,
},
returnText: {
fontSize: 12,
fontWeight: '600',
},
portfolioValue: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
},
// Stock Info
stockInfo: {
backgroundColor: '#F2F2F7',
borderRadius: 12,
padding: 12,
marginBottom: 8,
},
stockHeader: {
marginBottom: 8,
},
stockSymbol: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
},
stockName: {
fontSize: 12,
color: '#8E8E93',
},
stockPrice: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
},
stockPriceValue: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
},
stockChange: {
fontSize: 14,
fontWeight: '600',
},
// Post Actions
postActions: {
flexDirection: 'row',
justifyContent: 'space-around',
paddingTop: 12,
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
},
actionButton: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 8,
paddingHorizontal: 12,
},
actionText: {
fontSize: 14,
color: '#8E8E93',
marginLeft: 6,
},
actionTextActive: {
color: '#FF3B30',
},
// Comments Section
commentsSection: {
marginTop: 16,
paddingTop: 16,
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
},
comment: {
marginBottom: 12,
},
commentHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 6,
},
commentAvatar: {
width: 24,
height: 24,
borderRadius: 12,
marginRight: 8,
},
commentAvatarPlaceholder: {
width: 24,
height: 24,
borderRadius: 12,
backgroundColor: '#8E8E93',
justifyContent: 'center',
alignItems: 'center',
marginRight: 8,
},
commentAvatarText: {
fontSize: 10,
fontWeight: 'bold',
color: '#FFFFFF',
},
commentDetails: {
flex: 1,
},
commentUserName: {
fontSize: 12,
fontWeight: '600',
color: '#1C1C1E',
},
commentTime: {
fontSize: 10,
color: '#8E8E93',
},
commentText: {
fontSize: 14,
color: '#1C1C1E',
lineHeight: 20,
marginLeft: 32,
},
addCommentButton: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 8,
paddingHorizontal: 12,
backgroundColor: '#F2F2F7',
borderRadius: 20,
alignSelf: 'flex-start',
},
addCommentText: {
fontSize: 14,
color: '#007AFF',
marginLeft: 6,
fontWeight: '500',
},
});
export default SocialFeed;
