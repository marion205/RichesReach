import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  ScrollView,
  Alert,
  Share,
  Clipboard,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';

const { width } = Dimensions.get('window');

interface ReferralReward {
  id: string;
  type: 'cash' | 'premium' | 'crypto' | 'merchandise';
  amount: number;
  description: string;
  icon: string;
  color: string;
  isClaimed: boolean;
  expiresAt: string;
}

interface CommunityChallenge {
  id: string;
  title: string;
  description: string;
  type: 'referral' | 'trading' | 'learning' | 'social';
  reward: ReferralReward;
  progress: number;
  target: number;
  participants: number;
  timeRemaining: string;
  isActive: boolean;
  leaderboard: ChallengeParticipant[];
}

interface ChallengeParticipant {
  id: string;
  name: string;
  avatar: string;
  score: number;
  rank: number;
}

interface ViralGrowthSystemProps {
  onRewardClaimed: (reward: ReferralReward) => void;
  onChallengeJoined: (challenge: CommunityChallenge) => void;
}

export default function ViralGrowthSystem({ onRewardClaimed, onChallengeJoined }: ViralGrowthSystemProps) {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'referrals' | 'challenges' | 'rewards'>('referrals');
  const [referralCode, setReferralCode] = useState('RICHES2024');
  const [referralStats, setReferralStats] = useState({
    totalReferrals: 0,
    successfulReferrals: 0,
    totalEarnings: 0,
    pendingRewards: 0,
  });
  const [rewards, setRewards] = useState<ReferralReward[]>([]);
  const [challenges, setChallenges] = useState<CommunityChallenge[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    loadData();
    startEntranceAnimation();
    startPulseAnimation();
  }, []);

  const startEntranceAnimation = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Simulate API calls
      const mockRewards: ReferralReward[] = [
        {
          id: '1',
          type: 'cash',
          amount: 25,
          description: 'Referral bonus for successful signup',
          icon: '💰',
          color: '#34C759',
          isClaimed: false,
          expiresAt: '2024-12-31',
        },
        {
          id: '2',
          type: 'premium',
          amount: 1,
          description: '1 month free Premium subscription',
          icon: '👑',
          color: '#FFD700',
          isClaimed: true,
          expiresAt: '2024-12-31',
        },
        {
          id: '3',
          type: 'crypto',
          amount: 50,
          description: '$50 in Bitcoin for 5 successful referrals',
          icon: '₿',
          color: '#FF9500',
          isClaimed: false,
          expiresAt: '2024-12-31',
        },
      ];

      const mockChallenges: CommunityChallenge[] = [
        {
          id: '1',
          title: 'BIPOC Wealth Builder Challenge',
          description: 'Refer 10 friends and help build generational wealth in our community',
          type: 'referral',
          reward: mockRewards[2],
          progress: 3,
          target: 10,
          participants: 1247,
          timeRemaining: '15 days left',
          isActive: true,
          leaderboard: [
            {
              id: '1',
              name: 'Marcus Johnson',
              avatar: 'https://via.placeholder.com/40',
              score: 15,
              rank: 1,
            },
            {
              id: '2',
              name: 'Aisha Williams',
              avatar: 'https://via.placeholder.com/40',
              score: 12,
              rank: 2,
            },
            {
              id: '3',
              name: 'David Chen',
              avatar: 'https://via.placeholder.com/40',
              score: 10,
              rank: 3,
            },
          ],
        },
        {
          id: '2',
          title: 'Trading Mastery Challenge',
          description: 'Complete 50 successful trades and share your strategies',
          type: 'trading',
          reward: {
            id: '4',
            type: 'premium',
            amount: 3,
            description: '3 months free Premium',
            icon: '👑',
            color: '#FFD700',
            isClaimed: false,
            expiresAt: '2024-12-31',
          },
          progress: 23,
          target: 50,
          participants: 892,
          timeRemaining: '8 days left',
          isActive: true,
          leaderboard: [],
        },
      ];
      
      setRewards(mockRewards);
      setChallenges(mockChallenges);
    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load viral growth data');
    } finally {
      setLoading(false);
    }
  };

  const shareReferralCode = async () => {
    try {
      const message = `Join me on RichesReach - the AI-powered wealth building platform for BIPOC communities! Use my referral code ${referralCode} to get started with $25 bonus. Let's build generational wealth together! 🚀💰`;
      
      await Share.share({
        message,
        title: 'Join RichesReach',
        url: `https://richesreach.net/invite/${referralCode}`,
      });
    } catch (error) {
      console.error('Error sharing referral code:', error);
    }
  };

  const copyReferralCode = () => {
    Clipboard.setString(referralCode);
    Alert.alert('Copied!', 'Referral code copied to clipboard');
  };

  const claimReward = async (reward: ReferralReward) => {
    try {
      Alert.alert(
        'Claim Reward',
        `Claim ${reward.description}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Claim', 
            onPress: () => {
              setRewards(prev => 
                prev.map(r => 
                  r.id === reward.id 
                    ? { ...r, isClaimed: true }
                    : r
                )
              );
              onRewardClaimed(reward);
              Alert.alert('Success', 'Reward claimed successfully!');
            }
          },
        ]
      );
    } catch (error) {
      console.error('Error claiming reward:', error);
    }
  };

  const joinChallenge = async (challenge: CommunityChallenge) => {
    try {
      Alert.alert(
        'Join Challenge',
        `Join "${challenge.title}"?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Join', 
            onPress: () => {
              onChallengeJoined(challenge);
              Alert.alert('Success', 'Challenge joined successfully!');
            }
          },
        ]
      );
    } catch (error) {
      console.error('Error joining challenge:', error);
    }
  };

  const getRewardIcon = (type: string) => {
    switch (type) {
      case 'cash': return '💰';
      case 'premium': return '👑';
      case 'crypto': return '₿';
      case 'merchandise': return '🎁';
      default: return '🎯';
    }
  };

  const getChallengeIcon = (type: string) => {
    switch (type) {
      case 'referral': return '👥';
      case 'trading': return '📈';
      case 'learning': return '🎓';
      case 'social': return '💬';
      default: return '🏆';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator
          size="large"
          color="#EC4899"
          style={styles.loadingAnimation}
        />
        <Text style={styles.loadingText}>Loading viral growth system...</Text>
      </View>
    );
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Viral Growth</Text>
        <Text style={styles.headerSubtitle}>Earn while you grow the community</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        {[
          { id: 'referrals', name: 'Referrals', icon: '👥' },
          { id: 'challenges', name: 'Challenges', icon: '🏆' },
          { id: 'rewards', name: 'Rewards', icon: '🎁' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tabButton,
              activeTab === tab.id && styles.tabButtonActive,
            ]}
            onPress={() => setActiveTab(tab.id as any)}
          >
            <Text style={styles.tabIcon}>{tab.icon}</Text>
            <Text style={[
              styles.tabText,
              activeTab === tab.id && styles.tabTextActive,
            ]}>
              {tab.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'referrals' && (
          <View style={styles.referralsContent}>
            {/* Referral Stats */}
            <View style={styles.statsContainer}>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>{referralStats.totalReferrals}</Text>
                <Text style={styles.statLabel}>Total Referrals</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>{referralStats.successfulReferrals}</Text>
                <Text style={styles.statLabel}>Successful</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>${referralStats.totalEarnings}</Text>
                <Text style={styles.statLabel}>Total Earnings</Text>
              </View>
            </View>

            {/* Referral Code */}
            <View style={styles.referralCodeCard}>
              <View intensity={20} style={styles.referralCodeBlur}>
                <Text style={styles.referralCodeTitle}>Your Referral Code</Text>
                <Animated.View
                  style={[
                    styles.referralCodeContainer,
                    {
                      transform: [{ scale: pulseAnim }],
                    },
                  ]}
                >
                  <Text style={styles.referralCode}>{referralCode}</Text>
                </Animated.View>
                <Text style={styles.referralCodeDescription}>
                  Share this code with friends to earn rewards when they join!
                </Text>
                
                <View style={styles.referralActions}>
                  <TouchableOpacity style={styles.shareButton} onPress={shareReferralCode}>
                    <LinearGradient
                      colors={['#667eea', '#764ba2']}
                      style={styles.shareButtonGradient}
                    >
                      <Text style={styles.shareButtonText}>📤 Share</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                  
                  <TouchableOpacity style={styles.copyButton} onPress={copyReferralCode}>
                    <Text style={styles.copyButtonText}>📋 Copy</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>

            {/* Referral Benefits */}
            <View style={styles.benefitsContainer}>
              <Text style={styles.benefitsTitle}>Referral Benefits</Text>
              {[
                { icon: '💰', title: '$25 Cash Bonus', description: 'For each successful referral' },
                { icon: '👑', title: 'Premium Access', description: 'Free month for 3 referrals' },
                { icon: '₿', title: 'Crypto Rewards', description: '$50 Bitcoin for 5 referrals' },
                { icon: '🎁', title: 'Exclusive Merch', description: 'RichesReach swag for top referrers' },
              ].map((benefit, index) => (
                <View key={index} style={styles.benefitItem}>
                  <Text style={styles.benefitIcon}>{benefit.icon}</Text>
                  <View style={styles.benefitInfo}>
                    <Text style={styles.benefitTitle}>{benefit.title}</Text>
                    <Text style={styles.benefitDescription}>{benefit.description}</Text>
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}

        {activeTab === 'challenges' && (
          <View style={styles.challengesContent}>
            {challenges.map((challenge) => (
              <ChallengeCard
                key={challenge.id}
                challenge={challenge}
                onJoin={() => joinChallenge(challenge)}
                getChallengeIcon={getChallengeIcon}
              />
            ))}
          </View>
        )}

        {activeTab === 'rewards' && (
          <View style={styles.rewardsContent}>
            {rewards.map((reward) => (
              <RewardCard
                key={reward.id}
                reward={reward}
                onClaim={() => claimReward(reward)}
                getRewardIcon={getRewardIcon}
              />
            ))}
          </View>
        )}
      </ScrollView>
    </Animated.View>
  );
}

// Challenge Card Component
function ChallengeCard({ challenge, onJoin, getChallengeIcon }: any) {
  const progressPercentage = (challenge.progress / challenge.target) * 100;
  
  return (
    <View style={styles.challengeCard}>
      <View intensity={20} style={styles.challengeBlur}>
        {/* Header */}
        <View style={styles.challengeHeader}>
          <View style={styles.challengeInfo}>
            <Text style={styles.challengeIcon}>{getChallengeIcon(challenge.type)}</Text>
            <View>
              <Text style={styles.challengeTitle}>{challenge.title}</Text>
              <Text style={styles.challengeDescription} numberOfLines={2}>
                {challenge.description}
              </Text>
            </View>
          </View>
          
          <TouchableOpacity style={styles.joinChallengeButton} onPress={onJoin}>
            <Text style={styles.joinChallengeButtonText}>Join</Text>
          </TouchableOpacity>
        </View>

        {/* Progress */}
        <View style={styles.challengeProgress}>
          <View style={styles.progressHeader}>
            <Text style={styles.progressText}>
              {challenge.progress} / {challenge.target}
            </Text>
            <Text style={styles.progressPercentage}>
              {(progressPercentage || 0).toFixed(0)}%
            </Text>
          </View>
          
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${progressPercentage}%` }
              ]}
            />
          </View>
        </View>

        {/* Challenge Stats */}
        <View style={styles.challengeStats}>
          <View style={styles.challengeStat}>
            <Text style={styles.challengeStatValue}>{challenge.participants}</Text>
            <Text style={styles.challengeStatLabel}>Participants</Text>
          </View>
          <View style={styles.challengeStat}>
            <Text style={styles.challengeStatValue}>{challenge.timeRemaining}</Text>
            <Text style={styles.challengeStatLabel}>Time Left</Text>
          </View>
          <View style={styles.challengeStat}>
            <Text style={styles.challengeStatValue}>{challenge.reward.icon}</Text>
            <Text style={styles.challengeStatLabel}>Reward</Text>
          </View>
        </View>

        {/* Leaderboard */}
        {challenge.leaderboard.length > 0 && (
          <View style={styles.leaderboard}>
            <Text style={styles.leaderboardTitle}>Top Performers</Text>
            {challenge.leaderboard.map((participant: ChallengeParticipant) => (
              <View key={participant.id} style={styles.leaderboardItem}>
                <Text style={styles.leaderboardRank}>#{participant.rank}</Text>
                <Text style={styles.leaderboardName}>{participant.name}</Text>
                <Text style={styles.leaderboardScore}>{participant.score}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </View>
  );
}

// Reward Card Component
function RewardCard({ reward, onClaim, getRewardIcon }: any) {
  return (
    <View style={styles.rewardCard}>
      <View intensity={20} style={styles.rewardBlur}>
        <View style={styles.rewardHeader}>
          <View style={[styles.rewardIcon, { backgroundColor: reward.color }]}>
            <Text style={styles.rewardIconText}>{getRewardIcon(reward.type)}</Text>
          </View>
          
          <View style={styles.rewardInfo}>
            <Text style={styles.rewardTitle}>{reward.description}</Text>
            <Text style={styles.rewardAmount}>
              {reward.type === 'cash' && '$'}
              {reward.amount}
              {reward.type === 'premium' && ' months'}
              {reward.type === 'crypto' && ' BTC'}
            </Text>
          </View>
          
          <TouchableOpacity
            style={[
              styles.claimButton,
              reward.isClaimed && styles.claimedButton,
            ]}
            onPress={onClaim}
            disabled={reward.isClaimed}
          >
            <Text style={[
              styles.claimButtonText,
              reward.isClaimed && styles.claimedButtonText,
            ]}>
              {reward.isClaimed ? '✓ Claimed' : 'Claim'}
            </Text>
          </TouchableOpacity>
        </View>
        
        <Text style={styles.rewardExpiry}>
          Expires: {new Date(reward.expiresAt).toLocaleDateString()}
        </Text>
      </View>
    </View>
  );
}

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
  loadingAnimation: {
    width: 120,
    height: 120,
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabButtonActive: {
    borderBottomColor: '#667eea',
  },
  tabIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  tabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#667eea',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  referralsContent: {
    padding: 16,
  },
  statsContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  referralCodeCard: {
    marginBottom: 20,
  },
  referralCodeBlur: {
    padding: 20,
    borderRadius: 16,
  },
  referralCodeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 16,
  },
  referralCodeContainer: {
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  referralCode: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#667eea',
    letterSpacing: 2,
  },
  referralCodeDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  referralActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  shareButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  shareButtonGradient: {
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  shareButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  copyButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 20,
    backgroundColor: '#34C759',
  },
  copyButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  benefitsContainer: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
  },
  benefitsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  benefitIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  benefitInfo: {
    flex: 1,
  },
  benefitTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  benefitDescription: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  challengesContent: {
    padding: 16,
  },
  challengeCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  challengeBlur: {
    padding: 20,
  },
  challengeHeader: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  challengeInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  challengeIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  challengeTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  challengeDescription: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  joinChallengeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#667eea',
  },
  joinChallengeButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  challengeProgress: {
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressText: {
    fontSize: 14,
    color: '#666',
  },
  progressPercentage: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#667eea',
    borderRadius: 4,
  },
  challengeStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  challengeStat: {
    alignItems: 'center',
  },
  challengeStatValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  challengeStatLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  leaderboard: {
    marginTop: 16,
  },
  leaderboardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  leaderboardRank: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#667eea',
    width: 30,
  },
  leaderboardName: {
    fontSize: 14,
    color: '#1a1a1a',
    flex: 1,
  },
  leaderboardScore: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  rewardsContent: {
    padding: 16,
  },
  rewardCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  rewardBlur: {
    padding: 20,
  },
  rewardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  rewardIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  rewardIconText: {
    fontSize: 24,
  },
  rewardInfo: {
    flex: 1,
  },
  rewardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  rewardAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#667eea',
    marginTop: 2,
  },
  claimButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#667eea',
  },
  claimedButton: {
    backgroundColor: '#34C759',
  },
  claimButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  claimedButtonText: {
    color: 'white',
  },
  rewardExpiry: {
    fontSize: 12,
    color: '#666',
  },
});
