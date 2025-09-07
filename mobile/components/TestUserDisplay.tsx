import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import MockUserService from '../services/MockUserService';

interface TestUserDisplayProps {
  onNavigate: (screen: string, params?: any) => void;
}

const TestUserDisplay: React.FC<TestUserDisplayProps> = ({ onNavigate }) => {
  const mockUserService = MockUserService.getInstance();
  const testUser = mockUserService.getUserById('test-user-456');
  const currentUser = mockUserService.getCurrentUser();

  if (!testUser) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Test user not found</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🧪 Test User Created!</Text>
        <Text style={styles.subtitle}>
          Here's your test user that you can follow and view their profile
        </Text>
      </View>

      <View style={styles.userCard}>
        <View style={styles.userHeader}>
          <View style={styles.userImageContainer}>
            <View style={styles.userImagePlaceholder}>
              <Text style={styles.userImageText}>{testUser.name.charAt(0)}</Text>
            </View>
            <View style={[styles.experienceBadge, { backgroundColor: '#007AFF' }]}>
              <Icon name="trending-up" size={10} color="#FFFFFF" />
            </View>
          </View>

          <View style={styles.userInfo}>
            <Text style={styles.userName}>{testUser.name}</Text>
            <Text style={styles.userEmail}>{testUser.email}</Text>
            <Text style={styles.userTitle}>
              {testUser.experienceLevel.charAt(0).toUpperCase()}{testUser.experienceLevel.slice(1)} Investor
            </Text>
            <Text style={styles.memberSince}>
              Member since {new Date(testUser.createdAt).getFullYear()}
            </Text>
          </View>

          <View style={styles.followStatus}>
            <Icon name="user-check" size={16} color="#34C759" />
            <Text style={styles.followStatusText}>Following</Text>
          </View>
        </View>

        <View style={styles.userStats}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{testUser.followersCount}</Text>
            <Text style={styles.statLabel}>Followers</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{testUser.followingCount}</Text>
            <Text style={styles.statLabel}>Following</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{testUser.portfolios.length}</Text>
            <Text style={styles.statLabel}>Portfolios</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{testUser.stats.modulesCompleted}</Text>
            <Text style={styles.statLabel}>Modules</Text>
          </View>
        </View>

        <View style={styles.portfolioSection}>
          <Text style={styles.sectionTitle}>Public Portfolios</Text>
          {testUser.portfolios.map((portfolio) => (
            <View key={portfolio.id} style={styles.portfolioCard}>
              <View style={styles.portfolioHeader}>
                <Text style={styles.portfolioName}>{portfolio.name}</Text>
                <View style={[
                  styles.portfolioReturn,
                  { backgroundColor: portfolio.totalReturnPercent >= 0 ? '#E8F5E8' : '#FFE8E8' }
                ]}>
                  <Text style={[
                    styles.portfolioReturnText,
                    { color: portfolio.totalReturnPercent >= 0 ? '#34C759' : '#FF3B30' }
                  ]}>
                    {portfolio.totalReturnPercent >= 0 ? '+' : ''}{portfolio.totalReturnPercent.toFixed(1)}%
                  </Text>
                </View>
              </View>
              <Text style={styles.portfolioDescription}>{portfolio.description}</Text>
              <Text style={styles.portfolioValue}>
                ${portfolio.totalValue.toLocaleString()} • ${portfolio.totalReturn.toLocaleString()} return
              </Text>
            </View>
          ))}
        </View>

        <View style={styles.learningSection}>
          <Text style={styles.sectionTitle}>Learning Progress</Text>
          <View style={styles.learningStats}>
            <View style={styles.learningItem}>
              <Icon name="clock" size={16} color="#007AFF" />
              <Text style={styles.learningText}>{testUser.stats.totalLearningTime} minutes</Text>
            </View>
            <View style={styles.learningItem}>
              <Icon name="check-circle" size={16} color="#34C759" />
              <Text style={styles.learningText}>{testUser.stats.modulesCompleted} modules</Text>
            </View>
            <View style={styles.learningItem}>
              <Icon name="trending-up" size={16} color="#FF3B30" />
              <Text style={styles.learningText}>{testUser.stats.streakDays} day streak</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity
          style={styles.viewProfileButton}
          onPress={() => onNavigate('user-profile', { userId: testUser.id })}
        >
          <Icon name="user" size={20} color="#FFFFFF" />
          <Text style={styles.viewProfileButtonText}>View Full Profile</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.instructionsCard}>
        <Text style={styles.instructionsTitle}>📱 How to Test:</Text>
        <View style={styles.instructionsList}>
          <View style={styles.instructionItem}>
            <Text style={styles.instructionNumber}>1</Text>
            <Text style={styles.instructionText}>Go to the "Discuss" tab in bottom navigation</Text>
          </View>
          <View style={styles.instructionItem}>
            <Text style={styles.instructionNumber}>2</Text>
            <Text style={styles.instructionText}>Switch to the "Discover" tab at the top</Text>
          </View>
          <View style={styles.instructionItem}>
            <Text style={styles.instructionNumber}>3</Text>
            <Text style={styles.instructionText}>Look for "Test Investor" in the list</Text>
          </View>
          <View style={styles.instructionItem}>
            <Text style={styles.instructionNumber}>4</Text>
            <Text style={styles.instructionText}>Tap "View Profile" to see their full profile</Text>
          </View>
          <View style={styles.instructionItem}>
            <Text style={styles.instructionNumber}>5</Text>
            <Text style={styles.instructionText}>Switch to "Activity" tab to see their posts</Text>
          </View>
        </View>
      </View>

      <View style={styles.currentUserCard}>
        <Text style={styles.currentUserTitle}>👤 Your Current Profile:</Text>
        <Text style={styles.currentUserText}>
          You are following {currentUser?.followingCount || 0} users
        </Text>
        <Text style={styles.currentUserText}>
          You have {currentUser?.followersCount || 0} followers
        </Text>
        <Text style={styles.currentUserText}>
          You are a {currentUser?.experienceLevel || 'beginner'} investor
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E93',
    lineHeight: 22,
  },
  userCard: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  userHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  userImageContainer: {
    position: 'relative',
    marginRight: 16,
  },
  userImagePlaceholder: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  userImageText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  experienceBadge: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  userEmail: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  userTitle: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
    marginBottom: 2,
  },
  memberSince: {
    fontSize: 12,
    color: '#8E8E93',
  },
  followStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: '#E8F5E8',
    borderWidth: 1,
    borderColor: '#34C759',
  },
  followStatusText: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
    marginLeft: 4,
  },
  userStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#E5E5EA',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
  },
  portfolioSection: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  portfolioCard: {
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  portfolioName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  portfolioReturn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  portfolioReturnText: {
    fontSize: 12,
    fontWeight: '600',
  },
  portfolioDescription: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  portfolioValue: {
    fontSize: 12,
    color: '#1C1C1E',
    fontWeight: '500',
  },
  learningSection: {
    marginBottom: 20,
  },
  learningStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  learningItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  learningText: {
    fontSize: 12,
    color: '#1C1C1E',
    marginLeft: 4,
  },
  viewProfileButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 25,
  },
  viewProfileButtonText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
    marginLeft: 8,
  },
  instructionsCard: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  instructionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  instructionsList: {
    gap: 12,
  },
  instructionItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  instructionNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
  },
  instructionText: {
    flex: 1,
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 20,
  },
  currentUserCard: {
    backgroundColor: '#E3F2FD',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  currentUserTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 8,
  },
  currentUserText: {
    fontSize: 14,
    color: '#1C1C1E',
    marginBottom: 4,
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    textAlign: 'center',
    padding: 20,
  },
});

export default TestUserDisplay;
