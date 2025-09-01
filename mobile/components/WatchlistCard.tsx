import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface WatchlistCardProps {
  watchlist: {
    id: string;
    name: string;
    description: string;
    is_public: boolean;
    is_shared: boolean;
    item_count: number;
    created_at: string;
    user: {
      name: string;
      profile_pic?: string;
    };
  };
  onPress: () => void;
  onShare: () => void;
}

const WatchlistCard: React.FC<WatchlistCardProps> = ({
  watchlist,
  onPress,
  onShare,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <TouchableOpacity style={styles.container} onPress={onPress}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.userInfo}>
          {watchlist.user.profile_pic ? (
            <Image
              source={{ uri: watchlist.user.profile_pic }}
              style={styles.avatar}
            />
          ) : (
            <View style={styles.avatarFallback}>
              <Text style={styles.avatarText}>
                {watchlist.user.name.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          <View style={styles.userDetails}>
            <Text style={styles.userName}>{watchlist.user.name}</Text>
            <Text style={styles.timestamp}>{formatDate(watchlist.created_at)}</Text>
          </View>
        </View>
        
        <View style={styles.statusContainer}>
          {watchlist.is_public && (
            <View style={styles.publicBadge}>
              <Icon name="globe" size={12} color="#34C759" />
              <Text style={styles.publicText}>Public</Text>
            </View>
          )}
          {watchlist.is_shared && (
            <View style={styles.sharedBadge}>
              <Icon name="share-2" size={12} color="#007AFF" />
              <Text style={styles.sharedText}>Shared</Text>
            </View>
          )}
        </View>
      </View>

      {/* Content */}
      <View style={styles.content}>
        <Text style={styles.name}>{watchlist.name}</Text>
        {watchlist.description && (
          <Text style={styles.description} numberOfLines={2}>
            {watchlist.description}
          </Text>
        )}
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <View style={styles.stats}>
          <Icon name="list" size={16} color="#8E8E93" />
          <Text style={styles.statsText}>{watchlist.item_count} stocks</Text>
        </View>
        
        <TouchableOpacity style={styles.shareButton} onPress={onShare}>
          <Icon name="share-2" size={16} color="#007AFF" />
          <Text style={styles.shareText}>Share</Text>
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
    width: 32,
    height: 32,
    borderRadius: 16,
    marginRight: 12,
  },
  avatarFallback: {
    width: 32,
    height: 32,
    borderRadius: 16,
    marginRight: 12,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  timestamp: {
    fontSize: 12,
    color: '#8E8E93',
  },
  statusContainer: {
    alignItems: 'flex-end',
  },
  publicBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FFF0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 4,
  },
  publicText: {
    fontSize: 10,
    color: '#34C759',
    fontWeight: '600',
    marginLeft: 4,
  },
  sharedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F8FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  sharedText: {
    fontSize: 10,
    color: '#007AFF',
    fontWeight: '600',
    marginLeft: 4,
  },
  content: {
    marginBottom: 16,
  },
  name: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#3A3A3C',
    lineHeight: 20,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#F2F2F7',
    paddingTop: 12,
  },
  stats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statsText: {
    fontSize: 14,
    color: '#8E8E93',
    marginLeft: 6,
    fontWeight: '500',
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F8FF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  shareText: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
    marginLeft: 4,
  },
});

export default WatchlistCard;
