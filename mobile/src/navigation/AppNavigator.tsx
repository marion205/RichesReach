import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Feather from '@expo/vector-icons/Feather';
import { View, Platform, TouchableOpacity, Alert } from 'react-native';
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
import GoalPlanScreen from '../features/portfolio/screens/GoalPlanScreen';
import PortfolioManagementScreen from '../features/portfolio/screens/PortfolioManagementScreen';
import SocialTrading from '../components/SocialTrading';
import FiresideRoomsScreen from '../features/community/screens/FiresideRoomsScreen';
import FiresideRoomScreen from '../features/community/screens/FiresideRoomScreen';
import AIScansScreen from '../features/aiScans/screens/AIScansScreen';
import ScanPlaybookScreen from '../features/aiScans/screens/ScanPlaybookScreen';
import AIOptionsScreen from '../features/options/screens/AIOptionsScreen';
import OptionsCopilotScreen from '../features/options/screens/OptionsCopilotScreen';
import ActiveRepairWorkflow from '../screens/options/ActiveRepairWorkflow';
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
import { getOpportunityDiscoveryService } from '../features/invest/services/opportunityDiscoveryService';
import type { FinancialGraph } from '../features/invest/types/opportunityTypes';

// Wrapper that loads the Financial Intelligence Graph before rendering OracleInsights
function OracleInsightsScreen() {
  const [financialGraph, setFinancialGraph] = React.useState<FinancialGraph | null>(null);
  React.useEffect(() => {
    getOpportunityDiscoveryService()
      .getFinancialGraph()
      .then(setFinancialGraph)
      .catch(() => {});
  }, []);
  return <OracleInsights financialGraph={financialGraph ?? undefined} />;
}
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
import NFTDetailScreen from '../features/blockchain/screens/NFTDetailScreen';
import NFTJourneyScreen from '../features/blockchain/screens/NFTJourneyScreen';
import SecurityFortress from '../components/SecurityFortress';
import ViralGrowthSystem from '../components/ViralGrowthSystem';
import OnboardingScreen from '../features/auth/screens/OnboardingScreen';
import SubscriptionScreen from '../features/user/screens/SubscriptionScreen';
import CameraTestScreen from '../components/CameraTestScreen';

// New hub screen
import InvestHubScreen from '../features/invest/InvestHubScreen';
import DeFiFortressScreen from '../features/defi/screens/DeFiFortressScreen';
import DeFiPositionsScreen from '../features/defi/screens/DeFiPositionsScreen';
import DeFiAutopilotScreen from '../features/defi/screens/DeFiAutopilotScreen';
import ImpermanentLossCalculatorScreen from '../features/defi/screens/ImpermanentLossCalculatorScreen';
import VaultPortfolioScreen from '../features/defi/screens/VaultPortfolioScreen';
import InvestAdvancedSheet from '../features/invest/InvestAdvancedSheet';
import PrivateMarketsScreen from '../features/invest/screens/PrivateMarketsScreen';
import PrivateMarketsDealDetailScreen from '../features/invest/screens/PrivateMarketsDealDetailScreen';
import PrivateMarketsCompareScreen from '../features/invest/screens/PrivateMarketsCompareScreen';
import PrivateMarketsLearnScreen from '../features/invest/screens/PrivateMarketsLearnScreen';
import OpportunityDiscoveryScreen from '../features/invest/screens/OpportunityDiscoveryScreen';

// Financial GPS screens
import FinancialGPSScreen from '../features/wealth/screens/FinancialGPSScreen';
import InvestorQuizScreen from '../features/wealth/screens/InvestorQuizScreen';
import AdaptiveOnboardingScreen from '../features/onboarding/screens/AdaptiveOnboardingScreen';
import InvestorProfileScreen from '../features/wealth/screens/InvestorProfileScreen';
import LeakRedirectScreen from '../features/wealth/screens/LeakRedirectScreen';
import WeeklyDigestScreen from '../features/wealth/screens/WeeklyDigestScreen';
import MillionairePathScreen from '../features/wealth/screens/MillionairePathScreen';
import NetWorthScreen from '../features/wealth/screens/NetWorthScreen';
import WealthArrivalScreen from '../features/wealth/screens/WealthArrivalScreen';
import LeakDetectorScreen from '../features/wealth/screens/LeakDetectorScreen';
import FinancialHealthScreen from '../features/wealth/screens/FinancialHealthScreen';
import LifeDecisionScreen from '../features/wealth/screens/LifeDecisionScreen';
import IncomeIntelligenceScreen from '../features/wealth/screens/IncomeIntelligenceScreen';
import ReallocateScreen from '../features/wealth/screens/ReallocateScreen';
import AIPortfolioBuilderScreen from '../features/wealth/screens/AIPortfolioBuilderScreen';

// Swing Trading screens
import SwingTradingDashboard from '../features/swingTrading/screens/SwingTradingDashboard';
import SignalsScreen from '../features/swingTrading/screens/SignalsScreen';
import RiskCoachScreen from '../features/swingTrading/screens/RiskCoachScreen';
import BacktestingScreen from '../features/swingTrading/screens/BacktestingScreen';
import LeaderboardScreen from '../features/swingTrading/screens/LeaderboardScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator<any>();
const TabNavigator = Tab.Navigator as any;

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
  // SecurityFortress now handles biometric setup internally
  return (
    <SecurityFortress
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

function GoalPlanScreenWrapper(props: any) {
  return (
    <GoalPlanScreen
      navigateTo={(screen, params) => {
        try {
          // "Start this plan" goes to Portfolio, which lives in the Invest tab
          if (screen === 'portfolio') {
            const root = props.navigation.getParent?.();
            if (root) {
              root.navigate('Invest' as never, { screen: 'portfolio', params } as never);
            } else {
              props.navigation.navigate('Invest' as never, { screen: 'portfolio', params } as never);
            }
            return;
          }
          props.navigation.navigate(screen as never, params as never);
        } catch (e) {
          logger.error('GoalPlanScreen navigate error:', e);
        }
      }}
    />
  );
}

function HomeScreenWrapper(props: any) {
  return (
    <HomeScreen
      navigateTo={(screen, params) => {
        try {
          // RAHA screens use custom navigation system (not React Navigation)
          const customScreens = ['pro-labs', 'the-whisper', 'strategy-builder', 'strategy-dashboard', 
                                  'ml-training', 'strategy-blend', 'strategy-detail', 'auto-trading-settings',
                                  'notification-preferences', 'backtest-viewer'];
          
          if (customScreens.includes(screen)) {
            // Use the global custom navigation
            if (typeof window !== 'undefined') {
              if ((window as any).__navigateToGlobal) {
                (window as any).__navigateToGlobal(screen, params);
              } else if ((window as any).__setCurrentScreen) {
                (window as any).__setCurrentScreen(screen);
              }
            }
          } else {
            // Use React Navigation for standard screens
            props.navigation.navigate(screen as never, params as never);
          }
        } catch (e) {
          logger.error('HomeScreen navigate error:', e);
          // Fallback: try custom navigation
          if (typeof window !== 'undefined' && (window as any).__setCurrentScreen) {
            (window as any).__setCurrentScreen(screen);
          }
        }
      }}
    />
  );
}

function HomeStack() {
  const StackNavigator = Stack.Navigator as any;
  return (
    <StackNavigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeMain" component={HomeScreenWrapper} />
      {/* Legacy alias to preserve existing navigations */}
      <Stack.Screen name="home" component={HomeScreenWrapper} />
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
      <Stack.Screen name="premium-analytics" component={PremiumAnalyticsScreen} options={{ headerShown: true, title: 'Premium Analytics' }} />
      {/* V2 utility routes triggered from Home cards */}
      <Stack.Screen name="oracle-insights" component={OracleInsightsScreen} />
      {/* Financial GPS screens */}
      <Stack.Screen name="FinancialGPS" component={FinancialGPSScreen} options={{ headerShown: false }} />
      <Stack.Screen name="financial-gps" component={FinancialGPSScreen} options={{ headerShown: false }} />
      <Stack.Screen name="AdaptiveOnboarding" component={AdaptiveOnboardingScreen} options={{ headerShown: false }} />
      <Stack.Screen name="adaptive-onboarding" component={AdaptiveOnboardingScreen} options={{ headerShown: false }} />
      <Stack.Screen name="InvestorQuiz" component={InvestorQuizScreen} options={{ headerShown: false }} />
      <Stack.Screen name="investor-quiz" component={InvestorQuizScreen} options={{ headerShown: false }} />
      <Stack.Screen name="InvestorProfile" component={InvestorProfileScreen} options={{ headerShown: false }} />
      <Stack.Screen name="investor-profile" component={InvestorProfileScreen} options={{ headerShown: false }} />
      <Stack.Screen name="LeakRedirect" component={LeakRedirectScreen} options={{ headerShown: false }} />
      <Stack.Screen name="leak-redirect" component={LeakRedirectScreen} options={{ headerShown: false }} />
      <Stack.Screen name="WeeklyDigest" component={WeeklyDigestScreen} options={{ headerShown: false }} />
      <Stack.Screen name="weekly-digest" component={WeeklyDigestScreen} options={{ headerShown: false }} />
      <Stack.Screen name="MillionairePath" component={MillionairePathScreen} options={{ headerShown: false }} />
      <Stack.Screen name="millionaire-path" component={MillionairePathScreen} options={{ headerShown: false }} />
      <Stack.Screen name="NetWorth" component={NetWorthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="net-worth" component={NetWorthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="WealthArrival" component={WealthArrivalScreen} options={{ headerShown: false }} />
      <Stack.Screen name="wealth-arrival" component={WealthArrivalScreen} options={{ headerShown: false }} />
      <Stack.Screen name="LeakDetector" component={LeakDetectorScreen} options={{ headerShown: false }} />
      <Stack.Screen name="leak-detector" component={LeakDetectorScreen} options={{ headerShown: false }} />
      <Stack.Screen name="FinancialHealth" component={FinancialHealthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="financial-health" component={FinancialHealthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="LifeDecision" component={LifeDecisionScreen} options={{ headerShown: false }} />
      <Stack.Screen name="life-decision" component={LifeDecisionScreen} options={{ headerShown: false }} />
      <Stack.Screen name="IncomeIntelligence" component={IncomeIntelligenceScreen} options={{ headerShown: false }} />
      <Stack.Screen name="income-intelligence" component={IncomeIntelligenceScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Reallocate" component={ReallocateScreen} options={{ headerShown: false }} />
      <Stack.Screen name="reallocate" component={ReallocateScreen} options={{ headerShown: false }} />
      <Stack.Screen name="AIPortfolioBuilder" component={AIPortfolioBuilderScreen} options={{ headerShown: false }} />
      <Stack.Screen name="ai-portfolio-builder" component={AIPortfolioBuilderScreen} options={{ headerShown: false }} />
      <Stack.Screen name="voice-ai" component={VoiceAIAssistant} />
      <Stack.Screen name="blockchain-integration" component={BlockchainIntegration} />
      <Stack.Screen name="bridge-screen" component={BridgeScreen} options={{ headerShown: true, title: 'Cross-Chain Bridge' }} />
      <Stack.Screen name="nft-detail" component={NFTDetailScreen} options={{ headerShown: false }} />
      <Stack.Screen name="nft-journey" component={NFTJourneyScreen} options={{ headerShown: false }} />
      {/* Tutor screens reachable from NFT feature in HomeStack */}
      <Stack.Screen name="tutor-ask-explain" component={TutorAskExplainScreen} options={{ headerShown: true, title: 'Ask Tutor' }} />
      <Stack.Screen name="tutor-module" component={TutorModuleScreen} options={{ headerShown: true, title: 'Learn' }} />
      <Stack.Screen name="market-commentary" component={MarketCommentaryScreen} />
      <Stack.Screen name="ai-trading-coach" component={AITradingCoachScreen} />
      <Stack.Screen name="daily-voice-digest" component={DailyVoiceDigestScreen} />
      <Stack.Screen name="daily-brief" component={require('../features/learning/screens/DailyBriefScreen').default} options={{ headerShown: false }} />
      <Stack.Screen name="goal-plan" component={GoalPlanScreenWrapper} options={{ headerShown: true, title: 'Your $1M Plan' }} />
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
    </StackNavigator>
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
  const StackNavigator = Stack.Navigator as any;
  return (
    <StackNavigator 
      screenOptions={{ headerBackTitleVisible: false }}
      initialRouteName="InvestMain"
    >
      <Stack.Screen name="InvestMain" component={InvestHubScreen} options={{ headerShown: false }} />

      {/* Primary flows */}
      <Stack.Screen name="Stocks" component={StockScreenWrapper} options={{ headerShown: true, title: 'Stocks' }} />
      <Stack.Screen name="StockDetail" component={StockDetailScreen} options={{ headerShown: true, title: 'Stock Detail' }} />
      <Stack.Screen name="Crypto" component={CryptoScreen} options={{ headerShown: true, title: 'Crypto' }} />
      <Stack.Screen name="DeFiFortress" component={DeFiFortressScreen} options={{ headerShown: false }} />
      <Stack.Screen name="DeFiAutopilot" component={DeFiAutopilotScreen} options={{ headerShown: true, title: 'Auto-Pilot' }} />
      <Stack.Screen name="DeFiPositions" component={DeFiPositionsScreen} options={{ headerShown: false }} />
      <Stack.Screen name="ILCalculator" component={ImpermanentLossCalculatorScreen} options={{ headerShown: false }} />
      <Stack.Screen name="PoolAnalytics" component={require('../screens/PoolAnalyticsScreen').default} options={{ headerShown: true, title: 'Pool Analytics' }} />
      <Stack.Screen name="VaultPortfolio" component={VaultPortfolioScreen} options={{ headerShown: false }} />
      <Stack.Screen name="AIPortfolio" component={AIPortfolioScreen} options={{ headerShown: true, title: 'AI Portfolio' }} />
      <Stack.Screen name="Portfolio" component={PortfolioScreen} options={{ headerShown: true, title: 'Portfolio' }} />
      <Stack.Screen name="PortfolioManagement" component={PortfolioManagementScreen} options={{ headerShown: true, title: 'Manage Holdings' }} />
      <Stack.Screen name="Screeners" component={AIScansScreen} options={{ headerShown: true, title: 'Screeners' }} />
      <Stack.Screen name="scan-playbook" component={ScanPlaybookScreen} options={{ headerShown: true, title: 'Scan Playbook' }} />
      <Stack.Screen name="AIOptions" component={AIOptionsScreen} options={{ headerShown: true, title: 'Options' }} />
      <Stack.Screen name="ActiveRepairs" component={ActiveRepairWorkflow} options={{ headerShown: true, title: '🛡️ Active Repairs' }} />
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
      <Stack.Screen name="nft-detail" component={NFTDetailScreen} options={{ headerShown: false }} />
      <Stack.Screen name="nft-journey" component={NFTJourneyScreen} options={{ headerShown: false }} />
      {/* Tutor screens reachable from NFT feature in InvestStack */}
      <Stack.Screen name="tutor-ask-explain" component={TutorAskExplainScreen} options={{ headerShown: true, title: 'Ask Tutor' }} />
      <Stack.Screen name="tutor-module" component={TutorModuleScreen} options={{ headerShown: true, title: 'Learn' }} />
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
      <Stack.Screen name="PrivateMarkets" component={PrivateMarketsScreen} options={{ headerShown: true, title: 'Private Markets' }} />
      <Stack.Screen name="PrivateMarketsDealDetail" component={PrivateMarketsDealDetailScreen} options={{ headerShown: true, title: 'Deal Detail' }} />
      <Stack.Screen name="PrivateMarketsCompare" component={PrivateMarketsCompareScreen} options={{ headerShown: true, title: 'Compare Deals' }} />
      <Stack.Screen name="PrivateMarketsLearn" component={PrivateMarketsLearnScreen} options={{ headerShown: true, title: 'Learn' }} />
      <Stack.Screen name="OpportunityDiscovery" component={OpportunityDiscoveryScreen} options={{ headerShown: true, title: 'Discover' }} />
      <Stack.Screen name="OpportunityDetail" component={OpportunityDiscoveryScreen} options={{ headerShown: true, title: 'Opportunity Detail' }} />

      {/* Financial GPS screens (also accessible from Invest tab) */}
      <Stack.Screen name="FinancialGPS" component={FinancialGPSScreen} options={{ headerShown: false }} />
      <Stack.Screen name="financial-gps" component={FinancialGPSScreen} options={{ headerShown: false }} />
      <Stack.Screen name="AdaptiveOnboarding" component={AdaptiveOnboardingScreen} options={{ headerShown: false }} />
      <Stack.Screen name="adaptive-onboarding" component={AdaptiveOnboardingScreen} options={{ headerShown: false }} />
      <Stack.Screen name="InvestorQuiz" component={InvestorQuizScreen} options={{ headerShown: false }} />
      <Stack.Screen name="investor-quiz" component={InvestorQuizScreen} options={{ headerShown: false }} />
      <Stack.Screen name="InvestorProfile" component={InvestorProfileScreen} options={{ headerShown: false }} />
      <Stack.Screen name="investor-profile" component={InvestorProfileScreen} options={{ headerShown: false }} />
      <Stack.Screen name="LeakRedirect" component={LeakRedirectScreen} options={{ headerShown: false }} />
      <Stack.Screen name="leak-redirect" component={LeakRedirectScreen} options={{ headerShown: false }} />
      <Stack.Screen name="WeeklyDigest" component={WeeklyDigestScreen} options={{ headerShown: false }} />
      <Stack.Screen name="weekly-digest" component={WeeklyDigestScreen} options={{ headerShown: false }} />
      <Stack.Screen name="MillionairePath" component={MillionairePathScreen} options={{ headerShown: false }} />
      <Stack.Screen name="millionaire-path" component={MillionairePathScreen} options={{ headerShown: false }} />
      <Stack.Screen name="NetWorth" component={NetWorthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="net-worth" component={NetWorthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="WealthArrival" component={WealthArrivalScreen} options={{ headerShown: false }} />
      <Stack.Screen name="wealth-arrival" component={WealthArrivalScreen} options={{ headerShown: false }} />
      <Stack.Screen name="LeakDetector" component={LeakDetectorScreen} options={{ headerShown: false }} />
      <Stack.Screen name="leak-detector" component={LeakDetectorScreen} options={{ headerShown: false }} />
      <Stack.Screen name="FinancialHealth" component={FinancialHealthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="financial-health" component={FinancialHealthScreen} options={{ headerShown: false }} />
      <Stack.Screen name="LifeDecision" component={LifeDecisionScreen} options={{ headerShown: false }} />
      <Stack.Screen name="life-decision" component={LifeDecisionScreen} options={{ headerShown: false }} />
      <Stack.Screen name="IncomeIntelligence" component={IncomeIntelligenceScreen} options={{ headerShown: false }} />
      <Stack.Screen name="income-intelligence" component={IncomeIntelligenceScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Reallocate" component={ReallocateScreen} options={{ headerShown: false }} />
      <Stack.Screen name="reallocate" component={ReallocateScreen} options={{ headerShown: false }} />
      <Stack.Screen name="AIPortfolioBuilder" component={AIPortfolioBuilderScreen} options={{ headerShown: false }} />
      <Stack.Screen name="ai-portfolio-builder" component={AIPortfolioBuilderScreen} options={{ headerShown: false }} />

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
    </StackNavigator>
  );
}

function LearnStack() {
  const StackNavigator = Stack.Navigator as any;
  return (
    <StackNavigator screenOptions={{ headerShown: false }} initialRouteName="tutor">
      {/* Duolingo-style Learn (original) - default when opening Learn tab */}
      <Stack.Screen name="tutor" component={TutorScreen} />
      <Stack.Screen name="LearnMain" component={require('../features/learning/screens/LearningPathsScreen').default} />
      {/* Legacy alias */}
      <Stack.Screen name="learning-paths" component={require('../features/learning/screens/LearningPathsScreen').default} />
      {/* Explicit learning routes for deep links from Home */}
      <Stack.Screen name="tutor-ask-explain" component={TutorAskExplainScreen} />
      <Stack.Screen name="tutor-quiz" component={TutorQuizScreen} />
      <Stack.Screen name="tutor-module" component={TutorModuleScreen} />
      <Stack.Screen name="lesson-library" component={require('../features/learning/screens/LessonLibraryScreen').default} options={{ headerShown: false }} />
      <Stack.Screen name="lesson-detail" component={require('../features/learning/screens/LessonDetailScreen').default} options={{ headerShown: false }} />
    </StackNavigator>
  );
}

function CommunityStack() {
  // Use the SocialTrading screen with video news built-in; default to Feed tab
  const CommunityMain = () => (
    <SocialTrading userId={'me'} initialTab={'feed'} />
  );
  const StackNavigator = Stack.Navigator as any;
  return (
    <StackNavigator screenOptions={{ headerShown: false }}>
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
    </StackNavigator>
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
        logger.log('✅ NavigationService: Navigator set via ref callback');
      }, 0);
    }
  }, []);

  React.useEffect(() => {
    // Try to set navigator immediately
    if (navRef.current) {
      setNavigator(navRef.current);
      logger.log('✅ NavigationService: Navigator set in useEffect');
    }
    // Also set it after a short delay to ensure it's ready
    const timeout = setTimeout(() => {
      if (navRef.current) {
        setNavigator(navRef.current);
        logger.log('✅ NavigationService: Navigator set in useEffect (delayed)');
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
          logger.log('✅ NavigationService: Navigator set on ready (NavigationContainer ready)');
          // Ensure navigator is definitely set with a small delay
          setTimeout(() => {
            if (navRef.current) {
              setNavigator(navRef.current);
              logger.log('✅ NavigationService: Navigator re-set after onReady delay');
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
          <TabNavigator
            screenOptions={({ route }: any) => ({
            headerShown: false,
            tabBarLabelStyle: { fontSize: 12, fontWeight: '700', marginBottom: 4 },
            tabBarIcon: ({ color, size }: any) => {
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
              // tabBarTestID: TID.tabs.voiceAI, // Not available in this version
              tabBarAccessibilityLabel: TID.tabs.voiceAI,
              tabBarButton: (props: any) => (
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
              // tabBarTestID: TID.tabs.memeQuest, // Not available in this version
              tabBarAccessibilityLabel: TID.tabs.memeQuest,
              tabBarButton: (props: any) => (
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
                    (e as any).preventDefault();
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
                  (e as any).preventDefault();
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
              // tabBarTestID: TID.tabs.learning, // Not available in this version
              tabBarAccessibilityLabel: TID.tabs.learning,
              tabBarButton: (props: any) => (
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
                // Always go to the original Duolingo-style Learn screen (tutor), not Learning Paths or DeFi
                (e as any).preventDefault();
                navigation.navigate('Learn', {
                  screen: 'tutor',
                  params: undefined,
                });
              },
            })}
          />
          <Tab.Screen 
            name="Community" 
            component={CommunityStack}
            options={{
              // tabBarTestID: TID.tabs.community, // Not available in this version
              tabBarAccessibilityLabel: TID.tabs.community,
              tabBarButton: (props: any) => (
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
        </TabNavigator>
      </View>
      </GestureNavigation>
    </NavigationContainer>
  );
}


