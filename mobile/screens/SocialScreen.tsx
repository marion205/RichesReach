import React, { useState, useEffect } from 'react';
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
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useApolloClient } from '@apollo/client';
import { gql } from '@apollo/client';

import SocialNav from '../components/SocialNav';
import DiscussionCard from '../components/DiscussionCard';
import WatchlistCard from '../components/WatchlistCard';
import PortfolioCard from '../components/PortfolioCard';
import AchievementCard from '../components/AchievementCard';

// GraphQL Queries
const GET_TRENDING_DISCUSSIONS = gql`
  query GetTrendingDiscussions {
    trendingDiscussions {
      id
      title
      content
      discussion_type
      created_at
      like_count
      comment_count
      user {
        name
        profile_pic
      }
      stock {
        symbol
        company_name
      }
    }
  }
`;

const GET_PUBLIC_WATCHLISTS = gql`
  query GetPublicWatchlists {
    publicWatchlists {
      id
      name
      description
      is_public
      is_shared
      item_count
      created_at
      user {
        name
        profile_pic
      }
    }
  }
`;

const GET_PUBLIC_PORTFOLIOS = gql`
  query GetPublicPortfolios {
    publicPortfolios {
      id
      name
      description
      is_public
      position_count
      total_value
      total_return
      total_return_percent
      created_at
      user {
        name
        profile_pic
      }
    }
  }
`;

const GET_USER_ACHIEVEMENTS = gql`
  query GetUserAchievements {
    userAchievements {
      id
      title
      description
      icon
      earned_at
      user {
        name
        profile_pic
      }
    }
  }
`;

// Mock data for development
const mockDiscussions = [
  {
    id: '1',
    title: 'AAPL Technical Analysis - Bullish Pattern Forming',
    content: 'Looking at the daily chart, AAPL is forming a bullish flag pattern. The stock has been consolidating between $150-$160 for the past month, and I believe we\'re about to see a breakout to the upside. Key resistance at $165, support at $150.',
    discussion_type: 'analysis',
    created_at: new Date().toISOString(),
    like_count: 24,
    comment_count: 8,
    user: { name: 'StockGuru', profile_pic: null },
    stock: { symbol: 'AAPL', company_name: 'Apple Inc.' },
  },
  {
    id: '2',
    title: 'TSLA Earnings Preview - What to Expect',
    content: 'Tesla reports earnings next week. Based on delivery numbers and market conditions, I\'m expecting strong Q3 results. However, guidance for Q4 will be crucial given the current economic environment.',
    discussion_type: 'news',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    like_count: 18,
    comment_count: 12,
    user: { name: 'MarketWatcher', profile_pic: null },
    stock: { symbol: 'TSLA', company_name: 'Tesla Inc.' },
  },
];

const mockWatchlists = [
  {
    id: '1',
    name: 'Tech Giants Portfolio',
    description: 'A curated list of the most innovative technology companies with strong fundamentals and growth potential.',
    is_public: true,
    is_shared: true,
    item_count: 15,
    created_at: new Date().toISOString(),
    user: { name: 'TechInvestor', profile_pic: null },
  },
  {
    id: '2',
    name: 'Dividend Aristocrats',
    description: 'Companies that have increased dividends for 25+ consecutive years. Perfect for income-focused investors.',
    is_public: true,
    is_shared: false,
    item_count: 12,
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    user: { name: 'IncomeSeeker', profile_pic: null },
  },
];

const mockPortfolios = [
  {
    id: '1',
    name: 'Growth Portfolio',
    description: 'High-growth stocks with potential for significant returns over the next 5-10 years.',
    is_public: true,
    position_count: 8,
    total_value: 125000,
    total_return: 18500,
    total_return_percent: 17.4,
    created_at: new Date().toISOString(),
    user: { name: 'GrowthTrader', profile_pic: null },
  },
  {
    id: '2',
    name: 'Conservative Income',
    description: 'Low-risk portfolio focused on dividend income and capital preservation.',
    is_public: true,
    position_count: 12,
    total_value: 75000,
    total_return: 3200,
    total_return_percent: 4.3,
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    user: { name: 'ConservativeInvestor', profile_pic: null },
  },
];

const mockAchievements = [
  {
    id: '1',
    title: 'First Discussion Post',
    description: 'Posted your first discussion! Welcome to the community.',
    icon: '📝',
    earned_at: new Date().toISOString(),
    user: { name: 'NewUser', profile_pic: null },
  },
  {
    id: '2',
    title: 'Watchlist Creator',
    description: 'Created your first watchlist! Start building your investment strategy.',
    icon: '📋',
    earned_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    user: { name: 'WatchlistMaster', profile_pic: null },
  },
];

const SocialScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState('discussions');
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createType, setCreateType] = useState('');
  const [createTitle, setCreateTitle] = useState('');
  const [createContent, setCreateContent] = useState('');
  const [createStock, setCreateStock] = useState('');

  const client = useApolloClient();

  const onRefresh = async () => {
    setRefreshing(true);
    // Refresh data based on active tab
    try {
      switch (activeTab) {
        case 'discussions':
          await client.refetchQueries({
            include: ['GetTrendingDiscussions'],
          });
          break;
        case 'watchlists':
          await client.refetchQueries({
            include: ['GetPublicWatchlists'],
          });
          break;
        case 'portfolios':
          await client.refetchQueries({
            include: ['GetPublicPortfolios'],
          });
          break;
        case 'achievements':
          await client.refetchQueries({
            include: ['GetUserAchievements'],
          });
          break;
      }
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleTabPress = (tab: string) => {
    setActiveTab(tab);
  };

  const handleCreatePress = () => {
    setShowCreateModal(true);
  };

  const handleCreateSubmit = () => {
    if (!createTitle.trim() || !createContent.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    // Here you would submit the creation via GraphQL mutation
    Alert.alert('Success', `${createType} created successfully!`);
    setShowCreateModal(false);
    setCreateTitle('');
    setCreateContent('');
    setCreateStock('');
    setCreateType('');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'discussions':
        return (
          <View>
            {mockDiscussions.map((discussion) => (
              <DiscussionCard
                key={discussion.id}
                discussion={discussion}
                onLike={() => Alert.alert('Like', 'Discussion liked!')}
                onComment={() => Alert.alert('Comment', 'Comment feature coming soon!')}
                onPress={() => Alert.alert('Discussion', 'Discussion detail coming soon!')}
              />
            ))}
          </View>
        );
      
      case 'watchlists':
        return (
          <View>
            {mockWatchlists.map((watchlist) => (
              <WatchlistCard
                key={watchlist.id}
                watchlist={watchlist}
                onPress={() => Alert.alert('Watchlist', 'Watchlist detail coming soon!')}
                onShare={() => Alert.alert('Share', 'Share feature coming soon!')}
              />
            ))}
          </View>
        );
      
      case 'portfolios':
        return (
          <View>
            {mockPortfolios.map((portfolio) => (
              <PortfolioCard
                key={portfolio.id}
                portfolio={portfolio}
                onPress={() => Alert.alert('Portfolio', 'Portfolio detail coming soon!')}
                onShare={() => Alert.alert('Share', 'Share feature coming soon!')}
              />
            ))}
          </View>
        );
      
      case 'achievements':
        return (
          <View>
            {mockAchievements.map((achievement) => (
              <AchievementCard
                key={achievement.id}
                achievement={achievement}
                onPress={() => Alert.alert('Achievement', 'Achievement detail coming soon!')}
              />
            ))}
          </View>
        );
      
      default:
        return null;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Social Hub</Text>
        <TouchableOpacity style={styles.createButton} onPress={handleCreatePress}>
          <Icon name="plus" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Navigation */}
      <SocialNav activeTab={activeTab} onTabPress={handleTabPress} />

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {renderContent()}
      </ScrollView>

      {/* Create Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent={true}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create New {createType}</Text>
              <TouchableOpacity
                onPress={() => setShowCreateModal(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <Text style={styles.modalLabel}>Type</Text>
              <View style={styles.typeButtons}>
                {['Discussion', 'Watchlist', 'Portfolio'].map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.typeButton,
                      createType === type && styles.typeButtonActive
                    ]}
                    onPress={() => setCreateType(type)}
                  >
                    <Text style={[
                      styles.typeButtonText,
                      createType === type && styles.typeButtonTextActive
                    ]}>
                      {type}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {createType && (
                <>
                  <Text style={styles.modalLabel}>Title</Text>
                  <TextInput
                    style={styles.textInput}
                    value={createTitle}
                    onChangeText={setCreateTitle}
                    placeholder={`Enter ${createType.toLowerCase()} title`}
                  />

                  {createType === 'Discussion' && (
                    <>
                      <Text style={styles.modalLabel}>Stock Symbol</Text>
                      <TextInput
                        style={styles.textInput}
                        value={createStock}
                        onChangeText={setCreateStock}
                        placeholder="e.g., AAPL"
                        autoCapitalize="characters"
                      />
                    </>
                  )}

                  <Text style={styles.modalLabel}>Description</Text>
                  <TextInput
                    style={[styles.textInput, styles.textArea]}
                    value={createContent}
                    onChangeText={setCreateContent}
                    placeholder={`Enter ${createType.toLowerCase()} description`}
                    multiline
                    numberOfLines={4}
                  />
                </>
              )}
            </View>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowCreateModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.submitButton,
                  (!createType || !createTitle.trim() || !createContent.trim()) && styles.submitButtonDisabled
                ]}
                onPress={handleCreateSubmit}
                disabled={!createType || !createTitle.trim() || !createContent.trim()}
              >
                <Text style={styles.submitButtonText}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    paddingTop: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
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
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
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
    maxHeight: '80%',
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
  },
  modalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 8,
    marginTop: 16,
  },
  typeButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  typeButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  typeButtonActive: {
    backgroundColor: '#007AFF',
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  typeButtonTextActive: {
    color: '#FFFFFF',
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
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  submitButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default SocialScreen;
