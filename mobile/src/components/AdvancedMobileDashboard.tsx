/**
 * Advanced Mobile UI Components for RichesReach
 * Modern, responsive components with gesture support and voice integration
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Dimensions,
  Animated,
  PanGestureHandler,
  State,
  Vibration,
  Alert,
  Modal,
  FlatList,
  RefreshControl,
  StatusBar,
  SafeAreaView,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { useVoice } from '../contexts/VoiceContext';
import { useMutation, useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// GraphQL Queries
const GET_USER_DASHBOARD = gql`
  query GetUserDashboard {
    userProfile {
      id
      name
      avatar
      level
      xp
      streakDays
      portfolioValue
      todayPnL
      totalPnL
    }
    marketStatus {
      isOpen
      nextOpen
      nextClose
    }
    topMovers {
      symbol
      price
      change
      changePercent
    }
    recentTrades {
      id
      symbol
      side
      quantity
      price
      timestamp
      pnl
    }
  }
`;

const GET_EDUCATION_PROGRESS = gql`
  query GetEducationProgress {
    tutorProgress {
      xp
      level
      streakDays
      theta
      badges
    }
    tutorLeague(circle: "bipoc_wealth_builders", period: "weekly") {
      user
      xpWeek
      rank
    }
  }
`;

// Advanced Mobile Dashboard Component
export const AdvancedMobileDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const { speak, parseCommand } = useVoice();
  
  const { data: dashboardData, loading, refetch } = useQuery(GET_USER_DASHBOARD);
  const { data: educationData } = useQuery(GET_EDUCATION_PROGRESS);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(screenHeight)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const handleVoiceCommand = async (command: string) => {
    const parsed = await parseCommand(command);
    if (parsed.intent === 'trade') {
      // Navigate to trading screen
      speak(`Executing trade for ${parsed.symbol}`, { voice: 'Nova' });
    } else if (parsed.intent === 'education') {
      // Navigate to education screen
      speak(`Starting lesson on ${parsed.topic}`, { voice: 'Shimmer' });
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'trading', label: 'Trading', icon: '📈' },
    { id: 'education', label: 'Learn', icon: '🎓' },
    { id: 'social', label: 'Social', icon: '👥' },
    { id: 'profile', label: 'Profile', icon: '👤' },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      
      {/* Header with Voice Button */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.greeting}>
            Welcome back, {dashboardData?.userProfile?.name || 'Trader'}! 👋
          </Text>
          <TouchableOpacity
            style={styles.voiceButton}
            onPress={() => setShowVoiceModal(true)}
          >
            <Text style={styles.voiceIcon}>🎤</Text>
          </TouchableOpacity>
        </View>
        
        {/* Quick Stats */}
        <View style={styles.quickStats}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>
              ${dashboardData?.userProfile?.portfolioValue?.toLocaleString() || '0'}
            </Text>
            <Text style={styles.statLabel}>Portfolio</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={[
              styles.statValue,
              { color: (dashboardData?.userProfile?.todayPnL || 0) >= 0 ? '#00ff88' : '#ff4444' }
            ]}>
              ${dashboardData?.userProfile?.todayPnL?.toFixed(2) || '0.00'}
            </Text>
            <Text style={styles.statLabel}>Today's P&L</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>
              {dashboardData?.userProfile?.streakDays || 0}
            </Text>
            <Text style={styles.statLabel}>Streak</Text>
          </View>
        </View>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {tabs.map((tab) => (
            <TouchableOpacity
              key={tab.id}
              style={[
                styles.tab,
                activeTab === tab.id && styles.activeTab
              ]}
              onPress={() => setActiveTab(tab.id)}
            >
              <Text style={styles.tabIcon}>{tab.icon}</Text>
              <Text style={[
                styles.tabLabel,
                activeTab === tab.id && styles.activeTabLabel
              ]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Content Area */}
      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }]
          }
        ]}
      >
        <ScrollView
          style={styles.scrollView}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          {activeTab === 'overview' && <OverviewTab data={dashboardData} />}
          {activeTab === 'trading' && <TradingTab />}
          {activeTab === 'education' && <EducationTab data={educationData} />}
          {activeTab === 'social' && <SocialTab />}
          {activeTab === 'profile' && <ProfileTab />}
        </ScrollView>
      </Animated.View>

      {/* Voice Command Modal */}
      <VoiceCommandModal
        visible={showVoiceModal}
        onClose={() => setShowVoiceModal(false)}
        onCommand={handleVoiceCommand}
      />
    </SafeAreaView>
  );
};

// Overview Tab Component
const OverviewTab = ({ data }: { data: any }) => {
  return (
    <View style={styles.tabContent}>
      {/* Market Status */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Market Status</Text>
        <View style={styles.marketStatus}>
          <View style={[
            styles.statusIndicator,
            { backgroundColor: data?.marketStatus?.isOpen ? '#00ff88' : '#ff4444' }
          ]} />
          <Text style={styles.statusText}>
            {data?.marketStatus?.isOpen ? 'Market Open' : 'Market Closed'}
          </Text>
        </View>
        {!data?.marketStatus?.isOpen && (
          <Text style={styles.nextOpen}>
            Next open: {data?.marketStatus?.nextOpen}
          </Text>
        )}
      </View>

      {/* Top Movers */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Top Movers</Text>
        {data?.topMovers?.map((mover: any, index: number) => (
          <View key={index} style={styles.moverRow}>
            <Text style={styles.moverSymbol}>{mover.symbol}</Text>
            <Text style={styles.moverPrice}>${mover.price}</Text>
            <Text style={[
              styles.moverChange,
              { color: mover.change >= 0 ? '#00ff88' : '#ff4444' }
            ]}>
              {mover.change >= 0 ? '+' : ''}{mover.changePercent}%
            </Text>
          </View>
        ))}
      </View>

      {/* Recent Trades */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Recent Trades</Text>
        {data?.recentTrades?.map((trade: any, index: number) => (
          <View key={index} style={styles.tradeRow}>
            <View style={styles.tradeInfo}>
              <Text style={styles.tradeSymbol}>{trade.symbol}</Text>
              <Text style={styles.tradeDetails}>
                {trade.side} {trade.quantity} @ ${trade.price}
              </Text>
            </View>
            <Text style={[
              styles.tradePnl,
              { color: trade.pnl >= 0 ? '#00ff88' : '#ff4444' }
            ]}>
              ${trade.pnl?.toFixed(2)}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
};

// Trading Tab Component
const TradingTab = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [orderType, setOrderType] = useState('market');
  const [quantity, setQuantity] = useState('1');
  
  return (
    <View style={styles.tabContent}>
      {/* Quick Trade Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Quick Trade</Text>
        
        {/* Symbol Selection */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Symbol</Text>
          <TouchableOpacity style={styles.symbolButton}>
            <Text style={styles.symbolText}>{selectedSymbol}</Text>
            <Text style={styles.symbolArrow}>▼</Text>
          </TouchableOpacity>
        </View>

        {/* Order Type */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Order Type</Text>
          <View style={styles.orderTypeButtons}>
            {['market', 'limit', 'stop'].map((type) => (
              <TouchableOpacity
                key={type}
                style={[
                  styles.orderTypeButton,
                  orderType === type && styles.activeOrderType
                ]}
                onPress={() => setOrderType(type)}
              >
                <Text style={[
                  styles.orderTypeText,
                  orderType === type && styles.activeOrderTypeText
                ]}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Quantity */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Quantity</Text>
          <View style={styles.quantityInput}>
            <TouchableOpacity style={styles.quantityButton}>
              <Text style={styles.quantityButtonText}>-</Text>
            </TouchableOpacity>
            <Text style={styles.quantityText}>{quantity}</Text>
            <TouchableOpacity style={styles.quantityButton}>
              <Text style={styles.quantityButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity style={[styles.actionButton, styles.buyButton]}>
            <Text style={styles.buyButtonText}>BUY</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionButton, styles.sellButton]}>
            <Text style={styles.sellButtonText}>SELL</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Advanced Orders */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Advanced Orders</Text>
        <View style={styles.advancedOrders}>
          <TouchableOpacity style={styles.advancedOrderButton}>
            <Text style={styles.advancedOrderIcon}>📊</Text>
            <Text style={styles.advancedOrderText}>Bracket Order</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.advancedOrderButton}>
            <Text style={styles.advancedOrderIcon}>🎯</Text>
            <Text style={styles.advancedOrderText}>OCO Order</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.advancedOrderButton}>
            <Text style={styles.advancedOrderIcon}>📈</Text>
            <Text style={styles.advancedOrderText}>Trailing Stop</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

// Education Tab Component
const EducationTab = ({ data }: { data: any }) => {
  const [startLesson] = useMutation(gql`
    mutation StartLesson($topic: String!, $regime: String) {
      startLesson(topic: $topic, regime: $regime) {
        text
        quiz {
          q
          options
          correct
        }
        xpEarned
        streak
      }
    }
  `);

  const handleStartLesson = async (topic: string) => {
    try {
      const result = await startLesson({
        variables: { topic, regime: 'BULL' }
      });
      // Navigate to lesson screen
    } catch (error) {
      console.error('Error starting lesson:', error);
    }
  };

  return (
    <View style={styles.tabContent}>
      {/* Progress Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Learning Progress</Text>
        <View style={styles.progressInfo}>
          <View style={styles.progressItem}>
            <Text style={styles.progressValue}>{data?.tutorProgress?.xp || 0}</Text>
            <Text style={styles.progressLabel}>XP</Text>
          </View>
          <View style={styles.progressItem}>
            <Text style={styles.progressValue}>{data?.tutorProgress?.level || 1}</Text>
            <Text style={styles.progressLabel}>Level</Text>
          </View>
          <View style={styles.progressItem}>
            <Text style={styles.progressValue}>{data?.tutorProgress?.streakDays || 0}</Text>
            <Text style={styles.progressLabel}>Streak</Text>
          </View>
        </View>
        
        {/* XP Progress Bar */}
        <View style={styles.xpProgressBar}>
          <View style={styles.xpProgressFill} />
        </View>
      </View>

      {/* League Rankings */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>League Rankings</Text>
        {data?.tutorLeague?.map((entry: any, index: number) => (
          <View key={index} style={styles.leagueRow}>
            <Text style={styles.leagueRank}>#{entry.rank}</Text>
            <Text style={styles.leagueUser}>{entry.user}</Text>
            <Text style={styles.leagueXp}>{entry.xpWeek} XP</Text>
          </View>
        ))}
      </View>

      {/* Quick Lessons */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Quick Lessons</Text>
        <View style={styles.lessonButtons}>
          {['options', 'volatility', 'risk_management', 'hft'].map((topic) => (
            <TouchableOpacity
              key={topic}
              style={styles.lessonButton}
              onPress={() => handleStartLesson(topic)}
            >
              <Text style={styles.lessonButtonText}>
                {topic.replace('_', ' ').toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </View>
  );
};

// Social Tab Component
const SocialTab = () => {
  return (
    <View style={styles.tabContent}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Wealth Circles</Text>
        <Text style={styles.comingSoon}>Coming Soon!</Text>
      </View>
    </View>
  );
};

// Profile Tab Component
const ProfileTab = () => {
  return (
    <View style={styles.tabContent}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Profile Settings</Text>
        <Text style={styles.comingSoon}>Coming Soon!</Text>
      </View>
    </View>
  );
};

// Voice Command Modal Component
const VoiceCommandModal = ({ 
  visible, 
  onClose, 
  onCommand 
}: { 
  visible: boolean; 
  onClose: () => void; 
  onCommand: (command: string) => void;
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const { speak } = useVoice();

  const handleVoiceCommand = async () => {
    setIsListening(true);
    // Simulate voice recognition
    setTimeout(() => {
      setTranscript('Buy 100 shares of AAPL');
      setIsListening(false);
    }, 2000);
  };

  const executeCommand = () => {
    onCommand(transcript);
    onClose();
    setTranscript('');
  };

  return (
    <Modal visible={visible} transparent animationType="slide">
      <BlurView intensity={20} style={styles.modalOverlay}>
        <View style={styles.voiceModal}>
          <Text style={styles.voiceModalTitle}>Voice Command</Text>
          
          {isListening ? (
            <View style={styles.listeningContainer}>
              <Text style={styles.listeningText}>Listening...</Text>
              <View style={styles.listeningAnimation} />
            </View>
          ) : (
            <View style={styles.commandContainer}>
              <Text style={styles.transcriptText}>{transcript || 'Tap to speak'}</Text>
              <TouchableOpacity
                style={styles.listenButton}
                onPress={handleVoiceCommand}
              >
                <Text style={styles.listenButtonText}>🎤</Text>
              </TouchableOpacity>
            </View>
          )}

          <View style={styles.voiceModalActions}>
            <TouchableOpacity style={styles.cancelButton} onPress={onClose}>
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            {transcript && (
              <TouchableOpacity style={styles.executeButton} onPress={executeCommand}>
                <Text style={styles.executeButtonText}>Execute</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </BlurView>
    </Modal>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  greeting: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  voiceButton: {
    backgroundColor: '#007bff',
    borderRadius: 25,
    width: 50,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceIcon: {
    fontSize: 20,
  },
  quickStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 5,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#888',
  },
  tabContainer: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 10,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    marginHorizontal: 5,
    borderRadius: 20,
  },
  activeTab: {
    backgroundColor: '#007bff',
  },
  tabIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  tabLabel: {
    fontSize: 14,
    color: '#888',
    fontWeight: '500',
  },
  activeTabLabel: {
    color: '#fff',
  },
  content: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  tabContent: {
    padding: 20,
  },
  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  marketStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 10,
  },
  statusText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  nextOpen: {
    fontSize: 14,
    color: '#888',
  },
  moverRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  moverSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  moverPrice: {
    fontSize: 14,
    color: '#fff',
  },
  moverChange: {
    fontSize: 14,
    fontWeight: '500',
  },
  tradeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  tradeInfo: {
    flex: 1,
  },
  tradeSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  tradeDetails: {
    fontSize: 12,
    color: '#888',
  },
  tradePnl: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    color: '#888',
    marginBottom: 8,
  },
  symbolButton: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  symbolText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  symbolArrow: {
    fontSize: 12,
    color: '#888',
  },
  orderTypeButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  orderTypeButton: {
    backgroundColor: '#333',
    borderRadius: 8,
    paddingHorizontal: 20,
    paddingVertical: 10,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  activeOrderType: {
    backgroundColor: '#007bff',
  },
  orderTypeText: {
    fontSize: 14,
    color: '#888',
    fontWeight: '500',
  },
  activeOrderTypeText: {
    color: '#fff',
  },
  quantityInput: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  quantityButton: {
    backgroundColor: '#333',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityButtonText: {
    fontSize: 18,
    color: '#fff',
    fontWeight: 'bold',
  },
  quantityText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginHorizontal: 20,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 5,
  },
  buyButton: {
    backgroundColor: '#00ff88',
  },
  sellButton: {
    backgroundColor: '#ff4444',
  },
  buyButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
  },
  sellButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  advancedOrders: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  advancedOrderButton: {
    backgroundColor: '#333',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 5,
  },
  advancedOrderIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  advancedOrderText: {
    fontSize: 12,
    color: '#fff',
    textAlign: 'center',
  },
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  progressItem: {
    alignItems: 'center',
  },
  progressValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  progressLabel: {
    fontSize: 12,
    color: '#888',
  },
  xpProgressBar: {
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
  },
  xpProgressFill: {
    height: '100%',
    width: '65%',
    backgroundColor: '#007bff',
    borderRadius: 4,
  },
  leagueRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  leagueRank: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#007bff',
  },
  leagueUser: {
    fontSize: 14,
    color: '#fff',
    flex: 1,
    marginLeft: 10,
  },
  leagueXp: {
    fontSize: 14,
    color: '#888',
  },
  lessonButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  lessonButton: {
    backgroundColor: '#333',
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginBottom: 10,
    width: '48%',
    alignItems: 'center',
  },
  lessonButtonText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
  },
  comingSoon: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceModal: {
    backgroundColor: '#1a1a1a',
    borderRadius: 20,
    padding: 30,
    width: screenWidth * 0.9,
    alignItems: 'center',
  },
  voiceModalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 30,
  },
  listeningContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  listeningText: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 20,
  },
  listeningAnimation: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#007bff',
    opacity: 0.7,
  },
  commandContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  transcriptText: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 20,
    textAlign: 'center',
  },
  listenButton: {
    backgroundColor: '#007bff',
    borderRadius: 40,
    width: 80,
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listenButtonText: {
    fontSize: 30,
  },
  voiceModalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  cancelButton: {
    backgroundColor: '#333',
    borderRadius: 8,
    paddingHorizontal: 30,
    paddingVertical: 15,
    flex: 1,
    marginRight: 10,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  executeButton: {
    backgroundColor: '#00ff88',
    borderRadius: 8,
    paddingHorizontal: 30,
    paddingVertical: 15,
    flex: 1,
    marginLeft: 10,
    alignItems: 'center',
  },
  executeButtonText: {
    fontSize: 16,
    color: '#000',
    fontWeight: 'bold',
  },
});

export default AdvancedMobileDashboard;
