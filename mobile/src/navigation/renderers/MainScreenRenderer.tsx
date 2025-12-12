/**
 * MainScreenRenderer
 * Handles rendering of main app screens (home, portfolio, trading, social, etc.)
 * This is the largest renderer as it handles most of the app's screens
 */

import React, { Suspense } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import logger from '../../utils/logger';
import type { ScreenName, NavigateParams, WindowNavigationGlobals } from '../types';
import type { UserProfile } from '../../features/auth/screens/OnboardingScreen';

// Lazy-loaded screens
const AIPortfolioScreen = React.lazy(
  () => import('../../features/portfolio/screens/AIPortfolioScreen')
);
const PortfolioManagementScreen = React.lazy(
  () => import('../../features/portfolio/screens/PortfolioManagementScreen')
);
const StockDetailScreen = React.lazy(
  () => import('../../features/stocks/screens/StockDetailScreen')
);
const AIOptionsScreen = React.lazy(() => import('../../features/options/screens/AIOptionsScreen'));
const OptionsCopilotScreen = React.lazy(
  () => import('../../features/options/screens/OptionsCopilotScreen')
);

// Main screen imports
import HomeScreen from '../../navigation/HomeScreen';
import ProfileScreen from '../../features/user/screens/ProfileScreen';
import AccountManagementScreen from '../../features/user/screens/AccountManagementScreen';
import StockScreen from '../../features/stocks/screens/StockScreen';
import CryptoScreen from '../../navigation/CryptoScreen';
import PortfolioScreen from '../../features/portfolio/screens/PortfolioScreen';
import PremiumAnalyticsScreen from '../../navigation/PremiumAnalyticsScreen';
import SubscriptionScreen from '../../features/user/screens/SubscriptionScreen';
import LearningPathsScreen from '../../features/learning/screens/LearningPathsScreen';
import OnboardingScreen from '../../features/auth/screens/OnboardingScreen';
import DiscoverUsersScreen from '../../features/social/screens/DiscoverUsersScreen';
import UserProfileScreen from '../../features/user/screens/UserProfileScreen';
import UserPortfoliosScreen from '../../features/portfolio/screens/UserPortfoliosScreen';
import SimpleCircleDetailScreen from '../../features/community/screens/SimpleCircleDetailScreen';
import UserActivityScreen from '../../features/social/screens/UserActivityScreen';
import MessageScreen from '../../features/social/screens/MessageScreen';
import TradingScreen from '../../features/stocks/screens/TradingScreen';
import DayTradingScreen from '../../features/trading/screens/DayTradingScreen';
import MLSystemScreen from '../../features/ml/screens/MLSystemScreen';
import RiskManagementScreen from '../../features/risk/screens/RiskManagementScreen';
import { SignalsScreen, RiskCoachScreen, SwingTradingDashboard } from '../../features/swingTrading';
import LeaderboardScreen from '../../features/swingTrading/screens/LeaderboardScreen';
import BacktestingScreen from '../../features/swingTrading/screens/BacktestingScreen';
import AIScansScreen from '../../features/aiScans/screens/AIScansScreen';
import ScanPlaybookScreen from '../../features/aiScans/screens/ScanPlaybookScreen';
import BudgetingScreen from '../../features/banking/screens/BudgetingScreen';
import SpendingAnalysisScreen from '../../features/banking/screens/SpendingAnalysisScreen';
import NotificationsScreen from '../../features/notifications/screens/NotificationsScreen';
import OptionsLearningScreen from '../../features/options/screens/OptionsLearningScreen';
import SBLOCLearningScreen from '../../features/learning/screens/SBLOCLearningScreen';
import NewsPreferencesScreen from '../../features/news/screens/NewsPreferencesScreen';
import PortfolioLearningScreen from '../../features/learning/screens/PortfolioLearningScreen';
import TaxOptimizationScreen from '../../screens/TaxOptimizationScreen';
import SmartLotsScreen from '../../screens/SmartLotsScreen';
import BorrowVsSellScreen from '../../screens/BorrowVsSellScreen';
import WashGuardScreen from '../../screens/WashGuardScreen';
import TutorScreen from '../../features/education/screens/TutorScreen';
import TutorAskExplainScreen from '../../features/learning/screens/TutorAskExplainScreen';
import TutorQuizScreen from '../../features/learning/screens/TutorQuizScreen';
import TutorModuleScreen from '../../features/learning/screens/TutorModuleScreen';
import MarketCommentaryScreen from '../../features/news/screens/MarketCommentaryScreen';
import DailyVoiceDigestScreen from '../../features/learning/screens/DailyVoiceDigestScreen';
import NotificationCenterScreen from '../../features/notifications/screens/NotificationCenterScreen';
import WealthCircles2 from '../../components/WealthCircles2';
import SocialTrading from '../../components/SocialTrading';
import SocialScreen from '../../features/social/screens/SocialScreen';
import ViralGrowthSystem from '../../components/ViralGrowthSystem';
import SecurityFortress from '../../components/SecurityFortress';
import ScalabilityEngine from '../../components/ScalabilityEngine';
import MarketingRocket from '../../components/MarketingRocket';
import OracleInsights from '../../components/OracleInsights';
import VoiceAIAssistant from '../../components/VoiceAIAssistant';
import BlockchainIntegration from '../../components/BlockchainIntegration';
import ConnectivityTestScreen from '../../components/ConnectivityTestScreen';
import ThemeSettingsScreen from '../../components/ThemeSettingsScreen';
import SentryTestButton from '../../components/SentryTestButton';
import PeerProgressScreen from '../../features/community/screens/PeerProgressScreen';
import TradeChallengesScreen from '../../features/community/screens/TradeChallengesScreen';
import PersonalizationDashboardScreen from '../../features/personalization/screens/PersonalizationDashboardScreen';
import BehavioralAnalyticsScreen from '../../features/personalization/screens/BehavioralAnalyticsScreen';
import DynamicContentScreen from '../../features/personalization/screens/DynamicContentScreen';
import TradingCoachScreen from '../../features/coach/screens/TradingCoachScreen';
import AITradingCoachScreen from '../../features/coach/screens/AITradingCoachScreen';

// Loading fallback
const ScreenLoader = () => (
  <View
    style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}
  >
    <Text>Loading...</Text>
  </View>
);

interface MainScreenRendererProps {
  currentScreen: ScreenName;
  effectiveScreen: ScreenName;
  currentScreenParams: NavigateParams;
  navigateTo: (screen: ScreenName, params?: NavigateParams) => void;
  setCurrentScreen: (screen: ScreenName) => void;
  handleOnboardingComplete: (profile: UserProfile) => Promise<void>;
  handleLogout: () => Promise<void>;
  userId?: string;
}

export function MainScreenRenderer({
  currentScreen,
  effectiveScreen,
  currentScreenParams,
  navigateTo,
  setCurrentScreen,
  handleOnboardingComplete,
  handleLogout,
  userId,
}: MainScreenRendererProps): React.ReactElement | null {
  const windowWithNav =
    typeof window !== 'undefined' ? (window as Window & WindowNavigationGlobals) : null;

  switch (effectiveScreen) {
    case 'home':
      logger.log('🔍 Rendering HomeScreen');
      return <HomeScreen navigateTo={navigateTo} />;

    case 'onboarding':
      return (
        <OnboardingScreen
          onComplete={(profile: UserProfile) => handleOnboardingComplete(profile)}
        />
      );

    case 'profile':
      return <ProfileScreen navigateTo={navigateTo} onLogout={handleLogout} />;

    case 'account-management':
      return <AccountManagementScreen navigateTo={navigateTo} />;

    case 'stock':
      return <StockScreen navigateTo={navigateTo} />;

    case 'StockDetail':
      logger.log('🔍 Rendering StockDetailScreen');
      const stockDetailParams = windowWithNav?.__stockDetailParams || {};
      logger.log('🔍 StockDetail params:', stockDetailParams);
      return (
        <Suspense fallback={<ScreenLoader />}>
          <StockDetailScreen
            navigation={{
              navigate: navigateTo,
              goBack: () => setCurrentScreen('stock'),
              setParams: (params: NavigateParams) => {
                // Handle params update if needed
              },
            }}
            route={{ params: stockDetailParams }}
          />
        </Suspense>
      );

    case 'crypto':
      return (
        <CryptoScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('home'),
          }}
        />
      );

    case 'ai-portfolio':
      return (
        <Suspense fallback={<ScreenLoader />}>
          <AIPortfolioScreen navigateTo={navigateTo} />
        </Suspense>
      );

    case 'portfolio':
      return <PortfolioScreen navigateTo={navigateTo} />;

    case 'portfolio-management':
      return (
        <Suspense fallback={<ScreenLoader />}>
          <PortfolioManagementScreen navigateTo={navigateTo} />
        </Suspense>
      );

    case 'premium-analytics':
    case 'portfolio-analytics':
      return <PremiumAnalyticsScreen navigateTo={navigateTo} />;

    case 'subscription':
      return <SubscriptionScreen navigateTo={navigateTo} />;

    case 'budgeting':
      return <BudgetingScreen />;

    case 'spending-analysis':
      return <SpendingAnalysisScreen />;

    case 'stock-screening':
      return <StockScreen navigateTo={navigateTo} />;

    case 'ai-recommendations':
      return (
        <Suspense fallback={<ScreenLoader />}>
          <AIPortfolioScreen navigateTo={navigateTo} />
        </Suspense>
      );

    case 'social':
      return <SocialTrading userId={userId || 'me'} />;

    case 'learning-paths':
      return <LearningPathsScreen />;

    case 'discover-users':
      return <DiscoverUsersScreen onNavigate={navigateTo} />;

    case 'user-profile':
      // Extract userId from currentScreen if it's in format 'user-profile-{userId}'
      const extractedUserId = currentScreen.startsWith('user-profile-')
        ? currentScreen.replace('user-profile-', '')
        : 'default-user';
      return <UserProfileScreen userId={extractedUserId} onNavigate={navigateTo} />;

    case 'user-portfolios':
      const portfolioUserId = currentScreen.startsWith('user-portfolios-')
        ? currentScreen.replace('user-portfolios-', '')
        : 'default-user';
      return <UserPortfoliosScreen userId={portfolioUserId} onNavigate={navigateTo} />;

    case 'user-activity':
      const activityUserId = currentScreen.startsWith('user-activity-')
        ? currentScreen.replace('user-activity-', '')
        : 'default-user';
      return <UserActivityScreen userId={activityUserId} onNavigate={navigateTo} />;

    case 'message-user':
      const messageUserId = currentScreen.startsWith('message-user-')
        ? currentScreen.replace('message-user-', '')
        : 'default-user';
      return <MessageScreen userId={messageUserId} onNavigate={navigateTo} />;

    case 'social-feed':
      return <SocialScreen onNavigate={navigateTo} />;

    case 'ai-options':
      return (
        <Suspense fallback={<ScreenLoader />}>
          <AIOptionsScreen
            navigation={{
              navigate: navigateTo,
              goBack: () => setCurrentScreen('home'),
            }}
          />
        </Suspense>
      );

    case 'options-copilot':
      return (
        <Suspense fallback={<ScreenLoader />}>
          <OptionsCopilotScreen
            navigation={{
              navigate: navigateTo,
              goBack: () => setCurrentScreen('ai-options'),
            }}
          />
        </Suspense>
      );

    case 'tutor':
      return (
        <TutorScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('home'),
          }}
        />
      );

    case 'scan-playbook':
      return (
        <ScanPlaybookScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('ai-scans'),
          }}
          route={{
            params: {
              scan: {
                id: '',
                name: '',
                description: '',
                category: '',
                icon: '',
                tags: [],
                isActive: true,
              },
            },
          }}
        />
      );

    case 'trading':
      return <TradingScreen navigateTo={navigateTo} />;

    case 'day-trading':
      return <DayTradingScreen navigateTo={navigateTo} />;

    case 'ml-system':
      return <MLSystemScreen navigateTo={navigateTo} />;

    case 'risk-management':
      return <RiskManagementScreen navigateTo={navigateTo} />;

    case 'swing-trading-test':
      return <SwingTradingDashboard navigateTo={navigateTo} />;

    case 'swing-signals':
      return <SignalsScreen navigateTo={navigateTo} />;

    case 'swing-risk-coach':
      return <RiskCoachScreen navigateTo={navigateTo} />;

    case 'swing-backtesting':
      return <BacktestingScreen navigateTo={navigateTo} />;

    case 'swing-leaderboard':
      return <LeaderboardScreen navigateTo={navigateTo} />;

    case 'notifications':
      return <NotificationsScreen navigateTo={navigateTo} />;

    case 'options-learning':
      return (
        <OptionsLearningScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('home'),
          }}
        />
      );

    case 'sbloc-learning':
      return (
        <SBLOCLearningScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('home'),
          }}
        />
      );

    case 'portfolio-learning':
      return (
        <PortfolioLearningScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('home'),
          }}
        />
      );

    case 'news-preferences':
      return (
        <NewsPreferencesScreen
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('profile'),
          }}
        />
      );

    case 'tax-optimization':
      return <TaxOptimizationScreen />;

    case 'smart-lots':
      return <SmartLotsScreen />;

    case 'borrow-vs-sell':
      return <BorrowVsSellScreen />;

    case 'wash-guard':
      return <WashGuardScreen />;

    case 'tutor-ask-explain':
      return <TutorAskExplainScreen />;

    case 'tutor-quiz':
      return <TutorQuizScreen />;

    case 'tutor-module':
      return <TutorModuleScreen />;

    case 'market-commentary':
      return <MarketCommentaryScreen />;

    case 'daily-voice-digest':
      return <DailyVoiceDigestScreen />;

    case 'notification-center':
      return <NotificationCenterScreen />;

    case 'wealth-circles':
      return (
        <WealthCircles2
          onCirclePress={circle => setCurrentScreen('circle-detail')}
          onCreateCircle={() => logger.log('Create circle')}
          onJoinCircle={circleId => logger.log('Join circle:', circleId)}
        />
      );

    case 'circle-detail':
      return (
        <SimpleCircleDetailScreen
          route={{
            params: {
              circle: {
                id: '1',
                name: 'BIPOC Wealth Builders',
                description:
                  'Building generational wealth through smart investing and community support',
                memberCount: 1247,
                category: 'investment',
              },
            },
          }}
          navigation={{
            navigate: navigateTo,
            goBack: () => setCurrentScreen('wealth-circles'),
          }}
        />
      );

    case 'peer-progress':
      return <PeerProgressScreen />;

    case 'trade-challenges':
      return <TradeChallengesScreen />;

    case 'personalization-dashboard':
      return <PersonalizationDashboardScreen />;

    case 'behavioral-analytics':
      return <BehavioralAnalyticsScreen />;

    case 'dynamic-content':
      return <DynamicContentScreen />;

    case 'trading-coach':
      return <TradingCoachScreen />;

    case 'ai-trading-coach':
      return <AITradingCoachScreen onNavigate={navigateTo} />;

    case 'subscription':
      return <SubscriptionScreen navigateTo={navigateTo} />;

    // Version 2 New Routes
    case 'viral-growth':
      return (
        <ViralGrowthSystem
          onRewardClaimed={reward => {
            logger.log('Reward claimed:', reward);
          }}
          onChallengeJoined={challenge => {
            logger.log('Challenge joined:', challenge);
          }}
        />
      );

    case 'security-fortress':
      return <SecurityFortress onNavigate={navigateTo} />;

    case 'scalability-engine':
      return <ScalabilityEngine onNavigate={navigateTo} />;

    case 'marketing-rocket':
      return <MarketingRocket onNavigate={navigateTo} />;

    case 'oracle-insights':
      return (
        <OracleInsights
          onInsightPress={insight => {
            logger.log('Oracle insight pressed:', insight);
          }}
          onGenerateInsight={() => {
            logger.log('Generate insight requested');
          }}
        />
      );

    case 'voice-ai':
      return (
        <VoiceAIAssistant
          onClose={() => navigateTo('home')}
          onInsightGenerated={insight => {
            logger.log('Insight generated:', insight);
          }}
        />
      );

    case 'blockchain-integration':
      return (
        <BlockchainIntegration
          onPortfolioTokenize={portfolio => {
            logger.log('Portfolio tokenized:', portfolio);
          }}
          onDeFiPositionCreate={position => {
            logger.log('DeFi position created:', position);
          }}
          onGovernanceVote={(proposalId, vote) => {
            logger.log('Governance vote:', proposalId, vote);
          }}
        />
      );

    case 'theme-settings':
      return <ThemeSettingsScreen onClose={() => navigateTo('home')} />;

    case 'connectivity-test':
      return <ConnectivityTestScreen onClose={() => navigateTo('home')} />;

    case 'sentry-test':
      return (
        <View style={{ flex: 1, padding: 20, backgroundColor: '#fff' }}>
          <TouchableOpacity
            onPress={() => navigateTo('home')}
            style={{
              marginBottom: 20,
              padding: 10,
              backgroundColor: '#007AFF',
              borderRadius: 6,
            }}
          >
            <Text style={{ color: '#fff', textAlign: 'center' }}>← Back</Text>
          </TouchableOpacity>
          <SentryTestButton />
        </View>
      );

    default:
      // Handle user-profile and user-portfolios with userId pattern
      if (currentScreen.startsWith('user-profile-')) {
        const userId = currentScreen.replace('user-profile-', '');
        return <UserProfileScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('user-portfolios-')) {
        const userId = currentScreen.replace('user-portfolios-', '');
        return <UserPortfoliosScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('user-activity-')) {
        const userId = currentScreen.replace('user-activity-', '');
        return <UserActivityScreen userId={userId} onNavigate={navigateTo} />;
      }
      if (currentScreen.startsWith('message-user-')) {
        const userId = currentScreen.replace('message-user-', '');
        return <MessageScreen userId={userId} onNavigate={navigateTo} />;
      }
      logger.log('🔍 ⚠️ DEFAULT CASE REACHED - currentScreen:', currentScreen, '- Returning null');
      return null;
  }
}
