import React, {
    useState, useRef, useEffect, useMemo, useCallback, memo,
  } from 'react';
  import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView,
    FlatList, TextInput, RefreshControl,
  } from 'react-native';
  import { useApolloClient, useQuery, gql } from '@apollo/client';
  import Icon from 'react-native-vector-icons/Feather';
  import AsyncStorage from '@react-native-async-storage/async-storage';
  
import PortfolioPerformanceCard from '../features/portfolio/components/PortfolioPerformanceCard';
import PortfolioHoldings from '../features/portfolio/components/PortfolioHoldings';
import { BasicRiskMetrics } from '../components';
import PortfolioComparison from '../features/portfolio/components/PortfolioComparison';
import { GraphSkeleton, HoldingsSkeleton } from '../components/skeletons/HomeSkeletons';

import RealTimePortfolioService, { PortfolioMetrics } from '../features/portfolio/services/RealTimePortfolioService';
import webSocketService, { PortfolioUpdate } from '../services/WebSocketService';
import UserProfileService, { ExtendedUserProfile } from '../features/user/services/UserProfileService';
import FinancialChatbotService, { AlphaVantageRecommendationProvider } from '../services/FinancialChatbotService';
import { usePortfolioHistory, setPortfolioHistory } from '../shared/portfolioHistory';

// New imports for smart portfolio metrics
import { FEATURE_PORTFOLIO_METRICS } from '../config/flags';
import { isMarketDataHealthy } from '../services/healthService';
import { mark, PerformanceMarkers } from '../utils/timing';
import { API_BASE } from '../config/api';
  
  /* ===================== GraphQL ===================== */
  const GET_PORTFOLIO_METRICS = gql`
    query GetPortfolioMetrics {
      portfolioMetrics {
        totalValue
        totalCost
        totalReturn
        totalReturnPercent
        holdings {
          symbol
          companyName
          shares
          currentPrice
          totalValue
          costBasis
          returnAmount
          returnPercent
          sector
        }
      }
    }
  `;
  
  const GET_ME = gql`
    query GetMe {
      me {
        id
        name
        email
        hasPremiumAccess
        subscriptionTier
      }
    }
  `;
  
  /* ===================== Types ===================== */
  interface ChatMsg {
    id: string;
    role: 'user' | 'assistant';
    content: string;
  }
  
  const QUICK_PROMPTS = [
    'What is an ETF?',
    'Roth vs Traditional IRA',
    'Explain 50/30/20 budgeting',
    'How do index funds work?',
    'What is an expense ratio?',
    'Diversification basics',
    'Dollar-cost averaging',
    'How to analyze stocks?',
    'What is market cap?',
    'Emergency fund basics',
    'Credit score importance',
    'Compound interest explained',
    'Options trading basics',
    'How to trade options',
    'Trading fundamentals',
  ] as const;
  
  /* ===================== Chat Panel ===================== */
  const ChatPanel = memo(function ChatPanel({
    open,
    onClose,
    generateAIResponse,
  }: {
    open: boolean;
    onClose: () => void;
    generateAIResponse: (q: string) => Promise<string>;
  }) {
    const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [sending, setSending] = useState(false);
    const listRef = useRef<FlatList<ChatMsg>>(null);
    
    const STORAGE_KEY = 'chat:v1';
  
    // load saved thread when panel opens
    useEffect(() => {
      if (!open) return;
      (async () => {
        try {
          const raw = await AsyncStorage.getItem(STORAGE_KEY);
          if (raw) {
            const parsed: ChatMsg[] = JSON.parse(raw);
            if (Array.isArray(parsed) && parsed.length) setChatMessages(parsed);
          } else if (chatMessages.length === 0) {
            // seed welcome if nothing saved
            setChatMessages([{
              id: String(Date.now()),
              role: 'assistant',
              content:
                'Welcome to your Financial AI Assistant!\n\nI can help you with:\n• Investment basics (ETFs, index funds, stocks)\n• Retirement planning (IRAs, 401(k)s)\n• Budgeting strategies (50/30/20 rule)\n• Risk management and diversification\n• Financial terminology and concepts\n\nThis is educational information only.',
            }]);
          }
        } catch { /* ignore */ }
      })();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open]);
  
    // persist on change (debounced)
    useEffect(() => {
      const id = setTimeout(() => {
        AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(chatMessages)).catch(() => {});
      }, 400);
      return () => clearTimeout(id);
    }, [chatMessages]);
  
    const append = useCallback((m: ChatMsg) => {
      setChatMessages(prev => [...prev, m]);
      setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 80);
    }, []);
  
    const clear = useCallback(() => {
      setChatMessages([]);
      setChatInput('');
      AsyncStorage.removeItem(STORAGE_KEY).catch(() => {});
    }, [STORAGE_KEY]);
  
    const handleQuickPrompt = useCallback(async (prompt: string) => {
      const user: ChatMsg = { id: String(Date.now()), role: 'user', content: prompt };
      append(user);
      setSending(true);
      try {
        const text = await generateAIResponse(prompt);
        append({ id: String(Date.now() + 1), role: 'assistant', content: text });
      } catch {
        append({
          id: String(Date.now() + 1),
          role: 'assistant',
          content: 'Sorry—something went wrong. Please try again.',
        });
      } finally {
        setSending(false);
      }
    }, [append, generateAIResponse]);
  
    const send = useCallback(async () => {
      const trimmed = chatInput.trim();
      if (!trimmed || sending) return;
      const user: ChatMsg = { id: String(Date.now()), role: 'user', content: trimmed };
      append(user);
      setChatInput('');
      setSending(true);
      try {
        const text = await generateAIResponse(trimmed);
        append({ id: String(Date.now() + 1), role: 'assistant', content: text });
      } catch {
        append({
          id: String(Date.now() + 1),
          role: 'assistant',
          content: 'Sorry—something went wrong. Please try again.',
        });
      } finally {
        setSending(false);
      }
    }, [append, chatInput, sending, generateAIResponse]);
  
    if (!open) return null;
  
    return (
      <View style={styles.chatModal} accessibilityViewIsModal>
        <View style={styles.chatHeader}>
          <View style={styles.chatTitleContainer}>
            <Icon name="flash-on" size={20} color="#00cc99" style={styles.chatTitleIcon} />
            <Text style={styles.chatTitle}>Financial Education Assistant</Text>
          </View>
          <View style={styles.chatHeaderActions}>
            <TouchableOpacity onPress={clear} style={styles.chatActionButton} accessibilityLabel="Clear chat">
              <Icon name="trash-2" size={16} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity onPress={onClose} style={styles.chatCloseButton} accessibilityLabel="Close chat">
              <Icon name="x" size={20} color="#666" />
            </TouchableOpacity>
          </View>
        </View>
  
        {/* Quick prompts */}
        <View style={styles.quickPromptsContainer}>
          <FlatList
            data={QUICK_PROMPTS as unknown as string[]}
            keyExtractor={(item) => `prompt-${item}`}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.quickPromptsContent}
            renderItem={({ item }) => (
              <TouchableOpacity style={styles.quickPromptButton} onPress={() => handleQuickPrompt(item)}>
                <Text style={styles.quickPromptText}>{item}</Text>
              </TouchableOpacity>
            )}
          />
        </View>
  
        {/* Messages */}
        <FlatList
          ref={listRef}
          data={chatMessages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={[
              styles.chatMessage,
              item.role === 'user' ? styles.userMessage : styles.assistantMessage,
            ]}>
              <Text style={[
                styles.chatMessageText,
                item.role === 'user' ? styles.userMessageText : styles.assistantMessageText,
              ]}>
                {item.content}
              </Text>
            </View>
          )}
          style={styles.chatMessages}
          showsVerticalScrollIndicator={false}
        />
  
        {/* Input */}
        <View style={styles.chatInputContainer}>
          <TextInput
            style={styles.chatInput}
            placeholder="Ask about personal finance..."
            value={chatInput}
            onChangeText={setChatInput}
            multiline
            maxLength={500}
            accessibilityLabel="Chat input"
          />
          <TouchableOpacity
            style={[styles.chatSendButton, !chatInput.trim() && styles.chatSendButtonDisabled]}
            onPress={send}
            disabled={!chatInput.trim() || sending}
            accessibilityLabel="Send message"
          >
            <Icon name={sending ? 'refresh-cw' : 'send'} size={20} color={chatInput.trim() ? '#fff' : '#ccc'} />
          </TouchableOpacity>
        </View>
      </View>
    );
  });
  
  /* ===================== Home Screen ===================== */
  const HomeScreen = ({ navigateTo }: { navigateTo: (screen: string, data?: any) => void }) => {
    const client = useApolloClient();
    
    // Smart portfolio metrics state
    const [canQueryMetrics, setCanQueryMetrics] = useState(false);
    const [marketDataHealth, setMarketDataHealth] = useState<any>(null);
  
    // GraphQL
    const {
      data: portfolioData,
      loading: portfolioLoading,
      error: portfolioError,
      refetch: refetchPortfolio,
    } = useQuery(GET_PORTFOLIO_METRICS, {
      errorPolicy: 'all',
      fetchPolicy: 'cache-first',
      nextFetchPolicy: 'cache-first',
      notifyOnNetworkStatusChange: true,
      skip: !canQueryMetrics, // Only run when market data is healthy
    });
  
    const {
      data: userData,
      loading: userLoading,
      refetch: refetchUser,
    } = useQuery(GET_ME, {
      errorPolicy: 'ignore',
      fetchPolicy: 'cache-first',
      notifyOnNetworkStatusChange: false,
    });

    // Smart portfolio metrics: Check market data health when component mounts
    useEffect(() => {
      let active = true;
      
      const checkMarketDataHealth = async () => {
        if (!FEATURE_PORTFOLIO_METRICS) {
          console.log('[HomeScreen] Portfolio metrics feature disabled');
          return;
        }
        
        const stop = mark(PerformanceMarkers.MARKET_DATA_FETCH);
        
        try {
          const health = await isMarketDataHealthy(API_BASE);
          
          if (active) {
            setMarketDataHealth(health);
            
            if (health.isHealthy) {
              console.log('[HomeScreen] Market data is healthy, enabling portfolio metrics');
              // Small delay to let UI settle after navigation
              setTimeout(() => {
                if (active) {
                  setCanQueryMetrics(true);
                }
              }, 300);
            } else {
              console.warn('[HomeScreen] Market data is unhealthy:', health.error);
              setCanQueryMetrics(false);
            }
          }
          
          stop();
        } catch (error) {
          console.error('[HomeScreen] Error checking market data health:', error);
          if (active) {
            setCanQueryMetrics(false);
          }
          stop();
        }
      };
      
      checkMarketDataHealth();
      
      return () => {
        active = false;
        setCanQueryMetrics(false);
      };
    }, []); // Run once when component mounts
  
    // Profile
    const [userProfile, setUserProfile] = useState<ExtendedUserProfile | null>(null);
    const [profileLoading, setProfileLoading] = useState(true);
  
    // Live data
    const [live, setLive] = useState<PortfolioUpdate | null>(null);
  
    // Real-time service snapshot
    const [realPortfolio, setRealPortfolio] = useState<PortfolioMetrics | null>(null);
  
    // Chat
    const [chatOpen, setChatOpen] = useState(false);
  
    // Refresh
    const [refreshing, setRefreshing] = useState(false);
  
    /* ---------- load profile ---------- */
    useEffect(() => {
      let mounted = true;
      (async () => {
        try {
          const svc = UserProfileService.getInstance();
          const profile = await svc.getProfile();
          if (mounted) setUserProfile(profile);
        } catch (e) {
          console.warn('Profile load error', e);
        } finally {
          if (mounted) setProfileLoading(false);
        }
      })();
      return () => { mounted = false; };
    }, []);
  
    /* ---------- real portfolio snapshot ---------- */
    useEffect(() => {
      let mounted = true;
      (async () => {
        try {
          const snap = await RealTimePortfolioService.getPortfolioData();
          if (mounted && snap) setRealPortfolio(snap);
        } catch (e) {
          console.warn('Real portfolio snapshot error', e);
        }
      })();
      return () => { mounted = false; };
    }, []);
  
    /* ---------- websocket live updates ---------- */
    useEffect(() => {
      const handleUpdate = (p: PortfolioUpdate) => setLive(p);
      const prev = webSocketService.setCallbacks({ onPortfolioUpdate: handleUpdate });
      webSocketService.connect();
      webSocketService.subscribeToPortfolio();
  
      return () => {
        // restore previous callbacks (so other screens keep theirs)
        webSocketService.setCallbacks(prev || {});
        webSocketService.unsubscribeFromPortfolio();
      };
    }, []);
  
    /* ---------- AI service ---------- */
    const generateAIResponse = useCallback(async (userInput: string): Promise<string> => {
      try {
        const chatbotService = FinancialChatbotService.getInstance(
          new AlphaVantageRecommendationProvider('OHYSFF1AE446O7CR')
        );
        return await chatbotService.processUserInput(userInput);
      } catch (error) {
        console.error('AI error:', error);
        return 'I hit a snag processing that—mind trying again?';
      }
    }, []);
  
    /* ---------- helpers ---------- */
    const getExperienceIcon = useCallback((level: string) => {
      switch (level) {
        case 'beginner': return 'book-open';
        case 'intermediate': return 'trending-up';
        case 'advanced': return 'bar-chart-2';
        default: return 'user';
      }
    }, []);
  
    const getUserStyleSummary = useCallback((profile: ExtendedUserProfile): string => {
      const { experienceLevel: e, riskTolerance: r } = profile;
      if (e === 'beginner' && r === 'conservative') return 'Conservative Beginner - Focus on learning and low-risk investments';
      if (e === 'beginner' && r === 'moderate') return 'Balanced Beginner - Ready to explore moderate risk investments';
      if (e === 'intermediate' && r === 'aggressive') return 'Growth-Oriented Investor - Seeking higher returns with calculated risk';
      if (e === 'advanced' && r === 'aggressive') return 'Sophisticated Investor - Advanced strategies and high-risk opportunities';
      return 'Balanced Investor - Steady growth with moderate risk';
    }, []);
  
    // Unified resolver: prefers real -> live -> graphql -> hardcoded demo
    const resolved = useMemo(() => {
      const g = portfolioData?.portfolioMetrics;
      const liveVal = live?.totalValue;
      const liveRet = live?.totalReturn;
      const livePct = live?.totalReturnPercent;
  
      const totalValue =
        realPortfolio?.totalValue ??
        (isFinite(Number(liveVal)) ? Number(liveVal) : undefined) ??
        g?.totalValue ?? 14303.52;
  
      const totalReturn =
        realPortfolio?.totalReturn ??
        (isFinite(Number(liveRet)) ? Number(liveRet) : undefined) ??
        g?.totalReturn ?? 2145.53;
  
      const totalReturnPercent =
        realPortfolio?.totalReturnPercent ??
        (isFinite(Number(livePct)) ? Number(livePct) : undefined) ??
        g?.totalReturnPercent ?? 17.65;
  
      const holdings =
        realPortfolio?.holdings ??
        live?.holdings ??
        g?.holdings ??
        [];
  
      return { totalValue, totalReturn, totalReturnPercent, holdings };
    }, [realPortfolio, live, portfolioData]);
  
    // Use portfolio history from shared store
    const portfolioHistory = usePortfolioHistory();
    
    // Optional: reconcile from server when refresh happens
    useEffect(() => {
      // When we have fresh portfolio data, we could update the history store
      // setPortfolioHistory(serverHistoryPoints);
    }, [portfolioData]);
  
    const onRefresh = useCallback(async () => {
      setRefreshing(true);
      try {
        await Promise.all([
          refetchPortfolio(),
          refetchUser(),
          RealTimePortfolioService.getPortfolioData().then(s => s && setRealPortfolio(s)),
        ]);
      } catch (e) {
        console.warn('Refresh error', e);
      } finally {
        setRefreshing(false);
      }
    }, [refetchPortfolio, refetchUser]);
  
    const premium = !!userData?.me?.hasPremiumAccess;
  
    /* ===================== Render ===================== */
    return (
      <View style={styles.container}>
        <ScrollView
          style={styles.content}
          refreshControl={
            <RefreshControl refreshing={refreshing || portfolioLoading || userLoading || profileLoading} onRefresh={onRefresh} />
          }
          contentInsetAdjustmentBehavior="automatic"
        >
          {/* Welcome */}
          {userProfile && (
            <View style={styles.welcomeSection}>
              <View style={styles.welcomeHeader}>
                <View style={styles.profileIcon}>
                  <Icon name={getExperienceIcon(userProfile.experienceLevel)} size={20} color="#FFFFFF" />
                </View>
                <View style={styles.welcomeText}>
                  <Text style={styles.welcomeTitle}>Welcome back, {userProfile.experienceLevel} investor!</Text>
                  <Text style={styles.welcomeSubtitle}>{getUserStyleSummary(userProfile)}</Text>
                </View>
              </View>
  
              <View style={styles.quickStats}>
                <View style={styles.statItem}>
                  <Icon name="clock" size={16} color="#007AFF" />
                  <Text style={styles.statValue}>{userProfile.stats.totalLearningTime}m</Text>
                  <Text style={styles.statLabel}>Learning</Text>
                </View>
                <View style={styles.statItem}>
                  <Icon name="check-circle" size={16} color="#34C759" />
                  <Text style={styles.statValue}>{userProfile.stats.modulesCompleted}</Text>
                  <Text style={styles.statLabel}>Modules</Text>
                </View>
                <View style={styles.statItem}>
                  <Icon name="trending-up" size={16} color="#FF3B30" />
                  <Text style={styles.statValue}>{userProfile.stats.streakDays}</Text>
                  <Text style={styles.statLabel}>Streak</Text>
                </View>
              </View>
            </View>
          )}
  
          {/* Portfolio Graph and Holdings with skeleton loading */}
          {(portfolioLoading || profileLoading) ? (
            <>
              <GraphSkeleton />
              <HoldingsSkeleton />
            </>
          ) : (
            <>
              <PortfolioPerformanceCard
                totalValue={resolved.totalValue}
                totalReturn={resolved.totalReturn}
                totalReturnPercent={resolved.totalReturnPercent}
                benchmarkSymbol="SPY"
                useRealBenchmarkData={true}
              />

              {resolved.holdings?.length > 0 ? (
                <PortfolioHoldings
                  holdings={resolved.holdings}
                  onStockPress={(symbol) => navigateTo('StockDetail', { symbol })}
                />
              ) : (
                <HoldingsSkeleton />
              )}
            </>
          )}
  
          {/* Risk & Diversification */}
          {resolved.holdings?.length > 0 && (
            <BasicRiskMetrics
              holdings={resolved.holdings}
              totalValue={resolved.totalValue}
              totalReturn={resolved.totalReturn}
              totalReturnPercent={resolved.totalReturnPercent}
              onNavigate={navigateTo}
              hasPremiumAccess={premium}
            />
          )}
  
          {/* Comparison */}
          {resolved.holdings?.length > 0 && (
            <PortfolioComparison
              totalValue={resolved.totalValue}
              totalReturn={resolved.totalReturn}
              totalReturnPercent={resolved.totalReturnPercent}
              portfolioHistory={portfolioHistory}
            />
          )}

          {/* AI Tools Section */}
          <View style={styles.learningSection}>
            <View style={styles.learningHeader}>
              <View style={styles.learningHeaderLeft}>
                <Icon name="zap" size={20} color="#00cc99" />
                <Text style={styles.learningTitle}>AI Tools</Text>
              </View>
              <TouchableOpacity style={styles.learningButton} onPress={() => navigateTo('ai-scans')}>
                <Text style={styles.learningButtonText}>Explore All</Text>
                <Icon name="chevron-right" size={16} color="#00cc99" />
              </TouchableOpacity>
            </View>

            <View style={styles.learningCards}>
              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('ai-scans')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="search" size={24} color="#00cc99" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>AI Scans</Text>
                  <Text style={styles.learningCardDescription}>Market intelligence & scanning</Text>
                  <Text style={styles.learningCardMeta}>Hedge-fund grade analysis</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('ai-options')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="trending-up" size={24} color="#FF3B30" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>AI Options</Text>
                  <Text style={styles.learningCardDescription}>Options strategy recommendations</Text>
                  <Text style={styles.learningCardMeta}>Advanced options analysis</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>
  
          {/* Swing Trading Section */}
          <View style={styles.learningSection}>
            <View style={styles.learningHeader}>
              <View style={styles.learningHeaderLeft}>
                <Icon name="trending-up" size={20} color="#FF6B35" />
                <Text style={styles.learningTitle}>Swing Trading</Text>
              </View>
              <TouchableOpacity style={styles.learningButton} onPress={() => navigateTo('swing-trading-test')}>
                <Text style={styles.learningButtonText}>Test All</Text>
                <Icon name="chevron-right" size={16} color="#AF52DE" />
              </TouchableOpacity>
            </View>

            <View style={styles.learningCards}>
              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('swing-signals')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="activity" size={24} color="#FF6B35" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Live Signals</Text>
                  <Text style={styles.learningCardDescription}>AI-powered trading signals</Text>
                  <Text style={styles.learningCardMeta}>ML scores • Real-time</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('swing-risk-coach')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="shield" size={24} color="#10B981" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Risk Coach</Text>
                  <Text style={styles.learningCardDescription}>Position sizing & risk management</Text>
                  <Text style={styles.learningCardMeta}>Calculator • Analysis</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('swing-backtesting')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="bar-chart-2" size={24} color="#3B82F6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Backtesting</Text>
                  <Text style={styles.learningCardDescription}>Test strategies with historical data</Text>
                  <Text style={styles.learningCardMeta}>Performance • Analytics</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('swing-leaderboard')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="award" size={24} color="#F59E0B" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Leaderboard</Text>
                  <Text style={styles.learningCardDescription}>Top traders & performance rankings</Text>
                  <Text style={styles.learningCardMeta}>Community • Competition</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Learn section (unchanged aside from tiny spacing tweaks) */}
          <View style={styles.learningSection}>
            <View style={styles.learningHeader}>
              <View style={styles.learningHeaderLeft}>
                <Icon name="book-open" size={20} color="#AF52DE" />
                <Text style={styles.learningTitle}>Learn Investing</Text>
              </View>
              <TouchableOpacity style={styles.learningButton} onPress={() => navigateTo('learning-paths')}>
                <Text style={styles.learningButtonText}>View All</Text>
                <Icon name="chevron-right" size={16} color="#AF52DE" />
              </TouchableOpacity>
            </View>
  
            <View style={styles.learningCards}>
              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('learning-paths')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="play-circle" size={24} color="#34C759" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Getting Started</Text>
                  <Text style={styles.learningCardDescription}>Learn the basics of investing</Text>
                  <Text style={styles.learningCardMeta}>6 modules • 35 min</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
  
              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('portfolio-learning')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="bar-chart-2" size={24} color="#007AFF" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Portfolio Management</Text>
                  <Text style={styles.learningCardDescription}>Optimize your investments</Text>
                  <Text style={styles.learningCardMeta}>6 modules • 35 min</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('options-learning')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="trending-up" size={24} color="#00cc99" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Options Trading</Text>
                  <Text style={styles.learningCardDescription}>Master options strategies</Text>
                  <Text style={styles.learningCardMeta}>4 modules • 30 min</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => navigateTo('sbloc-learning')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="credit-card" size={24} color="#8B5CF6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>SBLOC Guide</Text>
                  <Text style={styles.learningCardDescription}>Securities-based lending</Text>
                  <Text style={styles.learningCardMeta}>5 modules • 25 min</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>

        </ScrollView>
  
        {/* Floating chat button */}
        <TouchableOpacity
          style={styles.chatButton}
          onPress={() => setChatOpen(true)}
          accessibilityLabel="Open financial assistant"
          testID="chat-fab"
        >
          <Icon name="message-circle" size={24} color="#fff" />
        </TouchableOpacity>
  
        {/* Chat modal */}
        <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} generateAIResponse={generateAIResponse} />
      </View>
    );
  };
  
  export default memo(HomeScreen);
  
  /* ===================== Styles (kept familiar; a few small fixes) ===================== */
  const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f8f9fa', paddingTop: 0 },
    content: { flex: 1 },
  
    /* Welcome */
    welcomeSection: {
      backgroundColor: '#FFFFFF', marginHorizontal: 16, marginTop: 16, marginBottom: 8,
      borderRadius: 16, padding: 20, shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1, shadowRadius: 8, elevation: 5, borderWidth: 1, borderColor: '#E5E5EA',
    },
    welcomeHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
    profileIcon: {
      width: 40, height: 40, borderRadius: 20, backgroundColor: '#007AFF',
      justifyContent: 'center', alignItems: 'center', marginRight: 12,
    },
    welcomeText: { flex: 1 },
    welcomeTitle: { fontSize: 18, fontWeight: 'bold', color: '#1C1C1E', marginBottom: 4 },
    welcomeSubtitle: { fontSize: 14, color: '#8E8E93', lineHeight: 20 },
    quickStats: {
      flexDirection: 'row', justifyContent: 'space-around', paddingTop: 16,
      borderTopWidth: 1, borderTopColor: '#E5E5EA',
    },
    statItem: { alignItems: 'center' },
    statValue: { fontSize: 16, fontWeight: 'bold', color: '#1C1C1E', marginTop: 4, marginBottom: 2 },
    statLabel: { fontSize: 12, color: '#8E8E93' },
  
    /* Learn */
    learningSection: { marginTop: 24, marginBottom: 16 },
    learningHeader: {
      flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      marginBottom: 16, paddingHorizontal: 16,
    },
    learningHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
    learningTitle: { fontSize: 18, fontWeight: '700', color: '#1C1C1E' },
    learningButton: { flexDirection: 'row', alignItems: 'center', gap: 4 },
    learningButtonText: { fontSize: 14, fontWeight: '600', color: '#AF52DE' },
    learningCards: { paddingHorizontal: 16, gap: 12 },
    learningCard: {
      backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, flexDirection: 'row', alignItems: 'center',
      shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1,
    },
    learningCardIcon: {
      width: 48, height: 48, borderRadius: 12, backgroundColor: '#F2F2F7',
      justifyContent: 'center', alignItems: 'center', marginRight: 12,
    },
    learningCardContent: { flex: 1 },
    learningCardTitle: { fontSize: 16, fontWeight: '600', color: '#1C1C1E', marginBottom: 4 },
    learningCardDescription: { fontSize: 13, color: '#8E8E93', marginBottom: 4 },
    learningCardMeta: { fontSize: 12, color: '#8E8E93' },
  
    /* Chat */
    chatButton: {
      position: 'absolute', bottom: 20, right: 20, backgroundColor: '#00cc99',
      width: 50, height: 50, borderRadius: 25, justifyContent: 'center', alignItems: 'center',
      elevation: 5, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.2, shadowRadius: 4,
    },
    chatModal: {
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: '#fff',
      padding: 20, paddingTop: 60, shadowColor: '#000', shadowOffset: { width: 0, height: -2 },
      shadowOpacity: 0.2, shadowRadius: 10, elevation: 10,
    },
    chatHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
    chatTitleContainer: { flexDirection: 'row', alignItems: 'center' },
    chatTitleIcon: { marginRight: 8 },
    chatTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
    chatHeaderActions: { flexDirection: 'row' },
    chatActionButton: { marginLeft: 10 },
    chatCloseButton: { marginLeft: 10 },
  
    quickPromptsContainer: {
      marginBottom: 10, paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: '#E5E5EA',
    },
    quickPromptsContent: { paddingHorizontal: 4, gap: 8 },
    quickPromptButton: {
      backgroundColor: '#F0F8FF', paddingVertical: 6, paddingHorizontal: 12, borderRadius: 18,
      marginRight: 8, borderWidth: 1, borderColor: '#E5E5EA', minWidth: 120,
    },
    quickPromptText: { fontSize: 12, color: '#007AFF', fontWeight: '500' },
  
    chatMessages: { flex: 1, marginBottom: 8 },
    chatMessage: { maxWidth: '88%', padding: 10, borderRadius: 10, marginBottom: 8 },
    userMessage: { alignSelf: 'flex-end', backgroundColor: '#00cc99', borderBottomRightRadius: 0 },
    assistantMessage: {
      alignSelf: 'flex-start', backgroundColor: '#f8f9fa', borderBottomLeftRadius: 0,
      borderWidth: 1, borderColor: '#e9ecef',
    },
    chatMessageText: { fontSize: 15, lineHeight: 20 },
    userMessageText: { color: '#fff' },
    assistantMessageText: { color: '#333' },
  
    chatInputContainer: {
      flexDirection: 'row', alignItems: 'flex-end', borderTopWidth: 1, borderTopColor: '#E5E5EA',
      paddingTop: 8, backgroundColor: '#fff',
    },
    chatInput: {
      flex: 1, paddingVertical: 8, paddingHorizontal: 12, borderRadius: 20, backgroundColor: '#F8F9FA',
      fontSize: 14, color: '#333', marginRight: 8, minHeight: 36, maxHeight: 100, borderWidth: 1, borderColor: '#E5E5EA',
    },
    chatSendButton: { backgroundColor: '#00cc99', padding: 8, borderRadius: 18 },
    chatSendButtonDisabled: { backgroundColor: '#ccc' },
  });