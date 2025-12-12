/**
 * Navigation types for the app
 * Centralizes type definitions for navigation-related code
 */

export type ScreenName =
  | 'login'
  | 'signup'
  | 'forgot-password'
  | 'onboarding'
  | 'home'
  | 'profile'
  | 'account-management'
  | 'stock'
  | 'StockDetail'
  | 'crypto'
  | 'ai-portfolio'
  | 'portfolio'
  | 'portfolio-management'
  | 'premium-analytics'
  | 'subscription'
  | 'portfolio-analytics'
  | 'budgeting'
  | 'spending-analysis'
  | 'stock-screening'
  | 'ai-recommendations'
  | 'social'
  | 'learning-paths'
  | 'discover-users'
  | 'user-profile'
  | 'user-portfolios'
  | 'user-activity'
  | 'message-user'
  | 'social-feed'
  | 'ai-options'
  | 'options-copilot'
  | 'tutor'
  | 'scan-playbook'
  | 'ai-scans'
  | 'trading'
  | 'day-trading'
  | 'raha-strategy-store'
  | 'raha-strategy-detail'
  | 'raha-backtest-viewer'
  | 'pro-labs'
  | 'strategy-builder'
  | 'strategy-dashboard'
  | 'ml-training'
  | 'strategy-blend-builder'
  | 'raha-notification-preferences'
  | 'raha-auto-trading-settings'
  | 'order-monitoring-dashboard'
  | 'the-whisper'
  | 'ml-system'
  | 'risk-management'
  | 'swing-trading-test'
  | 'swing-signals'
  | 'swing-risk-coach'
  | 'swing-backtesting'
  | 'swing-leaderboard'
  | 'notifications'
  | 'options-learning'
  | 'sbloc-learning'
  | 'portfolio-learning'
  | 'news-preferences'
  | 'tax-optimization'
  | 'smart-lots'
  | 'borrow-vs-sell'
  | 'wash-guard'
  | 'tutor-ask-explain'
  | 'tutor-quiz'
  | 'tutor-module'
  | 'market-commentary'
  | 'daily-voice-digest'
  | 'notification-center'
  | 'wealth-circles'
  | 'circle-detail'
  | 'peer-progress'
  | 'trade-challenges'
  | 'personalization-dashboard'
  | 'behavioral-analytics'
  | 'dynamic-content'
  | 'trading-coach'
  | 'ai-trading-coach'
  | 'viral-growth'
  | 'security-fortress'
  | 'scalability-engine'
  | 'marketing-rocket'
  | 'oracle-insights'
  | 'voice-ai'
  | 'blockchain-integration'
  | 'theme-settings'
  | 'connectivity-test'
  | 'sentry-test'
  | 'SBLOCBankSelection'
  | 'SBLOCApplication'
  | 'SblocStatus'
  | 'bank-accounts';

export type NavigateParams = Record<string, unknown>;

export interface NavigationService {
  navigateTo: (screen: ScreenName, params?: NavigateParams) => void;
  setCurrentScreen: (screen: ScreenName) => void;
  currentScreen: ScreenName;
  currentScreenParams: NavigateParams;
}

/**
 * Window globals for navigation fallback
 * Used when React Navigation isn't available
 */
export interface WindowNavigationGlobals {
  __navigateToGlobal?: (screen: string, params?: NavigateParams) => void;
  __setCurrentScreen?: (screen: string) => void;
  __currentScreen?: string;
  __currentScreenParams?: NavigateParams;
  __forceNavigateTo?: string;
  __forceNavigateTimestamp?: number;
  __sblocParams?: NavigateParams;
  __stockDetailParams?: NavigateParams;
}

declare global {
  interface Window extends WindowNavigationGlobals {}
}
