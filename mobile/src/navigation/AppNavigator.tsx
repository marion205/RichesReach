import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Feather from '@expo/vector-icons/Feather';
import { View, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import ProfileScreen from '../features/user/screens/ProfileScreen';
import BankAccountScreen from '../features/user/screens/BankAccountScreen';
import { setNavigator } from './NavigationService';

// Existing screens (paths reflect current project structure)
import HomeScreen from '../navigation/HomeScreen';
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
import MLSystemScreen from '../features/ml/screens/MLSystemScreen';
import RiskManagementScreen from '../features/risk/screens/RiskManagementScreen';
import PremiumAnalyticsScreen from './PremiumAnalyticsScreen';
// V2 single-screen utilities used from Home
import OracleInsights from '../components/OracleInsights';
import VoiceAIAssistant from '../components/VoiceAIAssistant';
import BlockchainIntegration from '../components/BlockchainIntegration';
import MarketCommentaryScreen from '../features/news/screens/MarketCommentaryScreen';
import AITradingCoachScreen from '../features/coach/screens/AITradingCoachScreen';
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
          console.log('Navigation error:', error);
        }
      }}
    />
  );
}

function SecurityFortressWrapper(props: any) {
  return (
    <SecurityFortress
      onBiometricSetup={() => console.log('Biometric setup requested')}
      onSecurityEventPress={(event) => console.log('Security event:', event)}
    />
  );
}

function ViralGrowthWrapper(props: any) {
  return (
    <ViralGrowthSystem
      onRewardClaimed={(reward) => console.log('Reward claimed:', reward)}
      onChallengeJoined={(challenge) => console.log('Challenge joined:', challenge)}
    />
  );
}

function OnboardingScreenWrapper(props: any) {
  return (
    <OnboardingScreen
      onComplete={(profile) => {
        console.log('Onboarding completed:', profile);
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
      <Stack.Screen name="notification-center" component={NotificationCenterScreen} />
      <Stack.Screen name="wealth-circles" component={WealthCirclesScreen} />
      <Stack.Screen name="circle-detail" component={SimpleCircleDetailScreen} />
      <Stack.Screen name="fireside" component={FiresideRoomsScreen} />
      <Stack.Screen name="fireside-room" component={FiresideRoomScreen} />
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
    </Stack.Navigator>
  );
}

function InvestStack() {
  return (
    <Stack.Navigator screenOptions={{ headerBackTitleVisible: false }}>
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
      <Stack.Screen name="MLSystem" component={MLSystemScreen} options={{ headerShown: true, title: 'ML System' }} />
      <Stack.Screen name="RiskManagement" component={RiskManagementScreen} options={{ headerShown: true, title: 'Risk Management' }} />
      <Stack.Screen name="ar-preview" component={ARNextMovePreview} options={{ headerShown: false }} />
      <Stack.Screen name="blockchain-integration" component={BlockchainIntegration} options={{ headerShown: false }} />
      <Stack.Screen name="bridge-screen" component={BridgeScreen} options={{ headerShown: true, title: 'Cross-Chain Bridge' }} />
      <Stack.Screen name="wellness-dashboard" component={WellnessDashboardScreen} options={{ headerShown: false }} />
      
      {/* Swing Trading screens */}
      <Stack.Screen name="swing-trading-test" component={SwingTradingDashboard} options={{ headerShown: true, title: 'Swing Trading' }} />
      <Stack.Screen name="swing-signals" component={SignalsScreen} options={{ headerShown: true, title: 'Swing Signals' }} />
      <Stack.Screen name="swing-risk-coach" component={RiskCoachScreen} options={{ headerShown: true, title: 'Guardrails' }} />
      <Stack.Screen name="swing-backtesting" component={BacktestingScreen} options={{ headerShown: true, title: 'Backtesting' }} />
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
      <Stack.Screen name="trading-coach" component={AITradingCoachScreen} options={{ headerShown: true, title: 'Trading Coach' }} />
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

  React.useEffect(() => {
    if (navRef.current) setNavigator(navRef.current);
  }, []);

  return (
    <NavigationContainer ref={navRef} onStateChange={handleStateChange}>
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
            listeners={{
              tabPress: (e) => {
                console.log('Home tab pressed');
              },
            }}
          />
          <Tab.Screen 
            name="Invest" 
            component={InvestStack}
            listeners={{
              tabPress: (e) => {
                console.log('Invest tab pressed');
              },
            }}
          />
          <Tab.Screen 
            name="Learn" 
            component={LearnStack}
            listeners={{
              tabPress: (e) => {
                console.log('Learn tab pressed');
              },
            }}
          />
          <Tab.Screen 
            name="Community" 
            component={CommunityStack}
            listeners={{
              tabPress: (e) => {
                console.log('Community tab pressed');
              },
            }}
          />
        </Tab.Navigator>
      </View>
    </NavigationContainer>
  );
}


