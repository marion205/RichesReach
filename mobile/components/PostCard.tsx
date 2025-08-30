import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInput,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type PostCardProps = {
  post: {
    id: string;
    content: string;
    createdAt: string;
    likesCount: number;
    commentsCount: number;
    isLikedByUser: boolean;
    user: {
      id: string;
      name: string;
      email: string;
      followersCount: number;
      followingCount: number;
      isFollowingUser: boolean;
      isFollowedByUser: boolean;
    };
  };
  onLikePress: (postId: string) => void;
  onCommentPress: (postId: string) => void;
  onFollowPress: (userId: string) => void;
  onUserPress: (userId: string) => void;
  showComments?: boolean;
  commentInput?: string;
  onCommentInputChange?: (text: string) => void;
  onCommentSubmit?: (postId: string) => void;
};

export default function PostCard({
  post,
  onLikePress,
  onCommentPress,
  onFollowPress,
  onUserPress,
  showComments = false,
  commentInput = '',
  onCommentInputChange,
  onCommentSubmit,
}: PostCardProps) {
  return (
    <View style={styles.postCard}>
      <View style={styles.postHeader}>
        <TouchableOpacity 
          style={styles.userInfo}
          onPress={() => onUserPress(post.user.id)}
        >
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{post.user.name.charAt(0).toUpperCase()}</Text>
          </View>
          <Text style={styles.author}>{post.user.name}</Text>
          <Icon name="chevron-right" size={12} color="#00cc99" style={{ marginLeft: 4 }} />
        </TouchableOpacity>
        <Text style={styles.timestamp}>
          {new Date(post.createdAt).toLocaleDateString()}
        </Text>
      </View>
      
      <Text style={styles.content}>{post.content}</Text>
      
      <View style={styles.postActions}>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => onLikePress(post.id)}
        >
          <Icon 
            name={post.isLikedByUser ? "heart" : "heart"} 
            size={20} 
            color={post.isLikedByUser ? "#ff4757" : "#666"} 
            style={{ opacity: post.isLikedByUser ? 1 : 0.6 }}
          />
          <Text style={[styles.actionCount, post.isLikedByUser && styles.likedText]}>
            {post.likesCount}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => onCommentPress(post.id)}
        >
          <Icon name="message-circle" size={20} color="#666" />
          <Text style={styles.actionCount}>{post.commentsCount}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => onFollowPress(post.user.id)}
        >
          <Icon 
            name={post.user.isFollowingUser ? "user-check" : "user-plus"} 
            size={20} 
            color={post.user.isFollowingUser ? "#00cc99" : "#666"} 
          />
          <Text style={[styles.actionText, post.user.isFollowingUser && styles.followingText]}>
            {post.user.isFollowingUser ? "Following" : "Follow"}
          </Text>
        </TouchableOpacity>
      </View>
      
      {showComments && onCommentInputChange && onCommentSubmit && (
        <View style={styles.commentsSection}>
          <View style={styles.commentInputContainer}>
            <TextInput
              style={styles.commentInput}
              placeholder="Write a comment..."
              value={commentInput}
              onChangeText={onCommentInputChange}
              multiline
            />
            <TouchableOpacity 
              style={styles.commentSubmitButton}
              onPress={() => onCommentSubmit(post.id)}
            >
              <Text style={styles.commentSubmitText}>Post</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  postCard: { 
    backgroundColor: '#fff', 
    padding: 20, 
    borderRadius: 12, 
    marginBottom: 15, 
    marginHorizontal: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  postHeader: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 8 
  },
  userInfo: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    padding: 4, 
    borderRadius: 8 
  },
  avatar: { 
    width: 32, 
    height: 32, 
    borderRadius: 16, 
    backgroundColor: '#00cc99', 
    alignItems: 'center', 
    justifyContent: 'center', 
    marginRight: 8 
  },
  avatarText: { 
    fontSize: 14, 
    fontWeight: 'bold', 
    color: '#fff' 
  },
  author: { 
    fontWeight: 'bold', 
    fontSize: 16, 
    color: '#00cc99', 
    textDecorationLine: 'underline' 
  },
  timestamp: { 
    color: '#666', 
    fontSize: 12 
  },
  content: { 
    fontSize: 16, 
    marginBottom: 5 
  },
  postActions: { 
    flexDirection: 'row', 
    marginTop: 15, 
    paddingTop: 15, 
    borderTopWidth: 1, 
    borderTopColor: '#f1f3f4',
    justifyContent: 'space-around',
  },
  actionButton: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
  },
  actionCount: { 
    marginLeft: 5, 
    fontSize: 14, 
    color: '#666', 
    fontWeight: '500' 
  },
  actionText: { 
    marginLeft: 5, 
    fontSize: 14, 
    color: '#666', 
    fontWeight: '500' 
  },
  likedText: { 
    color: '#ff4757', 
    fontWeight: 'bold' 
  },
  followingText: { 
    color: '#00cc99', 
    fontWeight: 'bold' 
  },
  commentsSection: { 
    marginTop: 10, 
    paddingTop: 10, 
    borderTopWidth: 1, 
    borderTopColor: '#eee' 
  },
  commentInputContainer: { 
    flexDirection: 'row', 
    alignItems: 'flex-end' 
  },
  commentInput: { 
    flex: 1, 
    borderWidth: 1, 
    borderColor: '#ddd', 
    borderRadius: 8, 
    padding: 8, 
    marginRight: 10, 
    minHeight: 40 
  },
  commentSubmitButton: { 
    backgroundColor: '#00cc99', 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    borderRadius: 6 
  },
  commentSubmitText: { 
    color: '#fff', 
    fontWeight: 'bold', 
    fontSize: 14 
  },
});
