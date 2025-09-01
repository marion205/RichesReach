import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface PortfolioCardProps {
  portfolio: {
    id: string;
    name: string;
    description: string;
    is_public: boolean;
    position_count: number;
    total_value: number;
    total_return: number;
    total_return_percent: number;
    created_at: string;
    user: {
      name: string;
      profile_pic?: string;
    };
  };
  onPress: () => void;
  onShare: () => void;
}

const PortfolioCard: React.FC<PortfolioCardProps> = ({
  portfolio,
  onPress,
  onShare,
}) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (percent: number) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getReturnColor = (returnValue: number) => {
    return returnValue >= 0 ? '#34C759' : '#FF3B30';
  };

  const getReturnIcon = (returnValue: number) => {
    return returnValue >= 0 ? 'trending-up' : 'trending-down';
  };

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
          {portfolio.user.profile_pic ? (
            <Image
              source={{ uri: portfolio.user.profile_pic }}
              style={styles.avatar}
            />
          ) : (
            <View style={styles.avatarFallback}>
              <Text style={styles.avatarText}>
                {portfolio.user.name.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          <View style={styles.userDetails}>
            <Text style={styles.userName}>{portfolio.user.name}</Text>
            <Text style={styles.timestamp}>{formatDate(portfolio.created_at)}</Text>
          </View>
        </View>
        
        <View style={styles.statusContainer}>
          {portfolio.is_public && (
            <View style={styles.publicBadge}>
              <Icon name="globe" size={12} color="#34C759" />
              <Text style={styles.publicText}>Public</Text>
            </View>
          )}
        </View>
      </View>

      {/* Content */}
      <View style={styles.content}>
        <Text style={styles.name}>{portfolio.name}</Text>
        {portfolio.description && (
          <Text style={styles.description} numberOfLines={2}>
            {portfolio.description}
          </Text>
        )}
      </View>

      {/* Performance Metrics */}
      <View style={styles.metrics}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Portfolio Value</Text>
          <Text style={styles.metricValue}>{formatCurrency(portfolio.total_value)}</Text>
        </View>
        
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Total Return</Text>
          <View style={styles.returnContainer}>
            <Icon
              name={getReturnIcon(portfolio.total_return) as any}
              size={16}
              color={getReturnColor(portfolio.total_return)}
            />
            <Text style={[
              styles.returnValue,
              { color: getReturnColor(portfolio.total_return) }
            ]}>
              {formatCurrency(portfolio.total_return)}
            </Text>
            <Text style={[
              styles.returnPercent,
              { color: getReturnColor(portfolio.total_return) }
            ]}>
              {formatPercentage(portfolio.total_return_percent)}
            </Text>
          </View>
        </View>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <View style={styles.stats}>
          <Icon name="trending-up" size={16} color="#8E8E93" />
          <Text style={styles.statsText}>{portfolio.position_count} positions</Text>
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
  },
  publicText: {
    fontSize: 10,
    color: '#34C759',
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
  metrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingVertical: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    paddingHorizontal: 16,
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  returnContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  returnValue: {
    fontSize: 16,
    fontWeight: '700',
    marginLeft: 4,
  },
  returnPercent: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 8,
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

export default PortfolioCard;
