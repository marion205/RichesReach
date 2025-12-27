import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Feather from '@expo/vector-icons/Feather';
import { View, Platform, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import ProfileScreen from '../features/user/screens/ProfileScreen';
import BankAccountScreen from '../features/user/screens/BankAccountScreen';
import { setNavigator } from './NavigationService';
import GestureNavigation from '../components/GestureNavigation';
import { TID } from '../testIDs';
// Create a safe logger that always works, even if the import fails
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
const logger = createSafeLogger();

// Existing screens (paths reflect current project structure)
import HomeScreen from '../navigation/HomeScreen';
import ChartTestScreen from '../components/charts/ChartTestScreen';
import CryptoScreen from '../navigation/CryptoScreen';
import AIPortfolioScreen from '../features/portfolio/screens/AIPortfolioScreen';
import TutorScreen from '../features/education/screens/TutorScreen';
import TutorAskExplainScreen from '../features/learning/screens/TutorAskExplainScreen';
import TutorQuizScreen from '../features/learning/screens/TutorQuizScreen';
import TutorModuleScreen from '../features/learning/screens/TutorModuleScreen';
import StockScreen from '../features/stocks/screens/StockScreen';
import StockScreenWrapper from './StockScreenWrapper';
import StockDetailScreen from '../features/stocks/screens/StockDetailScreen';
import PortfolioScreen from '../features/portfolio/screens/PortfolioScreen';
import PortfolioManagementScreen from '../features/portfolio/screens/PortfolioManagementScreen';
import SocialTrading from '../components/SocialTrading';
import FiresideRoomsScreen from '../features/community/screens/FiresideRoomsScreen';
import FiresideRoomScreen from '../features/community/screens/FiresideRoomScreen';
import AIScansScreen from '../features/aiScans/screens/AIScansScreen';
import ScanPlaybookScreen from '../features/aiScans/screens/ScanPlaybookScreen';
import AIOptionsScreen from '../features/options/screens/AIOptionsScreen';
import OptionsCopilotScreen from '../features/options/screens/OptionsCopilotScreen';
import TomorrowScreen from '../features/futures/screens/TomorrowScreen';
import DayTradingScreen from '../features/trading/screens/DayTradingScreen';
import TradingScreenWrapper from './TradingScreenWrapper';
import PaperTradingScreen from '../features/trading/screens/PaperTradingScreen';
import ForexScreen from '../features/forex/ForexScreen';
import MLSystemScreen from '../features/ml/screens/MLSystemScreen';
import RiskManagementScreen from '../features/risk/screens/RiskManagementScreen';
import PremiumAnalyticsScreen from './PremiumAnalyticsScreen';
import ResearchReportScreen from '../features/research/screens/ResearchReportScreen';
import SignalUpdatesScreen from '../features/portfolio/screens/SignalUpdatesScreen';
import PortfolioLeaderboardScreen from '../features/social/screens/PortfolioLeaderboardScreen';
// V2 single-screen utilities used from Home
import OracleInsights from '../components/OracleInsights';
import VoiceAIAssistant from '../components/VoiceAIAssistant';
import BlockchainIntegration from '../components/BlockchainIntegration';
import MarketCommentaryScreen from '../features/news/screens/MarketCommentaryScreen';
import AITradingCoachScreen from '../features/coach/screens/AITradingCoachScreen';
import TradingCoachScreen from '../features/coach/screens/TradingCoachScreen';
import DailyVoiceDigestScreen from '../features/learning/screens/DailyVoiceDigestScreen';
import NotificationCenterScreen from '../features/notifications/screens/NotificationCenterScreen';
import WealthCirclesScreen from '../features/community/screens/WealthCirclesScreen';
import SimpleCircleDetailScreen from '../features/community/screens/SimpleCircleDetailScreen';
import PeerProgressScreen from '../features/community/screens/PeerProgressScreen';
import TradeChallengesScreen from '../features/community/screens/TradeChallengesScreen';
import PersonalizationDashboardScreen from '../features/personalization/screens/PersonalizationDashboardScreen';
import BehavioralAnalyticsScreen from '../features/personalization/screens/BehavioralAnalyticsScreen';
import DynamicContentScreen from '../features/personalization/screens/DynamicContentScreen';
import ARNextMovePreview from '../features/ar/ARNextMovePreview';
import WellnessDashboardScreen from '../features/portfolio/screens/WellnessDashboardScreen';
import BridgeScreen from '../features/blockchain/screens/BridgeScreen';
import SecurityFortress from '../components/SecurityFortress';
import ViralGrowthSystem from '../components/ViralGrowthSystem';
import OnboardingScreen from '../features/auth/screens/OnboardingScreen';
import SubscriptionScreen from '../features/user/screens/SubscriptionScreen';
import CameraTestScreen from '../components/CameraTestScreen';

// New hub screen
import InvestHubScreen from '../features/invest/InvestHubScreen';
import InvestAdvancedSheet from '../features/invest/InvestAdvancedSheet';

// Swing Trading screens
import SwingTradingDashboard from '../features/swingTrading/screens/SwingTradingDashboard';
import SignalsScreen from '../features/swingTrading/screens/SignalsScreen';
import RiskCoachScreen from '../features/swingTrading/screens/RiskCoachScreen';
import BacktestingScreen from '../features/swingTrading/screens/BacktestingScreen';
import LeaderboardScreen from '../features/swingTrading/screens/LeaderboardScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Wrapper components for screens that need props
function SubscriptionScreenWrapper(props: any) {
  return (
    <SubscriptionScreen
      navigateTo={(screen) => {
        try {
          props.navigation.navigate(screen as never);
        } catch (error) {
          logger.error('Navigation error:', error);
        }
      }}
    />
  );
}

function SecurityFortressWrapper(props: any) {
  return (
    <SecurityFortress
      onBiometricSetup={() => logger.log('Biometric setup requested')}
      onSecurityEventPress={(event) => logger.log('Security event:', event)}
    />
  );
}

function ViralGrowthWrapper(props: any) {
  return (
    <ViralGrowthSystem
      onRewardClaimed={(reward) => logger.log('Reward claimed:', reward)}
      onChallengeJoined={(challenge) => logger.log('Challenge joined:', challenge)}
    />
  );
}

function OnboardingScreenWrapper(props: any) {
  return (
    <OnboardingScreen
      onComplete={(profile) => {
        logger.log('Onboarding completed:', profile);
        props.navigation.goBack();
      }}
    />
  );
}

function HomeStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeMain" component={HomeScreen} />
      {/* Legacy alias to preserve existing navigations */}
      <Stack.Screen name="home" component={HomeScreen} />
      <Stack.Screen name="Profile" component={ProfileScreen} />
      <Stack.Screen name="profile" component={ProfileScreen} />
      <Stack.Screen name="bank-accounts" component={BankAccountScreen} options={{ headerShown: true, title: 'Bank Accounts' }} />
      <Stack.Screen name="budgeting" component={require('../features/banking/screens/BudgetingScreen').default} options={{ headerShown: true, title: 'Budget Management' }} />
      <Stack.Screen name="spending-analysis" component={require('../features/banking/screens/SpendingAnalysisScreen').default} options={{ headerShown: true, title: 'Spending Analysis' }} />
      <Stack.Screen 
        name="subscription" 
        component={SubscriptionScreenWrapper}
        options={{ headerShown: true, title: 'Subscription' }}
      />
      {/* V2 utility routes triggered from Home cards */}
      <Stack.Screen name="oracle-insights" component={OracleInsights} />
      <Stack.Screen name="voice-ai" component={VoiceAIAssistant} />
      <Stack.Screen name="blockchain-integration" component={BlockchainIntegration} />
      <Stack.Screen name="bridge-screen" component={BridgeScreen} options={{ headerShown: true, title: 'Cross-Chain Bridge' }} />
      <Stack.Screen name="market-commentary" component={MarketCommentaryScreen} />
      <Stack.Screen name="ai-trading-coach" component={AITradingCoachScreen} />
      <Stack.Screen name="daily-voice-digest" component={DailyVoiceDigestScreen} />
      <Stack.Screen name="daily-brief" component={require('../features/learning/screens/DailyBriefScreen').default} options={{ headerShown: false }} />
      <Stack.Screen name="streak-progress" component={require('../features/learning/screens/StreakProgressScreen').default} options={{ headerShown: false }} />
      <Stack.Screen name="lesson-library" component={require('../features/learning/screens/LessonLibraryScreen').default} options={{ headerShown: false }} />
      <Stack.Screen name="notification-center" component={NotificationCenterScreen} />
      <Stack.Screen name="wealth-circles" component={WealthCirclesScreen} />
      <Stack.Screen name="circle-detail" component={SimpleCircleDetailScreen} />
      <Stack.Screen name="fireside" component={FiresideRoomsScreen} />
      <Stack.Screen name="fireside-room" component={FiresideRoomScreen} />
      <Stack.Screen name="chart-test" component={ChartTestScreen} options={{ headerShown: false }} />
      <Stack.Screen name="camera-test" component={CameraTestScreen} options={{ headerShown: true, title: 'Camera Test' }} />
      <Stack.Screen name="ar-preview" component={ARNextMovePreview} />
      <Stack.Screen name="peer-progress" component={PeerProgressScreen} />
      <Stack.Screen name="trade-challenges" component={TradeChallengesScreen} />
      <Stack.Screen name="personalization-dashboard" component={PersonalizationDashboardScreen} />
      <Stack.Screen name="behavioral-analytics" component={BehavioralAnalyticsScreen} />
      <Stack.Screen name="dynamic-content" component={DynamicContentScreen} />
      <Stack.Screen 
        name="security-fortress" 
        component={SecurityFortressWrapper}
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="viral-growth" 
        component={ViralGrowthWrapper}
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="onboarding" 
        component={OnboardingScreenWrapper}
        options={{ headerShown: false }}
      />
      {/* Convenience: allow Home to open these without switching tabs */}
      <Stack.Screen name="ai-options" component={AIOptionsScreen} />
      <Stack.Screen name="ai-scans" component={AIScansScreen} />
      <Stack.Screen name="scan-playbook" component={ScanPlaybookScreen} options={{ headerShown: true, title: 'Scan Playbook' }} />
      <Stack.Screen name="paper-trading" component={PaperTradingScreen} options={{ headerShown: true, title: 'Paper Trading' }} />
      <Stack.Screen name="PaperTrading" component={PaperTradingScreen} options={{ headerShown: true, title: 'Paper Trading' }} />
      {/* Allow navigation to Options Copilot from HomeStack */}
      <Stack.Screen name="options-copilot" component={OptionsCopilotScreen} options={{ headerShown: true, title: 'Options Copilot' }} />
    </Stack.Navigator>
  );
}

function SignalsScreenWrapper(props: any) {
  return (
    <SignalsScreen
      navigateTo={(screen) => {
        try {
          props.navigation.navigate(screen as never);
        } catch (error) {
          logger.error('Navigation error:', error);
        }
      }}
    />
  );
}

function BacktestingScreenWrapper(props: any) {
  return (
    <BacktestingScreen
      navigateTo={(screen) => {
        try {
          props.navigation.navigate(screen as never);
        } catch (error) {
          logger.error('Navigation error:', error);
        }
      }}
    />
  );
}

function InvestStack() {
  return (
    <Stack.Navigator 
      screenOptions={{ headerBackTitleVisible: false }}
      initialRouteName="InvestMain"
    >
      <Stack.Screen name="InvestMain" component={InvestHubScreen} options={{ headerShown: false }} />

      {/* Primary flows */}
      <Stack.Screen name="Stocks" component={StockScreenWrapper} options={{ headerShown: true, title: 'Stocks' }} />
      <Stack.Screen name="StockDetail" component={StockDetailScreen} options={{ headerShown: true, title: 'Stock Detail' }} />
      <Stack.Screen name="Crypto" component={CryptoScreen} options={{ headerShown: true, title: 'Crypto' }} />
      <Stack.Screen name="AIPortfolio" component={AIPortfolioScreen} options={{ headerShown: true, title: 'AI Portfolio' }} />
      <Stack.Screen name="Portfolio" component={PortfolioScreen} options={{ headerShown: true, title: 'Portfolio' }} />
      <Stack.Screen name="PortfolioManagement" component={PortfolioManagementScreen} options={{ headerShown: true, title: 'Manage Holdings' }} />
      <Stack.Screen name="Screeners" component={AIScansScreen} options={{ headerShown: true, title: 'Screeners' }} />
      <Stack.Screen name="scan-playbook" component={ScanPlaybookScreen} options={{ headerShown: true, title: 'Scan Playbook' }} />
      <Stack.Screen name="AIOptions" component={AIOptionsScreen} options={{ headerShown: true, title: 'Options' }} />
      <Stack.Screen name="OptionsCopilot" component={OptionsCopilotScreen} options={{ headerShown: true, title: 'Advanced' }} />
      <Stack.Screen name="options-copilot" component={OptionsCopilotScreen} options={{ headerShown: true, title: 'Advanced' }} />
      <Stack.Screen name="Tomorrow" component={TomorrowScreen} options={{ headerShown: true, title: 'Tomorrow' }} />
      <Stack.Screen name="DayTrading" component={TradingScreenWrapper} options={{ headerShown: false }} />
      <Stack.Screen name="Forex" component={ForexScreen} options={{ headerShown: true, title: 'Forex' }} />
      <Stack.Screen name="PaperTrading" component={PaperTradingScreen} options={{ headerShown: true, title: 'Paper Trading' }} />
      <Stack.Screen name="paper-trading" component={PaperTradingScreen} options={{ headerShown: true, title: 'Paper Trading' }} />
      <Stack.Screen name="ResearchReport" component={ResearchReportScreen} options={{ headerShown: true, title: 'Research Report' }} />
      <Stack.Screen name="research-report" component={ResearchReportScreen} options={{ headerShown: true, title: 'Research Report' }} />
      <Stack.Screen name="SignalUpdates" component={SignalUpdatesScreen} options={{ headerShown: true, title: 'Signal Updates' }} />
      <Stack.Screen name="signal-updates" component={SignalUpdatesScreen} options={{ headerShown: true, title: 'Signal Updates' }} />
      <Stack.Screen name="MLSystem" component={MLSystemScreen} options={{ headerShown: true, title: 'ML System' }} />
      <Stack.Screen name="RiskManagement" component={RiskManagementScreen} options={{ headerShown: true, title: 'Risk Management' }} />
      <Stack.Screen name="ar-preview" component={ARNextMovePreview} options={{ headerShown: false }} />
      <Stack.Screen name="blockchain-integration" component={BlockchainIntegration} options={{ headerShown: false }} />
      <Stack.Screen name="bridge-screen" component={BridgeScreen} options={{ headerShown: true, title: 'Cross-Chain Bridge' }} />
      <Stack.Screen name="wellness-dashboard" component={WellnessDashboardScreen} options={{ headerShown: false }} />
      
      {/* Swing Trading screens */}
      <Stack.Screen name="swing-trading-test" component={SwingTradingDashboard} options={{ headerShown: true, title: 'Swing Trading' }} />
      <Stack.Screen name="swing-signals" component={SignalsScreenWrapper} options={{ headerShown: true, title: 'Swing Signals' }} />
      <Stack.Screen name="swing-risk-coach" component={RiskCoachScreen} options={{ headerShown: true, title: 'Guardrails' }} />
      <Stack.Screen name="swing-backtesting" component={BacktestingScreenWrapper} options={{ headerShown: true, title: 'Backtesting' }} />
      <Stack.Screen name="swing-leaderboard" component={LeaderboardScreen} options={{ headerShown: true, title: 'Leaderboard' }} />
      <Stack.Screen
        name="InvestAdvanced"
        component={InvestAdvancedSheet}
        options={{ presentation: 'transparentModal', animation: 'fade', headerShown: false }}
      />

      {/* Legacy aliases to avoid breaking existing navigate calls */}
      <Stack.Screen name="stock" component={StockScreenWrapper} options={{ headerShown: true, title: 'Stocks' }} />
      <Stack.Screen name="crypto" component={CryptoScreen} options={{ headerShown: true, title: 'Crypto' }} />
      <Stack.Screen name="ai-recommendations" component={AIPortfolioScreen} options={{ headerShown: true, title: 'AI Portfolio' }} />
      <Stack.Screen name="portfolio" component={PortfolioScreen} options={{ headerShown: true, title: 'Portfolio' }} />
      <Stack.Screen name="portfolio-management" component={PortfolioManagementScreen} options={{ headerShown: true, title: 'Manage Holdings' }} />
      <Stack.Screen name="premium-analytics" component={PremiumAnalyticsScreen} options={{ headerShown: true, title: 'Premium Analytics' }} />
      <Stack.Screen name="subscription" component={PortfolioScreen} options={{ headerShown: true, title: 'Subscription' }} />
      <Stack.Screen name="portfolio-analytics" component={PortfolioScreen} options={{ headerShown: true, title: 'Analytics' }} />
      <Stack.Screen name="stock-screening" component={AIScansScreen} options={{ headerShown: true, title: 'Screeners' }} />
      <Stack.Screen name="trading" component={TradingScreenWrapper} options={{ headerShown: false }} />
      <Stack.Screen name="day-trading" component={DayTradingScreen} options={{ headerShown: false }} />
      <Stack.Screen name="trading-coach" component={TradingCoachScreen} options={{ headerShown: true, title: 'Trading Coach' }} />
      <Stack.Screen name="ai-trading-coach" component={AITradingCoachScreen} options={{ headerShown: true, title: 'AI Trading Coach' }} />
      {/* Legacy aliases for header buttons */}
      <Stack.Screen name="ml-system" component={MLSystemScreen} options={{ headerShown: true, title: 'ML System' }} />
      <Stack.Screen name="risk-management" component={RiskManagementScreen} options={{ headerShown: true, title: 'Risk Management' }} />
    </Stack.Navigator>
  );
}

function LearnStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="LearnMain" component={TutorScreen} />
      {/* Legacy alias */}
      <Stack.Screen name="tutor" component={TutorScreen} />
      {/* Explicit learning routes for deep links from Home */}
      <Stack.Screen name="tutor-ask-explain" component={TutorAskExplainScreen} />
      <Stack.Screen name="tutor-quiz" component={TutorQuizScreen} />
      <Stack.Screen name="tutor-module" component={TutorModuleScreen} />
      <Stack.Screen name="lesson-library" component={require('../features/learning/screens/LessonLibraryScreen').default} options={{ headerShown: false }} />
    </Stack.Navigator>
  );
}

function CommunityStack() {
  // Use the SocialTrading screen with video news built-in; default to News tab
  const CommunityMain = () => (
    <SocialTrading userId={'me'} initialTab={'news'} />
  );
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CommunityMain" component={CommunityMain} />
      {/* Legacy alias to keep deep links working */}
      <Stack.Screen name="social" component={CommunityMain} />
      {/* Community routes */}
      <Stack.Screen name="wealth-circles" component={WealthCirclesScreen} />
      <Stack.Screen name="circle-detail" component={SimpleCircleDetailScreen} />
      <Stack.Screen name="fireside" component={FiresideRoomsScreen} />
      <Stack.Screen name="fireside-room" component={FiresideRoomScreen} />
      <Stack.Screen name="chart-test" component={ChartTestScreen} options={{ headerShown: false }} />
      {/* Social features */}
      <Stack.Screen name="portfolio-leaderboard" component={PortfolioLeaderboardScreen} options={{ headerShown: true, title: 'Leaderboard' }} />
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  const navRef = React.useRef<any>(null);
  const [currentTabIndex, setCurrentTabIndex] = React.useState<number>(0);
  const tabOrder = React.useMemo(() => ['Home', 'Invest', 'Learn', 'Community'], []);
  const insets = useSafeAreaInsets();

  const handleStateChange = React.useCallback(() => {
    const rootState = navRef.current?.getRootState?.();
    if (!rootState || !Array.isArray(rootState.routes)) return;
    const idx = typeof rootState.index === 'number' ? rootState.index : 0;
    setCurrentTabIndex(idx);
  }, []);

  // Removed swipe gesture handler to fix tab navigation
  // Tabs should work with standard React Navigation tab bar

  // Set navigator reference when NavigationContainer is ready
  const setNavigatorRef = React.useCallback((ref: any) => {
    navRef.current = ref;
    if (ref) {
      // Use setTimeout to ensure ref is fully initialized
      setTimeout(() => {
        setNavigator(ref);
        console.log('✅ NavigationService: Navigator set via ref callback');
      }, 0);
    }
  }, []);

  React.useEffect(() => {
    // Try to set navigator immediately
    if (navRef.current) {
      setNavigator(navRef.current);
      console.log('✅ NavigationService: Navigator set in useEffect');
    }
    // Also set it after a short delay to ensure it's ready
    const timeout = setTimeout(() => {
      if (navRef.current) {
        setNavigator(navRef.current);
        console.log('✅ NavigationService: Navigator set in useEffect (delayed)');
      }
    }, 50);
    return () => clearTimeout(timeout);
  }, []);

  return (
    <NavigationContainer 
      ref={setNavigatorRef}
      onStateChange={handleStateChange}
      onReady={() => {
        // onReady is called when NavigationContainer is fully ready
        if (navRef.current) {
          setNavigator(navRef.current);
          console.log('✅ NavigationService: Navigator set on ready (NavigationContainer ready)');
          // Ensure navigator is definitely set with a small delay
          setTimeout(() => {
            if (navRef.current) {
              setNavigator(navRef.current);
              console.log('✅ NavigationService: Navigator re-set after onReady delay');
            }
          }, 50);
        }
      }}
    >
      <GestureNavigation
        onNavigate={(screen) => {
          const { globalNavigate } = require('../navigation/NavigationService');
          if (screen === 'InvestMain' || screen === 'invest') {
            globalNavigate('Invest');
          } else if (screen === 'home') {
            globalNavigate('Home');
          } else {
            globalNavigate(screen);
          }
        }}
        currentScreen={tabOrder[currentTabIndex] || 'Home'}
        onBack={() => {
          // Swipe left = go back (previous tab)
          if (currentTabIndex > 0) {
            const prevTab = tabOrder[currentTabIndex - 1];
            const { globalNavigate } = require('../navigation/NavigationService');
            globalNavigate(prevTab);
          }
        }}
        onForward={() => {
          // Swipe right = go forward (next tab)
          if (currentTabIndex < tabOrder.length - 1) {
            const nextTab = tabOrder[currentTabIndex + 1];
            const { globalNavigate } = require('../navigation/NavigationService');
            globalNavigate(nextTab);
          }
        }}
      >
        <View style={{ flex: 1 }}>
          <Tab.Navigator
          screenOptions={({ route }) => ({
            headerShown: false,
            tabBarLabelStyle: { fontSize: 12, fontWeight: '700', marginBottom: 4 },
            tabBarIcon: ({ color, size }) => {
              const iconMap: Record<string, keyof typeof Feather.glyphMap> = {
                Home: 'home',
                Invest: 'bar-chart-2',
                Learn: 'book-open',
                Community: 'users',
              };
              const name = iconMap[route.name] ?? 'grid';
              return <Feather name={name} size={size} color={color} />;
            },
            tabBarActiveTintColor: '#34C759', // mint
            tabBarInactiveTintColor: '#8E8E93',
            tabBarStyle: { 
              borderTopWidth: 0, 
              elevation: 0,
              paddingBottom: Platform.OS === 'ios' ? Math.max(insets.bottom, 8) : 8,
              paddingTop: 8,
              height: Platform.OS === 'ios' ? 60 + Math.max(insets.bottom, 8) : 60,
              backgroundColor: 'transparent',
            },
            tabBarBackground: () => (
              <LinearGradient
                colors={["#FFFFFF", "#FDF7E3", "#F5FFF8"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={{ flex: 1 }}
              />
            ),
            lazy: true,
          })}
        >
          <Tab.Screen 
            name="Home" 
            component={HomeStack}
            options={{
              tabBarTestID: TID.tabs.voiceAI, // Voice AI features are in Home tab
              tabBarAccessibilityLabel: TID.tabs.voiceAI,
              tabBarButton: (props) => (
                <TouchableOpacity
                  {...props}
                  testID={TID.tabs.voiceAI}
                  accessibilityLabel={TID.tabs.voiceAI}
                  accessibilityRole="button"
                />
              ),
            }}
            listeners={{
              tabPress: (e) => {
                logger.log('Home tab pressed');
              },
            }}
          />
          <Tab.Screen 
            name="Invest" 
            component={InvestStack}
            options={{
              tabBarTestID: TID.tabs.memeQuest, // MemeQuest features are in Invest tab
              tabBarAccessibilityLabel: TID.tabs.memeQuest,
              tabBarButton: (props) => (
                <TouchableOpacity
                  {...props}
                  testID={TID.tabs.memeQuest}
                  accessibilityLabel={TID.tabs.memeQuest}
                  accessibilityRole="button"
                />
              ),
            }}
            listeners={({ navigation }) => ({
              tabPress: (e) => {
                logger.log('Invest tab pressed');
                // Prevent default navigation and ensure we go to InvestMain
                const state = navigation.getState();
                const investRoute = state?.routes?.find((r: any) => r.name === 'Invest');
                if (investRoute?.state) {
                  const currentRoute = investRoute.state.routes?.[investRoute.state.index || 0];
                  logger.log('Current Invest stack route:', currentRoute?.name);
                  if (currentRoute?.name !== 'InvestMain') {
                    e.preventDefault();
                    // Navigate to InvestMain
                    logger.log('Navigating to InvestMain from:', currentRoute?.name);
                    navigation.navigate('Invest', { 
                      screen: 'InvestMain',
                      params: undefined 
                    });
                  } else {
                    logger.log('Already on InvestMain, allowing default navigation');
                  }
                } else {
                  // If no state, navigate to InvestMain
                  e.preventDefault();
                  logger.log('No Invest stack state, navigating to InvestMain');
                  navigation.navigate('Invest', { 
                    screen: 'InvestMain',
                    params: undefined 
                  });
                }
              },
            })}
          />
          <Tab.Screen 
            name="Learn"
            component={LearnStack}
            options={{
              tabBarTestID: TID.tabs.learning,
              tabBarAccessibilityLabel: TID.tabs.learning,
              tabBarButton: (props) => (
                <TouchableOpacity
                  {...props}
                  testID={TID.tabs.learning}
                  accessibilityLabel={TID.tabs.learning}
                  accessibilityRole="button"
                />
              ),
            }}
            listeners={({ navigation }) => ({
              tabPress: (e) => {
                logger.log('Learn tab pressed');
                // Prevent default navigation and ensure we go to LearnMain
                const state = navigation.getState();
                const learnRoute = state?.routes?.find((r: any) => r.name === 'Learn');
                if (learnRoute?.state) {
                  const currentRoute = learnRoute.state.routes?.[learnRoute.state.index || 0];
                  logger.log('Current Learn stack route:', currentRoute?.name);
                  if (currentRoute?.name !== 'LearnMain') {
                    e.preventDefault();
                    // Navigate to LearnMain
                    logger.log('Navigating to LearnMain from:', currentRoute?.name);
                    navigation.navigate('Learn', { 
                      screen: 'LearnMain',
                      params: undefined 
                    });
                  } else {
                    logger.log('Already on LearnMain, allowing default navigation');
                  }
                } else {
                  // If no state, navigate to LearnMain
                  e.preventDefault();
                  logger.log('No Learn stack state, navigating to LearnMain');
                  navigation.navigate('Learn', { 
                    screen: 'LearnMain',
                    params: undefined 
                  });
                }
              },
            })}
          />
          <Tab.Screen 
            name="Community" 
            component={CommunityStack}
            options={{
              tabBarTestID: TID.tabs.community,
              tabBarAccessibilityLabel: TID.tabs.community,
              tabBarButton: (props) => (
                <TouchableOpacity
                  {...props}
                  testID={TID.tabs.community}
                  accessibilityLabel={TID.tabs.community}
                  accessibilityRole="button"
                />
              ),
            }}
            listeners={{
              tabPress: (e) => {
                logger.log('Community tab pressed');
              },
            }}
          />
        </Tab.Navigator>
      </View>
      </GestureNavigation>
    </NavigationContainer>
  );
}


