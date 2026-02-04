import React, {
    useState, useRef, useEffect, useMemo, useCallback, memo,
  } from 'react';
  import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView,
    FlatList, TextInput, RefreshControl, DeviceEventEmitter,
  } from 'react-native';
  import { TID } from '../testIDs';
  import { useNavigation } from '@react-navigation/native';
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
import { assistantQuery } from '../services/aiClient';
import { usePortfolioHistory, setPortfolioHistory } from '../shared/portfolioHistory';

// New imports for smart portfolio metrics
import { FEATURE_PORTFOLIO_METRICS } from '../config/flags';
import { isMarketDataHealthy, MarketDataHealthStatus } from '../services/healthService';
import { mark, PerformanceMarkers } from '../utils/timing';
import { API_BASE, API_HTTP } from '../config/api';
import { useAuth } from '../contexts/AuthContext';
import { useDailyBriefProgress } from '../hooks/useDailyBriefProgress';
import type { NavigateParams } from './types';
// Create a safe logger that always works, even if the import fails
// This prevents "Property 'logger' doesn't exist" errors
const createSafeLogger = () => {
  let loggerBase: any = null;
  
  try {
    const loggerModule = require('../utils/logger');
    loggerBase = loggerModule?.default || loggerModule?.logger || loggerModule;
  } catch (e) {
    // Import failed, use console fallback
  }
  
  const safeConsole = typeof console !== 'undefined' ? console : {
    log: () => {},
    warn: () => {},
    error: () => {},
    info: () => {},
    debug: () => {},
  };
  
  return {
    log: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.log === 'function') {
          loggerBase.log(...args);
        } else {
          safeConsole.log(...args);
        }
      } catch (e) {
        safeConsole.log(...args);
      }
    },
    warn: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.warn === 'function') {
          loggerBase.warn(...args);
        } else {
          safeConsole.warn(...args);
        }
      } catch (e) {
        safeConsole.warn(...args);
      }
    },
    error: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.error === 'function') {
          loggerBase.error(...args);
        } else {
          safeConsole.error(...args);
        }
      } catch (e) {
        safeConsole.error(...args);
      }
    },
    info: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.info === 'function') {
          loggerBase.info(...args);
        } else {
          safeConsole.info(...args);
        }
      } catch (e) {
        safeConsole.info(...args);
      }
    },
    debug: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.debug === 'function') {
          loggerBase.debug(...args);
        } else {
          safeConsole.debug(...args);
        }
      } catch (e) {
        safeConsole.debug(...args);
      }
    },
  };
};

// Initialize logger immediately - this ensures it's always defined
let logger = createSafeLogger();

// Final safety check - ensure logger is always a valid object
if (!logger || typeof logger !== 'object') {
  logger = {
    log: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.log) {
          // Fallback to console if logger not available
          logger.log(...args);
        }
      } catch (e) {}
    },
    warn: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.warn) {
          // Fallback to console if logger not available
          logger.warn(...args);
        }
      } catch (e) {}
    },
    error: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.error) {
          // Fallback to console if logger not available
          logger.error(...args);
        }
      } catch (e) {}
    },
    info: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.info) {
          console.info(...args);
        }
      } catch (e) {}
    },
    debug: (...args: any[]) => {
      try {
        if (typeof console !== 'undefined' && console.debug) {
          console.debug(...args);
        }
      } catch (e) {}
    },
  };
}

// Ensure all methods exist
if (!logger.log) logger.log = () => {};
if (!logger.warn) logger.warn = () => {};
if (!logger.error) logger.error = () => {};
if (!logger.info) logger.info = () => {};
if (!logger.debug) logger.debug = () => {};
import AuraHalo from '../components/AuraHalo';
import CalmGoalNudge from '../components/CalmGoalNudge';
import { recognizeCalmGoalIntent } from '../services/VoiceCoachIntent';
import CalmGoalSheet from '../components/CalmGoalSheet';
import { navigate as globalNavigate } from './NavigationService';
import NextMoveModal from '../components/NextMoveModal';
import BreathCheck from '../components/BreathCheck';
import BreathCheckModal from '../components/BreathCheckModal';
import { onHotword, triggerHotword } from '../services/VoiceHotword';
import { personaCopy, inferPersona } from '../services/IntentPersona';
import VoiceCaptureSheet from '../features/voice/VoiceCaptureSheet';
import { parseIntent } from '../features/voice/intent';
import { getMockHomeScreenPortfolio } from '../services/mockPortfolioData';
  
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
    const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    
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
                'Ask me anything about your finances. I can help with:\n• Investment strategies and portfolio analysis\n• Market insights and economic trends\n• Financial planning and budgeting\n• Risk assessment and diversification\n• Trading education and terminology\n• Real-time market commentary\n• Personalized financial advice\n\nType or use voice—grounded in your data.',
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
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      scrollTimeoutRef.current = setTimeout(() => {
        listRef.current?.scrollToEnd?.({ animated: true });
        scrollTimeoutRef.current = null;
      }, 80);
    }, []);
    
    // Cleanup scroll timeout on unmount
    useEffect(() => {
      return () => {
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
          scrollTimeoutRef.current = null;
        }
      };
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
            <Text style={styles.chatTitle}>Ask</Text>
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
            testID="message-input"
            style={styles.chatInput}
            placeholder="Ask about personal finance..."
            value={chatInput}
            onChangeText={setChatInput}
            multiline
            maxLength={500}
            accessibilityLabel="Chat input"
          />
          <TouchableOpacity
            testID="send-message-button"
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
  const HomeScreen = ({ navigateTo }: { navigateTo?: (screen: string, data?: NavigateParams) => void }) => {
    const client = useApolloClient();
    // Timeout refs for various operations
    const marketDataTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const dailyBriefTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const navigationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const navigation = useNavigation();
    const { token } = useAuth();
    
    // Smart portfolio metrics state
    const [canQueryMetrics, setCanQueryMetrics] = useState(false);
    const [marketDataHealth, setMarketDataHealth] = useState<MarketDataHealthStatus | null>(null);
    
    // Daily Brief streak (custom hook with cleanup)
    const { streak: dailyBriefStreak, loading: dailyBriefLoading } = useDailyBriefProgress(token ?? null);
    const hasCheckedDailyBrief = useRef(false);
  
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
          logger.log('[HomeScreen] Portfolio metrics feature disabled');
          return;
        }
        
        const stop = mark(PerformanceMarkers.MARKET_DATA_FETCH);
        
        try {
          const health = await isMarketDataHealthy(API_BASE);
          
          if (active) {
            setMarketDataHealth(health);
            
            if (health.isHealthy) {
              logger.log('[HomeScreen] Market data is healthy, enabling portfolio metrics');
              // Small delay to let UI settle after navigation
              if (marketDataTimeoutRef.current) {
                clearTimeout(marketDataTimeoutRef.current);
              }
              marketDataTimeoutRef.current = setTimeout(() => {
                if (active) {
                  setCanQueryMetrics(true);
                }
                marketDataTimeoutRef.current = null;
              }, 300);
            } else {
              logger.warn('[HomeScreen] Market data is unhealthy:', health.error);
              setCanQueryMetrics(false);
            }
          }
          
          stop();
        } catch (error) {
          logger.error('[HomeScreen] Error checking market data health:', error);
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
        if (marketDataTimeoutRef.current) {
          clearTimeout(marketDataTimeoutRef.current);
          marketDataTimeoutRef.current = null;
        }
      };
    }, []); // Run once when component mounts

    // Auto-navigate to Daily Brief if not completed today (only once per session)
    useEffect(() => {
      let active = true;
      const checkAndNavigateToDailyBrief = async () => {
        if (!token || hasCheckedDailyBrief.current) return;
        try {
          await new Promise(resolve => setTimeout(resolve, 1000));
          if (!active) return;
          const response = await fetch(`${API_HTTP}/api/daily-brief/today`, {
            method: 'GET',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          if (!active) return;
          if (response.ok) {
            const data = await response.json();
            if (!data.is_completed && !hasCheckedDailyBrief.current) {
              hasCheckedDailyBrief.current = true;
              if (dailyBriefTimeoutRef.current) clearTimeout(dailyBriefTimeoutRef.current);
              dailyBriefTimeoutRef.current = setTimeout(() => {
                if (!active) return;
                if (navigateTo) navigateTo('daily-brief');
                else navigation.navigate('daily-brief' as never);
                dailyBriefTimeoutRef.current = null;
              }, 500);
            } else if (data.is_completed) {
              hasCheckedDailyBrief.current = true;
            }
          }
        } catch (error) {
          logger.log('Daily brief check failed:', error);
          hasCheckedDailyBrief.current = true;
        }
      };
      if (token && !hasCheckedDailyBrief.current) {
        checkAndNavigateToDailyBrief();
      }
      return () => {
        active = false;
        if (dailyBriefTimeoutRef.current) {
          clearTimeout(dailyBriefTimeoutRef.current);
          dailyBriefTimeoutRef.current = null;
        }
      };
    }, [token, navigateTo, navigation]);
  
    // Profile
    const [userProfile, setUserProfile] = useState<ExtendedUserProfile | null>(null);
    const [profileLoading, setProfileLoading] = useState(true);
  
    // Live data
    const [live, setLive] = useState<PortfolioUpdate | null>(null);
  
    // Real-time service snapshot
    const [realPortfolio, setRealPortfolio] = useState<PortfolioMetrics | null>(null);
  
    // Chat
    const [chatOpen, setChatOpen] = useState(false);
    const [showCalmSheet, setShowCalmSheet] = useState(false);
    const [showCalmNudge, setShowCalmNudge] = useState(false);
    const [nudgeCopy, setNudgeCopy] = useState<{title: string; subtitle: string}>({title: 'You seem anxious about spending.', subtitle: 'Want to set a calm investing goal?'});
    const [showNextMove, setShowNextMove] = useState(false);
    const [showBreathCheck, setShowBreathCheck] = useState(false);
    const micHoldRef = useRef(false);
    const [showVoice, setShowVoice] = useState(false);

    // Derived anxiousness score (fallback until on-device model is wired)
    // Note: resolved is declared later (line 1019), using realPortfolio here
    const anxiousnessScore = React.useMemo(() => {
      const ret = Number(realPortfolio?.totalReturnPercent ?? 0);
      if (isNaN(ret)) return 0.3;
      if (ret >= 0) return 0.3;
      // Map -10% to ~1.0, small losses to lower scores
      const score = Math.min(1, Math.abs(ret) / 10);
      return Math.max(0.3, score);
    }, [realPortfolio?.totalReturnPercent]);

    // Hotword subscription - listens for "Hey Riches"
    useEffect(() => {
      const cleanup = onHotword(() => {
        const ret = realPortfolio?.totalReturnPercent ?? 0;
        let score = 0.3;
        if (ret >= 0) score = 0.3;
        else {
          const calculatedScore = Math.min(1, Math.abs(ret) / 10);
          score = Math.max(0.3, calculatedScore);
        }
        const copy = personaCopy(inferPersona({ anxiety: score, opportunity: 0.5 }));
        logger.log('🎤 "Hey Riches" detected → opening voice assistant', copy);
        setShowNextMove(true);
      });
      return cleanup as () => void;
    }, [realPortfolio?.totalReturnPercent]);

    // Initialize wake word detection - tries ML first, then Whisper, then Porcupine
    useEffect(() => {
      let cleanup: (() => Promise<void>) | null = null;
      
      const initWakeWord = async () => {
        // Priority 1: ML-based detection (fastest, most efficient)
        try {
          const { mlWakeWordService } = await import('../services/MLWakeWordService');
          const started = await mlWakeWordService.start();
          if (started) {
            logger.log('✅ "Hey Riches" wake word detection active (ML-based)');
            cleanup = async () => {
              await mlWakeWordService.stop();
            };
            return; // Success with ML service
          }
        } catch (error: unknown) {
          logger.log('ℹ️ ML wake word not available, trying Whisper-based...');
        }

        // Priority 2: Whisper-based (uses your server, no API keys)
        try {
          const { customWakeWordService } = await import('../services/CustomWakeWordService');
          const started = await customWakeWordService.start();
          if (started) {
            logger.log('✅ "Hey Riches" wake word detection active (Whisper-based)');
            cleanup = async () => {
              await customWakeWordService.stop();
            };
            return; // Success with custom service
          }
        } catch (error: unknown) {
          logger.log('ℹ️ Whisper wake word not available, trying Porcupine...');
        }

        // Priority 3: Porcupine (requires API key and dependencies)
        // Wrap in try-catch to handle bundling errors gracefully
        try {
          // Use dynamic import with error handling
          let porcupineModule;
          try {
            porcupineModule = await import('../services/PorcupineWakeWordService');
          } catch (importError: any) {
            // If the module itself fails to load (bundling error), skip it
            const errorMsg = importError?.message || String(importError);
            if (errorMsg.includes('@picovoice/react-native-voice-processor') || 
                errorMsg.includes('Unable to resolve')) {
              logger.log('ℹ️ Porcupine not available (missing dependencies - using fallback services)');
              return; // Skip Porcupine, continue with other services
            }
            throw importError; // Re-throw unexpected errors
          }
          
          const { porcupineWakeWordService } = porcupineModule;
          const started = await porcupineWakeWordService.start();
          if (started) {
            logger.log('✅ "Hey Riches" wake word detection active (Porcupine)');
            cleanup = async () => {
              await porcupineWakeWordService.stop();
              await porcupineWakeWordService.release();
            };
          } else {
            logger.log('ℹ️ Porcupine wake word not available (missing dependencies or API key)');
          }
        } catch (error: unknown) {
          // Silently handle - Porcupine requires additional dependencies that may not be installed
          const errorMessage = error instanceof Error ? error.message : String(error);
          if (errorMessage.includes('@picovoice/react-native-voice-processor') || 
              errorMessage.includes('Unable to resolve')) {
            logger.log('ℹ️ Porcupine not available (missing dependencies - using fallback services)');
          } else {
            logger.log('ℹ️ Porcupine wake word not available:', errorMessage);
          }
        }
      };

      initWakeWord();

      return () => {
        if (cleanup) {
          cleanup();
        }
      };
    }, []);
    const [showLiquidityChip, setShowLiquidityChip] = useState(false);
    // Mic button listener from TopHeader -> open calm goal flow
    useEffect(() => {
      const sub = DeviceEventEmitter.addListener('calm_goal_mic', () => {
        logger.log('🎤 [HomeScreen] Received calm_goal_mic event, opening Calm Goal sheet');
        setShowCalmSheet(true);
      });
      logger.log('🎤 [HomeScreen] Registered calm_goal_mic event listener');
      return () => {
        logger.log('🎤 [HomeScreen] Removing calm_goal_mic event listener');
        sub.remove();
      };
    }, []);
    
  
    // Evaluate CalmGoal nudge (Predictive Empathy)
    useEffect(() => {
      const evaluate = async () => {
        try {
          const now = Date.now();
          const lastStr = await AsyncStorage.getItem('nudge:lastShown');
          const last = lastStr ? Number(lastStr) : 0;
          const cooldownMs = 1000 * 60 * 60 * 20; // 20h cooldown
          if (now - last < cooldownMs) { setShowCalmNudge(false); return; }

          // resolved is declared later, using realPortfolio here
          const retPct = Number(realPortfolio?.totalReturnPercent ?? 0);
          const streak = Number(userProfile?.stats?.streakDays ?? 0);
          const hour = new Date().getHours();
          const evening = hour >= 18 && hour <= 23;

          // Simple anxiety score
          let score = 0;
          if (retPct < -2) score += Math.min(10, Math.abs(retPct));
          if (streak <= 2) score += 3;
          if (evening) score += 2;

          // A/B copy selection (sticky)
          const savedVariant = await AsyncStorage.getItem('nudge:variant');
          let variant = savedVariant || (Math.random() < 0.5 ? 'calm' : 'coach');
          if (!savedVariant) await AsyncStorage.setItem('nudge:variant', variant);
          const copy = variant === 'coach'
            ? { title: 'Let’s steady the wheel.', subtitle: 'Set a calm investing goal in 30 seconds.' }
            : { title: 'You seem anxious about spending.', subtitle: 'Want to set a calm investing goal?' };
          setNudgeCopy(copy);

          setShowCalmNudge(score >= 6);
        } catch {}
      };
      evaluate();
    }, [realPortfolio?.totalReturnPercent, userProfile?.stats?.streakDays]);

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
          logger.warn('Profile load error', e);
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
          logger.warn('Real portfolio snapshot error', e);
        }
      })();
      return () => { mounted = false; };
    }, []);
  
    /* ---------- websocket live updates ---------- */
    useEffect(() => {
      const handleUpdate = (p: PortfolioUpdate) => setLive(p);
      webSocketService.setCallbacks({ onPortfolioUpdate: handleUpdate });
      webSocketService.connect();
      webSocketService.subscribeToPortfolio();
  
      return () => {
        // restore previous callbacks (so other screens keep theirs)
        webSocketService.setCallbacks({});
        webSocketService.unsubscribeFromPortfolio();
      };
    }, []);
  
    /* ---------- AI service ---------- */
    const generateAIResponse = useCallback(async (userInput: string): Promise<string> => {
      // Provide immediate fallback responses based on common questions (fast path)
      const lowerInput = userInput.toLowerCase();
      
      // Quick keyword-based responses for instant feedback
      if (lowerInput.includes('investment') || lowerInput.includes('invest') || lowerInput.includes('portfolio')) {
        // Try API first, but with quick timeout
        try {
          const userId = userData?.me?.id || (userProfile as any)?.id || 'demo-user';
          const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), 5000); // 5 second timeout
          });
          const apiPromise = assistantQuery({ user_id: userId, prompt: userInput });
          const response = await Promise.race([apiPromise, timeoutPromise]);
          if (response?.answer || response?.response) {
            return response.answer || response.response;
          }
        } catch (error: unknown) {
          // Fall through to fast fallback
        }
        return 'Diversification across different asset classes (stocks, bonds, ETFs) is a fundamental investment strategy. Consider your risk tolerance and time horizon when making investment decisions. For long-term growth, index funds and ETFs are excellent starting points.';
      }
      
      if (lowerInput.includes('budget') || lowerInput.includes('saving') || lowerInput.includes('spend')) {
        try {
          const userId = userData?.me?.id || (userProfile as any)?.id || 'demo-user';
          const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), 5000);
          });
          const apiPromise = assistantQuery({ user_id: userId, prompt: userInput });
          const response = await Promise.race([apiPromise, timeoutPromise]);
          if (response?.answer || response?.response) {
            return response.answer || response.response;
          }
        } catch (error: unknown) {
          // Fall through to fast fallback
        }
        return 'The 50/30/20 rule allocates 50% to needs (housing, food, utilities), 30% to wants (entertainment, dining), and 20% to savings and debt repayment. This is a great starting point for financial planning. Start by tracking your expenses for a month to see where your money goes.';
      }
      
      if (lowerInput.includes('stock') || lowerInput.includes('market') || lowerInput.includes('trading')) {
        try {
          const userId = userData?.me?.id || (userProfile as any)?.id || 'demo-user';
          const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), 5000);
          });
          const apiPromise = assistantQuery({ user_id: userId, prompt: userInput });
          const response = await Promise.race([apiPromise, timeoutPromise]);
          if (response?.answer || response?.response) {
            return response.answer || response.response;
          }
        } catch (error: unknown) {
          // Fall through to fast fallback
        }
        return 'Stock market investing involves risk, and it\'s important to do your research, diversify your portfolio, and invest for the long term rather than trying to time the market. Consider dollar-cost averaging to reduce the impact of volatility.';
      }
      
      if (lowerInput.includes('retirement') || lowerInput.includes('401k') || lowerInput.includes('ira')) {
        try {
          const userId = userData?.me?.id || (userProfile as any)?.id || 'demo-user';
          const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), 5000);
          });
          const apiPromise = assistantQuery({ user_id: userId, prompt: userInput });
          const response = await Promise.race([apiPromise, timeoutPromise]);
          if (response?.answer || response?.response) {
            return response.answer || response.response;
          }
        } catch (error: unknown) {
          // Fall through to fast fallback
        }
        return 'Start early, take advantage of employer 401(k) matching, and consider both traditional and Roth IRAs. The power of compound interest over time is your greatest ally in retirement planning. Aim to save at least 15% of your income for retirement.';
      }
      
      // For other questions, try API with timeout, then fallback
      try {
        const userId = userData?.me?.id || (userProfile as any)?.id || 'demo-user';
        const timeoutPromise = new Promise<never>((_, reject) => {
          setTimeout(() => reject(new Error('Request timeout')), 8000); // 8 second timeout
        });
        const apiPromise = assistantQuery({ user_id: userId, prompt: userInput });
        const response = await Promise.race([apiPromise, timeoutPromise]);
        return response?.answer || response?.response || 'I hit a snag processing that—mind trying again?';
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger.log('AI query timeout or error, using fallback:', errorMessage);
        // Provide helpful generic fallback
        return 'I\'m here to help with investment strategies, portfolio analysis, budgeting, retirement planning, and market insights. Could you rephrase your question or ask about a specific topic like "How do I start investing?" or "What is dollar-cost averaging?"';
      }
    }, [userData?.me?.id, (userProfile as any)?.id]);
  
    /* ---------- helpers ---------- */
    const go = useCallback((screen: string, params?: NavigateParams) => {
      logger.log('HomeScreen.go() called with:', screen, params);
      
      // Screens that are in InvestStack need nested navigation
      const investStackScreens = [
        'swing-signals', 
        'swing-risk-coach', 
        'swing-backtesting', 
        'swing-leaderboard', 
        'swing-trading-test',
        'portfolio-management',
        'portfolio',
        'trading',
        'stock',
        'StockDetail',
        'premium-analytics',
        'paper-trading',
        'PaperTrading'
      ];
      
      if (investStackScreens.includes(screen)) {
        try {
          globalNavigate('Invest', { screen, params });
          return;
        } catch (error) {
          logger.error('HomeScreen.go() nested navigation error:', error);
        }
      }
      
      try { 
        // Try direct navigation first
        (navigation.navigate as any)(screen, params);
      } catch (directError) {
        // Fallback to globalNavigate
        try {
          globalNavigate(screen, params);
        } catch (error) {
          logger.error('HomeScreen.go() globalNavigate error:', error);
        }
      }

      if (typeof navigateTo === 'function') {
        try {
          navigateTo?.(screen, params);
        } catch (error) {
          logger.error('HomeScreen.go() navigateTo error:', error);
        }
      }
    }, [navigateTo, navigation]);
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
  
      // Use mock data for demo when no real data available
      const mockData = getMockHomeScreenPortfolio();

      const totalValue =
        realPortfolio?.totalValue ??
        (isFinite(Number(liveVal)) ? Number(liveVal) : undefined) ??
        g?.totalValue ??
        mockData.portfolioMetrics.totalValue;

      const totalReturn =
        realPortfolio?.totalReturn ??
        (isFinite(Number(liveRet)) ? Number(liveRet) : undefined) ??
        g?.totalReturn ??
        mockData.portfolioMetrics.totalReturn;

      const totalReturnPercent =
        realPortfolio?.totalReturnPercent ??
        (isFinite(Number(livePct)) ? Number(livePct) : undefined) ??
        g?.totalReturnPercent ??
        mockData.portfolioMetrics.totalReturnPercent;

      const rawHoldings =
        realPortfolio?.holdings ??
        live?.holdings ??
        g?.holdings ??
        mockData.portfolioMetrics.holdings;
  
      // Transform holdings to match PortfolioHoldings interface
      interface RawHolding {
        symbol?: string;
        stock?: { symbol?: string; companyName?: string };
        shares?: number;
        quantity?: number;
        currentPrice?: number;
        totalValue?: number;
        returnAmount?: number;
        change?: number;
        returnPercent?: number;
        changePercent?: number;
        companyName?: string;
        name?: string;
        [key: string]: unknown;
      }
      const holdings = rawHoldings.map((h: RawHolding) => ({
        symbol: h.symbol || h.stock?.symbol || '',
        quantity: h.shares || h.quantity || 0,
        currentPrice: h.currentPrice || 0,
        totalValue: h.totalValue || 0,
        change: h.returnAmount || h.change || 0,
        changePercent: h.returnPercent || h.changePercent || 0,
        name: h.companyName || h.stock?.companyName || h.name,
      }));
  
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
        logger.warn('Refresh error', e);
      } finally {
        setRefreshing(false);
      }
    }, [refetchPortfolio, refetchUser]);
  
    const premium = !!userData?.me?.hasPremiumAccess;
  
    /* ===================== Render ===================== */
    return (
      <View testID={TID.screens.home} style={styles.container}>
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
              {/* Aura around the portfolio card */}
              <View style={{ marginHorizontal: 0 }}>
                <AuraHalo
                  score={Math.max(-1, Math.min(1, (resolved.totalReturnPercent ?? 0) / 20))}
                >
                  <PortfolioPerformanceCard
                    totalValue={resolved.totalValue}
                    totalReturn={resolved.totalReturn}
                    totalReturnPercent={resolved.totalReturnPercent}
                    benchmarkSymbol="SPY"
                    useRealBenchmarkData={true}
                    navigateTo={navigateTo}
                  />
                </AuraHalo>
              </View>

              <PortfolioHoldings
                holdings={(resolved.holdings || []) as any}
                onStockPress={(symbol) => go('StockDetail', { symbol })}
                onBuy={(holding) => {
                  go('trading', { symbol: holding.symbol, action: 'buy' });
                }}
                onSell={(holding) => {
                  go('trading', { symbol: holding.symbol, action: 'sell' });
                }}
                loading={portfolioLoading}
                onAddHoldings={() => go('portfolio-management')}
              />
            </>
          )}
  
          {/* Predictive empathy nudge (enhanced heuristic + cooldown + A/B copy) */}
          {showCalmNudge && (
            <CalmGoalNudge
              title={nudgeCopy.title}
              subtitle={nudgeCopy.subtitle}
              onStart={async () => {
                await AsyncStorage.setItem('nudge:lastShown', String(Date.now()));
                setShowCalmNudge(false);
                setShowCalmSheet(true);
              }}
              onDismiss={async () => {
                await AsyncStorage.setItem('nudge:lastShown', String(Date.now()));
                setShowCalmNudge(false);
              }}
            />
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

          {/* TEMPORARY: Camera Test Button - Commented out after successful WebRTC implementation */}
          {/* Uncomment below to re-enable camera diagnostic screen */}
          {/*
          <View style={styles.section}>
            <TouchableOpacity 
              style={[styles.learningCard, { backgroundColor: '#FF3B30', marginBottom: 12 }]} 
              onPress={() => {
                try {
                  navigation.navigate('camera-test' as never);
                } catch (error) {
                  logger.error('Navigation error:', error);
                  globalNavigate('camera-test');
                }
              }}
            >
              <View style={styles.learningCardIcon}>
                <Icon name="camera" size={24} color="#FFFFFF" />
              </View>
              <View style={styles.learningCardContent}>
                <Text style={[styles.learningCardTitle, { color: '#FFFFFF' }]}>🧪 Test Camera (Debug)</Text>
                <Text style={[styles.learningCardDescription, { color: '#FFFFFF', opacity: 0.9 }]}>WebRTC Front Camera Diagnostic</Text>
              </View>
              <Icon name="chevron-right" size={16} color="#FFFFFF" />
            </TouchableOpacity>
          </View>
          */}

          {/* Smart Wealth Suite Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionTitleContainer}>
                <Icon name="send" size={20} color="#8B5CF6" style={styles.sectionTitleIcon} />
                <Text style={styles.sectionTitle}>Smart Wealth Suite</Text>
              </View>
            </View>
            
            <View style={styles.learningCards}>
              {/* Breath Check card */}
              <BreathCheck onSuggest={() => {
                logger.log('BreathCheck: Starting breathing exercise');
                setShowBreathCheck(true);
              }} />

              {/* Daily Brief card */}
              <TouchableOpacity 
                style={[styles.learningCard, { backgroundColor: '#FFF4E6', borderWidth: 1, borderColor: '#FFE5CC' }]} 
                onPress={() => {
                  logger.log('Daily Brief pressed');
                  try {
                    if (navigateTo) {
                      navigateTo('daily-brief');
                    } else {
                      navigation.navigate('daily-brief' as never);
                    }
                  } catch (error) {
                    logger.error('Navigation error:', error);
                    globalNavigate('daily-brief');
                  }
                }}
              >
                <View style={[styles.learningCardIcon, { backgroundColor: '#FF6B35' }]}>
                  <Text style={{ fontSize: 24, color: '#FFFFFF' }}>🔥</Text>
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={[styles.learningCardTitle, { color: '#1a1a1a' }]}>🔥 Daily Brief</Text>
                  <Text style={[styles.learningCardDescription, { color: '#666' }]}>
                    {dailyBriefStreak !== null && dailyBriefStreak > 0 
                      ? `Day ${dailyBriefStreak} of your streak`
                      : 'Your 2-minute investing guide'}
                  </Text>
                  <Text style={[styles.learningCardMeta, { color: '#FF6B35', fontWeight: '600' }]}>
                    {dailyBriefStreak !== null && dailyBriefStreak > 0 
                      ? 'Keep it going!'
                      : 'Plain English • Personalized'}
                  </Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => setShowNextMove(true)} onLongPress={() => setShowVoice(true)}>
                <View style={styles.learningCardIcon}>
                  <Icon name="compass" size={24} color="#0EA5E9" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Next Move (Voice)</Text>
                  <Text style={styles.learningCardDescription}>Simulated trades based on your profile</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              {/* Fireside quick entry */}
              <TouchableOpacity style={styles.learningCard} onPress={() => {
                logger.log('Fireside Exchanges pressed');
                try {
                  navigation.navigate('fireside' as never);
                } catch (error) {
                  logger.error('Navigation error:', error);
                  globalNavigate('fireside');
                }
              }}>
                <View style={styles.learningCardIcon}>
                  <Icon name="mic" size={24} color="#8B5CF6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Fireside Exchanges</Text>
                  <Text style={styles.learningCardDescription}>Invite-only voice rooms with AI summaries</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              {showLiquidityChip && (
                <TouchableOpacity style={styles.learningCard} onPress={() => globalNavigate('Learn', { screen: 'tutor-module' })}>
                  <View style={styles.learningCardIcon}>
                    <Icon name="droplet" size={24} color="#34C759" />
                  </View>
                  <View style={styles.learningCardContent}>
                    <Text style={styles.learningCardTitle}>Liquidity 101</Text>
                    <Text style={styles.learningCardDescription}>Unlock achieved – Learn while doing</Text>
                    <Text style={styles.learningCardMeta}>Lesson • 3 min</Text>
                  </View>
                  <Icon name="chevron-right" size={16} color="#8E8E93" />
                </TouchableOpacity>
              )}
              <TouchableOpacity style={styles.learningCard} onPress={() => {
                logger.log('Why Now pressed');
                try {
                  navigation.navigate('oracle-insights' as never);
                } catch (error) {
                  logger.error('Navigation error:', error);
                  globalNavigate('oracle-insights');
                }
              }}>
                <View style={styles.learningCardIcon}>
                  <Icon name="eye" size={24} color="#8B5CF6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Why Now</Text>
                  <Text style={styles.learningCardDescription}>One sentence, one visual</Text>
                  <Text style={styles.learningCardMeta}>Predictive • AI</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => {
                logger.log('Ask pressed');
                try {
                  navigation.navigate('voice-ai' as never);
                } catch (error) {
                  logger.error('Navigation error:', error);
                  globalNavigate('voice-ai');
                }
              }}>
                <View style={styles.learningCardIcon}>
                  <Icon name="mic" size={24} color="#10B981" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Ask</Text>
                  <Text style={styles.learningCardDescription}>Hands-free trading & insights</Text>
                  <Text style={styles.learningCardMeta}>Voice • AI</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => {
                logger.log('Blockchain Integration pressed');
                try {
                  navigation.navigate('blockchain-integration' as never);
                } catch (error) {
                  logger.error('Navigation error:', error);
                  globalNavigate('blockchain-integration');
                }
              }}>
                <View style={styles.learningCardIcon}>
                  <Icon name="link" size={24} color="#8B5CF6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Blockchain Integration</Text>
                  <Text style={styles.learningCardDescription}>Tokenize your portfolio & access DeFi</Text>
                  <Text style={styles.learningCardMeta}>DeFi • Tokenization • Advanced</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => {
                logger.log('Pro/Labs pressed');
                try {
                  // Always use navigateTo if available (preferred method)
                  if (navigateTo) {
                    logger.log('Using navigateTo function');
                    navigateTo('pro-labs');
                  } 
                  // Fallback to global navigate function (from window - set in App.tsx)
                  else if (typeof window !== 'undefined' && (window as any).__navigateToGlobal) {
                    logger.log('Using window.__navigateToGlobal');
                    (window as any).__navigateToGlobal('pro-labs');
                  }
                  // Last resort: try to set screen directly via window
                  else if (typeof window !== 'undefined' && (window as any).__setCurrentScreen) {
                    logger.log('Using window.__setCurrentScreen');
                    (window as any).__setCurrentScreen('pro-labs');
                  }
                  // Final fallback: alert user (shouldn't happen)
                  else {
                    logger.error('No navigation method available!');
                    alert('Navigation not available. Please reload the app.');
                  }
                } catch (error) {
                  logger.error('Navigation error:', error);
                  // Emergency fallback: try window methods again
                  try {
                    if (typeof window !== 'undefined') {
                      if ((window as any).__navigateToGlobal) {
                        (window as any).__navigateToGlobal('pro-labs');
                      } else if ((window as any).__setCurrentScreen) {
                        (window as any).__setCurrentScreen('pro-labs');
                      }
                    }
                  } catch (e) {
                    logger.error('All navigation methods failed:', e);
                  }
                }
              }}>
                <View style={styles.learningCardIcon}>
                  <Icon name="sliders" size={24} color="#3B82F6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Pro / Labs</Text>
                  <Text style={styles.learningCardDescription}>Advanced RAHA controls & strategy builder</Text>
                  <Text style={styles.learningCardMeta}>Advanced • Power Users</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => {
                logger.log('The Whisper pressed');
                try {
                  // Use AAPL as default (we have signals for it)
                  // Realistic mock price data for AAPL
                  const mockPrice = 175.50;
                  const mockChange = 2.30;
                  const mockChangePercent = 1.33;
                  
                  if (navigateTo) {
                    navigateTo('the-whisper', {
                      symbol: 'AAPL',
                      currentPrice: mockPrice,
                      change: mockChange,
                      changePercent: mockChangePercent,
                    });
                  } else if (typeof window !== 'undefined' && (window as any).__navigateToGlobal) {
                    (window as any).__navigateToGlobal('the-whisper', {
                      symbol: 'AAPL',
                      currentPrice: mockPrice,
                      change: mockChange,
                      changePercent: mockChangePercent,
                    });
                  } else if (typeof window !== 'undefined' && (window as any).__setCurrentScreen) {
                    (window as any).__setCurrentScreen('the-whisper');
                    // Also set params in window
                    (window as any).__currentScreenParams = {
                      symbol: 'AAPL',
                      currentPrice: mockPrice,
                      change: mockChange,
                      changePercent: mockChangePercent,
                    };
                  }
                } catch (error) {
                  logger.error('Navigation error to The Whisper:', error);
                }
              }}>
                <View style={styles.learningCardIcon}>
                  <Icon name="eye" size={24} color="#10B981" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>The Whisper</Text>
                  <Text style={styles.learningCardDescription}>See your likely P&L before you trade</Text>
                  <Text style={styles.learningCardMeta}>Ghost Candle • RAHA</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Community Features Section (moved up) */}
          <View style={styles.learningSection}>
            <View style={styles.learningHeader}>
              <View style={styles.learningHeaderLeft}>
                <Icon name="users" size={20} color="#10B981" />
                <Text style={styles.learningTitle}>Community Features</Text>
              </View>
            </View>
            
            <View style={styles.learningCards}>
              <TouchableOpacity style={styles.learningCard} onPress={() => go('wealth-circles')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="circle" size={24} color="#10B981" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Wealth Circles</Text>
                  <Text style={styles.learningCardDescription}>Connect with your community</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('peer-progress')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="trending-up" size={24} color="#F59E0B" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Peer Progress</Text>
                  <Text style={styles.learningCardDescription}>See community achievements</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('trade-challenges')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="trending-up" size={24} color="#EF4444" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Trade Challenges</Text>
                  <Text style={styles.learningCardDescription}>Compete with the community</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Learning & AI Tools Section */}
          <View style={styles.learningSection}>
            <View style={styles.learningHeader}>
              <View style={styles.learningHeaderLeft}>
                <Icon name="book-open" size={20} color="#00cc99" />
                <Text style={styles.learningTitle}>Learning & AI Tools</Text>
              </View>
            </View>
            
            <View style={styles.learningCards}>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => globalNavigate('Learn', { screen: 'tutor-ask-explain' })}>
                <View style={styles.learningCardIcon}>
                  <Icon name="help-circle" size={24} color="#34C759" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Ask & Explain</Text>
                  <Text style={styles.learningCardDescription}>Ask questions or get explanations</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => globalNavigate('Learn', { screen: 'tutor-quiz' })}>
                <View style={styles.learningCardIcon}>
                  <Icon name="check-circle" size={24} color="#FF9500" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Knowledge Quiz</Text>
                  <Text style={styles.learningCardDescription}>Test your financial knowledge</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('Learn', { screen: 'tutor-module' })}>
                <View style={styles.learningCardIcon}>
                  <Icon name="book" size={24} color="#AF52DE" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Learning Modules</Text>
                  <Text style={styles.learningCardDescription}>Structured learning topics</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('Learn', { screen: 'lesson-library' })}>
                <View style={styles.learningCardIcon}>
                  <Icon name="book-open" size={24} color="#8B5CF6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Lesson Library</Text>
                  <Text style={styles.learningCardDescription}>Browse all investing lessons</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('market-commentary')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="trending-up" size={24} color="#FF3B30" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Market Commentary</Text>
                  <Text style={styles.learningCardDescription}>Daily market insights</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('ai-scans')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="search" size={24} color="#007AFF" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>AI Market Scans</Text>
                  <Text style={styles.learningCardDescription}>Market intelligence & analysis</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => go('ai-trading-coach')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="zap" size={24} color="#3B82F6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>AI Trading Coach</Text>
                  <Text style={styles.learningCardDescription}>Advanced AI-powered coaching</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('paper-trading')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="file-text" size={24} color="#00cc99" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Paper Trading</Text>
                  <Text style={styles.learningCardDescription}>Practice trading with $100k virtual money</Text>
                  <Text style={styles.learningCardMeta}>Risk-Free • Real-Time P&L</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('daily-voice-digest')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="mic" size={24} color="#F59E0B" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Daily Voice Digest</Text>
                  <Text style={styles.learningCardDescription}>60-second personalized market briefings</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>

          

          {/* Advanced Personalization Section */}
          <View style={styles.learningSection}>
            <View style={styles.learningHeader}>
              <View style={styles.learningHeaderLeft}>
                <Icon name="arrow-right" size={20} color="#8B5CF6" />
                <Text style={styles.learningTitle}>Advanced Personalization</Text>
              </View>
            </View>
            
            <View style={styles.learningCards}>
              <TouchableOpacity style={styles.learningCard} onPress={() => go('personalization-dashboard')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="user" size={24} color="#8B5CF6" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Personalization Dashboard</Text>
                  <Text style={styles.learningCardDescription}>Your AI-powered profile</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('behavioral-analytics')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="trending-up" size={24} color="#10B981" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Behavioral Analytics</Text>
                  <Text style={styles.learningCardDescription}>AI behavior insights</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('dynamic-content')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="zap" size={24} color="#F59E0B" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Dynamic Content</Text>
                  <Text style={styles.learningCardDescription}>Real-time adaptation</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.learningCard} onPress={() => go('ai-options')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="layers" size={24} color="#FF2D92" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>AI Options</Text>
                  <Text style={styles.learningCardDescription}>Options strategy recommendations</Text>
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
              <TouchableOpacity style={styles.learningButton} onPress={() => go('swing-trading-test')}>
                <Text style={styles.learningButtonText}>Explore All</Text>
                <Icon name="chevron-right" size={16} color="#AF52DE" />
              </TouchableOpacity>
            </View>

            <View style={styles.learningCards}>
              <TouchableOpacity style={styles.learningCard} onPress={() => go('swing-signals')}>
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

              <TouchableOpacity style={styles.learningCard} onPress={() => go('swing-risk-coach')}>
                <View style={styles.learningCardIcon}>
                  <Icon name="shield" size={24} color="#10B981" />
                </View>
                <View style={styles.learningCardContent}>
                  <Text style={styles.learningCardTitle}>Guardrails</Text>
                  <Text style={styles.learningCardDescription}>Position sizing & risk management</Text>
                  <Text style={styles.learningCardMeta}>Calculator • Analysis</Text>
                </View>
                <Icon name="chevron-right" size={16} color="#8E8E93" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.learningCard} onPress={() => go('swing-backtesting')}>
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

              <TouchableOpacity style={styles.learningCard} onPress={() => go('swing-leaderboard')}>
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


        </ScrollView>
  
        {/* Floating chat button */}
        <TouchableOpacity
          style={styles.chatButton}
          onPress={() => setChatOpen(true)}
          accessibilityLabel="Open Ask"
          testID="chat-fab"
        >
          <Icon name="message-circle" size={24} color="#fff" />
        </TouchableOpacity>
  
        {/* Chat modal */}
        <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} generateAIResponse={generateAIResponse} />

        {/* Calm Goal Sheet */}
        <CalmGoalSheet
          visible={showCalmSheet}
          onClose={() => setShowCalmSheet(false)}
          onConfirm={(plan) => {
            setShowCalmSheet(false);
            logger.log('Calm goal confirmed', plan);
            setShowLiquidityChip(true);
            // Navigate: Home -> Invest tab -> Portfolio
            try {
              globalNavigate('Invest');
              if (navigationTimeoutRef.current) {
                clearTimeout(navigationTimeoutRef.current);
              }
              navigationTimeoutRef.current = setTimeout(() => {
                globalNavigate('Invest', { screen: 'Portfolio' });
                navigationTimeoutRef.current = null;
              }, 50);
            } catch (e) {
              // Fallback for legacy routing
              go('portfolio');
            }
          }}
        />

        {/* Breath Check Modal */}
        <BreathCheckModal 
          visible={showBreathCheck} 
          onClose={() => setShowBreathCheck(false)}
          onComplete={(suggestion) => {
            setShowBreathCheck(false);
            if (suggestion) {
              logger.log('BreathCheck completed with suggestion:', suggestion);
              setShowNextMove(true);
            }
          }}
        />

        {/* Next Move Modal */}
        <NextMoveModal visible={showNextMove} onClose={() => setShowNextMove(false)} portfolioValue={resolved?.totalValue ?? 0} />

        {/* Voice Capture Sheet */}
        <VoiceCaptureSheet
          visible={showVoice}
          onClose={() => setShowVoice(false)}
          onResult={(text) => {
            const intent = parseIntent(text);
            if (intent.type === 'calm-goal') {
              setShowCalmSheet(true);
              return;
            }
            if (intent.type === 'next-move') {
              setShowNextMove(true);
              return;
            }
          }}
        />
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

    /* Smart Wealth Suite Section */
    section: { marginTop: 24, marginBottom: 16 },
    sectionHeader: {
      flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      marginBottom: 16, paddingHorizontal: 16,
    },
    sectionTitleContainer: { flexDirection: 'row', alignItems: 'center' },
    sectionTitleIcon: { marginRight: 8 },
    sectionTitle: { fontSize: 18, fontWeight: '700', color: '#1C1C1E' },
    sectionSubtitle: { fontSize: 14, color: '#8E8E93', marginTop: 4 },
    
    /* Badge */
    badgeContainer: {
      backgroundColor: '#F59E0B',
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 4,
      marginLeft: 8
    },
    badgeText: {
      color: '#ffffff',
      fontSize: 10,
      fontWeight: '700',
      textTransform: 'uppercase'
    },
  
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