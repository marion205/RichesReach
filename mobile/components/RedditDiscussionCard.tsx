import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Linking, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface RedditDiscussionCardProps {
    discussion: {
        id: string;
        title: string;
        content: string;
        discussionType: string;
        visibility?: string;
        createdAt: string;
        score: number;
        commentCount: number;
        user: {
            id: string;
            name: string;
            profilePic?: string;
            followersCount?: number;
            followingCount?: number;
            isFollowingUser?: boolean;
        };
        stock?: {
            symbol: string;
            companyName: string;
        } | null;
        upvotes?: number;
        downvotes?: number;
    };
    onUpvote: () => void;
    onDownvote: () => void;
    onComment: () => void;
    onPress: () => void;
}
const RedditDiscussionCard: React.FC<RedditDiscussionCardProps> = ({
    discussion,
    onUpvote,
    onDownvote,
    onComment,
    onPress,
}) => {
id: discussion.id,
title: discussion.title,
score: discussion.score,
commentCount: discussion.commentCount
});
const [userVote, setUserVote] = useState<'upvote' | 'downvote' | null>(null);
const [localScore, setLocalScore] = useState(discussion.score);
const [isSaved, setIsSaved] = useState(false);
// Helper functions for media detection
const isImageUrl = (url: string) => {
return /\.(jpg|jpeg|png|gif|webp)$/i.test(url);
};
const isVideoUrl = (url: string) => {
return /\.(mp4|mov|avi|webm|youtube\.com|youtu\.be|vimeo\.com)$/i.test(url);
};
const extractLinks = (text: string) => {
const urlRegex = /(https?:\/\/[^\s]+)/g;
return text.match(urlRegex) || [];
};
const extractMedia = (text: string) => {
const mediaRegex = /\[(IMAGE|VIDEO):\s*([^\]]+)\]/g;
const matches = [];
let match;
while ((match = mediaRegex.exec(text)) !== null) {
matches.push({
type: match[1].toLowerCase(),
uri: match[2].trim()
});
}
return matches;
};
const handleVote = (voteType: 'upvote' | 'downvote') => {
if (userVote === voteType) {
// Remove vote if clicking same button
setUserVote(null);
// Revert the score change
if (voteType === 'upvote') {
setLocalScore(prev => prev - 1);
} else {
setLocalScore(prev => prev + 1);
}
} else {
// Handle vote change
if (userVote === null) {
// First vote
setUserVote(voteType);
if (voteType === 'upvote') {
setLocalScore(prev => prev + 1);
} else {
setLocalScore(prev => prev - 1);
}
} else {
// Switching from one vote to another
if (userVote === 'upvote' && voteType === 'downvote') {
// Switching from upvote to downvote: -1 (remove upvote) -1 (add downvote) = -2
setLocalScore(prev => prev - 2);
} else if (userVote === 'downvote' && voteType === 'upvote') {
// Switching from downvote to upvote: +1 (remove downvote) +1 (add upvote) = +2
setLocalScore(prev => prev + 2);
}
setUserVote(voteType);
}
// Call the parent handlers
if (voteType === 'upvote') {
onUpvote();
} else {
onDownvote();
}
}
};
const getDiscussionIcon = (type: string) => {
switch (type) {
case 'analysis': return 'bar-chart-2';
case 'news': return 'file-text';
case 'strategy': return 'target';
case 'question': return 'help-circle';
case 'meme': return 'smile';
default: return 'message-circle';
}
};
const getDiscussionColor = (type: string) => {
switch (type) {
case 'analysis': return '#34C759';
case 'news': return '#34C759';
case 'strategy': return '#FF9500';
case 'question': return '#AF52DE';
case 'meme': return '#FF3B30';
default: return '#8E8E93';
}
};
const formatDate = (dateString: string) => {
const date = new Date(dateString);
const now = new Date();
const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
if (diffInHours < 1) return 'Just now';
if (diffInHours < 24) return `${diffInHours}h ago`;
return date.toLocaleDateString();
};
const links = extractLinks(discussion.content);
const mediaItems = extractMedia(discussion.content);
const hasMedia = links.some(link => isImageUrl(link) || isVideoUrl(link)) || mediaItems.length > 0;
return (
<View style={styles.container}>
{/* Reddit-style voting sidebar */}
<View style={styles.votingSidebar}>
<TouchableOpacity 
style={[styles.voteButton, userVote === 'upvote' && styles.voteButtonActive]}
onPress={(e) => {
e.preventDefault();
e.stopPropagation();
handleVote('upvote');
}}
activeOpacity={0.7}
>
<Icon 
name="chevron-up" 
size={24} 
color={userVote === 'upvote' ? '#FF4500' : '#8E8E93'} 
/>
</TouchableOpacity>
<Text style={styles.scoreText}>{localScore}</Text>
<TouchableOpacity 
style={[styles.voteButton, userVote === 'downvote' && styles.voteButtonActive]}
onPress={(e) => {
e.preventDefault();
e.stopPropagation();
handleVote('downvote');
}}
activeOpacity={0.7}
>
<Icon 
name="chevron-down" 
size={24} 
color={userVote === 'downvote' ? '#7193FF' : '#8E8E93'} 
/>
</TouchableOpacity>
</View>
{/* Main content area */}
<TouchableOpacity style={styles.contentArea} onPress={onPress}>
{/* Header with user info and type badge */}
<View style={styles.header}>
                <View style={styles.userInfo}>
                    <TouchableOpacity 
                        style={styles.avatarContainer}
                        onPress={() => {
                            // TODO: Navigate to user profile or show profile modal
                            Alert.alert(
                                'User Profile',
                                `${discussion.user.name}`,
                                [
                                    { text: 'Close', style: 'cancel' },
                                ]
                            );
                        }}
                        activeOpacity={0.7}
                    >
                        {discussion.user.profilePic ? (
                            <Image
                                source={{ uri: discussion.user.profilePic }}
                                style={styles.avatar}
                            />
                        ) : (
                            <View style={styles.avatarFallback}>
                                <Text style={styles.avatarText}>
                                    {discussion.user.name.charAt(0).toUpperCase()}
                                </Text>
                            </View>
                        )}
                    </TouchableOpacity>
                <View style={styles.userDetails}>
                    <TouchableOpacity 
                        onPress={() => {
                            Alert.alert(
                                'User Profile',
                                `${discussion.user.name}`,
                                [
                                    { text: 'Close', style: 'cancel' },
                                ]
                            );
                        }}
                        activeOpacity={0.7}
                    >
                        <Text style={styles.userName} numberOfLines={1} ellipsizeMode="tail">{discussion.user.name}</Text>
                    </TouchableOpacity>
                    <Text style={styles.timestamp}>{formatDate(discussion.createdAt)}</Text>
                </View>
</View>
<View style={styles.badgeContainer}>
<View style={styles.typeBadge}>
<Icon
name={getDiscussionIcon(discussion.discussionType) as any}
size={12}
color={getDiscussionColor(discussion.discussionType)}
/>
<Text style={[
styles.typeLabel,
{ color: getDiscussionColor(discussion.discussionType) }
]}>
{discussion.discussionType}
</Text>
</View>
{discussion.visibility && (
<View style={[
styles.visibilityBadge,
discussion.visibility === 'public' ? styles.publicBadge : styles.followersBadge
]}>
<Icon
name={discussion.visibility === 'public' ? 'globe' : 'users'}
size={10}
color={discussion.visibility === 'public' ? '#FFFFFF' : '#007AFF'}
/>
<Text style={[
styles.visibilityLabel,
discussion.visibility === 'public' ? styles.publicLabel : styles.followersLabel
]}>
{discussion.visibility === 'public' ? 'Public' : 'Followers'}
</Text>
</View>
)}
</View>
</View>
{/* Stock info if available */}
{discussion.stock && (
<View style={styles.stockInfo}>
<Text style={styles.stockSymbol}>${discussion.stock.symbol}</Text>
<Text style={styles.stockName}>{discussion.stock.companyName}</Text>
</View>
)}
{/* Title */}
<Text style={styles.title}>{discussion.title}</Text>
{/* Content with media detection */}
<View style={styles.content}>
<Text style={styles.description}>
{discussion.content.replace(/\[(IMAGE|VIDEO):\s*[^\]]+\]/g, '').trim()}
</Text>
{/* Display media if detected */}
{hasMedia && (
<View style={styles.mediaContainer}>
{/* Display uploaded media first */}
{mediaItems.map((media, index) => {
if (media.type === 'image') {
return (
<TouchableOpacity 
key={`media-${index}`} 
style={styles.mediaItem}
onPress={() => Linking.openURL(media.uri)}
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
onPress={() => Linking.openURL(media.uri)}
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
{/* Display regular links */}
{links.map((link, index) => {
if (isImageUrl(link)) {
return (
<TouchableOpacity 
key={`link-${index}`} 
style={styles.mediaItem}
onPress={() => Linking.openURL(link)}
>
<Image source={{ uri: link }} style={styles.mediaImage} />
<View style={styles.mediaOverlay}>
<Icon name="image" size={20} color="white" />
</View>
</TouchableOpacity>
);
} else if (isVideoUrl(link)) {
return (
<TouchableOpacity 
key={`link-${index}`} 
style={styles.mediaItem}
onPress={() => Linking.openURL(link)}
>
<View style={styles.videoPlaceholder}>
<Icon name="play-circle" size={40} color="#FF4500" />
<Text style={styles.videoText}>Video</Text>
</View>
</TouchableOpacity>
);
} else {
return (
<TouchableOpacity 
key={`link-${index}`} 
style={styles.linkItem}
onPress={() => Linking.openURL(link)}
>
<Icon name="external-link" size={16} color="#FF4500" />
<Text style={styles.linkText} numberOfLines={1}>{link}</Text>
</TouchableOpacity>
);
}
})}
</View>
)}
</View>
{/* Action buttons */}
<View style={styles.actions}>
<TouchableOpacity 
style={styles.actionButton} 
onPress={() => {
onComment();
}}
>
<Icon name="message-circle" size={18} color="#8E8E93" />
<Text style={styles.actionText}>{discussion.commentCount} Comments</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => {
// Create share text
const shareText = `Check out this discussion: "${discussion.title}"\n\n${discussion.content?.replace(/\[(IMAGE|VIDEO):\s*[^\]]+\]/g, '').trim()}\n\nShared from RichesReach`;
// For now, we'll use a simple alert
// In a real app, you'd use React Native's Share API
setTimeout(() => {
Alert.alert(
'Share Discussion',
'Discussion content ready to share!',
[
{ text: 'Cancel', style: 'cancel' },
{ 
text: 'Copy Link', 
onPress: () => {
Alert.alert('Success', 'Discussion link copied to clipboard!');
}
}
]
);
}, 100);
}}
>
<Icon name="share" size={18} color="#8E8E93" />
<Text style={styles.actionText}>Share</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => {
// Toggle saved state
setIsSaved(!isSaved);
if (!isSaved) {
// Saving
setTimeout(() => {
Alert.alert('Success', 'Discussion saved to your bookmarks!');
}, 100);
} else {
// Unsaving
setTimeout(() => {
Alert.alert('Success', 'Discussion removed from your bookmarks!');
}, 100);
}
}}
>
<Icon 
name={isSaved ? "bookmark" : "bookmark"} 
size={18} 
color={isSaved ? "#FF9500" : "#8E8E93"} 
style={isSaved ? { fill: "#FF9500" } : {}} 
/>
<Text style={[styles.actionText, isSaved && styles.savedText]}>
{isSaved ? 'Saved' : 'Save'}
</Text>
</TouchableOpacity>
</View>
</TouchableOpacity>
</View>
);
};
const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        backgroundColor: '#FFFFFF',
        marginHorizontal: 0,
        marginVertical: 2,
        borderRadius: 0,
        borderWidth: 0,
        borderBottomWidth: 1,
        borderColor: '#E1E5E9',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
votingSidebar: {
width: 50,
alignItems: 'center',
paddingVertical: 8,
backgroundColor: '#FAFAFA',
borderTopLeftRadius: 8,
borderBottomLeftRadius: 8,
},
voteButton: {
padding: 4,
borderRadius: 4,
},
voteButtonActive: {
backgroundColor: '#F0F0F0',
},
scoreText: {
fontSize: 12,
fontWeight: 'bold',
color: '#1A1A1B',
marginVertical: 4,
},
contentArea: {
flex: 1,
padding: 12,
},
header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    flexWrap: 'nowrap',
    minHeight: 32,
},
    userInfo: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
        flexShrink: 1,
        minWidth: 0,
        flexWrap: 'nowrap',
        maxWidth: 150,
    },
    avatarContainer: {
        marginRight: 8,
    },
    avatar: {
        width: 20,
        height: 20,
        borderRadius: 10,
    },
avatarFallback: {
width: 20,
height: 20,
borderRadius: 10,
backgroundColor: '#FF4500',
justifyContent: 'center',
alignItems: 'center',
marginRight: 8,
},
avatarText: {
color: 'white',
fontSize: 10,
fontWeight: 'bold',
},
    userDetails: {
        flex: 1,
        minWidth: 0,
        flexShrink: 1,
        flexWrap: 'nowrap',
        maxWidth: 100,
    },
    userName: {
        fontSize: 11,
        color: '#1A1A1B',
        fontWeight: '600',
        marginRight: 8,
        flexShrink: 1,
        flexWrap: 'nowrap',
        maxWidth: 80,
        minWidth: 0,
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        textAlign: 'left',
    },
    timestamp: {
        fontSize: 11,
        color: '#878A8C',
    },
badgeContainer: {
flexDirection: 'row',
alignItems: 'center',
gap: 8,
},
typeBadge: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F6F7F8',
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 12,
},
visibilityBadge: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 6,
paddingVertical: 3,
borderRadius: 10,
},
publicBadge: {
backgroundColor: '#34C759',
},
followersBadge: {
backgroundColor: '#F6F7F8',
borderWidth: 1,
borderColor: '#007AFF',
},
visibilityLabel: {
fontSize: 9,
fontWeight: '600',
marginLeft: 3,
textTransform: 'uppercase',
},
publicLabel: {
color: '#FFFFFF',
},
followersLabel: {
color: '#007AFF',
},
typeLabel: {
fontSize: 10,
fontWeight: '600',
marginLeft: 4,
textTransform: 'uppercase',
},
stockInfo: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 8,
},
stockSymbol: {
fontSize: 14,
fontWeight: 'bold',
color: '#1A1A1B',
marginRight: 8,
},
stockName: {
fontSize: 12,
color: '#878A8C',
},
title: {
fontSize: 16,
fontWeight: '600',
color: '#1A1A1B',
marginBottom: 8,
lineHeight: 22,
},
content: {
marginBottom: 12,
},
description: {
fontSize: 14,
color: '#1A1A1B',
lineHeight: 20,
},
mediaContainer: {
marginTop: 8,
},
mediaItem: {
position: 'relative',
marginBottom: 8,
},
mediaImage: {
width: '100%',
height: 200,
borderRadius: 8,
resizeMode: 'cover',
},
mediaOverlay: {
position: 'absolute',
top: 8,
right: 8,
backgroundColor: 'rgba(0,0,0,0.6)',
padding: 4,
borderRadius: 4,
},
videoPlaceholder: {
height: 120,
backgroundColor: '#F6F7F8',
borderRadius: 8,
justifyContent: 'center',
alignItems: 'center',
borderWidth: 1,
borderColor: '#E1E5E9',
},
videoText: {
fontSize: 12,
color: '#878A8C',
marginTop: 4,
},
linkItem: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F6F7F8',
padding: 12,
borderRadius: 8,
borderWidth: 1,
borderColor: '#E1E5E9',
},
linkText: {
fontSize: 12,
color: '#1A1A1B',
marginLeft: 8,
flex: 1,
},
actions: {
flexDirection: 'row',
alignItems: 'center',
paddingTop: 8,
borderTopWidth: 1,
borderTopColor: '#F6F7F8',
},
actionButton: {
flexDirection: 'row',
alignItems: 'center',
marginRight: 16,
paddingVertical: 4,
},
actionText: {
fontSize: 12,
color: '#878A8C',
marginLeft: 4,
fontWeight: '500',
},
savedText: {
color: '#FF9500',
fontWeight: '600',
},
});
export default RedditDiscussionCard;
