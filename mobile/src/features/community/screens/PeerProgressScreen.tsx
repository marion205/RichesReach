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

interface ProgressUpdate {
  id: string;
  userId: string;
  achievement: string;
  progress: number;
  timestamp: string;
  isAnonymous: boolean;
}

interface CommunityStats {
  totalUsers: number;
  activeToday: number;
  achievementsUnlocked: number;
  averageProgress: number;
}

const PeerProgressScreen: React.FC = () => {
  const [progressUpdates, setProgressUpdates] = useState<ProgressUpdate[]>([]);
  const [communityStats, setCommunityStats] = useState<CommunityStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      // Mock data for now
      const mockProgressUpdates: ProgressUpdate[] = [
        {
          id: '1',
          userId: 'user1',
          achievement: 'Completed Options Basics Course',
          progress: 100,
          timestamp: '2024-01-15T10:30:00Z',
          isAnonymous: true,
        },
        {
          id: '2',
          userId: 'user2',
          achievement: 'Reached 30-day trading streak',
          progress: 100,
          timestamp: '2024-01-15T09:15:00Z',
          isAnonymous: true,
        },
        {
          id: '3',
          userId: 'user3',
          achievement: 'Portfolio up 15% this month',
          progress: 85,
          timestamp: '2024-01-15T08:45:00Z',
          isAnonymous: true,
        },
        {
          id: '4',
          userId: 'user4',
          achievement: 'Completed Risk Management Module',
          progress: 100,
          timestamp: '2024-01-15T07:20:00Z',
          isAnonymous: true,
        },
        {
          id: '5',
          userId: 'user5',
          achievement: 'First profitable options trade',
          progress: 100,
          timestamp: '2024-01-14T16:30:00Z',
          isAnonymous: true,
        },
      ];

      const mockCommunityStats: CommunityStats = {
        totalUsers: 1247,
        activeToday: 89,
        achievementsUnlocked: 156,
        averageProgress: 73,
      };

      setProgressUpdates(mockProgressUpdates);
      setCommunityStats(mockCommunityStats);
    } catch (error) {
      console.error('Error loading peer progress data:', error);
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

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    return `${Math.floor(diffInHours / 24)}d ago`;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading peer progress...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Peer Progress Pulse</Text>
        <Text style={styles.subtitle}>See what your community is achieving</Text>
      </View>

      {/* Community Stats */}
      {communityStats && (
        <View style={styles.statsContainer}>
          <Text style={styles.statsTitle}>Community Overview</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{communityStats.totalUsers.toLocaleString()}</Text>
              <Text style={styles.statLabel}>Total Members</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{communityStats.activeToday}</Text>
              <Text style={styles.statLabel}>Active Today</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{communityStats.achievementsUnlocked}</Text>
              <Text style={styles.statLabel}>Achievements</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{communityStats.averageProgress}%</Text>
              <Text style={styles.statLabel}>Avg Progress</Text>
            </View>
          </View>
        </View>
      )}

      {/* Recent Achievements */}
      <View style={styles.achievementsContainer}>
        <Text style={styles.sectionTitle}>Recent Achievements</Text>
        {progressUpdates.map((update) => (
          <View key={update.id} style={styles.achievementCard}>
            <View style={styles.achievementIcon}>
              <Ionicons name="trophy" size={20} color="#FFD700" />
            </View>
            <View style={styles.achievementContent}>
              <Text style={styles.achievementText}>
                {update.isAnonymous ? 'Anonymous member' : `User ${update.userId}`}
              </Text>
              <Text style={styles.achievementDescription}>{update.achievement}</Text>
              <Text style={styles.achievementTime}>{formatTimestamp(update.timestamp)}</Text>
            </View>
            <View style={styles.progressBadge}>
              <Text style={styles.progressText}>{update.progress}%</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Motivational Section */}
      <View style={styles.motivationContainer}>
        <View style={styles.motivationCard}>
          <Ionicons name="trending-up" size={24} color="#4CAF50" />
          <Text style={styles.motivationTitle}>You're Not Alone</Text>
          <Text style={styles.motivationText}>
            Join {communityStats?.activeToday} members who are actively building wealth today. 
            Every achievement inspires the next one.
          </Text>
        </View>
      </View>

      {/* Privacy Notice */}
      <View style={styles.privacyContainer}>
        <Ionicons name="shield-checkmark" size={16} color="#666" />
        <Text style={styles.privacyText}>
          All progress updates are anonymous to protect privacy while maintaining motivation.
        </Text>
      </View>
    </ScrollView>
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
  statsContainer: {
    margin: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  achievementsContainer: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  achievementCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  achievementIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFF3CD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  achievementContent: {
    flex: 1,
  },
  achievementText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  achievementDescription: {
    fontSize: 14,
    color: '#333',
    marginTop: 2,
  },
  achievementTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  progressBadge: {
    backgroundColor: '#E8F5E8',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4CAF50',
  },
  motivationContainer: {
    margin: 16,
  },
  motivationCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  motivationTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginTop: 12,
    marginBottom: 8,
  },
  motivationText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
  privacyContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 16,
    padding: 12,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  privacyText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 8,
    flex: 1,
  },
});

export default PeerProgressScreen;
