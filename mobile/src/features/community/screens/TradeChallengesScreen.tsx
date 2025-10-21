import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Challenge {
  id: string;
  title: string;
  description: string;
  type: 'prediction' | 'simulation' | 'learning';
  status: 'active' | 'completed' | 'upcoming';
  participants: number;
  prize: string;
  endDate: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

interface Prediction {
  id: string;
  challengeId: string;
  userId: string;
  prediction: string;
  confidence: number;
  timestamp: string;
  isAnonymous: boolean;
}

interface LeaderboardEntry {
  rank: number;
  userId: string;
  score: number;
  isAnonymous: boolean;
}

const TradeChallengesScreen: React.FC = () => {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'challenges' | 'predictions' | 'leaderboard'>('challenges');

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Mock challenges data
      const mockChallenges: Challenge[] = [
        {
          id: '1',
          title: 'AAPL Earnings Prediction',
          description: 'Predict Apple\'s Q4 earnings beat or miss',
          type: 'prediction',
          status: 'active',
          participants: 47,
          prize: '$50 Amazon Gift Card',
          endDate: '2024-01-20T23:59:59Z',
          difficulty: 'intermediate',
        },
        {
          id: '2',
          title: 'Options Strategy Simulation',
          description: 'Build the most profitable options strategy in 30 days',
          type: 'simulation',
          status: 'active',
          participants: 23,
          prize: 'Premium Subscription (3 months)',
          endDate: '2024-01-25T23:59:59Z',
          difficulty: 'advanced',
        },
        {
          id: '3',
          title: 'Risk Management Mastery',
          description: 'Complete all risk management modules with 90%+ score',
          type: 'learning',
          status: 'upcoming',
          participants: 0,
          prize: 'Exclusive Trading Course',
          endDate: '2024-01-30T23:59:59Z',
          difficulty: 'beginner',
        },
      ];

      // Mock predictions data
      const mockPredictions: Prediction[] = [
        {
          id: '1',
          challengeId: '1',
          userId: 'user1',
          prediction: 'Beat - $1.25 EPS',
          confidence: 85,
          timestamp: '2024-01-15T14:30:00Z',
          isAnonymous: true,
        },
        {
          id: '2',
          challengeId: '1',
          userId: 'user2',
          prediction: 'Miss - $1.15 EPS',
          confidence: 72,
          timestamp: '2024-01-15T13:45:00Z',
          isAnonymous: true,
        },
        {
          id: '3',
          challengeId: '1',
          userId: 'user3',
          prediction: 'Beat - $1.30 EPS',
          confidence: 91,
          timestamp: '2024-01-15T12:20:00Z',
          isAnonymous: true,
        },
      ];

      // Mock leaderboard data
      const mockLeaderboard: LeaderboardEntry[] = [
        { rank: 1, userId: 'user1', score: 2450, isAnonymous: true },
        { rank: 2, userId: 'user2', score: 2380, isAnonymous: true },
        { rank: 3, userId: 'user3', score: 2290, isAnonymous: true },
        { rank: 4, userId: 'user4', score: 2150, isAnonymous: true },
        { rank: 5, userId: 'user5', score: 2080, isAnonymous: true },
      ];

      setChallenges(mockChallenges);
      setPredictions(mockPredictions);
      setLeaderboard(mockLeaderboard);
    } catch (error) {
      console.error('Error loading trade challenges data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const formatTimeRemaining = (endDate: string) => {
    const end = new Date(endDate);
    const now = new Date();
    const diffInHours = Math.floor((end.getTime() - now.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 0) return 'Ended';
    if (diffInHours < 24) return `${diffInHours}h left`;
    return `${Math.floor(diffInHours / 24)}d left`;
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return '#4CAF50';
      case 'intermediate': return '#FF9800';
      case 'advanced': return '#F44336';
      default: return '#666';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#4CAF50';
      case 'completed': return '#2196F3';
      case 'upcoming': return '#FF9800';
      default: return '#666';
    }
  };

  const renderChallenges = () => (
    <View style={styles.tabContent}>
      {challenges.map((challenge) => (
        <View key={challenge.id} style={styles.challengeCard}>
          <View style={styles.challengeHeader}>
            <Text style={styles.challengeTitle}>{challenge.title}</Text>
            <View style={[styles.statusBadge, { backgroundColor: getStatusColor(challenge.status) }]}>
              <Text style={styles.statusText}>{challenge.status.toUpperCase()}</Text>
            </View>
          </View>
          
          <Text style={styles.challengeDescription}>{challenge.description}</Text>
          
          <View style={styles.challengeMeta}>
            <View style={styles.metaItem}>
              <Ionicons name="people" size={16} color="#666" />
              <Text style={styles.metaText}>{challenge.participants} participants</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="gift" size={16} color="#666" />
              <Text style={styles.metaText}>{challenge.prize}</Text>
            </View>
          </View>
          
          <View style={styles.challengeFooter}>
            <View style={[styles.difficultyBadge, { backgroundColor: getDifficultyColor(challenge.difficulty) }]}>
              <Text style={styles.difficultyText}>{challenge.difficulty}</Text>
            </View>
            <Text style={styles.timeRemaining}>{formatTimeRemaining(challenge.endDate)}</Text>
          </View>
          
          {challenge.status === 'active' && (
            <TouchableOpacity style={styles.joinButton}>
              <Text style={styles.joinButtonText}>Join Challenge</Text>
            </TouchableOpacity>
          )}
        </View>
      ))}
    </View>
  );

  const renderPredictions = () => (
    <View style={styles.tabContent}>
      {predictions.map((prediction) => (
        <View key={prediction.id} style={styles.predictionCard}>
          <View style={styles.predictionHeader}>
            <Text style={styles.predictionUser}>
              {prediction.isAnonymous ? 'Anonymous Trader' : `User ${prediction.userId}`}
            </Text>
            <Text style={styles.predictionTime}>
              {new Date(prediction.timestamp).toLocaleDateString()}
            </Text>
          </View>
          
          <Text style={styles.predictionText}>{prediction.prediction}</Text>
          
          <View style={styles.confidenceBar}>
            <View style={styles.confidenceLabel}>
              <Text style={styles.confidenceText}>Confidence: {prediction.confidence}%</Text>
            </View>
            <View style={styles.confidenceTrack}>
              <View 
                style={[
                  styles.confidenceFill, 
                  { width: `${prediction.confidence}%` }
                ]} 
              />
            </View>
          </View>
        </View>
      ))}
    </View>
  );

  const renderLeaderboard = () => (
    <View style={styles.tabContent}>
      <View style={styles.leaderboardHeader}>
        <Text style={styles.leaderboardTitle}>Top Performers</Text>
        <Text style={styles.leaderboardSubtitle}>This month's challenge leaders</Text>
      </View>
      
      {leaderboard.map((entry) => (
        <View key={entry.rank} style={styles.leaderboardEntry}>
          <View style={styles.rankContainer}>
            <Text style={styles.rankNumber}>{entry.rank}</Text>
            {entry.rank <= 3 && (
              <Ionicons 
                name={entry.rank === 1 ? "trophy" : entry.rank === 2 ? "medal" : "ribbon"} 
                size={20} 
                color={entry.rank === 1 ? "#FFD700" : entry.rank === 2 ? "#C0C0C0" : "#CD7F32"} 
              />
            )}
          </View>
          
          <View style={styles.userInfo}>
            <Text style={styles.userName}>
              {entry.isAnonymous ? 'Anonymous Trader' : `User ${entry.userId}`}
            </Text>
            <Text style={styles.userScore}>{entry.score.toLocaleString()} points</Text>
          </View>
        </View>
      ))}
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading challenges...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Trade Challenges</Text>
        <Text style={styles.subtitle}>Compete, learn, and win with your community</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'challenges' && styles.activeTab]}
          onPress={() => setActiveTab('challenges')}
        >
          <Text style={[styles.tabText, activeTab === 'challenges' && styles.activeTabText]}>
            Challenges
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'predictions' && styles.activeTab]}
          onPress={() => setActiveTab('predictions')}
        >
          <Text style={[styles.tabText, activeTab === 'predictions' && styles.activeTabText]}>
            Predictions
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'leaderboard' && styles.activeTab]}
          onPress={() => setActiveTab('leaderboard')}
        >
          <Text style={[styles.tabText, activeTab === 'leaderboard' && styles.activeTabText]}>
            Leaderboard
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {activeTab === 'challenges' && renderChallenges()}
        {activeTab === 'predictions' && renderPredictions()}
        {activeTab === 'leaderboard' && renderLeaderboard()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  tabContent: {
    padding: 16,
  },
  challengeCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  challengeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  challengeTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  challengeDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    lineHeight: 20,
  },
  challengeMeta: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  metaText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  challengeFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  timeRemaining: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  joinButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  joinButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  predictionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  predictionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  predictionUser: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  predictionTime: {
    fontSize: 12,
    color: '#666',
  },
  predictionText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 12,
    fontWeight: '500',
  },
  confidenceBar: {
    marginTop: 8,
  },
  confidenceLabel: {
    marginBottom: 4,
  },
  confidenceText: {
    fontSize: 12,
    color: '#666',
  },
  confidenceTrack: {
    height: 6,
    backgroundColor: '#e1e5e9',
    borderRadius: 3,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 3,
  },
  leaderboardHeader: {
    marginBottom: 16,
  },
  leaderboardTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  leaderboardSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  leaderboardEntry: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  rankContainer: {
    width: 40,
    alignItems: 'center',
    marginRight: 16,
  },
  rankNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 2,
  },
  userScore: {
    fontSize: 14,
    color: '#666',
  },
});

export default TradeChallengesScreen;
