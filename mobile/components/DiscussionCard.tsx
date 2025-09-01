import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface DiscussionCardProps {
  discussion: {
    id: string;
    title: string;
    content: string;
    discussion_type: string;
    created_at: string;
    like_count: number;
    comment_count: number;
    user: {
      name: string;
      profile_pic?: string;
    };
    stock: {
      symbol: string;
      company_name: string;
    };
  };
  onLike: () => void;
  onComment: () => void;
  onPress: () => void;
}

const DiscussionCard: React.FC<DiscussionCardProps> = ({
  discussion,
  onLike,
  onComment,
  onPress,
}) => {
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
      case 'analysis': return '#007AFF';
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

  return (
    <TouchableOpacity style={styles.container} onPress={onPress}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.userInfo}>
          {discussion.user.profile_pic ? (
            <Image
              source={{ uri: discussion.user.profile_pic }}
              style={styles.avatar}
            />
          ) : (
            <View style={styles.avatarFallback}>
              <Text style={styles.avatarText}>
                {discussion.user.name.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          <View style={styles.userDetails}>
            <Text style={styles.userName}>{discussion.user.name}</Text>
            <Text style={styles.timestamp}>{formatDate(discussion.created_at)}</Text>
          </View>
        </View>
        <View style={styles.stockInfo}>
          <Text style={styles.stockSymbol}>{discussion.stock.symbol}</Text>
          <Text style={styles.stockName}>{discussion.stock.company_name}</Text>
        </View>
      </View>

      {/* Discussion Type Badge */}
      <View style={styles.typeContainer}>
        <Icon
          name={getDiscussionIcon(discussion.discussion_type) as any}
          size={16}
          color={getDiscussionColor(discussion.discussion_type)}
        />
        <Text style={[
          styles.typeLabel,
          { color: getDiscussionColor(discussion.discussion_type) }
        ]}>
          {discussion.discussion_type.charAt(0).toUpperCase() + discussion.discussion_type.slice(1)}
        </Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        <Text style={styles.title}>{discussion.title}</Text>
        <Text style={styles.contentText} numberOfLines={3}>
          {discussion.content}
        </Text>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionButton} onPress={onLike}>
          <Icon name="heart" size={20} color="#FF3B30" />
          <Text style={styles.actionText}>{discussion.like_count}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton} onPress={onComment}>
          <Icon name="message-circle" size={20} color="#007AFF" />
          <Text style={styles.actionText}>{discussion.comment_count}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton}>
          <Icon name="share" size={20} color="#8E8E93" />
          <Text style={styles.actionText}>Share</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  avatarFallback: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 18,
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
  timestamp: {
    fontSize: 12,
    color: '#8E8E93',
  },
  stockInfo: {
    alignItems: 'flex-end',
  },
  stockSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#007AFF',
    marginBottom: 2,
  },
  stockName: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'right',
  },
  typeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 12,
  },
  typeLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  content: {
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
    lineHeight: 24,
  },
  contentText: {
    fontSize: 14,
    color: '#3A3A3C',
    lineHeight: 20,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: '#F2F2F7',
    paddingTop: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  actionText: {
    fontSize: 14,
    color: '#8E8E93',
    marginLeft: 6,
    fontWeight: '500',
  },
});

export default DiscussionCard;
