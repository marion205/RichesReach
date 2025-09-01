import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Linking,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { NewsArticle } from '../services/newsService';

interface NewsCardProps {
  news: NewsArticle;
  onSave?: (article: NewsArticle) => void;
  onUnsave?: (articleId: string) => void;
  showSaveButton?: boolean;
}

const NewsCard: React.FC<NewsCardProps> = ({ 
  news, 
  onSave, 
  onUnsave, 
  showSaveButton = true 
}) => {
  const handleNewsPress = async () => {
    try {
      await Linking.openURL(news.url);
    } catch (error) {
      console.error('Failed to open news URL:', error);
    }
  };

  const handleSavePress = () => {
    if (news.isSaved && onUnsave) {
      onUnsave(news.id);
    } else if (!news.isSaved && onSave) {
      onSave(news);
    }
  };

  const getSentimentColor = () => {
    switch (news.sentiment) {
      case 'positive': return '#34C759';
      case 'negative': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const getSentimentIcon = () => {
    switch (news.sentiment) {
      case 'positive': return 'trending-up';
      case 'negative': return 'trending-down';
      default: return 'minus';
    }
  };

  const formatTimeAgo = (publishedAt: string) => {
    const now = new Date();
    const published = new Date(publishedAt);
    const diffInHours = Math.floor((now.getTime() - published.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return published.toLocaleDateString();
  };

  return (
    <TouchableOpacity style={styles.container} onPress={handleNewsPress}>
      <View style={styles.header}>
        <View style={styles.sourceInfo}>
          <Icon name="globe" size={16} color="#8E8E93" />
          <Text style={styles.source}>{news.source}</Text>
          <Text style={styles.timeAgo}>• {formatTimeAgo(news.publishedAt)}</Text>
        </View>
        {news.sentiment && (
          <View style={[styles.sentimentBadge, { backgroundColor: getSentimentColor() }]}>
            <Icon name={getSentimentIcon()} size={12} color="#FFFFFF" />
          </View>
        )}
      </View>

      <Text style={styles.title} numberOfLines={3}>
        {news.title}
      </Text>

      {news.description && (
        <Text style={styles.description} numberOfLines={3}>
          {news.description}
        </Text>
      )}

      {news.imageUrl && (
        <Image source={{ uri: news.imageUrl }} style={styles.image} />
      )}

      <View style={styles.footer}>
        <View style={styles.footerLeft}>
          {news.readTime && (
            <View style={styles.readTimeContainer}>
              <Icon name="clock" size={14} color="#8E8E93" />
              <Text style={styles.readTimeText}>{news.readTime} min read</Text>
            </View>
          )}
          {news.category && (
            <View style={styles.categoryContainer}>
              <Text style={styles.categoryText}>{news.category.replace('-', ' ')}</Text>
            </View>
          )}
        </View>
        
        <View style={styles.footerRight}>
          {showSaveButton && (
            <TouchableOpacity 
              style={styles.saveButton} 
              onPress={handleSavePress}
            >
              <Icon 
                name={news.isSaved ? "bookmark" : "bookmark"} 
                size={16} 
                color={news.isSaved ? "#34C759" : "#8E8E93"} 
                style={news.isSaved ? {} : { opacity: 0.5 }}
              />
            </TouchableOpacity>
          )}
          <View style={styles.actionButton}>
            <Icon name="external-link" size={16} color="#8E8E93" />
            <Text style={styles.actionText}>Read Article</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sourceInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  source: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  timeAgo: {
    fontSize: 12,
    color: '#8E8E93',
  },
  sentimentBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    lineHeight: 22,
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 12,
  },
  image: {
    width: '100%',
    height: 160,
    borderRadius: 8,
    marginBottom: 12,
  },
  footer: {
    marginTop: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  footerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  footerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  readTimeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  readTimeText: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '500',
  },
  categoryContainer: {
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  categoryText: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  saveButton: {
    padding: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#F2F2F7',
    borderRadius: 16,
  },
  actionText: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '500',
  },
});

export default NewsCard;
