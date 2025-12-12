/**
 * RAHAScreenRenderer
 * Handles rendering of RAHA-specific screens (pro-labs, the-whisper, strategy screens)
 */

import React from 'react';
import logger from '../../utils/logger';
import type { ScreenName, NavigateParams, WindowNavigationGlobals } from '../types';

// RAHA screen imports
import ProLabsScreen from '../../features/raha/screens/ProLabsScreen';
import TheWhisperScreen from '../../features/raha/screens/TheWhisperScreen';
import StrategyDetailScreen from '../../features/raha/screens/StrategyDetailScreen';
import StrategyBuilderScreen from '../../features/raha/screens/StrategyBuilderScreen';
import StrategyDashboardScreen from '../../features/raha/screens/StrategyDashboardScreen';
import MLTrainingScreen from '../../features/raha/screens/MLTrainingScreen';
import StrategyBlendBuilderScreen from '../../features/raha/screens/StrategyBlendBuilderScreen';
import NotificationPreferencesScreen from '../../features/raha/screens/NotificationPreferencesScreen';
import AutoTradingSettingsScreen from '../../features/raha/screens/AutoTradingSettingsScreen';
import OrderMonitoringDashboardScreen from '../../features/raha/screens/OrderMonitoringDashboardScreen';

interface RAHAScreenRendererProps {
  currentScreen: ScreenName;
  effectiveScreen: ScreenName;
  currentScreenParams: NavigateParams;
  navigateTo: (screen: ScreenName, params?: NavigateParams) => void;
}

export function RAHAScreenRenderer({
  currentScreen,
  effectiveScreen,
  currentScreenParams,
  navigateTo,
}: RAHAScreenRendererProps): React.ReactElement | null {
  const windowWithNav =
    typeof window !== 'undefined' ? (window as Window & WindowNavigationGlobals) : null;

  switch (effectiveScreen) {
    case 'raha-strategy-store':
      // Moved to Pro/Labs - redirect for backwards compatibility
      return <ProLabsScreen navigateTo={navigateTo} />;

    case 'raha-strategy-detail':
      return (
        <StrategyDetailScreen
          strategyId={currentScreenParams?.strategyId as string | undefined}
          navigateTo={navigateTo}
          onBack={() => {
            if (navigateTo) {
              navigateTo('pro-labs');
            } else if (windowWithNav?.__setCurrentScreen) {
              windowWithNav.__setCurrentScreen('pro-labs');
            }
          }}
        />
      );

    case 'raha-backtest-viewer':
      // Moved to Pro/Labs - redirect for backwards compatibility
      return <ProLabsScreen navigateTo={navigateTo} />;

    case 'pro-labs':
      // Pro/Labs - Advanced RAHA controls (Strategy Store, Backtest Viewer, etc.)
      logger.log('🔍 ✅✅✅ CASE PRO-LABS MATCHED! Rendering ProLabsScreen');
      logger.log('🔍 ProLabsScreen - currentScreen:', currentScreen);
      logger.log('🔍 ProLabsScreen - effectiveScreen:', effectiveScreen);
      logger.log('🔍 ProLabsScreen - navigateTo type:', typeof navigateTo);
      logger.log('🔍 ProLabsScreen - navigateTo exists:', !!navigateTo);
      // Ensure window is updated
      if (windowWithNav) {
        windowWithNav.__currentScreen = 'pro-labs';
      }
      const proLabsComponent = <ProLabsScreen navigateTo={navigateTo} />;
      logger.log('🔍 ProLabsScreen component created successfully');
      return proLabsComponent;

    case 'strategy-builder':
      // Strategy Builder - Create custom trading strategies
      logger.log('🔍 Rendering StrategyBuilderScreen');
      return (
        <StrategyBuilderScreen navigateTo={navigateTo} onBack={() => navigateTo('pro-labs')} />
      );

    case 'strategy-dashboard':
      // Strategy Dashboard - Performance analytics and comparison
      logger.log('🔍 ✅✅✅ CASE STRATEGY-DASHBOARD MATCHED! Rendering StrategyDashboardScreen');
      logger.log('🔍 StrategyDashboardScreen - currentScreen:', currentScreen);
      logger.log('🔍 StrategyDashboardScreen - navigateTo exists:', !!navigateTo);
      const dashboardComponent = (
        <StrategyDashboardScreen navigateTo={navigateTo} onBack={() => navigateTo('pro-labs')} />
      );
      logger.log('🔍 StrategyDashboardScreen component created successfully');
      return dashboardComponent;

    case 'ml-training':
      // ML Model Training - Train custom models on trading history
      logger.log('🔍 Rendering MLTrainingScreen');
      return <MLTrainingScreen navigateTo={navigateTo} onBack={() => navigateTo('pro-labs')} />;

    case 'strategy-blend-builder':
      // Strategy Blend Builder - Combine strategies with custom weights
      logger.log(
        '🔍 ✅✅✅ CASE STRATEGY-BLEND-BUILDER MATCHED! Rendering StrategyBlendBuilderScreen',
      );
      return (
        <StrategyBlendBuilderScreen navigateTo={navigateTo} onBack={() => navigateTo('pro-labs')} />
      );

    case 'raha-notification-preferences':
      // Notification Preferences - Configure push notifications for RAHA
      logger.log('🔍 Rendering NotificationPreferencesScreen');
      return (
        <NotificationPreferencesScreen
          navigateTo={navigateTo}
          onBack={() => navigateTo('pro-labs')}
        />
      );

    case 'raha-auto-trading-settings':
      // Auto-Trading Settings - Configure automatic signal execution
      logger.log('🔍 Rendering AutoTradingSettingsScreen');
      return (
        <AutoTradingSettingsScreen navigateTo={navigateTo} onBack={() => navigateTo('pro-labs')} />
      );

    case 'order-monitoring-dashboard':
      // Order Monitoring Dashboard - Real-time order status and trade history
      logger.log('🔍 Rendering OrderMonitoringDashboardScreen');
      return (
        <OrderMonitoringDashboardScreen
          navigateTo={navigateTo}
          onBack={() => navigateTo('pro-labs')}
        />
      );

    case 'the-whisper':
      // The Whisper - The one magical P&L moment
      // This is accessed from DayTradingScreen when user wants to see their likely outcome
      // Get params from state or window fallback
      const whisperParams = currentScreenParams || windowWithNav?.__currentScreenParams || {};
      // Default to AAPL with realistic mock prices if no params provided
      return (
        <TheWhisperScreen
          symbol={(whisperParams?.symbol as string) || 'AAPL'}
          currentPrice={(whisperParams?.currentPrice as number) || 175.5}
          change={(whisperParams?.change as number) || 2.3}
          changePercent={(whisperParams?.changePercent as number) || 1.33}
        />
      );

    default:
      return null;
  }
}
